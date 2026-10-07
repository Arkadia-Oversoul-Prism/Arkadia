"""Arkadia Voice — Phase 2 contract tests (GATE 1).

Unit coverage for the canonical voice contracts: VoiceEvent creation, audio
hashing, transcript normalization, bounded action/risk policy, the stage order
of the evidence timeline, the explicit error-state catalog, and the digest
machinery that keeps every chain object traceable backwards.
"""
from __future__ import annotations

from solspire.voice_contracts import (
    RISK_LEVELS,
    STAGE_ORDER,
    VOICE_ERROR_STATES,
    ChainStage,
    Intent,
    Transcript,
    VoiceAction,
    VoiceEvent,
    VoiceStage,
    canonical_digest,
    chain_digest,
    hash_audio,
    new_id,
    requires_approval,
)


# ── VoiceEvent ───────────────────────────────────────────────────────────────

def test_voice_event_creation_carries_contract_fields():
    event = VoiceEvent.create(
        subject="uid-1",
        workspace_ref="ws-1",
        audio_hash=hash_audio(b"audio"),
        audio_reference="voice-audio:pending",
        language="en",
        session_id="sess-1",
        audio_mime="audio/webm",
        audio_size=5,
        duration_ms=1200,
    )
    data = event.to_dict()
    for field in ("event_id", "session_id", "subject", "audio_reference",
                  "audio_hash", "timestamp", "language", "asr_provenance",
                  "transcript"):
        assert field in data, f"missing contract field: {field}"
    assert event.event_id.startswith("VE-")
    assert event.subject == "uid-1"
    assert event.session_id == "sess-1"
    assert data["asr_provenance"] == {"state": "PENDING"}
    assert event.status == "RECEIVED"


def test_voice_event_ids_are_unique():
    ids = {
        VoiceEvent.create(subject="u", workspace_ref="w",
                          audio_hash="x", audio_reference="r").event_id
        for _ in range(50)
    }
    assert len(ids) == 50


def test_voice_event_session_defaults_to_workspace():
    event = VoiceEvent.create(subject="u", workspace_ref="ws-9", audio_hash="x",
                              audio_reference="r")
    assert event.session_id == "ws-9"


# ── audio hashing ────────────────────────────────────────────────────────────

def test_audio_hash_is_sha256_and_deterministic():
    audio = b"\x1a\x45\xdfa-payload"
    digest = hash_audio(audio)
    assert len(digest) == 64
    assert digest == hash_audio(audio)
    assert digest != hash_audio(audio + b"x")


def test_audio_hash_detects_single_byte_change():
    assert hash_audio(b"aaaa") != hash_audio(b"aaab")


# ── transcript normalization ─────────────────────────────────────────────────

def test_transcript_normalization_collapses_whitespace():
    assert Transcript.normalize("  hello   world \n\t ") == "hello world"


def test_transcript_normalization_of_empty_is_empty():
    assert Transcript.normalize("") == ""
    assert Transcript.normalize(None) == ""
    assert Transcript.normalize("   \n ") == ""


# ── intent contract shape ────────────────────────────────────────────────────

def test_intent_contract_fields():
    intent = Intent(
        intent_id="IN-1",
        action=VoiceAction.CREATE.value,
        entities={"entity": "PROJECT", "name": "Eden Pilot"},
        requested_effect="CREATE_ENTITY",
        confidence=1.0,
        source_event_id="VE-1",
    )
    data = intent.to_dict()
    assert data["action"] == "CREATE"
    assert data["entities"]["name"] == "Eden Pilot"
    assert data["source_event_id"] == "VE-1"
    assert data["parser"] == "rule_based"


# ── risk / approval policy ───────────────────────────────────────────────────

def test_risk_policy_is_explicit_for_every_action():
    assert set(RISK_LEVELS) == set(VoiceAction)


def test_informational_actions_need_no_approval():
    assert requires_approval(VoiceAction.ASK) is False
    assert requires_approval(VoiceAction.SEARCH) is False


def test_consequential_actions_require_approval():
    for action in (VoiceAction.CREATE, VoiceAction.MODIFY, VoiceAction.EXECUTE):
        assert requires_approval(action) is True, action


def test_unknown_action_requires_approval_is_conservative():
    # UNKNOWN is not informational: it must never auto-approve.
    assert requires_approval(VoiceAction.UNKNOWN) is True


# ── evidence timeline ────────────────────────────────────────────────────────

def test_stage_order_contains_the_full_required_chain():
    required = [
        "VOICE_EVENT", "TRANSCRIPT", "INTENT", "CONTEXT", "AUTHORITY",
        "PROPOSAL", "APPROVAL", "AUTHORIZATION", "EXECUTION", "RESULT",
        "WORK_EVENT", "EVIDENCE", "VERIFICATION",
    ]
    stages = [stage.value for stage in STAGE_ORDER]
    for name in required:
        assert name in stages, f"missing stage {name}"
    assert stages == sorted(stages, key=stages.index)  # stable order
    assert stages.index("PROPOSAL") < stages.index("EXECUTION")
    assert stages.index("APPROVAL") < stages.index("AUTHORIZATION")
    assert stages.index("AUTHORIZATION") < stages.index("EXECUTION")
    assert stages.index("EVIDENCE") >= stages.index("WORK_EVENT")


def test_error_catalog_covers_every_phase_12_state():
    required = [
        "MICROPHONE_DENIED", "AUDIO_CAPTURE_FAILED", "ASR_UNAVAILABLE",
        "ASR_FAILED", "TRANSCRIPT_EMPTY", "INTENT_UNKNOWN", "CONTEXT_AMBIGUOUS",
        "AUTHORITY_MISSING", "AUTHORIZATION_DENIED", "APPROVAL_REQUIRED",
        "EXECUTION_FAILED", "VERIFICATION_PENDING", "VERIFICATION_FAILED",
    ]
    for state in required:
        assert state in VOICE_ERROR_STATES, f"missing error state {state}"
        assert VOICE_ERROR_STATES[state]["recovery"], f"{state} has no recovery action"


# ── evidence linkage ─────────────────────────────────────────────────────────

def test_chain_stage_links_backwards():
    first = ChainStage(stage="A", seq=1, record_type="R", record_id="r1",
                       payload={"x": 1}, created_at=0.0, prev_record_id=None,
                       payload_digest="d1")
    second = ChainStage(stage="B", seq=2, record_type="R", record_id="r2",
                        payload={"x": 2}, created_at=1.0, prev_record_id="r1",
                        payload_digest="d2")
    digest = chain_digest([first, second])
    assert digest == chain_digest([first, second])
    assert digest != chain_digest([first])


def test_chain_digest_changes_when_a_payload_changes():
    a = ChainStage(stage="A", seq=1, record_type="R", record_id="r1",
                   payload={"x": 1}, created_at=0.0, payload_digest="d1")
    b = ChainStage(stage="A", seq=1, record_type="R", record_id="r1",
                   payload={"x": 2}, created_at=0.0, payload_digest="d2")
    assert chain_digest([a]) != chain_digest([b])


def test_canonical_digest_is_order_independent_for_dicts():
    assert canonical_digest({"a": 1, "b": 2}) == canonical_digest({"b": 2, "a": 1})


def test_new_id_prefix_and_uniqueness():
    assert new_id("VE").startswith("VE-")
    assert new_id("VE") != new_id("VE")


def test_voice_stage_values_match_chain_stage_names():
    values = {stage.value for stage in VoiceStage}
    for stage in STAGE_ORDER:
        assert stage.value in values
