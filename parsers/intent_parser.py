"""SolSpire Phase 2 — hybrid intent parser.

Pipeline:
  1. RULES (fast path, no LLM) split the message into clauses, score each one
     against deterministic trigger sets, and emit task entries.
  2. CONFIDENCE scoring decides whether the rules result is trustworthy.
  3. LLM FALLBACK is invoked only if the rules path is ambiguous AND a model
     is available.
  4. NORMALIZATION coerces the final dict into the strict intent schema.

No agent frameworks. No async. No memory. Just a deterministic compiler with
LLM assistance at the edges.
"""
from __future__ import annotations

import re
from typing import Any

from schemas.intent_schema import (
    INTENT_SCHEMA,
    empty_intent,
    normalize_intent,
)
from solspire import llm as llm_mod


# ── Trigger vocabulary ──────────────────────────────────────────────────────
# Keep these surfaces tiny and unambiguous. Multi-word phrases checked first.
TRIGGERS: dict[str, list[str]] = {
    "image_generate": ["image", "images", "draw", "visual", "picture", "render"],
    "oracle_update":  ["log", "update", "store", "record", "save"],
    "compress":       ["compress", "encode"],
    "query":          ["query", "fetch", "lookup", "list", "show"],
    "text_generate":  ["generate", "write", "verse", "compose", "poem"],
}

# Connectors that split a single message into multiple task clauses.
_SPLIT_RE = re.compile(r"\s*(?:,|;|\band\b|\bthen\b|\b&\b|\+)\s*", re.IGNORECASE)

# A simple `key 123` / `123 key` extractor for oracle_update parameters.
_NUM_BEFORE_NOUN = re.compile(r"(\d+)\s+([a-z][a-z_\-]*)", re.IGNORECASE)
_NUM_AFTER_NOUN  = re.compile(r"([a-z][a-z_\-]*)\s*[:=]\s*(\d+)", re.IGNORECASE)

# Stop-words that should never be stored as Oracle keys.
_STOP_KEYS = {
    "log", "logs", "update", "updates", "store", "stored", "record", "save",
    "image", "images", "picture", "pictures", "visual", "visuals",
    "and", "then", "the", "a", "an", "of", "to", "for",
    "compress", "generate", "write", "verse", "poem", "draw", "render",
    "items", "item", "things", "thing", "data", "entries", "entry",
}


# ── Clause-level rule scoring ───────────────────────────────────────────────

def _detect_task(clause: str) -> tuple[str | None, int]:
    """Return (task_type, hits) for a single clause.

    Order matters — image wins over the bare `generate` verb so that
    "generate 3 images" routes to image_generate, not text_generate.
    """
    lc = clause.lower()
    tokens = set(re.findall(r"[a-z]+", lc))

    hits_by_type: dict[str, int] = {}
    for ttype, keywords in TRIGGERS.items():
        h = sum(1 for kw in keywords if kw in tokens)
        if h:
            hits_by_type[ttype] = h

    if not hits_by_type:
        return None, 0

    # Disambiguation: if both image and text triggers fired, prefer image.
    if "image_generate" in hits_by_type and "text_generate" in hits_by_type:
        hits_by_type.pop("text_generate", None)

    # Disambiguation: if oracle_update fires, it dominates the verb 'generate'
    # ("log 100 livestock" should not be classified as text_generate).
    if "oracle_update" in hits_by_type and "text_generate" in hits_by_type:
        hits_by_type.pop("text_generate", None)

    # Pick the type with the most hits (stable on insertion order on ties).
    best_type = max(hits_by_type, key=lambda k: hits_by_type[k])
    return best_type, hits_by_type[best_type]


def _extract_image_count(clause: str) -> int:
    """Find a leading integer count for image generation. Defaults to 1."""
    m = re.search(r"(\d+)", clause)
    if m:
        try:
            n = int(m.group(1))
            return max(1, n)
        except ValueError:
            pass
    return 1


def _extract_oracle_params(clause: str) -> dict[str, Any]:
    """Pull `noun: number` pairs out of a clause for Oracle updates."""
    params: dict[str, Any] = {}

    for num, noun in _NUM_BEFORE_NOUN.findall(clause):
        key = noun.strip().lower()
        if key in _STOP_KEYS:
            continue
        try:
            params[key] = int(num)
        except ValueError:
            continue

    for noun, num in _NUM_AFTER_NOUN.findall(clause):
        key = noun.strip().lower()
        if key in _STOP_KEYS:
            continue
        try:
            params[key] = int(num)
        except ValueError:
            continue

    return params


