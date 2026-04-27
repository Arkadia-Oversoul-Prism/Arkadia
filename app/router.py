"""SolSpire Phase 2 — clean execution layer.

route_request(message) → parse_intent → execute each task → update Oracle
state → return {intent, results, state_snapshot}.

No autonomy, no loops, no async. The router is a flat compiler pass.
"""
from __future__ import annotations

from typing import Any

from api import arkadia_engine as arkadia
from parsers.intent_parser import parse_intent
from solspire import image, llm, oracle


def execute_task(task: dict[str, Any]) -> dict[str, Any]:
    """Dispatch a single normalized task to its tool.

    Strict match — anything unknown collapses to the LLM fallback.
    """
    ttype = task.get("type", "llm_fallback")
    params = task.get("parameters") or {}

    match ttype:
        case "text_generate":
            verse = arkadia.generate_verse()
            return {
                "task":   "text_generate",
                "tool":   "arkadia",
                "verse":  verse,
                "lines":  verse.split("\n"),
            }

        case "compress":
            text = params.get("text", "")
            if not text:
                # Generate one and compress it so the route is observable
                # even when the user said only "compress text".
                text = arkadia.generate_verse()
            return {
                "task":       "compress",
                "tool":       "arkadia",
                "original":   text,
                "compressed": arkadia.compress(text),
            }

        case "image_generate":
            count = params.get("count", 1)
            return {"task": "image_generate", **image.generate_images(count)}

        case "oracle_update":
            result = oracle.update_data(params)
            return {"task": "oracle_update", "tool": "oracle", **result}

        case "query":
            result = oracle.query_data(params)
            return {"task": "query", "tool": "oracle", "data": result}

        case _:
            return {"task": "llm_fallback", **llm.call_llm(task)}


def update_state(intent: dict[str, Any], results: list[dict[str, Any]]) -> None:
    """Reserved hook for cross-task state effects. Kept as a no-op in Phase 2
    because oracle_update tasks already mutate the Oracle directly.
    Phase 3 (Postgres + replay log) will wire here.
    """
    return None


def route_request(message: str) -> dict[str, Any]:
    """Top-level entry: language → executed plan."""
    intent = parse_intent(message)

    results: list[dict[str, Any]] = []
    for task in intent["tasks"]:
        results.append(execute_task(task))

    update_state(intent, results)

    return {
        "intent":         intent,
        "results":        results,
        "state_snapshot": oracle.snapshot(),
    }


__all__ = ["route_request", "execute_task", "update_state"]
