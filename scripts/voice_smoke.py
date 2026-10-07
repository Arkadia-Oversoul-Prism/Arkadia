"""Arkadia Voice — end-to-end smoke harness (manual evidence tool).

Runs the complete voice chain against a temporary SQLite store without touching
the repository's runtime databases:

    status → audio capture+hash → ASR(TestProvider) → transcript → intent →
    context → proposal → approval → (blocked) authorization gates →
    authorize → execute → work event → evidence → verification → chain

Usage:
    python3 scripts/voice_smoke.py
"""
from __future__ import annotations

import base64
import json
import sys
import tempfile
import time
from pathlib import Path

# Sandbox every canonical store module BEFORE importing the app (mirrors the
# session fixtures in conftest.py, without reading any environment).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
_TMP = Path(tempfile.mkdtemp(prefix="voice_smoke_"))
for _name, _module in list(sys.modules.items()):
    if _name.startswith(("solspire.", "weaver.", "lab.")):
        if isinstance(getattr(_module, "_DB_PATH", None), str):
            _module._DB_PATH = str(_TMP / "solspire_projects.db")

import solspire.voice_store as vs  # noqa: E402
import solspire.workspace_manager as wm  # noqa: E402
import solspire.proposal_manager as pm  # noqa: E402
import solspire.workevent_manager as wem  # noqa: E402
import solspire.project_manager as projm  # noqa: E402
import solspire.eden_ops as eo  # noqa: E402
import weaver.enterprise_orchestration as ew  # noqa: E402

_DB = str(_TMP / "solspire_projects.db")
for _mod in (vs, wm, pm, wem, projm, eo, ew):
    _mod._DB_PATH = _DB

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from solspire.console_router import router  # noqa: E402

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def _b64(obj) -> str:
    return base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip("=")


def _token(uid: str = "voice-smoke", node_key: str = "zahrune") -> str:
    """Unsigned dev-mode JWT (mirrors web/console AuthContext) with a
    node_key claim so the identity resolves to an access_level-3 node."""
    payload = {"sub": uid, "user_id": uid, "email": f"{uid}@local"}
    if node_key:
        payload["node_key"] = node_key
    return f"{_b64({'alg': 'none', 'typ': 'JWT'})}.{_b64(payload)}."


HEADERS = {"Authorization": f"Bearer {_token()}"}
FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


