"""Arkadia Social Field.

This router does not create a second identity or memory system.

Public identity comes from the existing user profile store. Node discovery reads
that same store. Relational context is derived from the existing ReasoMate
message threads, so the relationship itself remains a view over canonical
conversation history rather than a parallel memory database.
"""
from __future__ import annotations

import os
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from api.auth import (
    require_auth,
    load_user_profile_store,
    normalize_handle,
    _profiles_dir,
)
from api.messages import _read_thread

router = APIRouter(tags=["social"])


def _profile(uid: str) -> dict[str, Any]:
    stored = load_user_profile_store(uid)
    username = (stored.get("username") or "").strip()
    return {
        "uid": uid,
        "username": username or None,
        "handle": f"@{username}" if username else None,
        "display_name": (stored.get("display_name") or "").strip() or (username or "Node"),
        "bio": (stored.get("bio") or "").strip() or None,
        "avatar_url": (stored.get("avatar_url") or "").strip() or None,
    }


def _all_profiles() -> list[dict[str, Any]]:
    root = _profiles_dir()
    if not os.path.isdir(root):
        return []
    profiles: list[dict[str, Any]] = []
    for name in os.listdir(root):
        if not name.endswith(".json") or name == "_username_index.json":
            continue
        uid = name[:-5]
        if not uid:
            continue
        stored = load_user_profile_store(uid)
        if not stored:
            continue
        profiles.append(_profile(uid))
    return profiles


@router.get("/api/social/nodes")
async def discover_nodes(q: str = "", limit: int = 40, user: dict = Depends(require_auth)):
    """Authenticated Node discovery over the canonical public profile store."""
    query = q.strip().lower()
    limit = max(1, min(int(limit), 100))
    me = user["uid"]
    profiles = [p for p in _all_profiles() if p["uid"] != me]
    if query:
        profiles = [
            p for p in profiles
            if query in (p.get("username") or "").lower()
            or query in (p.get("display_name") or "").lower()
            or query in (p.get("bio") or "").lower()
        ]
    profiles.sort(key=lambda p: ((p.get("display_name") or "").lower(), (p.get("username") or "").lower()))
    return {"nodes": profiles[:limit], "count": len(profiles)}


@router.get("/api/social/nodes/{uid}")
async def get_discovered_node(uid: str, user: dict = Depends(require_auth)):
    if uid == user["uid"]:
        return {"node": _profile(uid)}
    profile = load_user_profile_store(uid)
    if not profile:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"node": _profile(uid)}


@router.get("/api/relationships/{peer_uid}/context")
async def relationship_context(peer_uid: str, user: dict = Depends(require_auth)):
    """Return the shared relational window derived from the existing DM thread.

    This endpoint intentionally persists nothing. It exposes a bounded view of
    canonical conversation history that a user's companion can use when relating
    to the other Node and their companion.
    """
    me = user["uid"]
    peer = peer_uid.strip()
    if not peer or peer == me:
        raise HTTPException(status_code=400, detail="Invalid peer")
    peer_profile = load_user_profile_store(peer)
    if not peer_profile:
        raise HTTPException(status_code=404, detail="Node not found")

    messages = _read_thread(me, peer)
    recent = messages[-24:]
    first = messages[0]["timestamp"] if messages else None
    last = messages[-1]["timestamp"] if messages else None
    return {
        "relationship": {
            "participants": [_profile(me), _profile(peer)],
            "interaction_count": len(messages),
            "first_interaction_at": first,
            "last_interaction_at": last,
            "shared_memory_source": "reasomate.messages",
            "memory_policy": "Shared relational context is derived from the existing conversation thread. No parallel relationship memory store is created.",
        },
        "messages": recent,
    }


@router.get("/api/social/handle/{handle}")
async def social_handle(handle: str, user: dict = Depends(require_auth)):
    try:
        canonical = normalize_handle(handle)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid handle format")
    for profile in _all_profiles():
        if profile.get("username") == canonical:
            return {"node": profile}
    raise HTTPException(status_code=404, detail="Node not found")
