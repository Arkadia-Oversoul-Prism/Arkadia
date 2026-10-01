from __future__ import annotations

import json

from weaver.enterprise_orchestration import EnterpriseOrchestrationStore, simulate_eden_supplier_path


def _store(tmp_path, monkeypatch):
    import weaver.enterprise_orchestration as mod
    monkeypatch.setattr(mod, "_DB_PATH", str(tmp_path / "orchestration.db"))
    return mod.EnterpriseOrchestrationStore()


def test_transition_contracts_and_reverse_walk(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)

    canonical = store.canonical_record(
        subject="subject-a",
        source_channel="test",
        raw_payload={"message": "supplier says available"},
        ingested_by="test",
    )
    interpretation = store.interpretation(
        subject="subject-a",
        canonical_record_id=canonical.id,
        interpreter="arkana-test",
        interpretation={"availability": "APPEARS_AVAILABLE"},
        confidence=0.71,
    )
    proposal = store.proposal(
        subject="subject-a",
        enterprise_id="eden",
        objective="verify supplier",
        rationale="availability requires verification",
        recommended_actions=["verify"],
        required_authority="human",
        tool_selections=["supplier_verification"],
        caused_by_kind="INTERPRETATION",
        caused_by_id=interpretation.id,
        correlation_id=interpretation.correlation_id,
    )

    try:
        store.execution_attempt(
            subject="subject-a", authorization_id="missing",
            tool_channel="test", request_payload={}
        )
    except ValueError as exc:
        assert "authorization" in str(exc)
    else:
        raise AssertionError("execution without authorization must be rejected")

    authority = store.authority_event(
        subject="subject-a", actor="subject-a", authority_context="eden",
        action="APPROVE_PROPOSAL", previous_state="AWAITING_AUTHORITY",
        new_state="AUTHORIZED", origin="human",
        authentication_context="authenticated_subject",
        correlation_id=proposal.correlation_id,
    )
    authorization = store.authorize(
        subject="subject-a", proposal_id=proposal.id,
        authority_event_id=authority.id, scope={"objective": "verify supplier"},
        constraints={},
    )

    unrelated_authority = store.authority_event(
        subject="subject-a", actor="subject-a", authority_context="other",
        action="AUTHORIZE", previous_state="PENDING", new_state="AUTHORIZED",
        origin="human", authentication_context="authenticated_subject",
    )
    try:
        store.authorize(
            subject="subject-a", proposal_id=proposal.id,
            authority_event_id=unrelated_authority.id, scope={}, constraints={},
        )
    except ValueError as exc:
        assert "causally bound" in str(exc)
    else:
        raise AssertionError("unrelated authority must not authorize a proposal")
    attempt = store.execution_attempt(
        subject="subject-a", authorization_id=authorization.id,
        tool_channel="test", request_payload={"supplier": "A"},
    )

    try:
        store.verify(
            subject="subject-a", claim="supplier verified",
            evidence_refs=["missing"], verifier="test", verdict="VERIFIED",
        )
    except ValueError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("verification without evidence must be rejected")

    evidence = store.evidence(
        subject="subject-a", execution_attempt_id=attempt.id,
        evidence_type="test", content_or_ref={"price": "UNKNOWN"},
    )
    verification = store.verify(
        subject="subject-a", claim="supplier response captured",
        evidence_refs=[evidence.id], verifier="test", verdict="VERIFIED",
    )
    walk = store.reverse_walk(subject="subject-a", kind="VERIFICATION", record_id=verification.id)
    kinds = {r["kind"] for r in walk["records"]}

    assert walk["complete"] is True
    assert {"VERIFICATION", "EVIDENCE", "EXECUTION_ATTEMPT", "AUTHORIZATION",
            "PROPOSAL", "AUTHORITY_EVENT", "INTERPRETATION", "CANONICAL_RECORD"} <= kinds
    assert "WORK_EVENT" not in kinds


