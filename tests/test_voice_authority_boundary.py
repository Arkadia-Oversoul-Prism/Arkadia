"""Arkadia Voice — authority-boundary reuse guard.

Arkadia Voice (`solspire/voice_pipeline.py`) shipped on `main` in `74e8ea5` (a commit
with no associated pull request) and touches the authority boundary: it extracted
`authorize_proposal_sync` out of the `/proposals/{id}/authorize` route handler and added
`project_update` to the canonical `ExecutionRuntime`. Its own module docstring states the
security property — "Voice creates no second executor, no second proposal ledger, no second
authority" — but none of the 118 tests that shipped with it pin that property. Deleting the
canonical authority hop and minting a local authorization would leave every existing voice
test green.

This guard proves the property against the real code path, so removing it fails CI:

* the HumanAuthorityEvent and Authorization rows the voice `authorize` step persists are the
  canonical rows, written by the canonical boundary;
* the voice pipeline reaches authorization *through* `authorize_proposal_sync` (spied);
* the blocked path mints nothing;
* the pipeline source decides no proposal and writes no authority ledger of its own.

The canonical enterprise store is a SQLite database addressed by `_DB_PATH`, so the row
probes must operate on a *materialised* schema — the store creates its tables lazily on the
first operation, not in the constructor.
"""
from __future__ import annotations

import inspect
import sqlite3
import uuid

import pytest

from solspire.voice_pipeline import VoiceError, get_voice_pipeline


@pytest.fixture()
def voice_db(tmp_path, monkeypatch):
    db = str(tmp_path / "voice_authority.db")
    import solspire.eden_ops as eo
    import solspire.project_manager as projm
    import solspire.proposal_manager as pm
    import solspire.voice_store as vs
    import solspire.workevent_manager as wem
    import solspire.workspace_manager as wm
    import weaver.enterprise_orchestration as ew

    for mod in (vs, wm, pm, wem, projm, eo, ew):
        monkeypatch.setattr(mod, "_DB_PATH", db)
    # The enterprise store resolves _DB_PATH in its constructor but creates its tables
    # lazily on the first operation. Materialise the schema now so the row probes in this
    # file read a real table instead of measuring an uninitialised database.
    with ew._db():
        pass
    return db


def _user(govern: bool = True, uid: str | None = None) -> dict:
    return {
        "uid": uid or f"voice-{uuid.uuid4().hex[:12]}",
        "role": "Flamekeeper" if govern else "Guest",
        "access_level": 3 if govern else 0,
    }


def _ingest(user: dict, hint: str) -> str:
    result = get_voice_pipeline().ingest(
        user,
        audio=b"\x1a\x45\xdfa" + hint.encode()[:64] + uuid.uuid4().bytes,
        mime="audio/webm",
        provider="test",
        transcript_hint=hint,
        duration_ms=1000,
    )
    return result["event"]["event_id"]


def _chain_to_authorized(user: dict) -> tuple[str, dict]:
    """Drive the real pipeline to an authorized CREATE event; return (event_id, result)."""
    pipeline = get_voice_pipeline()
    name = f"Voice Boundary {uuid.uuid4().hex[:10]}"
    event_id = _ingest(user, f"Create a project called {name}")
    pipeline.understand(user, event_id)
    pipeline.propose(user, event_id)
    pipeline.decide(user, event_id, "ACCEPTED")
    authorized = pipeline.authorize(user, event_id)
    return event_id, authorized


def _rows(db: str, table: str, subject: str) -> list[sqlite3.Row]:
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    try:
        return list(
            conn.execute(f"SELECT * FROM {table} WHERE subject=?", (subject,)).fetchall()
        )
    finally:
        conn.close()


# ── canonical authority is persisted, not simulated ──────────────────────────