def main() -> int:
    print("== GATE: status ==")
    r = client.get("/solspire/voice/status", headers=HEADERS)
    providers = [f"{p['name']}={p['state']}" for p in r.json()["asr"]["providers"]]
    check("status 200", r.status_code == 200, ", ".join(providers))

    print("== GATE: audio capture + hash ==")
    audio = b"\x1a\x45\xdfa" + b"x" * 512
    r = client.post(
        "/solspire/voice/events",
        headers=HEADERS,
        files={"file": ("clip.webm", audio, "audio/webm")},
        data={"provider": "test", "transcript_hint": "Create a project called Eden Pilot",
              "language": "en", "duration_ms": "1500"},
    )
    check("ingest 200", r.status_code == 200, r.text[:200] if r.status_code != 200 else "")
    if r.status_code != 200:
        return 1
    body = r.json()
    event_id = body["event"]["event_id"]
    check("audio hash recorded",
          bool(body["event"]["audio_hash"]) and len(body["event"]["audio_hash"]) == 64)
    check("transcript produced by provider", body["transcript"]["provider"] == "test")

    r = client.get(f"/solspire/voice/events/{event_id}/audio", headers=HEADERS)
    check("audio playback round-trip",
          r.status_code == 200 and r.content == audio,
          f"{len(r.content)} bytes")

    print("== GATE: intent + context ==")
    r = client.post(f"/solspire/voice/events/{event_id}/understand", headers=HEADERS, json={})
    understood = r.json() if r.status_code == 200 else {}
    check("understand 200", r.status_code == 200, r.text[:200] if r.status_code != 200 else "")
    check("intent CREATE", understood.get("intent", {}).get("action") == "CREATE")
    check("entity name extracted",
          understood.get("intent", {}).get("entities", {}).get("name") == "Eden Pilot")
    check("context KNOWN", understood.get("context", {}).get("resolution_status") == "KNOWN")
    check("requires proposal", understood.get("requires_proposal") is True)

    print("== GATE: proposal ==")
    r = client.post(f"/solspire/voice/events/{event_id}/propose", headers=HEADERS)
    check("propose 200", r.status_code == 200, r.text[:200] if r.status_code != 200 else "")
    if r.status_code != 200:
        return 1
    check("proposal PRESENTED", r.json()["proposal"]["proposal_status"] == "PRESENTED")
    check("risk MEDIUM", r.json()["voice_proposal"]["risk_level"] == "MEDIUM")

    print("== NEGATIVE: execution blocked without approval ==")
    r = client.post(f"/solspire/voice/events/{event_id}/execute", headers=HEADERS)
    check("409 APPROVAL_REQUIRED",
          r.status_code == 409 and r.json()["detail"]["state"] == "APPROVAL_REQUIRED",
          r.json().get("detail", {}).get("state", ""))

    print("== GATE: human approval ==")
    r = client.post(f"/solspire/voice/events/{event_id}/decision", headers=HEADERS,
                    json={"decision": "ACCEPTED"})
    check("decision ACCEPTED",
          r.status_code == 200 and r.json()["proposal"]["proposal_status"] == "ACCEPTED")

    print("== NEGATIVE: execution blocked without authorization ==")
    r = client.post(f"/solspire/voice/events/{event_id}/execute", headers=HEADERS)
    check("409 AUTHORIZATION_REQUIRED",
          r.status_code == 409 and r.json()["detail"]["state"] == "AUTHORIZATION_REQUIRED",
          r.json().get("detail", {}).get("state", ""))

    print("== NEGATIVE: authorization denied without govern authority ==")
    no_govern = {"Authorization": f"Bearer {_token(node_key=None)}"}
    r = client.post(f"/solspire/voice/events/{event_id}/authorize", headers=no_govern)
    check("403 AUTHORIZATION_DENIED",
          r.status_code == 403 and r.json()["detail"]["state"] == "AUTHORIZATION_DENIED",
          f"status={r.status_code}")

    print("== GATE: authorization (govern authority) ==")
    r = client.post(f"/solspire/voice/events/{event_id}/authorize", headers=HEADERS)
    check("authorize 200", r.status_code == 200, r.text[:300] if r.status_code != 200 else "")

    print("== GATE: execution + work event + evidence ==")
    t0 = time.time()
    r = client.post(f"/solspire/voice/events/{event_id}/execute", headers=HEADERS)
    check("execute 200", r.status_code == 200, r.text[:300] if r.status_code != 200 else "")
    if r.status_code == 200:
        body = r.json()
        check("executor completed", body["execution"]["status"] == "completed",
              f"{round(time.time() - t0, 2)}s")
        check("canonical work event", bool(body["work_event"]["work_event_id"]))
        check("evidence recorded", bool(body["evidence_id"]))
        check("verification PENDING (not conflated)", body["verification_state"] == "PENDING")
        check("project actually created",
              any(s.get("tool") == "project_create" and s.get("ok")
                  for s in body["execution"]["steps"]),
              json.dumps(body["execution"]["steps"])[:160])

        print("== GATE: verification (separate human act) ==")
        r = client.post(f"/solspire/voice/events/{event_id}/verify", headers=HEADERS,
                        json={"verdict": "VERIFIED"})
        check("verify 200 VERIFIED",
              r.status_code == 200 and r.json()["verdict"] == "VERIFIED",
              r.text[:200])

    print("== GATE: evidence chain ==")
    r = client.get(f"/solspire/voice/events/{event_id}/chain", headers=HEADERS)
    stages = r.json().get("stages", []) if r.status_code == 200 else []
    names = [s["stage"] for s in stages]
    print("     stages:", " -> ".join(names))
    expected = ["VOICE_EVENT", "TRANSCRIPT", "INTENT", "CONTEXT", "AUTHORITY",
                "PROPOSAL", "APPROVAL", "AUTHORIZATION", "EXECUTION", "RESULT",
                "WORK_EVENT", "EVIDENCE", "VERIFICATION"]
    check("full causal chain present", all(s in names for s in expected),
          f"missing={[s for s in expected if s not in names]}")
    check("chain digest computed", bool(r.json().get("chain_digest")))
    linked = all(
        stages[i]["prev_record_id"] == stages[i - 1]["record_id"]
        for i in range(1, len(stages))
    )
    check("every stage traceable backwards", linked)

    print("== NEGATIVE: unknown intent stays unresolved ==")
    r = client.post(
        "/solspire/voice/events", headers=HEADERS,
        files={"file": ("b.webm", b"\x1a\x45\xdfa" + b"y" * 64, "audio/webm")},
        data={"provider": "test", "transcript_hint": "purple monkey dishwasher"},
    )
    eid2 = r.json()["event"]["event_id"]
    client.post(f"/solspire/voice/events/{eid2}/understand", headers=HEADERS, json={})
    r = client.post(f"/solspire/voice/events/{eid2}/propose", headers=HEADERS)
    check("unknown intent blocked",
          r.status_code == 422 and r.json()["detail"]["state"] == "INTENT_UNKNOWN",
          f"status={r.status_code} state={r.json().get('detail', {}).get('state')}")

    print("== NEGATIVE: empty transcript ==")
    r = client.post(
        "/solspire/voice/events", headers=HEADERS,
        files={"file": ("c.webm", b"\x1a\x45\xdfa" + b"z" * 64, "audio/webm")},
        data={"provider": "test"},
    )
    check("TRANSCRIPT_EMPTY explicit",
          r.status_code == 422 and r.json()["detail"]["state"] == "TRANSCRIPT_EMPTY",
          f"status={r.status_code}")

    print("== NEGATIVE: unavailable provider ==")
    r = client.post(
        "/solspire/voice/events", headers=HEADERS,
        files={"file": ("d.webm", b"\x1a\x45\xdfa" + b"w" * 64, "audio/webm")},
        data={"provider": "natlas"},
    )
    check("ASR_UNAVAILABLE explicit (N-ATLAS not configured)",
          r.status_code == 503 and r.json()["detail"]["state"] == "ASR_UNAVAILABLE",
          f"status={r.status_code} {r.text[:160]}")

    print("== NEGATIVE: unauthenticated access ==")
    r = client.get("/solspire/voice/status")
    check("401 without auth", r.status_code == 401, f"status={r.status_code}")

    print()
    if FAILURES:
        print(f"SMOKE FAILED: {len(FAILURES)} checks: {FAILURES}")
        return 1
    print("SMOKE PASSED: all checks green")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
