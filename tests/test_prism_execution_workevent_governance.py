from __future__ import annotations

import pytest

import solspire.workevent_manager as wem
import weaver.enterprise_orchestration as eo
from weaver.execution_workevent_bridge import capture_execution_workevent


@pytest.fixture
def stores(tmp_path, monkeypatch):
    weaver_db = str(tmp_path / "weaver.db")
    workevent_db = str(tmp_path / "workevents.db")
    monkeypatch.setattr(eo, "_DB_PATH", weaver_db)
    monkeypatch.setattr(wem, "_DB_PATH", workevent_db)
    return eo.EnterpriseOrchestrationStore(), wem.WorkEventManager()


def _proposal_and_acceptance(store):
    proposal = store.proposal(
        subject="human-1",
        enterprise_id="workspace-1",
        objective="bounded execution",
        rationale="test",
        recommended_actions=["execute"],
        required_authority="human",
        tool_selections=["test-tool"],
        correlation_id="corr-prism-1",
    )
    evidence = store.evidence(
        subject="human-1",
        evidence_type="RESULT",
        content_or_ref={"claim": "bounded execution is eligible"},
        source_ref="test-fixture://verified-claim",
        correlation_id="corr-prism-1",
    )
    verification = store.verify(
        subject="human-1",
        claim="bounded execution is eligible",
        evidence_refs=[evidence.id],
        verifier="verifier-1",
        verdict="VERIFIED",
        correlation_id="corr-prism-1",
    )
    acceptance = store.acceptance(
        subject="human-1",
        verification_id=verification.id,
        accepted_result_ref=proposal.id,
        accepting_authority="human-1",
        authorization_scope={"tools": ["test-tool"]},
        context_ref="workspace-1",
        correlation_id="corr-prism-1",
    )
    authority = store.authority_event(
        subject="human-1",
        actor="human-1",
        authority_context="workspace-1",
        action="AUTHORIZE",
        previous_state="ACCEPTED",
        new_state="AUTHORIZED",
        origin="human",
        authentication_context="firebase",
        correlation_id="corr-prism-1",
    )
    return proposal, acceptance, authority


def test_execution_attempt_creates_one_causally_joined_workevent(stores):
    store, manager = stores
    proposal, acceptance, authority = _proposal_and_acceptance(store)

    authorization = store.authorize(
        subject="human-1",
        proposal_id=proposal.id,
        authority_event_id=authority.id,
        acceptance_id=acceptance.id,
        scope={"tools": ["test-tool"]},
        constraints={"external_side_effects": "bounded"},
    )
    attempt = store.execution_attempt(
        subject="human-1",
        authorization_id=authorization.id,
        tool_channel="test-tool",
        request_payload={"operation": "bounded"},
    )
    evidence = store.evidence(
        subject="human-1",
        evidence_type="EXECUTION_RESULT",
        content_or_ref={"status": "SUCCEEDED"},
        execution_attempt_id=attempt.id,
        correlation_id=attempt.correlation_id,
    )
    assert evidence.execution_attempt_id == attempt.id

    completed_attempt = store.complete_execution_attempt(
        subject="human-1",
        execution_attempt_id=attempt.id,
        result_status="SUCCEEDED",
    )

    # The actual Weaver terminal transition invokes the bridge automatically.
    automatic_event = manager.get_by_execution_attempt(attempt.id, "human-1")
    assert automatic_event is not None
    assert automatic_event.execution_attempt_ref == completed_attempt.id
    assert automatic_event.workspace_ref == "workspace-1"
    assert len(manager.list("human-1")) == 1

    # Calling the bridge explicitly again is a safe idempotent replay.
    event = capture_execution_workevent(
        store=store,
        subject="human-1",
        execution_attempt_id=completed_attempt.id,
        workspace_ref="workspace-1",
    )

    assert event.execution_attempt_ref == attempt.id
    assert event.work_ref == attempt.id
    assert event.scope_ref == authorization.id
    assert event.state_before_ref == "AUTHORIZED"
    assert event.state_after_ref == "SUCCEEDED"
    assert manager.get_by_execution_attempt(attempt.id, "human-1").work_event_id == event.work_event_id

    # The bridge is idempotent: one execution cannot mint multiple WorkEvents.
    assert capture_execution_workevent(
        store=store,
        subject="human-1",
        execution_attempt_id=attempt.id,
        workspace_ref="workspace-1",
    ).work_event_id == event.work_event_id
    assert len(manager.list("human-1")) == 1