def _extract_query_params(clause: str) -> dict[str, Any]:
    """Identify candidate keys after a query verb."""
    lc = clause.lower()
    keys = []
    for tok in re.findall(r"[a-z][a-z_\-]+", lc):
        if tok in TRIGGERS["query"] or tok in _STOP_KEYS:
            continue
        keys.append(tok)
    return {"keys": keys[:8]} if keys else {}


def _build_task(clause: str, ttype: str) -> dict[str, Any]:
    if ttype == "image_generate":
        return {"type": ttype, "parameters": {"count": _extract_image_count(clause)}}
    if ttype == "oracle_update":
        return {"type": ttype, "parameters": _extract_oracle_params(clause)}
    if ttype == "query":
        return {"type": ttype, "parameters": _extract_query_params(clause)}
    if ttype in ("compress", "text_generate"):
        return {"type": ttype, "parameters": {}}
    return {"type": "llm_fallback", "parameters": {"prompt": clause.strip()}}


# ── Rule-based parse ────────────────────────────────────────────────────────

def _parse_with_rules(message: str) -> dict[str, Any]:
    """Pure-rules parse. Always returns a normalized intent envelope."""
    clauses = [c.strip() for c in _SPLIT_RE.split(message) if c and c.strip()]
    if not clauses:
        clauses = [message.strip()]

    tasks: list[dict[str, Any]] = []
    total_hits = 0
    matched_clauses = 0

    for clause in clauses:
        ttype, hits = _detect_task(clause)
        if ttype is None:
            continue
        tasks.append(_build_task(clause, ttype))
        total_hits += hits
        matched_clauses += 1

    if not tasks:
        return normalize_intent(
            {
                "type":        "unknown",
                "confidence":  0.0,
                "tasks":       [],
                "raw_message": message,
                "source":      "rules",
            },
            raw_message=message,
        )

    # Confidence = matched clauses divided by total clauses, with a small
    # bonus for total keyword density. Clamped in normalize_intent.
    base = matched_clauses / max(1, len(clauses))
    density_bonus = min(0.25, 0.05 * total_hits)
    confidence = round(base + density_bonus, 3)

    if len(tasks) > 1:
        top_type = "multi_task"
    else:
        only = tasks[0]["type"]
        top_type = {
            "text_generate":  "generate",
            "image_generate": "generate",
            "oracle_update":  "execute",
            "compress":       "compress",
            "query":          "query",
            "llm_fallback":   "unknown",
        }.get(only, "unknown")

    return normalize_intent(
        {
            "type":        top_type,
            "confidence":  confidence,
            "tasks":       tasks,
            "raw_message": message,
            "source":      "rules",
        },
        raw_message=message,
    )


# ── Public entry point ─────────────────────────────────────────────────────

CONFIDENCE_THRESHOLD = 0.75


def parse_intent(message: str) -> dict[str, Any]:
    """Hybrid parse: rules first, LLM fallback only if confidence is low.

    Always returns a schema-compliant intent dict.
    """
    if not isinstance(message, str) or not message.strip():
        return empty_intent(raw_message=str(message or ""))

    rules_intent = _parse_with_rules(message)

    # Rule 2: structure output immediately if confident.
    if rules_intent["confidence"] >= CONFIDENCE_THRESHOLD and rules_intent["tasks"]:
        return rules_intent

    # Rule 3: LLM fallback only if rules are ambiguous.
    llm_intent = llm_mod.parse_intent_via_llm(message, INTENT_SCHEMA)
    if llm_intent:
        normalized = normalize_intent(llm_intent, raw_message=message)
        normalized["source"] = "llm"
        if normalized["tasks"]:
            return normalized

    # No tasks at all — surface a single llm_fallback task so the router
    # can still attempt something. Keep source honest as 'rules'.
    if not rules_intent["tasks"]:
        rules_intent["tasks"] = [
            {"type": "llm_fallback", "parameters": {"prompt": message.strip()}}
        ]
    return rules_intent


__all__ = ["parse_intent", "CONFIDENCE_THRESHOLD", "TRIGGERS"]
