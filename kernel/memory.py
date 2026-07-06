"""
Arkadia Knowledge OS — Memory / Context Retrieval (Upgraded)
=============================================================
Phase 8 → Knowledge OS upgrade:
  - Primary: semantic retrieval from SQLite Knowledge Vault (knowledge/context_engine.py)
  - Fallback: keyword-based oracle_store scan (backward-compatible with Phase 8)

The contract (return type) is unchanged so the planner is never broken.
Swap the retrieval strategy here without touching the planner.

LAW IV: Oracle retrieves knowledge. Providers generate language.
"""
from __future__ import annotations

import re
from typing import Any

from kernel import oracle_store

MAX_ITEMS = 5
MAX_KEYWORD_EVENTS = 5
_WORD_RE = re.compile(r"\w{3,}")


def _keywords(text: str) -> set[str]:
    if not isinstance(text, str):
        return set()
    return set(_WORD_RE.findall(text.lower()))


def _summarize_event(evt: dict[str, Any]) -> dict[str, Any]:
    """Strip events down to the fields a planner actually needs."""
    payload = evt.get("payload") or {}
    inner   = payload.get("payload") if isinstance(payload, dict) else None
    return {
        "ts":   evt.get("ts"),
        "kind": payload.get("kind") if isinstance(payload, dict) else None,
        "ref":  inner if isinstance(inner, dict) else None,
    }


def _semantic_context(user_input: str) -> dict[str, Any] | None:
    """
    Attempt semantic retrieval from the Knowledge Vault.
    Returns None if the vault is not yet initialised or unavailable.
    """
    try:
        from knowledge.context_engine import assemble_context, format_context_for_provider
        package = assemble_context(
            query=user_input,
            max_notes=5,
            graph_depth=1,
            include_timeline=True,
            timeline_limit=5,
        )
        formatted = format_context_for_provider(package)
        if not formatted.strip():
            return None
        return {
            "source": "knowledge_vault",
            "relevant_notes": package.get("relevant_notes", []),
            "formatted_context": formatted,
        }
    except Exception:
        return None


def retrieve_context(user_input: str, *, max_items: int = MAX_ITEMS) -> dict[str, Any]:
    """
    Return a structured memory slice for the planner.

    Priority:
    1. Semantic retrieval from Knowledge Vault (if available)
    2. Keyword-based oracle_store scan (backward-compat fallback)

    Never raises — always returns a valid dict.
    """
    # ── 1. Try Knowledge Vault semantic retrieval ─────────────────────────────
    semantic = _semantic_context(user_input)

    # ── 2. Oracle store (always included for backward compat) ─────────────────
    try:
        snap = oracle_store.snapshot()
    except Exception:
        snap = {}

    txns   = snap.get("transactions") or []
    loops  = snap.get("open_loops") or []
    events = snap.get("events") or []

    recent_txns = list(reversed(txns[-max_items:])) if txns else []
    open_loops  = [l for l in loops if (l.get("status") or "open") == "open"][-max_items:]

    kws = _keywords(user_input)
    relevant_events: list[dict[str, Any]] = []
    if kws and events:
        for evt in reversed(events):
            haystack = " ".join(
                str(v) for v in (
                    (evt.get("payload") or {}).get("kind"),
                    (evt.get("payload") or {}).get("payload"),
                ) if v is not None
            ).lower()
            if any(kw in haystack for kw in kws):
                relevant_events.append(_summarize_event(evt))
                if len(relevant_events) >= MAX_KEYWORD_EVENTS:
                    break

    result: dict[str, Any] = {
        "balance":             snap.get("balance") or {},
        "recent_transactions": recent_txns,
        "open_loops":          open_loops,
        "relevant_events":     relevant_events,
    }

    # Attach semantic context if available
    if semantic:
        result["knowledge_vault"] = semantic

    return result


def has_signal(context: dict[str, Any]) -> bool:
    """True if the context has anything worth showing the planner."""
    if not isinstance(context, dict):
        return False
    return bool(
        context.get("balance")
        or context.get("recent_transactions")
        or context.get("open_loops")
        or context.get("relevant_events")
        or context.get("knowledge_vault")
    )


__all__ = ["retrieve_context", "has_signal", "MAX_ITEMS"]
