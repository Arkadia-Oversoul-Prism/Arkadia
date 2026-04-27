"""SolSpire LLM fallback.

Used in two places:
  1. Intent parsing — when rule confidence is too low (intent_parser).
  2. Task execution — when a task slips through as `llm_fallback`.

Uses Gemini (`google-generativeai`) when GOOGLE_API_KEY is set. Otherwise
returns a transparent stub so the router never crashes.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

logger = logging.getLogger("solspire.llm")

_MODEL_NAME = os.environ.get("SOLSPIRE_LLM_MODEL", "gemini-1.5-flash")

try:
    import google.generativeai as genai  # type: ignore
    _HAS_GENAI = True
except Exception:
    genai = None  # type: ignore
    _HAS_GENAI = False


def _client():
    """Lazily configure and return a Gemini model, or None if unavailable."""
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not (_HAS_GENAI and api_key):
        return None
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(_MODEL_NAME)
    except Exception as e:
        logger.warning("solspire.llm: configure failed: %s", e)
        return None


def _extract_json(text: str) -> dict[str, Any] | None:
    """Pull the first {...} JSON object out of an LLM response."""
    if not isinstance(text, str):
        return None
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fence.group(1) if fence else None
    if not candidate:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        candidate = m.group(0) if m else None
    if not candidate:
        return None
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def parse_intent_via_llm(message: str, schema_hint: dict) -> dict[str, Any] | None:
    """Ask the LLM to emit a structured intent. Returns None on any failure."""
    model = _client()
    if model is None:
        return None

    prompt = (
        "Extract structured intent from the user message.\n"
        "Return JSON ONLY in this schema:\n"
        f"{json.dumps(schema_hint, indent=2)}\n\n"
        "Allowed task.type values: text_generate, image_generate, compress, "
        "oracle_update, query, llm_fallback.\n"
        "Allowed top-level type values: generate, compress, query, execute, "
        "multi_task, unknown.\n"
        "Use 'multi_task' when there is more than one task. Set 'source' to 'llm'.\n\n"
        f"Message:\n{message}\n"
    )
    try:
        resp = model.generate_content(prompt)
        return _extract_json(getattr(resp, "text", "") or "")
    except Exception as e:
        logger.warning("solspire.llm: parse_intent_via_llm failed: %s", e)
        return None


def call_llm(task: dict[str, Any]) -> dict[str, Any]:
    """Execute a task that fell through to the LLM.

    Returns a transparent envelope so callers can see the model used.
    """
    params = task.get("parameters") or {}
    prompt = params.get("prompt") or task.get("raw") or ""
    model = _client()
    if model is None:
        return {
            "tool":   "llm",
            "status": "stub",
            "model":  _MODEL_NAME,
            "reason": "GOOGLE_API_KEY not set or google-generativeai unavailable",
            "echo":   prompt,
        }
    try:
        resp = model.generate_content(prompt or json.dumps(task))
        return {
            "tool":   "llm",
            "status": "ok",
            "model":  _MODEL_NAME,
            "text":   getattr(resp, "text", "") or "",
        }
    except Exception as e:
        logger.warning("solspire.llm: call_llm failed: %s", e)
        return {"tool": "llm", "status": "error", "model": _MODEL_NAME, "error": str(e)}


__all__ = ["parse_intent_via_llm", "call_llm"]
