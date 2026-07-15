"""SolSpire — Routing Engine.

Classifies an incoming message into ONE of:
    A. Conversational / Reasoning   → gemini
    B. Deterministic Creative       → arkadia
    C. Memory Query                 → oracle
    D. Command Execution            → arkadia / image / etc.
    E. Hybrid                       → multiple tools in sequence

Output envelope (matches the spec exactly):
    {
      "route":   "gemini | arkadia | oracle | hybrid",
      "actions": [{"tool": "...", "purpose": "..."}],
      "response_strategy": "..."
    }

Built on top of `parse_intent` so it inherits the same clause-splitter,
keyword triggers, and LLM fallback. No new agent frameworks.
"""
from __future__ import annotations

from typing import Any

from parsers.intent_parser import parse_intent
from solspire.registry import TASK_TO_TOOL, get_tool


# Which Phase 2 task types belong to which routing category.
_ROUTE_OF_TASK = {
    "text_generate":  "arkadia",   # B / D — deterministic creative
    "compress":       "arkadia",   # B
    "image_generate": "arkadia",   # D — command execution via tool
    "oracle_update":  "oracle",    # C
    "query":          "oracle",    # C
    "llm_fallback":   "gemini",    # A
}

_STRATEGY = {
    "arkadia": "Use the Arkadia engine — output structure matters more than adaptation.",
    "gemini":  "Use Gemini — reasoning or natural-language adaptation is required.",
    "oracle":  "Read or write Oracle state — context/memory is the primary need.",
    "hybrid":  "Orchestrate tools in sequence — fan out tasks, then compose results.",
    "unknown": "No confident classification — fall through to Gemini for clarification.",
}


def classify(message: str) -> dict[str, Any]:
    """Return the routing envelope for a single raw message."""
    intent = parse_intent(message)
    tasks = intent.get("tasks") or []

    actions: list[dict[str, str]] = []
    routes_seen: list[str] = []

    for task in tasks:
        ttype = task.get("type", "llm_fallback")
        tool_name = TASK_TO_TOOL.get(ttype, "gemini_chat")
        tool_def = get_tool(tool_name) or {}
        purpose = tool_def.get("purpose", f"Handle task '{ttype}'.")
        actions.append({"tool": tool_name, "purpose": purpose})

        r = _ROUTE_OF_TASK.get(ttype, "gemini")
        if r not in routes_seen:
            routes_seen.append(r)

    if not routes_seen:
        route = "unknown"
    elif len(routes_seen) > 1:
        route = "hybrid"
    else:
        route = routes_seen[0]

    return {
        "route":             route,
        "actions":           actions,
        "response_strategy": _STRATEGY.get(route, _STRATEGY["unknown"]),
        "intent":            intent,
    }


__all__ = ["classify"]
