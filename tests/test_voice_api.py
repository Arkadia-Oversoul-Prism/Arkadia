"""Arkadia Voice — HTTP surface tests (Phase 11 backend contract).

Boots the canonical ``/solspire`` router (which mounts ``/voice``) behind a
TestClient and exercises the routes exactly as the operator UI does:

  * authentication is required (401 without a subject)
  * the full chain works over HTTP
  * subject scoping holds (another subject's event is 404)
  * every failure returns its canonical error state with recovery guidance
"""
from __future__ import annotations

import base64
import json
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture()
def voice_db(tmp_path, monkeypatch):
    db = str(tmp_path / "voice_api.db")
    import solspire.eden_ops as eo
    import solspire.project_manager as projm
    import solspire.proposal_manager as pm
    import solspire.voice_store as vs
    import solspire.workevent_manager as wem
    import solspire.workspace_manager as wm
    import weaver.enterprise_orchestration as ew

    for mod in (vs, wm, pm, wem, projm, eo, ew):
        monkeypatch.setattr(mod, "_DB_PATH", db)
    return db


@pytest.fixture()
def client(voice_db):
    from solspire.console_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _b64(obj) -> str:
    return base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip("=")


def _token(uid: str, node_key: str | None = "zahrune") -> str:
    """Unsigned dev-mode JWT (the substrate's dev-mode identity contract)."""
    payload = {"sub": uid, "user_id": uid, "email": f"{uid}@local"}
    if node_key:
        payload["node_key"] = node_key
    return f"{_b64({'alg': 'none', 'typ': 'JWT'})}.{_b64(payload)}."


def _headers(uid: str | None = None, node_key: str | None = "zahrune") -> dict:
    uid = uid or f"voice-api-{uuid.uuid4().hex[:10]}"
    return {"Authorization": f"Bearer {_token(uid, node_key)}"}


def _capture(client, headers, hint, provider="test", extra=None):
    data = {"provider": provider, "language": "en", "duration_ms": "900"}
    if hint is not None:
        data["transcript_hint"] = hint
    if extra:
        data.update(extra)
    return client.post(
        "/solspire/voice/events",
        headers=headers,
        files={"file": ("clip.webm", b"\x1a\x45\xdfa" + uuid.uuid4().bytes * 4,
                        "audio/webm")},
        data=data,
    )


# ── authentication ───────────────────────────────────────────────────────────

def test_voice_requires_authentication(client):
    assert client.get("/solspire/voice/status").status_code == 401
    assert client.get("/solspire/voice/events").status_code == 401
    assert client.post("/solspire/voice/events").status_code == 401


def test_status_shape_and_provider_states(client):
    headers = _headers()
    body = client.get("/solspire/voice/status", headers=headers).json()
    assert body["surface"] == "arkadia_voice"
    assert "VOICE_EVENT" in body["chain"] and "VERIFICATION" in body["chain"]
    assert "MICROPHONE_DENIED" in body["error_states"]
    names = {p["name"] for p in body["asr"]["providers"]}
    assert names == {"test", "local", "natlas", "cloud"}
    # The subject identity is visible to the operator surface.
    assert body["subject"]["access_level"] >= 0


def test_providers_route_lists_all_providers(client):
    body = client.get("/solspire/voice/providers", headers=_headers()).json()
    assert {p["name"] for p in body["providers"]} == {"test", "local", "natlas", "cloud"}
    assert body["selection_env"] == "ARKADIA_VOICE_ASR_PROVIDER"


# ── full chain over HTTP ─────────────────────────────────────────────────────

