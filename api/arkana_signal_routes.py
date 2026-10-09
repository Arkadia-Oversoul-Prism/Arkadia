"""Arkana Signal routes (ARK-01 Gate 01 audio boundary).

Extracted verbatim from api/main.py to restore the 2600-line architecture budget
(tests/architecture/test_layer_boundaries.py::test_api_main_line_count_within_budget).
Route paths, request/response shapes, and behaviour are unchanged. This is a
pure move, not a rewrite.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import uuid as _uuid_mod
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger("arkadia")

try:
    from api.auth import get_current_user as _get_current_user
except Exception:
    async def _get_current_user(request):
        return None

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

router = APIRouter(tags=["Arkana Signal"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_CANDIDATE_STATUSES = ("candidate", "unknown", "resolved", "uncertain_derived_signal")
_CONFIDENCE_KEY = "transcript"


def _as_confidence(value):
    """Coerce a model-supplied confidence to a schema-valid [0, 1] number.

    The canonical confidence map is number-only, so an absent, null, boolean or
    non-numeric reading must drop the key rather than write an invalid value.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return max(0.0, min(1.0, float(value)))


def _as_candidate(item):
    """Normalize one interpretation candidate to the schema's `$defs/candidate`.

    Every candidate requires a `status`; model output routinely omits it (the
    prompt asks for candidates, not for the enum). An omitted status is recorded
    as `unknown` rather than `candidate`, because nothing in the reading resolved
    it — and the contract reserves `candidate` for an explicit model assertion.
    Non-object entries are dropped, since they carry no evidence.
    """
    if not isinstance(item, dict):
        return None
    out = dict(item)
    status = out.get("status")
    if not isinstance(status, str) or status not in _CANDIDATE_STATUSES:
        status = "unknown"
    out["status"] = status
    return out


def _as_duration_ms(value):
    """Coerce a client-supplied duration to the schema's integer >= 0 or null."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _as_candidate_list(value):
    if not isinstance(value, list):
        return []
    out = []
    for item in value:
        norm = _as_candidate(item)
        if norm is not None:
            out.append(norm)
    return out


def _build_signal(*, signal_id, session_id, mime_type, duration_ms, raw_hash,
                  client_hash, client_streams, derived, model):
    """Assemble the ARK-01 evidence envelope.

    Kept separate from the route so a test can exercise the exact object the
    endpoint returns. Output conforms to
    `schemas/arkana/signal/1.0/arkana-signal.schema.json`.
    """
    confidence = _as_confidence(derived.get("transcript_confidence"))
    interpretation_confidence = {}
    if confidence is not None:
        interpretation_confidence[_CONFIDENCE_KEY] = confidence
    return {
        "schema": "arkana.signal",
        "schema_version": "1.0",
        "id": signal_id,
        "session_id": session_id,
        "created_at": _now_iso(),
        "source": {
            "type": "microphone",
            "modality": "audio",
            "format": mime_type,
            "duration_ms": _as_duration_ms(duration_ms),
        },
        "raw": {
            "asset_ref": f"client://indexeddb/arkana-signal/{signal_id}",
            "sha256": raw_hash,
            "client_sha256": client_hash,
            "inline_forwarded_for_inference": True,
        },
        "streams": {
            "speech": {"segments": derived.get("speech_segments", [])},
            "prosody": derived.get("prosody") or {},
            "acoustic": {**(derived.get("acoustic") or {}), "client": client_streams},
            "timing": {"duration_ms": duration_ms},
            "language": {"value": derived.get("language")},
        },
        "interpretation": {
            "transcript": {
                "text": derived.get("transcript"),
                "confidence": confidence,
                "status": "derived",
            },
            "intent_candidates": _as_candidate_list(derived.get("intent_candidates")),
            "entities": [e for e in (derived.get("entities") or []) if isinstance(e, dict)],
            "references": _as_candidate_list(derived.get("references")),
            "confidence": interpretation_confidence,
        },
        "provenance": {
            "derived_from": [signal_id],
            "processor": "arkana-signal-gate-01",
            "processor_version": "1.0",
            "model": model,
            "model_version": "current",
        },
        "integrity": {
            "raw_preserved": True,
            "interpretation_is_derived": True,
        },
    }


@router.post("/api/arkana/signal/ingest")
async def arkana_signal_ingest(request: Request):
    """ARKANA SIGNAL GATE 01: preserve one audio event and derive structured evidence."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    audio_b64 = (body.get("audio_base64") or "").strip()
    mime_type = (body.get("mime_type") or "audio/webm").strip()
    signal_id = (body.get("signal_id") or ("sig_" + str(_uuid_mod.uuid4()))).strip()
    session_id = (body.get("session_id") or ("session_" + str(_uuid_mod.uuid4()))).strip()
    duration_ms = body.get("duration_ms")
    client_streams = body.get("streams") or {}
    client_hash = (body.get("sha256") or "").strip() or None

    if not audio_b64:
        raise HTTPException(status_code=400, detail="audio_base64 is required")
    if len(audio_b64) > 12_000_000:
        raise HTTPException(status_code=413, detail="Audio payload too large for Gate 01 inline capture")

    try:
        raw_bytes = base64.b64decode(audio_b64, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail="audio_base64 is not valid base64")
    raw_hash = hashlib.sha256(raw_bytes).hexdigest()

    active_key = None
    try:
        node_user = await _get_current_user(request)
        uid = node_user.get("uid") if node_user else None
        if uid:
            from api.user_key_store import get_active_key_for_user
            active_key = get_active_key_for_user(uid)
    except Exception:
        pass
    if not active_key:
        try:
            from api.key_pool import acquire_key
            active_key = acquire_key() or GOOGLE_API_KEY
        except Exception:
            active_key = GOOGLE_API_KEY
    if not active_key:
        raise HTTPException(status_code=503, detail="No Gemini API key configured")

    prompt = """Analyze this audio for ARKANA SIGNAL GATE 01. Return JSON only.
Do not infer a factual emotional state or personality trait about the speaker.
Keep uncertain acoustic/prosodic observations explicitly uncertain.
Return exactly these top-level keys:
transcript, transcript_confidence, language, speech_segments, intent_candidates,
entities, references, prosody, acoustic.
Use null/unknown rather than inventing values. intent_candidates and references
must remain candidates unless the audio itself clearly resolves them.
For prosody, report observable/estimated properties such as speech_rate,
pauses, emphasis, pitch_contour, energy_contour and mark confidence/status.
For acoustic, report observable properties such as duration_ms, energy_rms,
peak_amplitude when available. Do not claim emotion as fact."""

    model = "gemini-3.8-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={active_key}"
    payload = {
        "contents": [{
            "role": "user",
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": mime_type, "data": audio_b64}},
            ],
        }],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
            "maxOutputTokens": 1800,
        },
    }
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        text_out = data["candidates"][0]["content"]["parts"][0]["text"]
        derived = json.loads(text_out)
    except Exception as e:
        logger.exception("[ARKANA-SIGNAL] multimodal derivation failed")
        raise HTTPException(status_code=502, detail=f"Signal interpretation failed: {e}")

    signal = _build_signal(
        signal_id=signal_id,
        session_id=session_id,
        mime_type=mime_type,
        duration_ms=duration_ms,
        raw_hash=raw_hash,
        client_hash=client_hash,
        client_streams=client_streams,
        derived=derived,
        model=model,
    )
    return {"signal": signal, "raw_audio_forwarded": True}


