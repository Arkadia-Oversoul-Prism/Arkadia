"""Arkadia Social Field.

One public identity projection, one Node directory, one ReasoMate conversation
spine. This router creates no second identity or memory system.

Public profile data comes from the existing user profile store. Relationship
context is derived from the existing ReasoMate message threads. Firebase UIDs
are internal identifiers and are returned only on authenticated social routes
where the client needs them to address an existing thread.
"""
from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from api.auth import require_auth, load_user_profile_store, normalize_handle, _profiles_dir

router = APIRouter(tags=["social"])


def _profile(uid: str, include_uid: bool = True) -> dict[str, Any]:
    stored = load_user_profile_store(uid)
    username = (stored.get("username") or "").strip()
    result: dict[str, Any] = {
        "username": username or None,
        "handle": f"@{username}" if username else None,
        "display_name": (stored.get("display_name") or "").strip() or (username or "Node"),
        "bio": (stored.get("bio") or "").strip()[:500] or None,
        "avatar_url": (stored.get("avatar_url") or "").strip() or None,
    }
    if include_uid:
        result["uid"] = uid
    return result


def _all_profiles() -> list[tuple[str, dict[str, Any]]]:
    root = _profiles_dir()
    if not os.path.isdir(root):
        return []
    profiles: list[tuple[str, dict[str, Any]]] = []
    for name in os.listdir(root):
        if not name.endswith(".json") or name == "_username_index.json":
            continue
        uid = name[:-5]
        if not uid:
            continue
        stored = load_user_profile_store(uid)
        if stored:
            profiles.append((uid, _profile(uid, include_uid=True)))
    return profiles


@router.get("/api/social/nodes")
async def discover_nodes(q: str = "", limit: int = 40, user: dict = Depends(require_auth)):
    """Authenticated Node discovery over the canonical public profile store."""
    query = q.strip().lower().lstrip("@")
    limit = max(1, min(int(limit), 100))
    me = user["uid"]
    matches: list[dict[str, Any]] = []
    for uid, profile in _all_profiles():
        if uid == me:
            continue
        haystack = " ".join([
            profile.get("username") or "",
            profile.get("display_name") or "",
            profile.get("bio") or "",
        ]).lower()
        if query and query not in haystack:
            continue
        matches.append(profile)
    matches.sort(key=lambda p: ((p.get("display_name") or "").lower(), (p.get("username") or "").lower()))
    return {"nodes": matches[:limit], "count": len(matches)}


@router.get("/api/social/handle/{handle}")
async def social_handle(handle: str, user: dict = Depends(require_auth)):
    try:
        canonical = normalize_handle(handle)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid handle format")
    for _, profile in _all_profiles():
        if profile.get("username") == canonical:
            return {"node": profile}
    raise HTTPException(status_code=404, detail="Node not found")


@router.get("/api/relationships/{peer_uid}/context")
async def relationship_context(peer_uid: str, user: dict = Depends(require_auth)):
    """Bounded shared-field context derived from the existing DM thread.

    Nothing is persisted here. The existing ReasoMate thread is the durable
    relational memory. This route projects it for the two participants.
    """
    from api.messages import _read_thread

    me = user["uid"]
    peer = peer_uid.strip()
    if not peer or peer == me:
        raise HTTPException(status_code=400, detail="Invalid peer")
    if not load_user_profile_store(peer):
        raise HTTPException(status_code=404, detail="Node not found")

    messages = _read_thread(me, peer)
    recent = messages[-24:]
    return {
        "relationship": {
            "participants": [_profile(me), _profile(peer)],
            "interaction_count": len(messages),
            "first_interaction_at": messages[0]["timestamp"] if messages else None,
            "last_interaction_at": messages[-1]["timestamp"] if messages else None,
            "shared_memory_source": "reasomate.messages",
            "memory_policy": "Shared relational context is derived from the existing conversation thread. No parallel relationship memory store exists.",
        },
        "messages": [
            {
                "sender_uid": m.get("sender_uid"),
                "recipient_uid": m.get("recipient_uid"),
                "content": m.get("content"),
                "timestamp": m.get("timestamp"),
            }
            for m in recent
        ],
    }


@router.get("/api/social/nodes/{uid}")
async def get_discovered_node(uid: str, user: dict = Depends(require_auth)):
    profile = load_user_profile_store(uid)
    if not profile or uid == user["uid"]:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"node": _profile(uid)}
