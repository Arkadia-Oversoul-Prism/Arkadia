"""Arkadia Voice — integration + negative tests (Phases 4–10).

Proves the full causal chain over canonical primitives:

    audio → transcript → intent → context → proposal → approval →
    authorization → execution → work event → evidence → verification

and every required negative path:

    unknown user blocked · unauthorized target blocked · ambiguous context →
    clarification · missing approval → execution blocked · missing
    authorization → execution blocked · non-govern principal → authorization
    denied · ASR unavailable → explicit state · execution failure → evidence
    preserved · human-only operation refused · unknown intent blocked
"""
from __future__ import annotations

import uuid

import pytest

from solspire.voice_contracts import VOICE_ERROR_STATES
from solspire.voice_pipeline import VoiceError, get_voice_pipeline


@pytest.fixture()
def voice_db(tmp_path, monkeypatch):
    db = str(tmp_path / "voice_pipe.db")
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


def _user(govern: bool = True, uid: str | None = None) -> dict:
    return {
        "uid": uid or f"voice-{uuid.uuid4().hex[:12]}",
        "role": "Flamekeeper" if govern else "Guest",
        "access_level": 3 if govern else 0,
    }


def _ingest(user: dict, hint: str, provider: str = "test") -> str:
    result = get_voice_pipeline().ingest(
        user,
        audio=b"\x1a\x45\xdfa" + hint.encode()[:64] + uuid.uuid4().bytes,
        mime="audio/webm",
        provider=provider,
        transcript_hint=hint,
        duration_ms=1000,
    )
    return result["event"]["event_id"]


# ── GATE: full integration path ──────────────────────────────────────────────

def test_full_chain_audio_to_verified_evidence(voice_db):
    pipeline = get_voice_pipeline()
    user = _user()
    name = f"Voice Chain {uuid.uuid4().hex[:10]}"

    # audio → transcript
    event_id = _ingest(user, f"Create a project called {name}")
    view = pipeline.get(user, event_id)
    assert view["event"]["audio_hash"] and len(view["event"]["audio_hash"]) == 64
    assert view["event"]["transcript"]["text"].startswith("Create a project")
    assert view["event"]["asr_provenance"]["provider"] == "test"

    # transcript → intent → context → authority
    understood = pipeline.understand(user, event_id)
    assert understood["intent"]["action"] == "CREATE"
    assert understood["context"]["resolution_status"] == "KNOWN"
    assert understood["authority"]["required_approval"] is True
    assert understood["authority"]["authority_status"] == "GOVERN_AUTHORITY_REQUIRED"
    assert understood["error"] is None

    # proposal
    proposed = pipeline.propose(user, event_id)
    proposal_id = proposed["proposal"]["proposal_id"]
    assert proposed["proposal"]["proposal_status"] == "PRESENTED"
    assert proposed["voice_proposal"]["risk_level"] == "MEDIUM"

    # missing approval blocks execution
    with pytest.raises(VoiceError) as exc:
        pipeline.execute(user, event_id)
    assert exc.value.state == "APPROVAL_REQUIRED"

    # human approval (canonical record_decision)
    decided = pipeline.decide(user, event_id, "ACCEPTED")
    assert decided["proposal"]["proposal_status"] == "ACCEPTED"
    approval_id = decided["approval_id"]
    assert approval_id

    # approval is not authorization: execution still blocked
    with pytest.raises(VoiceError) as exc:
        pipeline.execute(user, event_id)
    assert exc.value.state == "AUTHORIZATION_REQUIRED"

    # authorization (govern authority enforced inside the canonical boundary)
    authorized = pipeline.authorize(user, event_id)
    assert authorized["authorization"]["id"]

    # execution → canonical executor + work event + evidence
    executed = pipeline.execute(user, event_id)
    assert executed["execution"]["status"] == "completed"
    assert executed["verification_state"] == "PENDING"
    assert executed["work_event"]["work_event_id"]
    assert executed["evidence_id"]

    # project really exists (executor effect)
    from solspire.project_manager import get_project_manager
    projects = [p for p in get_project_manager().list_projects() if p.name == name]
    assert len(projects) == 1

    # verification is a separate human act
    verified = pipeline.verify(user, event_id, "VERIFIED")
    assert verified["verdict"] == "VERIFIED"

    # evidence chain: complete, ordered, backwards-traceable
    chain = pipeline.chain(user, event_id)
    stages = [s["stage"] for s in chain["stages"]]
    for expected in ("VOICE_EVENT", "TRANSCRIPT", "INTENT", "CONTEXT", "AUTHORITY",
                     "PROPOSAL", "APPROVAL", "AUTHORIZATION", "EXECUTION", "RESULT",
                     "WORK_EVENT", "EVIDENCE", "VERIFICATION"):
        assert expected in stages, f"missing {expected}"
    for i in range(1, len(chain["stages"])):
        assert chain["stages"][i]["prev_record_id"] == chain["stages"][i - 1]["record_id"]
    assert chain["chain_digest"]

    # linkage: proposal → approval → execution → work event → evidence → verification
    event = pipeline.get(user, event_id)["event"]
    assert event["proposal_id"] == proposal_id
    assert event["approval_ref"] == approval_id
    assert event["execution_id"] == executed["execution"]["execution_id"]
    assert event["work_event_id"] == executed["work_event"]["work_event_id"]
    assert event["evidence_ref"] == executed["evidence_id"]
    assert event["verification_ref"] == verified["verification"]["id"]

    # authorized execution references the canonical execution-bound WorkEvent
    from solspire.workevent_manager import get_workevent_manager
    attempt_id = executed["execution"].get("attempt_id")
    we = get_workevent_manager().get(event["work_event_id"], user["uid"])
    assert we is not None
    assert we.subject_ref == user["uid"]