def test_voice_authorize_persists_the_canonical_human_authority_event(voice_db):
    pipeline = get_voice_pipeline()
    user = _user()
    event_id, authorized = _chain_to_authorized(user)

    hae = authorized["human_authority_event"]
    assert hae["origin"] == "human", "authority must originate from a human gesture"
    assert hae["action"] == "APPROVE_PROPOSAL"
    assert hae["authentication_context"] == "firebase_id_token"
    assert hae["subject"] == user["uid"]

    rows = _rows(voice_db, "ew_authority_events", user["uid"])
    ids = {r["id"] for r in rows}
    assert hae["id"] in ids, "the voice authorize step must persist the canonical HAE row"

    # the HAE is bound to the event's proposal lineage, not a voice-local id
    event = pipeline.get(user, event_id)["event"]
    assert hae["correlation_id"] == f"solariun-proposal:{event['proposal_id']}:v1"


def test_voice_authorize_persists_a_real_authorization_row(voice_db):
    user = _user()
    _, authorized = _chain_to_authorized(user)

    authorization = authorized["authorization"]
    rows = _rows(voice_db, "ew_authorizations", user["uid"])
    assert authorization["id"] in {r["id"] for r in rows}
    assert authorization["authority_event_id"] == authorized["human_authority_event"]["id"]
    assert authorization["subject"] == user["uid"]


# ── the pipeline reaches authorization through the canonical boundary only ────

def test_voice_pipeline_reuses_the_canonical_authorization_boundary(voice_db, monkeypatch):
    """The voice authorize step must *call* the canonical boundary, not reimplement it."""
    import solspire.console_authority_router as car

    calls: list[str] = []
    real = car.authorize_proposal_sync

    def spy(proposal_id, body, user):
        calls.append(proposal_id)
        return real(proposal_id, body, user)

    monkeypatch.setattr(car, "authorize_proposal_sync", spy)

    user = _user()
    event_id, authorized = _chain_to_authorized(user)

    assert len(calls) == 1, "voice authorize must route through authorize_proposal_sync exactly once"
    assert authorized["authorization"]["id"], "the canonical boundary must mint the authorization"


def test_blocked_authorization_mints_no_authority_row(voice_db):
    """Without human approval no authorization row may exist — the canonical guard holds."""
    pipeline = get_voice_pipeline()
    user = _user()
    event_id = _ingest(user, f"Create a project called Nope {uuid.uuid4().hex[:8]}")
    pipeline.understand(user, event_id)
    pipeline.propose(user, event_id)
    # no decide() — approval is missing, so authorization must refuse

    with pytest.raises(VoiceError) as exc:
        pipeline.authorize(user, event_id)
    assert exc.value.state == "APPROVAL_REQUIRED"

    assert _rows(voice_db, "ew_authorizations", user["uid"]) == []
    assert _rows(voice_db, "ew_authority_events", user["uid"]) == []


# ── no parallel authority ledger in the pipeline source ──────────────────────

def _mints_authority_locally(source: str) -> list[str]:
    """Return the local-authority constructs present in a module source string."""
    forbidden = (
        "EdenOps(",
        "INSERT INTO ew_authorizations",
        "INSERT INTO ew_authority_events",
        "def authorize_proposal",
    )
    return [needle for needle in forbidden if needle in source]


def test_voice_pipeline_decides_no_proposal_and_writes_no_authority_ledger():
    import solspire.voice_pipeline as vp

    source = inspect.getsource(vp)
    assert "authorize_proposal_sync" in source, "the canonical boundary must be referenced"
    assert _mints_authority_locally(source) == [], (
        "voice_pipeline must not decide a proposal or write an authority ledger itself"
    )


def test_local_authority_detector_flags_the_parallel_form():
    """Negative control: the detector must catch a second-authority construct."""
    bad = (
        "from solspire.eden_ops import EdenOps\n"
        "EdenOps(store).decide_proposal(...)\n"
        "conn.execute('INSERT INTO ew_authorizations ...')\n"
    )
    flagged = _mints_authority_locally(bad)
    assert "EdenOps(" in flagged
    assert "INSERT INTO ew_authorizations" in flagged
