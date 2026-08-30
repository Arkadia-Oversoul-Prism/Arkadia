"""A.I.S capability profile projection over the canonical Arkadia user identity.

This module deliberately reuses the existing Firebase UID and user-profile store.
It is not an authentication layer and does not create a second identity store.
"""
from __future__ import annotations

import json
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from api.auth import _profiles_dir, load_user_profile_store, require_auth

router = APIRouter()

_KEY = "ais_capability_portfolio"
_ALLOWED_TYPES = ("diagnostic_seed", "portfolio")


def _profile_path(uid: str) -> str:
    return os.path.join(_profiles_dir(), f"{uid}.json")


def _save_projection(uid: str, payload: dict[str, Any]) -> dict[str, Any]:
    stored = load_user_profile_store(uid)
    stored[_KEY] = payload
    os.makedirs(_profiles_dir(), exist_ok=True)
    with open(_profile_path(uid), "w", encoding="utf-8") as handle:
        json.dump(stored, handle, indent=2, ensure_ascii=False)
    return payload


@router.get("/api/me/ais-profile")
async def get_ais_profile(user: dict = Depends(require_auth)):
    """Return the authenticated user's A.I.S capability projection, if present."""
    stored = load_user_profile_store(user["uid"])
    return {"profile": stored.get(_KEY)}


@router.patch("/api/me/ais-profile")
async def patch_ais_profile(request: Request, user: dict = Depends(require_auth)):
    """Attach a diagnostic seed or completed portfolio to the existing user profile."""
    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Invalid body")

    kind = body.get("kind")
    profile = body.get("profile")
    if kind not in _ALLOWED_TYPES or not isinstance(profile, dict):
        raise HTTPException(status_code=400, detail="Expected kind and profile")
    if profile.get("version") != 1:
        raise HTTPException(status_code=400, detail="Unsupported A.I.S profile version")

    payload = {"kind": kind, "profile": profile}
    _save_projection(user["uid"], payload)
    return {"profile": payload}
