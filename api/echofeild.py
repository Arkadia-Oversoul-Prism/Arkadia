"""Echofeild Aggregator — GET /api/me/field  (Consolidation Pass 02)

A composed READ MODEL of the authenticated user's personal field.

This endpoint is a connector, not a storage system. It composes existing
owner-scoped primitives only:

  identity      — the canonical /api/me profile model (api.auth)
  notes         — knowledge.vault.list_notes(user_id=uid)
  graph         — knowledge.graph.full_graph_export(user_id=uid)
  timeline      — knowledge.timeline.recent(user_id=uid)
  projects      — knowledge.vault.list_projects(user_id=uid)
  conversations — api.messages inbox reader (pair-keyed JSONL, participant-only)
  messages      — api.messages thread reader, bounded, participant-only
  executions    — [] (SolSpire is not owner-scoped in this repo state; excluded
                       rather than weakening any boundary)

Ownership is derived exclusively from the authenticated Firebase uid via
api.auth.require_auth. No request parameter (uid/user_id/owner/node_key/...)
can influence whose field is returned.

Read-only: performs no writes against any store.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends

from api.auth import require_auth

router = APIRouter(tags=["echofeild"])

# Bounded read-model sizes, aligned with existing route limits.
_NOTES_LIMIT = 100
_TIMELINE_LIMIT = 100
_MESSAGES_PER_THREAD = 20
_MESSAGES_TOTAL = 50


def _source(sources: list[dict], name: str, primitive: str, included: bool, detail: str = "") -> None:
    entry = {"source": name, "primitive": primitive, "included": included}
    if detail:
        entry["detail"] = detail
    sources.append(entry)


def _read_notes(uid: str) -> list[dict]:
    from knowledge.vault import list_notes
    return list_notes(user_id=uid, limit=_NOTES_LIMIT)


def _read_graph(uid: str) -> dict:
    from knowledge.graph import full_graph_export
    return full_graph_export(user_id=uid)


def _read_timeline(uid: str) -> list[dict]:
    from knowledge import timeline as tl
    return tl.recent(limit=_TIMELINE_LIMIT, user_id=uid)


def _read_projects(uid: str) -> list[dict]:
    from knowledge.vault import list_projects
    return list_projects(user_id=uid)


def _read_messages(uid: str) -> tuple[list[dict], list[dict]]:
    """Reuse the existing ReasoMate DM readers (pair-keyed JSONL).

    Participant-only by construction: pair files are keyed on both uids and
    the inbox scan only selects files containing the authenticated uid.
    Strictly read-only — if the messages directory does not exist yet, no
    directory is created.
    """
    import api.messages as msg

    if not os.path.isdir(msg._MSG_DIR):
        return [], []

    conversations: list[dict] = []
    messages: list[dict] = []
    for name in sorted(os.listdir(msg._MSG_DIR)):
        if not name.endswith(".jsonl"):
            continue
        parts = name[:-6].split("__")
        if uid not in parts:
            continue
        peer = parts[0] if parts[1] == uid else parts[1]
        thread = msg._read_thread(uid, peer)
        if not thread:
            continue
        conversations.append({
            "peer_uid": peer,
            "last_message": thread[-1],
            "count": len(thread),
        })
        messages.extend(thread[-_MESSAGES_PER_THREAD:])

    messages.sort(key=lambda m: m.get("timestamp", 0))
    return conversations, messages[-_MESSAGES_TOTAL:]


@router.get("/api/me/field")
async def get_my_field(user: dict = Depends(require_auth)) -> dict[str, Any]:
    """Compose the authenticated user's personal Echofeild read model."""
    uid = user["uid"]
    sources: list[dict] = []

    # Identity — the same profile model exposed by /api/me (no secrets, no tokens).
    identity = {
        "uid": user.get("uid"),
        "email": user.get("email"),
        "display_name": user.get("display_name"),
        "username": user.get("username"),
        "bio": user.get("bio"),
        "avatar_url": user.get("avatar_url"),
        "role": user.get("role"),
        "node_key": user.get("node_key"),
        "access_level": user.get("access_level"),
        "profile_complete": user.get("profile_complete"),
    }
    _source(sources, "identity", "api.auth.require_auth profile model", True)

    try:
        notes = _read_notes(uid)
        _source(sources, "notes", "knowledge.vault.list_notes(user_id=uid)", True)
    except Exception:
        notes = []
        _source(sources, "notes", "knowledge.vault.list_notes(user_id=uid)", False, "unavailable")

    try:
        graph = _read_graph(uid)
        _source(sources, "graph", "knowledge.graph.full_graph_export(user_id=uid)", True)
    except Exception:
        graph = {"nodes": [], "edges": []}
        _source(sources, "graph", "knowledge.graph.full_graph_export(user_id=uid)", False, "unavailable")

    try:
        timeline = _read_timeline(uid)
        _source(sources, "timeline", "knowledge.timeline.recent(user_id=uid)", True)
    except Exception:
        timeline = []
        _source(sources, "timeline", "knowledge.timeline.recent(user_id=uid)", False, "unavailable")

    try:
        projects = _read_projects(uid)
        _source(sources, "projects", "knowledge.vault.list_projects(user_id=uid)", True)
    except Exception:
        projects = []
        _source(sources, "projects", "knowledge.vault.list_projects(user_id=uid)", False, "unavailable")

    try:
        conversations, messages = _read_messages(uid)
        _source(sources, "conversations", "api.messages pair-keyed thread readers (participant-only)", True)
    except Exception:
        conversations, messages = [], []
        _source(sources, "conversations", "api.messages pair-keyed thread readers (participant-only)", False, "unavailable")

    # SolSpire projects/executions are intentionally excluded: the SolSpire
    # console store is not owner-scoped in the current repository state, so
    # aggregating it would leak cross-user data. Excluded per the
    # source-of-truth rule rather than weakening the boundary.
    executions: list = []
    _source(
        sources, "solspire",
        "solspire.project_store",
        False,
        "excluded — not owner-scoped in current repository state",
    )

    return {
        "identity": identity,
        "notes": notes,
        "graph": graph,
        "timeline": timeline,
        "projects": projects,
        "conversations": conversations,
        "messages": messages,
        "executions": executions,
        "meta": {
            "owner_uid": uid,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sources": sources,
        },
    }