@router.post("/api/arkana/signal/respond")
async def arkana_signal_respond(request: Request):
    """Gate 01 runtime seam: Arkana receives raw audio plus its Signal Object."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    signal = body.get("signal")
    audio_b64 = (body.get("audio_base64") or "").strip()
    mime_type = (body.get("mime_type") or "audio/webm").strip()
    if not isinstance(signal, dict) or not audio_b64:
        raise HTTPException(status_code=400, detail="signal and audio_base64 are required")
    if len(audio_b64) > 12_000_000:
        raise HTTPException(status_code=413, detail="Audio payload too large for Gate 01")

    active_key = None
    try:
        node_user = await _get_current_user(request)
        uid = node_user.get("uid") if node_user else None
        if uid:
            from api.user_key_store import get_active_key_for_user
            active_key = get_active_key_for_user(uid)
    except Exception:
        pass
    if not active_key:
        try:
            from api.key_pool import acquire_key
            active_key = acquire_key() or GOOGLE_API_KEY
        except Exception:
            active_key = GOOGLE_API_KEY
    if not active_key:
        raise HTTPException(status_code=503, detail="No Gemini API key configured")

    system = """You are ARKANA at Signal Gate 01.
You receive BOTH the original human audio and a machine-readable Arkana Signal Object.
Treat the audio as source evidence and the Signal Object as derived interpretation.
Do not silently promote candidates into facts. If a reference is unresolved, say so.
Do not infer or state emotional/personality attributes as facts. Human authority remains absolute.
Respond directly to the human. Do not mention internal model mechanics unless relevant."""
    user_text = json.dumps({
        "signal_object": signal,
        "instruction": "Respond to the captured utterance using the raw audio and structured evidence together."
    }, ensure_ascii=False)
    model = "gemini-3.8-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={active_key}"
    payload = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{
            "role": "user",
            "parts": [
                {"text": user_text},
                {"inline_data": {"mime_type": mime_type, "data": audio_b64}},
            ],
        }],
        "generationConfig": {"temperature": 0.65, "maxOutputTokens": 1400},
    }
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        reply = data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logger.exception("[ARKANA-SIGNAL] multimodal response failed")
        raise HTTPException(status_code=502, detail=f"Signal response failed: {e}")

    response_id = "gen_" + str(_uuid_mod.uuid4())
    return {
        "response": {
            "schema": "arkana.generated_media",
            "schema_version": "1.0",
            "id": response_id,
            "derived_from": [signal.get("id")],
            "generation_intent": "spoken_response",
            "text": reply,
            "provenance": {
                "reasoning_ref": response_id,
                "processor": "arkana-signal-gate-01",
                "model": model,
                "model_version": "current",
                "created_at": _now_iso(),
            },
        }
    }