def test_eden_simulated_path_preserves_unknown_until_evidence(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    result = simulate_eden_supplier_path(store, subject="architect", enterprise_id="eden-01")

    assert result["interpretation"].interpretation["price"] == "UNKNOWN"
    assert result["verification"].verdict == "VERIFIED"
    assert result["evidence"].content_or_ref["price_ngn_per_kg"] == 1200

    walk = store.reverse_walk(
        subject="architect", kind="VERIFICATION", record_id=result["verification"].id
    )
    assert walk["complete"] is True
    assert any(r["kind"] == "CANONICAL_RECORD" for r in walk["records"]) is True
    # The verified price claim is sourced from a simulated execution response,
    # while the original supplier message deliberately left price UNKNOWN.
    assert result["canonical"].raw_payload["message"].endswith("price not confirmed.")


def test_human_authority_event_is_distinct_from_workevent(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    authority = store.authority_event(
        subject="architect", actor="architect", authority_context="eden",
        action="APPROVE_PROPOSAL", previous_state="PENDING",
        new_state="AUTHORIZED", origin="human",
        authentication_context="authenticated_subject",
    )
    assert authority.id.startswith("hae-")
    assert not hasattr(authority, "work_event_id")
    assert not hasattr(authority, "status")


def test_execution_success_requires_evidence(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    proposal = store.proposal(
        subject="s", enterprise_id="e", objective="x", rationale="r",
        recommended_actions=["a"], required_authority="human", tool_selections=["t"],
    )
    authority = store.authority_event(
        subject="s", actor="s", authority_context="e", action="AUTHORIZE",
        previous_state="PENDING", new_state="AUTHORIZED", origin="human",
        authentication_context="authenticated_subject",
        correlation_id=proposal.correlation_id,
    )
    auth = store.authorize(
        subject="s", proposal_id=proposal.id, authority_event_id=authority.id,
        scope={"objective": "x"}, constraints={},
    )
    try:
        store.execution_attempt(
            subject="s", authorization_id=auth.id, tool_channel="t",
            request_payload={}, result_status="SUCCEEDED",
        )
    except ValueError as exc:
        assert "EvidenceRecord" in str(exc)
    else:
        raise AssertionError("execution cannot self-assert success")


def test_enterprise_canonical_record_crosses_gate01_capture(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    import knowledge.db as kdb
    from knowledge import capture as cap
    kdb._DB_PATH = tmp_path / "knowledge.db"
    kdb._local.conn = None
    from knowledge.db import get_connection

    payload = {"message": "captured before interpretation", "enterprise_id": "eden"}
    canonical = store.canonical_record(
        subject="subject-a",
        source_channel="human_entry",
        raw_payload=payload,
        ingested_by="subject-a",
    )

    assert canonical.capture_ref is not None
    provenance = cap.provenance_for_capture(canonical.capture_ref)
    assert provenance["raw_checksum"] == canonical.payload_hash
    assert provenance["authorship"]["declared"] is False

    conn = get_connection()
    row = conn.execute(
        "SELECT capture_uuid, note_id FROM capture_records WHERE capture_uuid = ?",
        (canonical.capture_ref,),
    ).fetchone()
    assert row is not None
    assert row["note_id"] is None


def test_enterprise_interpretation_requires_canonical_capture_projection(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    import knowledge.db as kdb
    kdb._DB_PATH = tmp_path / "knowledge.db"
    kdb._local.conn = None
    canonical = store.canonical_record(
        subject="subject-a",
        source_channel="supplier",
        raw_payload={"message": "source"},
        ingested_by="test",
    )
    interpretation = store.interpretation(
        subject="subject-a",
        canonical_record_id=canonical.id,
        interpreter="test",
        interpretation={"state": "UNKNOWN"},
    )
    assert interpretation.canonical_record_id == canonical.id
    assert canonical.capture_ref is not None
