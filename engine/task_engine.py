"""SolSpire Phase 3 — Task Engine.

Sits ABOVE the Phase 2 router. Converts a raw user message into a
structured task plan, then executes it sequentially with retries,
fallbacks, and per-task state tracking.

Output envelope (matches the scroll spec):
    {
      "plan_id": "...",
      "goal":    "...",
      "tasks":   [TaskState, ...],
      "execution": {"mode": "sequential", "retry": true},
      "autonomy_level": 3,
      "requires_confirmation": bool,
      "safety_triggers": [...],
    }

A TaskState entry is:
    {
      "task_id": "...",
      "step":    "...",
      "tool":    "...",
      "input":   {...},
      "expected_output": "...",
      "status":  "pending | running | complete | failed | skipped",
      "results": {...} | null,
      "history": [{at, event}, ...],
    }
"""
from __future__ import annotations

import logging
import time
from typing import Any

from app.router import execute_task as execute_phase2_task
from engine import safety, state
from parsers.intent_parser import parse_intent
from solspire import oracle
from solspire.registry import TASK_TO_TOOL, get_tool

logger = logging.getLogger("solspire.engine")

# Default autonomy. The scroll's Phase 3 target is Level 3 (autonomous
# multi-step execution). Risky tasks downgrade to Level 2 via safety gate.
DEFAULT_AUTONOMY_LEVEL = 3
MAX_RETRIES = 1


def _short_goal(message: str) -> str:
    """Trim a one-line goal summary from the raw message."""
    s = " ".join(message.split())
    return s if len(s) <= 140 else s[:137] + "..."


def _expected_output(task_type: str, params: dict[str, Any]) -> str:
    if task_type == "text_generate":
        return "A 4-line shaped Arkadia verse."
    if task_type == "compress":
        return "Symbolic-token compressed text."
    if task_type == "image_generate":
        n = params.get("count", 1)
        return f"{n} image descriptor(s)."
    if task_type == "oracle_update":
        return "Oracle state updated and snapshot returned."
    if task_type == "query":
        return "Oracle data subset for the requested keys."
    return "LLM-generated free-form response."


def _step_description(task_type: str, params: dict[str, Any]) -> str:
    if task_type == "image_generate":
        return f"Generate {params.get('count', 1)} image(s)"
    if task_type == "oracle_update":
        if params:
            kvs = ", ".join(f"{k}={v}" for k, v in params.items())
            return f"Log to Oracle: {kvs}"
        return "Log to Oracle"
    if task_type == "query":
        keys = params.get("keys") or []
        return f"Query Oracle: {', '.join(keys) if keys else 'snapshot'}"
    if task_type == "compress":
        return "Compress text via Arkadia lexicon"
    if task_type == "text_generate":
        return "Generate Arkadia verse"
    return "LLM fallback"


# ── Planning ────────────────────────────────────────────────────────────────

def plan(message: str, autonomy_level: int = DEFAULT_AUTONOMY_LEVEL) -> dict[str, Any]:
    """STEP 1-3: extract intent → decompose → map tools → emit plan envelope."""
    intent = parse_intent(message)
    parser_tasks = intent.get("tasks") or []

    tasks: list[dict[str, Any]] = []
    safety_triggers: list[str] = []

    for idx, ptask in enumerate(parser_tasks):
        ttype = ptask.get("type", "llm_fallback")
        params = ptask.get("parameters") or {}
        tool_name = TASK_TO_TOOL.get(ttype, "gemini_chat")
        tool_def = get_tool(tool_name) or {}

        task_state = {
            "task_id":         state.new_task_id(idx),
            "step":            _step_description(ttype, params),
            "tool":            tool_name,
            "task_type":       ttype,
            "input":           dict(params),
            "expected_output": _expected_output(ttype, params),
            "tool_purpose":    tool_def.get("purpose", ""),
            "status":          "pending",
            "results":         None,
            "history":         [],
        }
        triggers = safety.task_is_sensitive(task_state)
        if triggers:
            task_state["safety_triggers"] = triggers
            safety_triggers.extend(t for t in triggers if t not in safety_triggers)
        tasks.append(task_state)

    plan_envelope = {
        "plan_id":               state.new_plan_id(),
        "goal":                  _short_goal(message),
        "raw_message":           message,
        "intent_type":           intent.get("type", "unknown"),
        "intent_confidence":     intent.get("confidence", 0.0),
        "intent_source":         intent.get("source", "rules"),
        "tasks":                 tasks,
        "execution": {
            "mode":        "sequential",
            "retry":       True,
            "max_retries": MAX_RETRIES,
        },
        "autonomy_level":        autonomy_level,
        "requires_confirmation": bool(safety_triggers),
        "safety_triggers":       safety_triggers,
        "status":                "planned",
    }
    return state.save_plan(plan_envelope)


