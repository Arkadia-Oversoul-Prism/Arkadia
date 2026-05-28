"""Arkadia Node Registry API — /api/nodes, /api/me, /api/codex/personal.

Routes:
  GET  /api/me                      — current user's profile (requires auth)
  GET  /api/me/codex                — current user's Personal Codex
  GET  /api/nodes                   — full node registry (sovereign only)
  GET  /api/nodes/{node_key}        — single node profile (sovereign only)
  GET  /api/nodes/{node_key}/codex  — node's Personal Codex (sovereign only)
  POST /api/nodes/{node_key}/codex  — update/seed a node's Personal Codex (sovereign)
  GET  /api/nodes/public            — public node list (names + roles, no PII)
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
)

logger = logging.getLogger("arkadia.nodes")

router = APIRouter()

_CODEX_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "personal_codices")


# ── /api/me ───────────────────────────────────────────────────────────────────

@router.get("/api/me")
async def get_me(user: dict = Depends(require_auth)):
    """Return the authenticated user's profile."""
    return {"user": user}


@router.get("/api/me/codex")
async def get_my_codex(user: dict = Depends(require_auth)):
    """Return the authenticated user's Personal Codex."""
    node_key = user.get("node_key")
    if not node_key:
        raise HTTPException(
            status_code=404,
            detail="No Personal Codex found — your IMS session has not been completed yet."
        )
    codex = get_personal_codex(node_key)
    if not codex:
        raise HTTPException(
            status_code=404,
            detail="Personal Codex not yet seeded. Contact the Flamekeeper."
        )
    return {"codex": codex, "node_key": node_key}


# ── /api/nodes (sovereign) ────────────────────────────────────────────────────

@router.get("/api/nodes")
async def list_nodes(user: dict = Depends(require_sovereign)):
    """Full node registry — sovereign access only."""
    nodes = list(_nodes_by_key.values())
    for n in nodes:
        n["codex_available"] = (n.get("personal_codex_file") is not None)
    return {"nodes": nodes, "count": len(nodes)}


@router.get("/api/nodes/public")
async def list_nodes_public():
    """Public-safe node list — names and roles only, no PII or access details."""
    safe = []
    for n in _nodes_by_key.values():
        if n.get("status") in ("active", "training"):
            safe.append({
                "display_name": n["display_name"],
                "role":         n["role"],
                "role_sigil":   n.get("role_sigil", "◈"),
                "ims_id":       n.get("ims_id"),
                "status":       n.get("status"),
            })
    return {"nodes": safe, "count": len(safe)}


@router.get("/api/nodes/{node_key}")
async def get_node(node_key: str, user: dict = Depends(require_sovereign)):
    """Single node profile — sovereign access only."""
    node = get_node_by_key(node_key)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_key}' not found")
    return {"node": node}


@router.get("/api/nodes/{node_key}/codex")
async def get_node_codex(node_key: str, user: dict = Depends(require_sovereign)):
    """Return a node's Personal Codex — sovereign access only."""
    node = get_node_by_key(node_key)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_key}' not found")
    codex = get_personal_codex(node_key)
    if not codex:
        raise HTTPException(
            status_code=404,
            detail=f"No Personal Codex found for '{node_key}'"
        )
    return {"codex": codex, "node_key": node_key}


@router.post("/api/nodes/{node_key}/codex")
async def upsert_node_codex(
    node_key: str,
    request: Request,
    user: dict = Depends(require_sovereign),
):
    """Seed or update a node's Personal Codex — sovereign access only."""
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
