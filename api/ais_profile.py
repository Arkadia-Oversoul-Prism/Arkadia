"""A.I.S capability profile and longitudinal identity spine.

A.I.S remains the first-run identity instrument. This module projects that
seed into the existing authenticated user profile store; it does not create
a second authentication, memory, or identity system.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from api.auth import _profiles_dir, load_user_profile_store, require_auth

router = APIRouter()

_KEY = "ais_capability_portfolio"
_SPINE_KEY = "identity_spine"
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


def _seed_from_ais(stored: dict[str, Any]) -> dict[str, Any] | None:
    projection = stored.get(_KEY)
    if not isinstance(projection, dict):
        return None
    profile = projection.get("profile")
    return profile if isinstance(profile, dict) else None


def _build_identity_spine(uid: str, user: dict[str, Any], stored: dict[str, Any]) -> dict[str, Any]:
    """Build a read model from canonical auth identity + A.I.S + existing field state."""
    seed = _seed_from_ais(stored)
    existing = stored.get(_SPINE_KEY)
    if not isinstance(existing, dict):
        existing = {}
    now = datetime.now(timezone.utc).isoformat()

    identity = {
        "uid": uid,
        "canonical_name": user.get("display_name") or stored.get("display_name") or "",
        "preferred_name": stored.get("display_name") or user.get("display_name") or "",
        "username": user.get("username") or stored.get("username") or None,
        "role": user.get("role") or "Authenticated Node",
        "role_sigil": user.get("role_sigil") or "◈",
        "ims_id": user.get("ims_id"),
    }
    baseline = {
        "identity": seed.get("identity", "") if seed else "",
        "capabilities": seed.get("capabilities", []) if seed else [],
        "builds": seed.get("builds", "") if seed else "",
        "evidence": seed.get("evidence", "") if seed else "",
        "projects": seed.get("projects", "") if seed else "",
        "offer": seed.get("offer", "") if seed else "",
        "credentials": seed.get("credentials", "") if seed else "",
        "growth": seed.get("growth", []) if seed else [],
    }

    old_cap = existing.get("capability") if isinstance(existing.get("capability"), dict) else {}
    capability = {
        "baseline": baseline,
        "evidence_count": int(old_cap.get("evidence_count", 0) or 0),
        "development_events": old_cap.get("development_events", []),
        "last_assessed_at": old_cap.get("last_assessed_at"),
    }

    old_rel = existing.get("relationship") if isinstance(existing.get("relationship"), dict) else {}
    relationship = {
        "preferred_ai_role": old_rel.get("preferred_ai_role") or None,
        "communication_preference": old_rel.get("communication_preference") or None,
        "collaboration_preference": old_rel.get("collaboration_preference") or None,
    }

    old_index = existing.get("relational_index") if isinstance(existing.get("relational_index"), dict) else {}
    relational = {
        "version": 1,
        "status": old_index.get("status") or ("seeded" if seed else "awaiting_seed"),
        "score": old_index.get("score"),
        "confidence": old_index.get("confidence", 0),
        "dimensions": old_index.get("dimensions", {
            "identity_coherence": None,
            "context_continuity": None,
            "personalization_fidelity": None,
            "agency_preservation": None,
            "trust_calibration": None,
            "responsiveness": None,
            "developmental_coherence": None,
            "relational_alignment": None,
        }),
        "observations": old_index.get("observations", []),
        "last_evaluated_at": old_index.get("last_evaluated_at"),
    }

    old_symbolic = existing.get("symbolic") if isinstance(existing.get("symbolic"), dict) else {}
    symbolic = {
        "seed_phrase": old_symbolic.get("seed_phrase") or None,
        "seed_symbols": old_symbolic.get("seed_symbols") or [],
        "sigil_seed": old_symbolic.get("sigil_seed") or "◈",
        "resonance_signature": old_symbolic.get("resonance_signature") or None,
    }

    provenance = {
        "ais_version": seed.get("version") if seed else None,
        "seed_created_at": seed.get("completedAt") if seed else None,
        "last_reconciled_at": now,
        "schema_version": 1,
    }
    return {
        "version": 1,
        "identity": identity,
        "capability": capability,
        "relationship": relationship,
        "relational_index": relational,
        "symbolic": symbolic,
        "provenance": provenance,
    }


def _save_spine(uid: str, spine: dict[str, Any]) -> dict[str, Any]:
    stored = load_user_profile_store(uid)
    stored[_SPINE_KEY] = spine
    os.makedirs(_profiles_dir(), exist_ok=True)
    with open(_profile_path(uid), "w", encoding="utf-8") as handle:
        json.dump(stored, handle, indent=2, ensure_ascii=False)
    return spine


@router.get("/api/me/ais-profile")
async def get_ais_profile(user: dict = Depends(require_auth)):
    stored = load_user_profile_store(user["uid"])
    return {"profile": stored.get(_KEY)}


@router.patch("/api/me/ais-profile")
async def patch_ais_profile(request: Request, user: dict = Depends(require_auth)):
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
    spine = _build_identity_spine(user["uid"], user, load_user_profile_store(user["uid"]))
    _save_spine(user["uid"], spine)
    return {"profile": payload, "identity_spine": spine}


@router.get("/api/me/identity-spine")
async def get_identity_spine(user: dict = Depends(require_auth)):
    """Return the authenticated node's canonical longitudinal identity read model."""
    uid = user["uid"]
    stored = load_user_profile_store(uid)
    spine = _build_identity_spine(uid, user, stored)
    _save_spine(uid, spine)
    return {"identity_spine": spine}
