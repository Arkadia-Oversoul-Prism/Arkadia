"""Curated Knowledge OS access for the Chief Agent — Gate 1B.

The existing `knowledge.context_engine.assemble_context` owner filter admits
*every* note owned by the supplied UID. That is correct for a human reading
their own knowledge, and far too broad for a delegated machine principal: it
would expose private conversations, personal codex and unrelated personal
notes.

This module therefore does not pass the Founder UID into generic retrieval.
It reads only the note IDs named by the delegation's curated collection, and
re-applies the same private-boundary rules the context engine uses. A note that
is not in the collection is not reachable, whatever its owner.
"""
from __future__ import annotations

from typing import Any

from knowledge.db import execute

#: Note types that are never readable by the machine principal, even if a
#: collection names them. Conversation material is private by construction.
DENIED_NOTE_TYPES = frozenset({"conversation"})


def curated_note_ids(principal: Any) -> list[str]:
    """The note IDs the delegation explicitly curates. Empty means no access."""
    scope = getattr(principal, "resource_scope", None)
    if not isinstance(scope, dict):
        return []
    collection = scope.get("knowledge_collection") or []
    if not isinstance(collection, list):
        return []
    return [str(item).strip() for item in collection if str(item).strip()]


def read_curated_notes(principal: Any, *, limit: int = 20) -> list[dict[str, Any]]:
    """Read only the curated notes, filtered by owner and note type.

    Every predicate is derived from the validated principal, never from a
    request argument. A missing collection returns an empty list rather than
    falling back to owner-wide retrieval.
    """
    note_ids = curated_note_ids(principal)
    if not note_ids:
        return []
    owner_uid = str(getattr(principal, "owner_uid", "") or "").strip()
    if not owner_uid:
        return []

    placeholders = ",".join("?" * len(note_ids))
    denied = ",".join("?" * len(DENIED_NOTE_TYPES))
    rows = execute(
        f"SELECT id, uuid, title, note_type, tags, created_at FROM notes "
        f"WHERE id IN ({placeholders}) AND user_id = ? AND note_type NOT IN ({denied}) "
        f"ORDER BY updated_at DESC LIMIT ?",
        (*note_ids, owner_uid, *sorted(DENIED_NOTE_TYPES), int(limit)),
    )
    return [dict(row) for row in rows]


def curated_context(principal: Any, *, limit: int = 20) -> dict[str, Any]:
    """A context package shaped like `assemble_context`, but collection-bounded.

    Deliberately does not call `assemble_context`: that function's owner filter
    is the exact boundary this module exists to narrow.
    """
    notes = read_curated_notes(principal, limit=limit)
    return {
        "query": None,
        "relevant_notes": notes,
        "graph_expansions": [],
        "project_context": None,
        "recent_timeline": [],
        "curated": True,
        "collection_size": len(curated_note_ids(principal)),
        "returned": len(notes),
    }


__all__ = [
    "DENIED_NOTE_TYPES",
    "curated_note_ids",
    "read_curated_notes",
    "curated_context",
]
