"""SolSpire Phase 8 — Memory / Context Retrieval.

Reads the Oracle store and returns a compact, planner-ready context slice
for a given user input. Keep this small and relevant: huge context blows
out the LLM token budget AND degrades plan quality.

Strategy (deliberately simple in Phase 8):
  • Always include current balance and the last N transactions
  • Always include OPEN loops only (closed ones are noise)
  • Keyword-match the event log so the planner sees prior runs of similar
    work (e.g. "verse" → recent verse generations)
  • Cap every list at MAX_ITEMS

This is RAG-style retrieval over local state. Swap in a vector store
later without touching the planner — the contract is just a dict.
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


def retrieve_context(user_input: str, *, max_items: int = MAX_ITEMS) -> dict[str, Any]:
    """Return a small, structured memory slice keyed off the input.
    Never raises — falls back to an empty-ish dict so the planner is
    always callable even when the store is missing or unreadable.
    """
    try:
        snap = oracle_store.snapshot()
    except Exception:  # noqa: BLE001
        return {"balance": {}, "recent_transactions": [], "open_loops": [], "relevant_events": []}

    txns = snap.get("transactions") or []
    loops = snap.get("open_loops") or []
    events = snap.get("events") or []

    # Recent transactions — newest first, capped
    recent_txns = list(reversed(txns[-max_items:])) if txns else []

    # Open loops only — closed ones are not relevant for planning
    open_loops = [l for l in loops if (l.get("status") or "open") == "open"][-max_items:]

    # Keyword-match recent events so the planner sees prior similar work
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

    return {
        "balance":             snap.get("balance") or {},
        "recent_transactions": recent_txns,
        "open_loops":          open_loops,
        "relevant_events":     relevant_events,
    }


def has_signal(context: dict[str, Any]) -> bool:
    """True if the context has anything worth showing the planner.
    Used to skip the context-injection block when memory is empty."""
    if not isinstance(context, dict):
        return False
    return bool(
        context.get("balance")
        or context.get("recent_transactions")
        or context.get("open_loops")
        or context.get("relevant_events")
    )


__all__ = ["retrieve_context", "has_signal", "MAX_ITEMS"]
