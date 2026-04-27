"""SolSpire Phase 2 — strict intent contract.

Every intent that flows from parser → router conforms to this shape.
Keep this module tiny: it is the wire between language and execution.
"""
from __future__ import annotations

from typing import Any

ALLOWED_INTENT_TYPES = {
    "generate",
    "compress",
    "query",
    "execute",
    "multi_task",
    "unknown",
}

ALLOWED_TASK_TYPES = {
    "text_generate",
    "image_generate",
    "compress",
    "oracle_update",
    "query",
    "llm_fallback",
}

ALLOWED_SOURCES = {"rules", "llm"}


INTENT_SCHEMA = {
    "type":         "generate | compress | query | execute | multi_task | unknown",
    "confidence":   "float",
    "tasks": [
        {
            "type":       "text_generate | image_generate | compress | "
                          "oracle_update | query | llm_fallback",
            "parameters": "dict",
        }
    ],
    "raw_message":  "str",
    "source":       "rules | llm",
}


def empty_intent(raw_message: str = "", source: str = "rules") -> dict[str, Any]:
    """Construct a baseline intent envelope with safe defaults."""
    return {
        "type":        "unknown",
        "confidence":  0.0,
        "tasks":       [],
        "raw_message": raw_message,
        "source":      source if source in ALLOWED_SOURCES else "rules",
    }


def normalize_intent(intent: dict[str, Any], raw_message: str = "") -> dict[str, Any]:
    """Coerce any dict into a schema-compliant intent envelope.

    Rule 4 from the Phase 2 spec:
      - lowercase intent / task types
      - tasks is always a list
      - parameters is always a dict (never None)
      - clamp confidence into [0.0, 1.0]
      - source restricted to {"rules", "llm"}
    """
    if not isinstance(intent, dict):
        return empty_intent(raw_message=raw_message)

    out = empty_intent(
        raw_message=raw_message or str(intent.get("raw_message", "") or ""),
        source=str(intent.get("source", "rules") or "rules").lower(),
    )

    itype = str(intent.get("type", "unknown") or "unknown").lower()
    out["type"] = itype if itype in ALLOWED_INTENT_TYPES else "unknown"

    try:
        conf = float(intent.get("confidence", 0.0))
    except (TypeError, ValueError):
        conf = 0.0
    out["confidence"] = max(0.0, min(1.0, conf))

    raw_tasks = intent.get("tasks") or []
    if not isinstance(raw_tasks, list):
        raw_tasks = []

    cleaned_tasks: list[dict[str, Any]] = []
    for task in raw_tasks:
        if not isinstance(task, dict):
            continue
        ttype = str(task.get("type", "llm_fallback") or "llm_fallback").lower()
        if ttype not in ALLOWED_TASK_TYPES:
            ttype = "llm_fallback"
        params = task.get("parameters")
        if not isinstance(params, dict):
            params = {}
        cleaned_tasks.append({"type": ttype, "parameters": params})

    out["tasks"] = cleaned_tasks
    return out


__all__ = [
    "INTENT_SCHEMA",
    "ALLOWED_INTENT_TYPES",
    "ALLOWED_TASK_TYPES",
    "ALLOWED_SOURCES",
    "empty_intent",
    "normalize_intent",
]
