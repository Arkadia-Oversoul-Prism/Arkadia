"""Arkadia Voice — authenticated HTTP surface (Phase 11 backend).

Mounted by ``solspire/console_router.py`` into the canonical ``/solspire``
router, so every route resolves as ``/solspire/voice/*`` and inherits the
existing ``require_auth`` subject boundary. Every endpoint is a thin handler:
validation, governance and evidence live in :mod:`solspire.voice_pipeline`.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from api.auth import require_auth
from solspire.voice_asr import provider_status_report
from solspire.voice_contracts import (
    STAGE_ORDER,
    VOICE_ERROR_STATES,
    VoiceStage,
    requires_approval,
)
from solspire.voice_pipeline import MAX_AUDIO_BYTES, VoiceError, get_voice_pipeline

router = APIRouter(
    prefix="/voice",
    tags=["Arkadia Voice"],
    dependencies=[Depends(require_auth)],
)

#: Canonical HTTP status per voice error state.
_VOICE_HTTP_STATUS: dict[str, int] = {
    "MICROPHONE_DENIED": 400,
    "AUDIO_CAPTURE_FAILED": 400,
    "AUDIO_EMPTY": 400,
    "ASR_UNAVAILABLE": 503,
    "ASR_FAILED": 502,
    "TRANSCRIPT_EMPTY": 422,
    "INTENT_UNKNOWN": 422,
    "CONTEXT_AMBIGUOUS": 409,
    "CONTEXT_UNKNOWN": 409,
    "AUTHORITY_MISSING": 403,
    "AUTHORIZATION_DENIED": 403,
    "AUTHORIZATION_REQUIRED": 409,
    "PROPOSAL_REQUIRED": 409,
    "APPROVAL_REQUIRED": 409,
    "EXECUTION_FAILED": 500,
    "VERIFICATION_PENDING": 409,
    "VERIFICATION_FAILED": 409,
}


def _voice_http(error: VoiceError) -> HTTPException:
    return HTTPException(
        status_code=_VOICE_HTTP_STATUS.get(error.state, 400),
        detail=error.to_dict(),
    )


def _load(event_id: str, user: dict[str, Any]) -> dict[str, Any]:
    pipeline = get_voice_pipeline()
    try:
        return pipeline._event_or_raise(event_id, user["uid"])
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ── status / providers ───────────────────────────────────────────────────────

@router.get("/status")
async def voice_status(user: dict = Depends(require_auth)) -> dict[str, Any]:
    """Everything the operator surface needs to render truthful states."""
    return {
        "surface": "arkadia_voice",
        "subject": {"uid": user.get("uid"), "role": user.get("role"),
                    "access_level": user.get("access_level")},
        "chain": [stage.value for stage in STAGE_ORDER],
        "error_states": VOICE_ERROR_STATES,
        "risk_policy": {
            "ASK": "INFORMATIONAL", "SEARCH": "INFORMATIONAL",
            "CREATE": "MEDIUM", "MODIFY": "HIGH", "EXECUTE": "MEDIUM",
            "note": "Informational (observation-only) requests need no proposal "
                    "or approval; every other action passes proposal → human "
                    "decision → authorization → execution.",
        },
        "max_audio_bytes": MAX_AUDIO_BYTES,
        "asr": provider_status_report(),
        "governance": {
            "proposal": "/solspire/proposals",
            "authorize": "/solspire/authority/proposals/{proposal_id}/authorize",
            "approval_authority": "Flamekeeper role or access_level >= 3",
            "verification": "separate human act — POST /solspire/voice/events/{id}/verify",
        },
    }


@router.get("/providers")
async def voice_providers(user: dict = Depends(require_auth)) -> dict[str, Any]:
    return provider_status_report()


# ── capture ──────────────────────────────────────────────────────────────────

@router.post("/events")
async def create_voice_event(
    file: UploadFile = File(..., description="Captured audio (webm/ogg/wav/mp3)"),
    language: str = Form("en"),
    provider: str | None = Form(None),
    session_id: str | None = Form(None),
    duration_ms: int | None = Form(None),
    transcript_hint: str | None = Form(
        None,
        description="Deterministic transcript for the test provider only "
                    "(ignored by recognizing providers)",
    ),
    user: dict = Depends(require_auth),
) -> dict[str, Any]:
    """Phase 4: audio capture reaches the backend, is hashed, and is transcribed."""
    pipeline = get_voice_pipeline()
    audio = await file.read()
    try:
        return pipeline.ingest(
            user,
            audio=audio,
            mime=file.content_type or "",
            language=language,
            provider=provider,
            transcript_hint=transcript_hint,
            session_id=session_id,
            duration_ms=duration_ms,
        )
    except VoiceError as err:
        raise _voice_http(err)


@router.get("/events")
async def list_voice_events(
    session_id: str | None = None,
    limit: int = 50,
    user: dict = Depends(require_auth),
) -> dict[str, Any]:
    return get_voice_pipeline().list(user, session_id=session_id, limit=min(limit, 200))


@router.get("/events/{event_id}")
async def get_voice_event(event_id: str, user: dict = Depends(require_auth)) -> dict[str, Any]:
    _load(event_id, user)
    return get_voice_pipeline().get(user, event_id)


@router.get("/events/{event_id}/chain")
async def get_voice_chain(event_id: str, user: dict = Depends(require_auth)) -> dict[str, Any]:
    _load(event_id, user)
    return get_voice_pipeline().chain(user, event_id)


@router.get("/events/{event_id}/audio")
async def get_voice_audio(event_id: str, user: dict = Depends(require_auth)) -> Response:
    _load(event_id, user)
    found = get_voice_pipeline().audio(user, event_id)
    if found is None:
        raise HTTPException(status_code=404, detail="audio not found for this subject")
    audio_bytes, mime, audio_hash = found
    return Response(
        content=audio_bytes,
        media_type=mime or "application/octet-stream",
        headers={"X-Arkadia-Audio-SHA256": audio_hash},
    )


# ── understanding ────────────────────────────────────────────────────────────

class UnderstandRequest(BaseModel):
    disambiguations: dict[str, Any] = Field(default_factory=dict)


@router.post("/events/{event_id}/understand")
async def understand_voice_event(
    event_id: str,
    body: UnderstandRequest | None = None,
    user: dict = Depends(require_auth),
) -> dict[str, Any]:
    _load(event_id, user)
    payload = body.disambiguations if body else None
    try:
        return get_voice_pipeline().understand(user, event_id, payload)
    except VoiceError as err:
        raise _voice_http(err)


@router.post("/events/{event_id}/propose")
async def propose_voice_event(event_id: str, user: dict = Depends(require_auth)) -> dict[str, Any]:
    _load(event_id, user)
    try:
        return get_voice_pipeline().propose(user, event_id)
    except VoiceError as err:
        raise _voice_http(err)


class DecisionRequest(BaseModel):
    decision: str  # ACCEPTED | DECLINED | WITHDRAWN


@router.post("/events/{event_id}/decision")
async def decide_voice_event(
    event_id: str,
    body: DecisionRequest,
    user: dict = Depends(require_auth),
) -> dict[str, Any]:
    _load(event_id, user)
    try:
        return get_voice_pipeline().decide(user, event_id, body.decision)
    except VoiceError as err:
        raise _voice_http(err)


class ReviseRequest(BaseModel):
    objective: str | None = None
    requested_action: str | None = None
    requested_decision: str | None = None
    reason: str = "operator edit"


@router.post("/events/{event_id}/revise")
async def revise_voice_event(
    event_id: str,
    body: ReviseRequest,
    user: dict = Depends(require_auth),
) -> dict[str, Any]:
    _load(event_id, user)
    try:
        return get_voice_pipeline().revise(user, event_id, body.model_dump())
    except VoiceError as err:
        raise _voice_http(err)


@router.post("/events/{event_id}/authorize")
async def authorize_voice_event(event_id: str, user: dict = Depends(require_auth)) -> dict[str, Any]:
    _load(event_id, user)
    try:
        return get_voice_pipeline().authorize(user, event_id)
    except VoiceError as err:
        raise _voice_http(err)


@router.post("/events/{event_id}/execute")
async def execute_voice_event(event_id: str, user: dict = Depends(require_auth)) -> dict[str, Any]:
    _load(event_id, user)
    try:
        return get_voice_pipeline().execute(user, event_id)
    except VoiceError as err:
        raise _voice_http(err)


class VerifyRequest(BaseModel):
    verdict: str  # VERIFIED | INSUFFICIENT | CONTRADICTED
    claim: str = ""


@router.post("/events/{event_id}/verify")
async def verify_voice_event(
    event_id: str,
    body: VerifyRequest,
    user: dict = Depends(require_auth),
) -> dict[str, Any]:
    _load(event_id, user)
    try:
        return get_voice_pipeline().verify(user, event_id, body.verdict, body.claim)
    except VoiceError as err:
        raise _voice_http(err)


__all__ = ["router", "requires_approval", "VoiceStage"]