def test_workevent_capture_does_not_mark_completion(stores):
    store, manager = stores
    proposal, acceptance, authority = _proposal_and_acceptance(store)
    authorization = store.authorize(
        subject="human-1",
        proposal_id=proposal.id,
        authority_event_id=authority.id,
        acceptance_id=acceptance.id,
        scope={"tools": ["test-tool"]},
        constraints={},
    )
    attempt = store.execution_attempt(
        subject="human-1",
        authorization_id=authorization.id,
        tool_channel="test-tool",
        request_payload={},
    )
    store.complete_execution_attempt(
        subject="human-1",
        execution_attempt_id=attempt.id,
        result_status="SUCCEEDED",
    )
    event = capture_execution_workevent(
        store=store,
        subject="human-1",
        execution_attempt_id=attempt.id,
        workspace_ref="workspace-1",
    )
    assert event.status == "RECORDED"
    assert not hasattr(event, "completion_id")
    assert not hasattr(event, "production_acceptance_id")


def test_governance_records_require_the_previous_boundary(stores):
    store, manager = stores
    with pytest.raises(ValueError, match="matching verification"):
        store.acceptance(
            subject="human-1",
            verification_id="missing",
            accepted_result_ref="result",
            accepting_authority="human-1",
            authorization_scope={"tools": ["x"]},
            context_ref="workspace-1",
        )

    event = manager.create(
        subject_ref="human-1",
        workspace_ref="workspace-1",
        event_type="EXECUTION_SUCCEEDED",
        occurred_at=1.0,
        execution_attempt_ref="exec-x",
    )
    review = store.review(
        subject="human-1",
        work_event_id=event.work_event_id,
        reviewer="reviewer-1",
        verdict="ACCEPTED",
        findings={"observed": True},
    )
    completion = store.completion(
        subject="human-1",
        work_event_id=event.work_event_id,
        review_id=review.id,
        condition="observable transition satisfies the declared outcome",
        supporting_evidence_refs=["exec-x"],
    )
    production = store.production_acceptance(
        subject="human-1",
        completion_id=completion.id,
        accepting_authority="human-1",
        context_ref="workspace-1",
    )
    assert review.work_event_id == event.work_event_id
    assert completion.review_id == review.id
    assert production.completion_id == completion.id
    assert production.status == "ACCEPTED"

def test_workevent_schema_migrates_legacy_table(tmp_path, monkeypatch):
    import sqlite3

    legacy_db = str(tmp_path / "legacy-workevents.db")
    with sqlite3.connect(legacy_db) as conn:
        conn.execute("""
            CREATE TABLE work_events (
                work_event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL,
                event_version INTEGER NOT NULL, occurred_at REAL NOT NULL,
                recorded_at REAL NOT NULL, effective_from REAL, effective_until REAL,
                subject_ref TEXT NOT NULL, workspace_ref TEXT NOT NULL, work_ref TEXT,
                parent_event_ref TEXT, sequence_ref TEXT, scope_ref TEXT, actor_ref TEXT,
                artifact_refs TEXT NOT NULL DEFAULT '[]', state_before_ref TEXT,
                state_after_ref TEXT, decision_ref TEXT, witness_ref TEXT, status TEXT NOT NULL,
                supersedes_ref TEXT, reversal_of_ref TEXT, created_by_event TEXT,
                schema_version TEXT NOT NULL
            )
        """)
    monkeypatch.setattr(wem, "_DB_PATH", legacy_db)
    event = wem.WorkEventManager().create(
        subject_ref="human-1", workspace_ref="workspace-1",
        event_type="LEGACY_MIGRATION_PROBE", occurred_at=1.0,
        execution_attempt_ref="exec-migrated",
    )
    assert event.execution_attempt_ref == "exec-migrated"
    assert wem.WorkEventManager().get_by_execution_attempt("exec-migrated", "human-1")


def test_authorization_schema_migrates_legacy_table(tmp_path, monkeypatch):
    import sqlite3

    legacy_db = str(tmp_path / "legacy-weaver.db")
    with sqlite3.connect(legacy_db) as conn:
        conn.execute("""
            CREATE TABLE ew_authorizations (
                id TEXT PRIMARY KEY, subject TEXT NOT NULL, proposal_id TEXT NOT NULL,
                authority_event_id TEXT NOT NULL, scope TEXT NOT NULL,
                constraints TEXT NOT NULL, expires_at REAL, granted_at REAL NOT NULL,
                correlation_id TEXT NOT NULL
            )
        """)
    monkeypatch.setattr(eo, "_DB_PATH", legacy_db)
    with eo._db() as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(ew_authorizations)")}
    assert "acceptance_id" in columns

