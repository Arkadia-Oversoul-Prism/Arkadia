"""
API key management endpoints — extracted from api/main.py (Phase 2
decomposition). Paths and behaviour unchanged:

  /api/keys            — legacy multi-key Gemini store (auth → per-user)
  /api/provider-keys   — one key per provider (gemini/openai/claude/deepseek)
  /api/keys/pool       — distributed Gemini pool status / reset
  /api/tts/keys        — multi-key TTS / ElevenLabs store
"""
import logging

from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger("arkadia")

try:
    from api.auth import get_current_user as _get_current_user
except Exception:  # dev fallback — matches api/main.py's in-flight fallback
    async def _get_current_user(request):  # type: ignore
        return None

router = APIRouter()


# ── Legacy multi-key Gemini store ─────────────────────────────────────────────


@router.get("/api/keys")
async def api_list_keys(request: Request):
    """List API keys for the authenticated user."""
    user = await _get_current_user(request)
    user_id = user.get("uid") if user else None

    if not user_id:
        from api.key_manager import list_keys
        return {"keys": list_keys()}

    from api.user_key_store import get_user_keys
    return {"keys": get_user_keys(user_id)}


@router.post("/api/keys")
async def api_add_key(request: Request):
    """Add a new API key for the authenticated user."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    key = (body.get("key") or "").strip()
    label = (body.get("label") or "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="'key' is required")

    user = await _get_current_user(request)
    user_id = user.get("uid") if user else None

    if not user_id:
        try:
            from api.key_manager import add_key
            return add_key(key, label)
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

    from api.user_key_store import add_user_key
    try:
        return add_user_key(user_id, key, label)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/api/keys/{key_id}")
async def api_remove_key(key_id: str, request: Request):
    """Remove an API key for the authenticated user."""
    user = await _get_current_user(request)
    user_id = user.get("uid") if user else None

    if not user_id:
        from api.key_manager import remove_key
        ok = remove_key(key_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Key not found")
        return {"deleted": key_id}

    from api.user_key_store import remove_user_key
    ok = remove_user_key(user_id, key_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"deleted": key_id}


@router.patch("/api/keys/{key_id}/activate")
async def api_activate_key(key_id: str, request: Request):
    """Set the active API key for the authenticated user."""
    user = await _get_current_user(request)
    user_id = user.get("uid") if user else None

    if not user_id:
        from api.key_manager import set_active
        ok = set_active(key_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Key not found")
        return {"active": key_id}

    from api.user_key_store import set_active_user_key
    ok = set_active_user_key(user_id, key_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"active": key_id}


@router.patch("/api/keys/{key_id}/reset-quota")
async def api_reset_quota(key_id: str):
    """Reset quota for an API key."""
    from api.key_manager import reset_quota
    ok = reset_quota(key_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"reset": key_id}


# ── Multi-provider key store (gemini / openai / claude / deepseek) ────────────


@router.get("/api/provider-keys")
async def api_list_provider_keys():
    """List one key entry per provider (masked), including env-var sources."""
    from api.provider_key_store import list_keys
    return {"keys": list_keys()}


@router.post("/api/provider-keys")
async def api_set_provider_key(request: Request):
    """Store or replace the key for a given provider."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    provider = (body.get("provider") or "").strip().lower()
    key = (body.get("key") or "").strip()
    label = (body.get("label") or "").strip()
    if not provider or not key:
        raise HTTPException(status_code=400, detail="'provider' and 'key' are required")
    from api.provider_key_store import set_key
    try:
        result = set_key(provider, key, label)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    logger.info("[provider-keys] stored key for %s", provider)
    return result


@router.delete("/api/provider-keys/{provider}")
async def api_remove_provider_key(provider: str):
    """Remove the stored key for a provider."""
    from api.provider_key_store import remove_key
    ok = remove_key(provider)
    if not ok:
        raise HTTPException(status_code=404, detail="No stored key for this provider")
    return {"removed": provider}


@router.patch("/api/provider-keys/{provider}/reset-quota")
async def api_reset_provider_quota(provider: str):
    """Reset quota-hit flag for a provider's key."""
    from api.provider_key_store import reset_quota
    ok = reset_quota(provider)
    if not ok:
        raise HTTPException(status_code=404, detail="No stored key for this provider")
    return {"provider": provider, "quota_reset": True}


# ── Distributed Gemini Key Pool — status / reset ─────────────────────────────


@router.get("/api/keys/pool")
async def api_key_pool_status():
    """Report the live Gemini key pool: total / available / cooled keys."""
    from api.key_pool import pool_snapshot
    snap = pool_snapshot()
    return {
        "size": snap["size"],
        "available": snap["available"],
        "cooled": snap["cooled"],
        "strategy": "round-robin (load-balanced) — concurrent callers spread across the pool",
    }


@router.post("/api/keys/pool/reset")
async def api_key_pool_reset():
    """Clear all Gemini key cooldowns in the pool."""
    from api.key_pool import reset_all
    reset_all()
    return {"reset": True}


# ── TTS key store (ElevenLabs) ────────────────────────────────────────────────


@router.get("/api/tts/keys")
async def api_list_tts_keys():
    from api.tts_key_manager import list_keys
    return {"keys": list_keys()}


@router.post("/api/tts/keys")
async def api_add_tts_key(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    key = (body.get("key") or "").strip()
    label = (body.get("label") or "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="'key' is required")
    try:
        from api.tts_key_manager import add_key
        result = add_key(key, label)
        return result
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/api/tts/keys/{key_id}")
async def api_remove_tts_key(key_id: str):
    from api.tts_key_manager import remove_key
    ok = remove_key(key_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"deleted": key_id}


@router.patch("/api/tts/keys/{key_id}/activate")
async def api_activate_tts_key(key_id: str):
    from api.tts_key_manager import set_active
    ok = set_active(key_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"active": key_id}


@router.patch("/api/tts/keys/{key_id}/reset-quota")
async def api_reset_tts_quota(key_id: str):
    from api.tts_key_manager import reset_quota
    ok = reset_quota(key_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"reset": key_id}