def test_informational_request_needs_no_proposal_or_approval(voice_db):
    pipeline = get_voice_pipeline()
    user = _user()
    token = uuid.uuid4().hex[:10]
    from knowledge.pipeline import ingest
    ingest(title=f"Voice Pipe Doc {token}", content="pipeline observation body",
           note_type="note", user_id=user["uid"],
           auto_tag=False, auto_embed=False, auto_link=False)

    event_id = _ingest(user, f"find Voice Pipe Doc {token}")
    understood = pipeline.understand(user, event_id)
    assert understood["intent"]["action"] == "SEARCH"
    assert understood["authority"]["required_approval"] is False
    assert understood["authority"]["authority_status"] == "OBSERVATION_ONLY"
    assert understood["requires_proposal"] is False

    proposed = pipeline.propose(user, event_id)
    assert proposed["proposal"] is None
    assert "no proposal" in proposed["note"]

    executed = pipeline.execute(user, event_id)  # no approval, no authorization
    assert executed["execution"]["status"] == "completed"
    assert executed["execution"]["observation"]["count"] >= 1
    assert executed["verification_state"] == "PENDING"

    verified = pipeline.verify(user, event_id, "VERIFIED")
    assert verified["verdict"] == "VERIFIED"

    stages = [s["stage"] for s in pipeline.chain(user, event_id)["stages"]]
    assert "EXECUTION" in stages and "EVIDENCE" in stages and "VERIFICATION" in stages
    # observation requests legitimately skip proposal/approval/authorization
    assert "PROPOSAL" not in stages
    assert "APPROVAL" not in stages


# ── negative: identity / ownership ───────────────────────────────────────────

def test_unknown_user_cannot_read_another_subjects_event(voice_db):
    pipeline = get_voice_pipeline()
    owner = _user()
    stranger = _user()
    event_id = _ingest(owner, "find the vault policy")
    with pytest.raises(LookupError):
        pipeline.get(stranger, event_id)
    with pytest.raises(LookupError):
        pipeline.chain(stranger, event_id)


def test_unauthenticated_voice_status_contract_exists(voice_db):
    # Router-level auth is covered in test_voice_api; here we assert the error
    # catalog every failure surface depends on.
    assert VOICE_ERROR_STATES["AUTHORIZATION_DENIED"]["recovery"]


def test_foreign_project_target_blocks_proposal(voice_db):
    pipeline = get_voice_pipeline()
    user = _user()
    name = f"Voice Owned {uuid.uuid4().hex[:10]}"
    from solspire.project_manager import get_project_manager
    get_project_manager().create(name, owner_uid="someone-else")

    event_id = _ingest(user, f"rename project {name} to Stolen")
    pipeline.understand(user, event_id)
    with pytest.raises(VoiceError) as exc:
        pipeline.propose(user, event_id)
    assert exc.value.state == "AUTHORIZATION_DENIED"


# ── negative: ambiguity → clarification ──────────────────────────────────────

