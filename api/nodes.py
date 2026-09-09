"""Arkadia Node Registry + public social identity API.

Routes:
  GET  /api/me
  PATCH /api/me
  GET  /api/users/by-handle/{handle}
  GET  /api/users/search?q=...
  GET  /api/me/codex
  GET  /api/codex/personal
  GET  /api/nodes/public
  GET  /api/nodes/... (sovereign registry/codex)

Public social routes expose only deliberately public profile fields. Firebase
UIDs, Personal Codex contents, and private memory remain outside the public
field.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from api.auth import (
    get_current_user, require_auth, require_sovereign,
    get_node_by_key, get_personal_codex, _nodes_by_key,
    load_user_profile_store, _profiles_dir, _load_username_index,
    normalize_handle, public_profile_by_handle,
)

logger = logging.getLogger("arkadia.nodes")
router = APIRouter()

# A.I.S capability projection uses the same authenticated router boundary.
from api.ais_profile import router as _ais_profile_router
router.include_router(_ais_profile_router)

# Engineering Lab is an authenticated read-only intelligence seam. It is
# included through this already-mounted composition router, avoiding a second
# application/router hierarchy while preserving the Lab's own /api/lab prefix.
from api.lab_routes import router as _lab_router
router.include_router(_lab_router)

_CODEX_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "personal_codices")

_tools_counter = None


def configure_tools_counter(counter) -> None:
    """Inject the tool-count capability: () -> int. Called once at startup."""
    global _tools_counter
    _tools_counter = counter


def _safe_public_profile(uid: str, fallback_handle: str | None = None) -> dict[str, Any] | None:
    """Return the public social identity projection for a user, never the UID."""
    stored = load_user_profile_store(uid) or {}
    raw = stored.get("username") or fallback_handle or ""
    try:
        handle = normalize_handle(raw)
    except ValueError:
        return None
    return {
        "username": handle,
        "handle": handle,
        "display_name": (stored.get("display_name") or "").strip() or handle,
        "bio": (stored.get("bio") or "").strip()[:500] or None,
        "avatar_url": (stored.get("avatar_url") or "").strip() or None,
    }


# ── /api/codex/personal ──────────────────────────────────────────────────────

@router.get("/api/codex/personal")
async def get_sovereign_codex_public():
    """Legacy public sovereign codex surface."""
    node = get_node_by_key("zahrune")
    if not node:
        raise HTTPException(status_code=404, detail="Sovereign node not found")
    codex = get_personal_codex("zahrune")

    collective = []
    for n in _nodes_by_key.values():
        if n.get("node_key") != "zahrune":
            collective.append({
                "display_name": n["display_name"],
                "role": n["role"],
                "role_sigil": n.get("role_sigil", "◈"),
                "ims_id": n.get("ims_id"),
                "status": n.get("status", "unknown"),
                "access_level": n.get("access_level", 0),
                "node_key": n.get("node_key"),
            })

    tools_count = 4
    if _tools_counter is not None:
        try:
            tools_count = _tools_counter()
        except Exception:
            pass

    return {
        "node": node,
        "codex": codex,
        "collective": collective,
        "system": {"tools_count": tools_count},
    }


# ── Authenticated identity ────────────────────────────────────────────────────

@router.get("/api/me")
async def get_me(user: dict = Depends(require_auth)):
    return {"user": user}


@router.get("/api/users/by-handle/{handle}")
async def get_user_by_handle(handle: str):
    """Public handle discovery. UID and private fields are never returned."""
    try:
        normalized = normalize_handle(handle)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid handle format")
    profile = public_profile_by_handle(normalized)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    # Keep the public projection deliberately explicit and include bio.
    uid = _load_username_index().get(normalized)
    safe = _safe_public_profile(uid, normalized) if uid else None
    if not safe:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": safe}


@router.get("/api/users/search")
async def search_users(q: str = "", limit: int = 20):
    """Public Node discovery by handle/name/bio. Never returns Firebase UIDs."""
    query = (q or "").strip().lower().lstrip("@")
    limit = max(1, min(int(limit), 50))
    index = _load_username_index()
    results: list[dict[str, Any]] = []
    for handle, uid in index.items():
        if query and query not in handle:
            profile = load_user_profile_store(uid) or {}
            haystack = " ".join([
                str(profile.get("display_name") or ""),
                str(profile.get("bio") or ""),
            ]).lower()
            if query not in haystack:
                continue
        safe = _safe_public_profile(uid, handle)
        if safe:
            results.append(safe)
        if len(results) >= limit:
            break
    results.sort(key=lambda p: (p.get("display_name") or p.get("handle") or "").lower())
    return {"users": results, "count": len(results)}


@router.patch("/api/me")
async def patch_me(request: Request, user: dict = Depends(require_auth)):
    """Update only the authenticated user's public product profile."""
    from api.auth import save_user_profile_store, build_user_profile
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Invalid body")
    patch = {k: body[k] for k in ("display_name", "username", "bio", "avatar_url") if k in body}
    if not patch:
        raise HTTPException(status_code=400, detail="No profile fields provided")
    try:
        save_user_profile_store(user["uid"], patch)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e) or "Invalid profile") from e
    updated = build_user_profile(
        user["uid"],
        {"email": user.get("email"), "name": user.get("display_name")},
        user.get("email", ""),
    )
    return {"user": updated}


