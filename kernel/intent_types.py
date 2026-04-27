"""SolSpire Phase 4 — strict intent contract for the Execution Kernel.

Phase 4 deliberately narrows the intent surface to FOUR canonical types.
Anything outside this set falls through to the existing Arkana / Gemini
response path — Phase 4 does not try to handle every possible message,
only the ones it can complete deterministically end-to-end.
"""
from __future__ import annotations

from typing import Any

ALLOWED_TYPES = {
    "generate_images",
    "log_transaction",
    "update_open_loops",
    "generate_verse",
    # Phase 7 — meta-intent that delegates to the LLM planner + chain
    # executor. Payload shape: {"input": "raw user text"} OR
    # {"plan": {"steps": [...]}} for a pre-built plan.
    "__plan__",
}

ALLOWED_SOURCES = {"telegram", "web", "api", "internal"}


def empty_intent(source: str = "api") -> dict[str, Any]:
    return {
        "type":    None,
        "payload": {},
        "source":  source if source in ALLOWED_SOURCES else "api",
    }


def normalize(intent: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(intent, dict):
        return empty_intent()
    itype = intent.get("type")
    if itype not in ALLOWED_TYPES:
        itype = None
    payload = intent.get("payload")
    if not isinstance(payload, dict):
        payload = {}
    source = intent.get("source", "api")
    if source not in ALLOWED_SOURCES:
        source = "api"
    return {"type": itype, "payload": payload, "source": source}


__all__ = ["ALLOWED_TYPES", "ALLOWED_SOURCES", "empty_intent", "normalize"]
