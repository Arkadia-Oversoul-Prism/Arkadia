"""GATE L1 — the native agent loop.

Turns the Engineering Lab substrate into an actual agent runtime:

    MODEL -> decision -> TOOL CALL -> observation -> MODEL -> ... -> TERMINAL

The loop is deliberately bounded and non-mutating. It reasons through multiple
tool turns inside the existing sandbox, emits inspectable AgentEvents onto the
existing live stream, and terminates on exactly one of:

    DONE | BLOCKED | ERROR | HUMAN_AUTHORIZATION_REQUIRED

It never edits the repository and never authorizes. Mutation crosses the
PassSpec -> K15 -> K3 boundary in GATE L2, not here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .contracts import utc_now
from .gateway import ModelGateway, ModelUnavailable
from .tools import ToolRegistry


#: Terminal states the loop may stop on. No state implies a later one.
TERMINAL_STATES: tuple[str, ...] = (
    "DONE",
    "BLOCKED",
    "ERROR",
    "HUMAN_AUTHORIZATION_REQUIRED",
)


@dataclass
class AgentTurn:
    """One model turn + the resulting tool observation, for inspection."""

    turn_index: int
    text: str
    tool_name: str | None
    tool_arguments: dict[str, Any]
    observation: dict[str, Any] | None
    decision: str
    timestamp_utc: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_index": self.turn_index,
            "text": self.text,
            "tool_name": self.tool_name,
            "tool_arguments": self.tool_arguments,
            "observation": self.observation,
            "decision": self.decision,
            "timestamp_utc": self.timestamp_utc,
        }


@dataclass
class LoopResult:
    """The inspectable outcome of a bounded agent loop."""

    state: str
    turns: list[AgentTurn]
    reason: str = ""
    model_selection: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "reason": self.reason,
            "turn_count": len(self.turns),
            "turns": [t.to_dict() for t in self.turns],
            "model_selection": self.model_selection,
        }


class AgentLoop:
    """A bounded model->tool->observation loop over one sandbox + tool set."""

    def __init__(
        self,
        *,
        gateway: ModelGateway,
        tools: ToolRegistry,
        provider: str,
        model: str,
        max_turns: int = 8,
    ) -> None:
        self._gateway = gateway
        self._tools = tools
        self._provider = provider
        self._model = model
        self._max_turns = max_turns

    def run(
        self,
        *,
        objective: str,
        system_prompt: str = "",
        on_event: Any | None = None,
    ) -> LoopResult:
        """Run the loop to a terminal state.

        ``on_event(event_type, payload)`` — when provided — is called for every
        model turn, tool intent, and observation so the caller can stream them
        onto the Lab event stream. The loop itself holds no transport concern.
        """
        def emit(event_type: str, payload: dict[str, Any]) -> None:
            if on_event is not None:
                on_event(event_type, payload)

        messages: list[dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": objective})

        tool_specs = self._tools.available()
        turns: list[AgentTurn] = []

        for turn_index in range(1, self._max_turns + 1):
            try:
                response = self._gateway.generate(
                    provider=self._provider,
                    model=self._model,
                    messages=messages,
                    tools=tool_specs or None,
                )
            except ModelUnavailable as exc:
                emit("BLOCKED", {"reason": "model_unavailable", "detail": str(exc)})
                return LoopResult(state="BLOCKED", turns=turns, reason=str(exc))
            except Exception as exc:  # provider raised mid-call
                emit("ERROR", {"reason": "model_error", "detail": str(exc)})
                return LoopResult(state="ERROR", turns=turns, reason=str(exc))

            emit("MODEL_TURN", {"turn_index": turn_index, "text": response.text,
                                "tool_calls": len(response.tool_calls)})

            if not response.tool_calls:
                # No tool intent => the model is finished reasoning.
                turn = AgentTurn(turn_index, response.text, None, {}, None, "DONE")
                turns.append(turn)
                emit("AGENT_DECISION", {"turn_index": turn_index, "decision": "DONE"})
                return LoopResult(state="DONE", turns=turns)

            call = response.tool_calls[0]
            name = call.get("name", "")
            arguments = call.get("arguments") or {}
            if isinstance(arguments, str):
                # Some providers return JSON-encoded arguments.
                import json

                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}
            emit("TOOL_INTENT", {"turn_index": turn_index, "tool": name,
                                 "arguments": arguments})

            observation = self._tools.invoke(name, arguments)
            emit("TOOL_OBSERVATION", {"turn_index": turn_index, "tool": name,
                                      "ok": observation.get("ok", False)})

            decision = "CONTINUE" if observation.get("ok") else "TOOL_FAILED"
            turn = AgentTurn(turn_index, response.text, name, arguments, observation, decision)
            turns.append(turn)
            emit("AGENT_DECISION", {"turn_index": turn_index, "decision": decision})

            # Feed the observation back to the model for the next turn.
            messages.append({"role": "assistant", "content": response.text})
            messages.append({
                "role": "tool",
                "content": _observation_text(observation),
                "tool_name": name,
            })

        emit("HUMAN_AUTHORIZATION_REQUIRED",
             {"reason": "turn_budget_exhausted", "max_turns": self._max_turns})
        return LoopResult(
            state="HUMAN_AUTHORIZATION_REQUIRED",
            turns=turns,
            reason=f"turn budget exhausted after {self._max_turns} turns",
        )


def _observation_text(observation: dict[str, Any]) -> str:
    import json

    try:
        return json.dumps(observation)[:4000]
    except (TypeError, ValueError):
        return str(observation)[:4000]