def test_ambiguous_context_blocks_proposal_until_clarified(voice_db):
    pipeline = get_voice_pipeline()
    user = _user()
    token = uuid.uuid4().hex[:10]
    from solspire.project_manager import get_project_manager
    get_project_manager().create(f"Voice Amb A {token}", owner_uid=user["uid"])
    get_project_manager().create(f"Voice Amb B {token}", owner_uid=user["uid"])

    event_id = _ingest(user, "rename project Voice Amb to Nope")
    understood = pipeline.understand(user, event_id)
    assert understood["context"]["resolution_status"] == "AMBIGUOUS"
    assert understood["error"]["state"] == "CONTEXT_AMBIGUOUS"

    with pytest.raises(VoiceError) as exc:
        pipeline.propose(user, event_id)
    assert exc.value.state == "CONTEXT_AMBIGUOUS"

    # clarify: operator names the exact target → resolution becomes KNOWN
    clarified = pipeline.understand(
        user, event_id, {"target": f"Voice Amb A {token}"})
    assert clarified["context"]["resolution_status"] == "KNOWN"
    proposed = pipeline.propose(user, event_id)
    assert proposed["proposal"]["proposal_status"] == "PRESENTED"

    # the clarification itself is on the evidence chain
    stages = [s["stage"] for s in pipeline.chain(user, event_id)["stages"]]
    assert "CLARIFICATION" in stages


def test_unknown_context_blocks_proposal(voice_db):
    pipeline = get_voice_pipeline()
    user = _user()
    event_id = _ingest(user, f"rename project Voice Missing {uuid.uuid4().hex[:8]} to X")
    pipeline.understand(user, event_id)
    with pytest.raises(VoiceError) as exc:
        pipeline.propose(user, event_id)
    assert exc.value.state == "CONTEXT_UNKNOWN"


# ── negative: unknown intent / human-only ────────────────────────────────────

def test_unknown_intent_never_reaches_a_proposal(voice_db):
    pipeline = get_voice_pipeline()
    user = _user()
    event_id = _ingest(user, "purple monkey dishwasher")
    understood = pipeline.understand(user, event_id)
    assert understood["intent"]["action"] == "UNKNOWN"
    assert understood["error"]["state"] == "INTENT_UNKNOWN"
    with pytest.raises(VoiceError) as exc:
        pipeline.propose(user, event_id)
    assert exc.value.state == "INTENT_UNKNOWN"
    with pytest.raises(VoiceError) as exc:
        pipeline.execute(user, event_id)
    assert exc.value.state == "INTENT_UNKNOWN"


def test_human_only_operation_is_refused_by_voice(voice_db):
    pipeline = get_voice_pipeline()
    user = _user()  # even a govern-holding subject cannot dispatch by voice
    event_id = _ingest(user, "merge the pull request")
    understood = pipeline.understand(user, event_id)
    assert understood["intent"]["requested_effect"] == "REFUSED_HUMAN_ONLY"
    with pytest.raises(VoiceError) as exc:
        pipeline.propose(user, event_id)
    assert exc.value.state == "AUTHORITY_MISSING"
    with pytest.raises(VoiceError) as exc:
        pipeline.execute(user, event_id)
    assert exc.value.state == "AUTHORITY_MISSING"


# ── negative: authority / authorization ──────────────────────────────────────

def test_non_govern_principal_cannot_authorize(voice_db):
    pipeline = get_voice_pipeline()
    user = _user(govern=False)
    name = f"Voice NoGov {uuid.uuid4().hex[:10]}"
    event_id = _ingest(user, f"Create a project called {name}")
    pipeline.understand(user, event_id)
    pipeline.propose(user, event_id)
    pipeline.decide(user, event_id, "ACCEPTED")

    with pytest.raises(VoiceError) as exc:
        pipeline.authorize(user, event_id)
    assert exc.value.state == "AUTHORIZATION_DENIED"
    # failure is evidence
    stages = [s for s in pipeline.chain(user, event_id)["stages"]
              if s["stage"] == "ERROR"]
    assert stages and stages[-1]["payload"]["state"] == "AUTHORIZATION_DENIED"


def test_declined_proposal_blocks_execution(voice_db):
    pipeline = get_voice_pipeline()
    user = _user()
    name = f"Voice Declined {uuid.uuid4().hex[:10]}"
    event_id = _ingest(user, f"Create a project called {name}")
    pipeline.understand(user, event_id)
    pipeline.propose(user, event_id)
    pipeline.decide(user, event_id, "DECLINED")
    with pytest.raises(VoiceError) as exc:
        pipeline.execute(user, event_id)
    assert exc.value.state == "APPROVAL_REQUIRED"


# ── negative: ASR availability ───────────────────────────────────────────────

def test_asr_unavailable_is_explicit_and_persisted(voice_db):
    pipeline = get_voice_pipeline()
    user = _user()
    with pytest.raises(VoiceError) as exc:
        _ingest(user, "create project called X", provider="natlas")
    assert exc.value.state == "ASR_UNAVAILABLE"
    event_id = exc.value.extra.get("event_id")
    assert event_id
    event = pipeline.get(user, event_id)["event"]
    assert event["error_state"] == "ASR_UNAVAILABLE"
    stages = [s["stage"] for s in pipeline.chain(user, event_id)["stages"]]
    assert "ERROR" in stages  # evidence of the failure is preserved