def test_full_voice_chain_over_http(client):
    headers = _headers()
    name = f"Voice HTTP {uuid.uuid4().hex[:10]}"

    # capture → transcript
    r = _capture(client, headers, f"Create a project called {name}")
    assert r.status_code == 200, r.text
    event_id = r.json()["event"]["event_id"]
    assert r.json()["event"]["audio_hash"]
    assert r.json()["transcript"]["provider"] == "test"

    # audio playback round-trip (same bytes back)
    audio = client.get(f"/solspire/voice/events/{event_id}/audio", headers=headers)
    assert audio.status_code == 200
    assert audio.content.startswith(b"\x1a\x45\xdfa")
    assert len(audio.headers["x-arkadia-audio-sha256"]) == 64

    # understand → intent + context + authority
    r = client.post(f"/solspire/voice/events/{event_id}/understand", headers=headers,
                    json={})
    assert r.status_code == 200
    body = r.json()
    assert body["intent"]["action"] == "CREATE"
    assert body["context"]["resolution_status"] == "KNOWN"
    assert body["authority"]["required_approval"] is True

    # proposal
    r = client.post(f"/solspire/voice/events/{event_id}/propose", headers=headers)
    assert r.status_code == 200
    assert r.json()["voice_proposal"]["risk_level"] == "MEDIUM"
    proposal_id = r.json()["proposal"]["proposal_id"]

    # approval gates execution
    r = client.post(f"/solspire/voice/events/{event_id}/execute", headers=headers)
    assert r.status_code == 409
    assert r.json()["detail"]["state"] == "APPROVAL_REQUIRED"
    assert r.json()["detail"]["recovery"]

    # human decision
    r = client.post(f"/solspire/voice/events/{event_id}/decision", headers=headers,
                    json={"decision": "ACCEPTED"})
    assert r.status_code == 200
    assert r.json()["proposal"]["proposal_status"] == "ACCEPTED"

    # authorization still required after approval
    r = client.post(f"/solspire/voice/events/{event_id}/execute", headers=headers)
    assert r.status_code == 409
    assert r.json()["detail"]["state"] == "AUTHORIZATION_REQUIRED"

    # govern authority via node_key claim (access_level 3)
    r = client.post(f"/solspire/voice/events/{event_id}/authorize", headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["authorization"]["id"]

    # execution → work event → evidence
    r = client.post(f"/solspire/voice/events/{event_id}/execute", headers=headers)
    assert r.status_code == 200, r.text
    executed = r.json()
    assert executed["execution"]["status"] == "completed"
    assert executed["verification_state"] == "PENDING"
    assert executed["work_event"]["work_event_id"]

    # verification (separate act)
    r = client.post(f"/solspire/voice/events/{event_id}/verify", headers=headers,
                    json={"verdict": "VERIFIED"})
    assert r.status_code == 200
    assert r.json()["verdict"] == "VERIFIED"

    # evidence timeline
    r = client.get(f"/solspire/voice/events/{event_id}/chain", headers=headers)
    assert r.status_code == 200
    stages = [s["stage"] for s in r.json()["stages"]]
    for expected in ("VOICE_EVENT", "TRANSCRIPT", "INTENT", "CONTEXT", "AUTHORITY",
                     "PROPOSAL", "APPROVAL", "AUTHORIZATION", "EXECUTION", "RESULT",
                     "WORK_EVENT", "EVIDENCE", "VERIFICATION"):
        assert expected in stages
    assert r.json()["chain_digest"]

    # full event view exposes the typed linkage
    r = client.get(f"/solspire/voice/events/{event_id}", headers=headers)
    event = r.json()["event"]
    assert event["proposal_id"] == proposal_id
    assert event["approval_ref"]
    assert event["execution_id"]
    assert event["work_event_id"]
    assert event["evidence_ref"]
    assert event["verification_ref"]


def test_informational_chain_over_http(client):
    headers = _headers()
    r = _capture(client, headers, "find the vault index")
    event_id = r.json()["event"]["event_id"]
    body = client.post(f"/solspire/voice/events/{event_id}/understand",
                       headers=headers, json={}).json()
    assert body["requires_proposal"] is False
    assert body["authority"]["authority_status"] == "OBSERVATION_ONLY"

    proposed = client.post(f"/solspire/voice/events/{event_id}/propose",
                           headers=headers).json()
    assert proposed["proposal"] is None

    r = client.post(f"/solspire/voice/events/{event_id}/execute", headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["execution"]["status"] == "completed"


# ── subject scoping ──────────────────────────────────────────────────────────

def test_event_is_invisible_to_another_subject(client):
    owner = _headers(uid=f"voice-owner-{uuid.uuid4().hex[:8]}")
    stranger = _headers(uid=f"voice-stranger-{uuid.uuid4().hex[:8]}")
    event_id = _capture(client, owner, "find something").json()["event"]["event_id"]

    assert client.get(f"/solspire/voice/events/{event_id}",
                      headers=stranger).status_code == 404
    assert client.get(f"/solspire/voice/events/{event_id}/chain",
                      headers=stranger).status_code == 404
    assert client.get(f"/solspire/voice/events/{event_id}/audio",
                      headers=stranger).status_code == 404
    assert client.post(f"/solspire/voice/events/{event_id}/understand",
                       headers=stranger, json={}).status_code == 404


# ── explicit error states over HTTP ──────────────────────────────────────────

def test_natlas_unavailable_is_503_with_recovery(client):
    r = _capture(client, _headers(), "create project called X", provider="natlas")
    assert r.status_code == 503
    detail = r.json()["detail"]
    assert detail["state"] == "ASR_UNAVAILABLE"
    assert "OFFICIAL_ACCESS_NOT_CONFIGURED" in detail["detail"]
    assert detail["recovery"]


def test_unknown_provider_is_rejected(client):
    r = _capture(client, _headers(), "hello", provider="not-a-provider")
    assert r.status_code == 503
    assert r.json()["detail"]["state"] == "ASR_UNAVAILABLE"


def test_empty_transcript_is_422(client):
    r = _capture(client, _headers(), None)
    assert r.status_code == 422
    assert r.json()["detail"]["state"] == "TRANSCRIPT_EMPTY"


def test_unknown_intent_propose_is_422(client):
    headers = _headers()
    event_id = _capture(client, headers, "purple monkey dishwasher").json()["event"]["event_id"]
    client.post(f"/solspire/voice/events/{event_id}/understand", headers=headers, json={})
    r = client.post(f"/solspire/voice/events/{event_id}/propose", headers=headers)
    assert r.status_code == 422
    assert r.json()["detail"]["state"] == "INTENT_UNKNOWN"


def test_verify_before_execute_is_pending(client):
    headers = _headers()
    event_id = _capture(client, headers, "find the vault index").json()["event"]["event_id"]
    r = client.post(f"/solspire/voice/events/{event_id}/verify", headers=headers,
                    json={"verdict": "VERIFIED"})
    assert r.status_code == 409
    assert r.json()["detail"]["state"] == "VERIFICATION_PENDING"


def test_unsupported_verdict_is_explicit(client):
    headers = _headers()
    event_id = _capture(client, headers, "find the vault index").json()["event"]["event_id"]
    client.post(f"/solspire/voice/events/{event_id}/understand", headers=headers, json={})
    client.post(f"/solspire/voice/events/{event_id}/execute", headers=headers)
    r = client.post(f"/solspire/voice/events/{event_id}/verify", headers=headers,
                    json={"verdict": "MAYBE"})
    assert r.status_code == 409
    assert r.json()["detail"]["state"] == "VERIFICATION_FAILED"


def test_oversized_audio_is_rejected(client):
    headers = _headers()
    r = client.post(
        "/solspire/voice/events",
        headers=headers,
        files={"file": ("big.webm", b"\x1a\x45\xdfa" + b"x" * (6 * 1024 * 1024),
                        "audio/webm")},
        data={"provider": "test", "transcript_hint": "hello"},
    )
    assert r.status_code == 400
    assert r.json()["detail"]["state"] == "AUDIO_CAPTURE_FAILED"


def test_unknown_event_id_is_404(client):
    headers = _headers()
    assert client.get("/solspire/voice/events/VE-does-not-exist",
                      headers=headers).status_code == 404
