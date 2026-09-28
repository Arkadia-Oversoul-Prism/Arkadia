"""GATE-02..09 delta tests: canonical event vocabulary, forward provenance,
and proposal lifecycle reconciliation.

These extend the verified ARK-WEAVER-01 spine (weaver/enterprise_orchestration.py)
additively. They exercise the real store code paths, no mocks.
"""
from __future__ import annotations

from weaver.enterprise_orchestration import (
    OPERATIONAL_EVENT_TYPES,
    PROPOSAL_STATUSES,
    EnterpriseOrchestrationStore,
    simulate_eden_supplier_path,
)

GATE_05_VOCABULARY = {
    "INPUT_RECEIVED", "SOURCE_ATTRIBUTED", "CANONICALIZED", "KNOWLEDGE_UPDATED",
    "ENTITY_LINKED", "UNCERTAINTY_DETECTED", "TOOL_SELECTED", "TOOL_EXECUTED",
    "RESULT_RECEIVED", "PROPOSAL_GENERATED", "AUTHORIZATION_REQUIRED", "AUTHORIZED",
    "EXECUTION_PREPARED", "EXECUTED", "EVIDENCE_RECEIVED", "VERIFIED", "RECALIBRATED",
}


def _store(tmp_path, monkeypatch):
    import weaver.enterprise_orchestration as mod
    monkeypatch.setattr(mod, "_DB_PATH", str(tmp_path / "orchestration.db"))
    return mod.EnterpriseOrchestrationStore()


def test_event_vocabulary_covers_required_transitions():
    assert GATE_05_VOCABULARY <= OPERATIONAL_EVENT_TYPES


def test_operational_event_rejects_unknown_type(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    try:
        store.operational_event(
            subject="s", enterprise_id="e", event_type="MADE_UP_EVENT", payload={},
        )
    except ValueError as exc:
        assert "unsupported operational event type" in str(exc)
    else:
        raise AssertionError("unnamed operational transitions must be rejected")


def test_operational_event_accepts_canonical_type(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    ev = store.operational_event(
        subject="s", enterprise_id="e", event_type="proposal_generated",
        payload={"proposal": "p1"},
    )
    assert ev.event_type == "PROPOSAL_GENERATED"


def test_forward_walk_traces_source_to_consequence(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    canonical = store.canonical_record(
        subject="architect", source_channel="supplier",
        raw_payload={"message": "available, price unconfirmed"}, ingested_by="test",
    )
    store.interpretation(
        subject="architect", canonical_record_id=canonical.id, interpreter="arkana",
        interpretation={"price": "UNKNOWN"},
    )
    store.operational_event(
        subject="architect", enterprise_id="eden", event_type="INPUT_RECEIVED",
        payload={"canonical_record_id": canonical.id},
        caused_by_kind="CANONICAL_RECORD", caused_by_id=canonical.id,
    )

    walk = store.forward_walk(subject="architect", kind="CANONICAL_RECORD", record_id=canonical.id)
    kinds = [r["kind"] for r in walk["records"]]
    assert kinds[0] == "CANONICAL_RECORD"
    assert "INTERPRETATION" in kinds
    assert "OPERATIONAL_EVENT" in kinds


def test_forward_walk_traces_authority_to_verification(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    result = simulate_eden_supplier_path(store, subject="architect", enterprise_id="eden-01")

    walk = store.forward_walk(
        subject="architect", kind="AUTHORITY_EVENT", record_id=result["authority_event"].id
    )
    kinds = {r["kind"] for r in walk["records"]}
    assert {"AUTHORITY_EVENT", "AUTHORIZATION", "EXECUTION_ATTEMPT", "EVIDENCE",
            "VERIFICATION"} <= kinds


def test_forward_walk_respects_subject_isolation(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    canonical = store.canonical_record(
        subject="subject-a", source_channel="c", raw_payload={}, ingested_by="test",
    )
    walk = store.forward_walk(subject="subject-b", kind="CANONICAL_RECORD", record_id=canonical.id)
    assert walk["records"] == []


def test_proposal_lifecycle_reconciled():
    assert {"PROPOSED", "AWAITING_AUTHORITY", "AUTHORIZED", "EXECUTION_READY",
            "COMPLETED", "REJECTED"} <= PROPOSAL_STATUSES
    assert {"DRAFT", "EXPIRED", "SUPERSEDED"} <= PROPOSAL_STATUSES


def test_operational_state_separates_proposed_from_authorized(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    proposal = store.proposal(
        subject="architect", enterprise_id="eden-01", objective="verify price",
        rationale="price UNKNOWN", recommended_actions=["verify"],
        required_authority="human", tool_selections=["supplier_verification"],
    )
    state = store.operational_state(subject="architect", enterprise_id="eden-01")
    assert proposal.id in state["awaiting_authority"]
    assert state["authorized"] == []
    assert state["verified_claims"] == []


def test_operational_state_reports_verified_only_with_verification(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    result = simulate_eden_supplier_path(store, subject="architect", enterprise_id="eden-01")
    state = store.operational_state(subject="architect", enterprise_id="eden-01")
    assert state["proposals"].get(result["proposal"].id) == "AUTHORIZED"
    assert result["proposal"].id in state["authorized"]
    assert any(v["verdict"] == "VERIFIED" for v in state["verified_claims"])
    assert state["unknowns"], "UNCERTAINTY_DETECTED events must surface as unknowns"


def test_explain_execution_is_inspectable_rationale(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    result = simulate_eden_supplier_path(store, subject="architect", enterprise_id="eden-01")
    rationale = store.explain_execution(
        subject="architect", execution_attempt_id=result["execution_attempt"].id
    )
    assert rationale["complete"] is True
    assert rationale["objective"]
    assert rationale["required_authority"] == "human"
    assert rationale["tool_channel"] == "simulated_supplier_verification"
    assert rationale["authority_event"]["action"] == "APPROVE_PROPOSAL"
    assert rationale["evidence_refs"]


def test_explain_execution_unknown_for_absent_attempt(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    rationale = store.explain_execution(subject="architect", execution_attempt_id="missing")
    assert rationale["complete"] is False
    assert rationale["reason"] == "UNKNOWN"