def test_empty_transcript_is_explicit(voice_db):
    pipeline = get_voice_pipeline()
    user = _user()
    with pytest.raises(VoiceError) as exc:
        pipeline.ingest(user, audio=b"\x1a\x45\xdfa-no-hint", mime="audio/webm",
                        provider="test")
    assert exc.value.state == "TRANSCRIPT_EMPTY"


def test_empty_audio_is_rejected(voice_db):
    with pytest.raises(VoiceError) as exc:
        get_voice_pipeline().ingest(_user(), audio=b"", provider="test")
    assert exc.value.state == "AUDIO_EMPTY"


# ── negative: execution failure preserves evidence ───────────────────────────

def test_execution_failure_preserves_evidence(voice_db):
    pipeline = get_voice_pipeline()
    user = _user()
    # fs_list against a path that cannot resolve → executor step failure
    event_id = _ingest(user, "run the listing for no-such-directory-here")
    pipeline.understand(user, event_id)
    pipeline.propose(user, event_id)
    pipeline.decide(user, event_id, "ACCEPTED")
    pipeline.authorize(user, event_id)

    with pytest.raises(VoiceError) as exc:
        pipeline.execute(user, event_id)
    assert exc.value.state == "EXECUTION_FAILED"
    event = pipeline.get(user, event_id)["event"]
    assert event["evidence_ref"], "failed execution must still produce evidence"
    stages = [s["stage"] for s in pipeline.chain(user, event_id)["stages"]]
    assert "EVIDENCE" in stages and "ERROR" in stages


def test_unsupported_executor_is_explicit_not_silent(voice_db):
    pipeline = get_voice_pipeline()
    user = _user()
    token = uuid.uuid4().hex[:10]
    from knowledge.pipeline import ingest
    ingest(title=f"Voice Send Doc {token}", content="sendable report body",
           note_type="report", user_id=user["uid"],
           auto_tag=False, auto_embed=False, auto_link=False)
    ingest(title=f"Voice Send Person {token}", content="contact body",
           note_type="person", user_id=user["uid"],
           auto_tag=False, auto_embed=False, auto_link=False)

    event_id = _ingest(
        user, f"Send the report Voice Send Doc {token} to Voice Send Person {token}")
    pipeline.understand(user, event_id)
    proposed = pipeline.propose(user, event_id)
    # proposal is visible and truthful about the missing executor
    assert proposed["voice_proposal"]["detail"]["warning"] == "NO_CANONICAL_EXECUTOR"
    pipeline.decide(user, event_id, "ACCEPTED")
    pipeline.authorize(user, event_id)

    with pytest.raises(VoiceError) as exc:
        pipeline.execute(user, event_id)
    assert exc.value.state == "EXECUTION_FAILED"
    assert "NO_CANONICAL_EXECUTOR" in exc.value.detail
    event = pipeline.get(user, event_id)["event"]
    assert event["evidence_ref"]


# ── edit (revise) ────────────────────────────────────────────────────────────

def test_revision_withdraws_and_supersedes_the_proposal(voice_db):
    pipeline = get_voice_pipeline()
    user = _user()
    name = f"Voice Edit {uuid.uuid4().hex[:10]}"
    event_id = _ingest(user, f"Create a project called {name}")
    pipeline.understand(user, event_id)
    first = pipeline.propose(user, event_id)
    first_id = first["proposal"]["proposal_id"]

    revised = pipeline.revise(user, event_id, {
        "objective": f"[VOICE] CREATE: {name} (revised)",
        "reason": "operator narrowed the scope",
    })
    assert revised["supersedes"] == first_id
    assert revised["proposal"]["proposal_id"] != first_id

    from solspire.proposal_manager import get_proposal_manager
    old = get_proposal_manager().get_proposal(first_id, user["uid"])
    assert old.proposal_status == "WITHDRAWN"

    revisions = [s for s in pipeline.chain(user, event_id)["stages"]
                 if s["record_type"] == "ProposalRevision"]
    assert revisions and revisions[-1]["payload"]["supersedes"] == first_id


# ── provider conformance through the pipeline ────────────────────────────────

def test_provider_provenance_is_recorded_on_the_event(voice_db):
    pipeline = get_voice_pipeline()
    user = _user()
    event_id = _ingest(user, "find something")
    event = pipeline.get(user, event_id)["event"]
    assert event["asr_provenance"]["provider"] == "test"
    assert event["asr_provenance"]["recognized"] is False
    transcript = event["transcript"]
    assert transcript["provider"] == "test"
    assert transcript["provenance"]["mode"] == "supplied_transcript"