@router.get("/api/me/codex")
async def get_my_codex(user: dict = Depends(require_auth)):
    node_key = user.get("node_key")
    if not node_key:
        raise HTTPException(status_code=404, detail="No Personal Codex found — your IMS session has not been completed yet.")
    codex = get_personal_codex(node_key)
    if not codex:
        raise HTTPException(status_code=404, detail="Personal Codex not yet seeded. Contact the Flamekeeper.")
    return {"codex": codex, "node_key": node_key}


# ── Sovereign node registry ───────────────────────────────────────────────────

@router.get("/api/nodes")
async def list_nodes(user: dict = Depends(require_sovereign)):
    nodes = list(_nodes_by_key.values())
    for n in nodes:
        n["codex_available"] = (n.get("personal_codex_file") is not None)
    return {"nodes": nodes, "count": len(nodes)}


@router.get("/api/nodes/public")
async def list_nodes_public():
    """Legacy public node projection for registered/system nodes."""
    safe = []
    for n in _nodes_by_key.values():
        if n.get("status") in ("active", "training"):
            safe.append({
                "display_name": n["display_name"],
                "role": n["role"],
                "role_sigil": n.get("role_sigil", "◈"),
                "ims_id": n.get("ims_id"),
                "status": n.get("status"),
            })
    return {"nodes": safe, "count": len(safe)}


@router.get("/api/nodes/{node_key}")
async def get_node(node_key: str, user: dict = Depends(require_sovereign)):
    node = get_node_by_key(node_key)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_key}' not found")
    return {"node": node}


@router.get("/api/nodes/{node_key}/codex")
async def get_node_codex(node_key: str, user: dict = Depends(require_sovereign)):
    node = get_node_by_key(node_key)
    if not node:
        raise HTTPException(status_code=404, detail=f"No node '{node_key}' found")
    codex = get_personal_codex(node_key)
    if not codex:
        raise HTTPException(status_code=404, detail=f"No Personal Codex found for '{node_key}'")
    return {"codex": codex, "node_key": node_key}


@router.post("/api/nodes/{node_key}/codex")
async def upsert_node_codex(node_key: str, request: Request, user: dict = Depends(require_sovereign)):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    path = os.path.join(_CODEX_DIR, f"{node_key}.json")
    os.makedirs(_CODEX_DIR, exist_ok=True)
    existing: dict[str, Any] = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            pass
    existing.update(body)
    existing["node_key"] = node_key
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
    logger.info(f"[NODES] Codex upserted for node '{node_key}' by {user.get('node_key','?')}")
    return {"message": "Codex saved", "node_key": node_key}