# ── Execution ───────────────────────────────────────────────────────────────

def _to_phase2_task(task: dict[str, Any]) -> dict[str, Any]:
    """Convert an engine TaskState back into the parser-shape the
    Phase 2 router executor understands.
    """
    return {
        "type":       task.get("task_type", "llm_fallback"),
        "parameters": dict(task.get("input") or {}),
    }


def _run_one(task: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    """Run a task once. Returns (ok, result-or-error)."""
    try:
        result = execute_phase2_task(_to_phase2_task(task))
        return True, result
    except Exception as e:  # noqa: BLE001
        logger.warning("task %s failed: %s", task.get("task_id"), e)
        return False, {"error": str(e)}


def execute(plan_id: str, confirmed: bool = False) -> dict[str, Any]:
    """STEP 4 + execution loop. Run every task in the plan with retries.

    Honors the safety gate: if the plan needs confirmation and `confirmed`
    is False, no tasks run — they are marked `skipped` and the envelope
    surfaces the reason.
    """
    p = state.get_plan(plan_id)
    if p is None:
        return {"error": f"unknown plan_id: {plan_id}"}

    # Safety gate
    if p.get("requires_confirmation") and not confirmed:
        for task in p["tasks"]:
            if task["status"] == "pending":
                state.update_task(
                    plan_id, task["task_id"],
                    status="skipped",
                    event={"kind": "safety_skip",
                           "triggers": p.get("safety_triggers", [])},
                )
        p["status"] = "awaiting_confirmation"
        p["state_snapshot"] = oracle.snapshot()
        return p

    p["status"] = "running"
    p["started_at"] = time.time()
    max_retries = int(p.get("execution", {}).get("max_retries", MAX_RETRIES))
    retry_enabled = bool(p.get("execution", {}).get("retry", True))

    for task in p["tasks"]:
        if task["status"] != "pending":
            continue

        state.update_task(plan_id, task["task_id"], status="running",
                          event={"kind": "start"})

        ok, result = _run_one(task)
        attempts = 1

        # Retry once if enabled
        while not ok and retry_enabled and attempts <= max_retries:
            state.update_task(plan_id, task["task_id"],
                              event={"kind": "retry", "attempt": attempts,
                                     "error": result.get("error")})
            ok, result = _run_one(task)
            attempts += 1

        # Fallback to llm if still failing
        if not ok:
            state.update_task(plan_id, task["task_id"],
                              event={"kind": "fallback_to_llm",
                                     "error": result.get("error")})
            fallback_task = {
                "type": "llm_fallback",
                "parameters": {
                    "prompt": f"The tool '{task.get('tool')}' failed. "
                              f"Goal: {p['goal']}. "
                              f"Step: {task.get('step')}. "
                              f"Produce a graceful textual response.",
                },
            }
            try:
                result = execute_phase2_task(fallback_task)
                ok = True
            except Exception as e:  # noqa: BLE001
                result = {"error": str(e)}

        if ok:
            state.update_task(plan_id, task["task_id"],
                              status="complete", results=result,
                              event={"kind": "complete",
                                     "attempts": attempts})
        else:
            state.update_task(plan_id, task["task_id"],
                              status="failed", results=result,
                              event={"kind": "failed",
                                     "attempts": attempts,
                                     "error": result.get("error")})

    p["status"] = "complete" if all(
        t["status"] == "complete" for t in p["tasks"]
    ) else "partial"
    p["finished_at"] = time.time()
    p["state_snapshot"] = oracle.snapshot()
    return p


def run(message: str, confirmed: bool = False,
        autonomy_level: int = DEFAULT_AUTONOMY_LEVEL) -> dict[str, Any]:
    """Convenience: plan + execute in one call."""
    p = plan(message, autonomy_level=autonomy_level)
    return execute(p["plan_id"], confirmed=confirmed)


__all__ = ["plan", "execute", "run", "DEFAULT_AUTONOMY_LEVEL"]
