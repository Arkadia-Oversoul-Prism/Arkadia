from __future__ import annotations

import asyncio


def test_console_authorization_creates_canonical_chain(tmp_path, monkeypatch):
    import solspire.proposal_manager as pm
    import solspire.workspace_manager as wm
    import weaver.enterprise_orchestration as ew
    from solspire.console_authority_router import authorize_proposal, AuthorizationRequest
    from weaver.console_adapter import WeaverConsoleAdapter

    db = str(tmp_path / "console.db")
    monkeypatch.setattr(pm, "_DB_PATH", db)
    monkeypatch.setattr(wm, "_DB_PATH", db)
    monkeypatch.setattr(ew, "_DB_PATH", db)

    subject = "firebase-uid-123"
    workspace = wm.WorkspaceManager().get_or_create(subject)
    proposal = pm.ProposalManager().create_proposal(
        subject_ref=subject,
        workspace_ref=workspace.id,
        objective="Verify supplier price",
        scope="Supplier A / potatoes",
        requested_decision="verify_price",
    )
    pm.ProposalManager().record_decision(
        proposal_id=proposal.proposal_id,
        subject_ref=subject,
        decision="ACCEPTED",
    )

    result = asyncio.run(
        authorize_proposal(
            proposal.proposal_id,
            AuthorizationRequest(
                scope={"tools": ["filesystem.list"]},
                constraints={"read_only": True, "repository_root": str(tmp_path), "network": False},
            ),
            user={"uid": subject, "role": "Flamekeeper", "access_level": 1},
        )
    )

    assert result["human_authority_event"]["action"] == "APPROVE_PROPOSAL"
    assert result["authorization"]["proposal_id"] == result["enterprise_proposal"]["id"]
    assert result["execution_authorized"] is True

    bound = pm.ProposalManager().get_proposal(proposal.proposal_id, subject)
    assert bound is not None
    assert bound.proposal_status == "ACCEPTED"
    assert bound.authorization_ref == result["authorization"]["id"]

    store = ew.EnterpriseOrchestrationStore()
    attempt = store.execution_attempt(
        subject=subject,
        authorization_id=result["authorization"]["id"],
        tool_channel="test",
        request_payload={"test": True},
    )
    evidence = store.evidence(
        subject=subject,
        execution_attempt_id=attempt.id,
        evidence_type="test_result",
        content_or_ref={"observed": "completed"},
    )
    verification = store.verify(
        subject=subject,
        claim="The test execution produced the observed result.",
        evidence_refs=[evidence.id],
        verifier="test",
        verdict="VERIFIED",
    )

    assert attempt.result_status == "ATTEMPTED"
    assert evidence.execution_attempt_id == attempt.id
    assert verification.evidence_refs == [evidence.id]


def test_console_authorized_tool_dispatch_records_automatic_evidence(tmp_path, monkeypatch):
    import solspire.workspace_manager as wm
    import weaver.enterprise_orchestration as ew
    from weaver.console_adapter import WeaverConsoleAdapter

    db = str(tmp_path / "dispatch.db")
    monkeypatch.setattr(wm, "_DB_PATH", db)
    monkeypatch.setattr(ew, "_DB_PATH", db)
    store = ew.EnterpriseOrchestrationStore()
    proposal = store.proposal(
        subject="firebase-uid-dispatch", enterprise_id="workspace-1",
        objective="Inspect bounded workspace", rationale="Console proof",
        recommended_actions=["list"], required_authority="human",
        tool_selections=["filesystem.list"], correlation_id="console-dispatch-1",
    )
    hae = store.authority_event(
        subject="firebase-uid-dispatch", actor="firebase-uid-dispatch",
        authority_context="workspace-1", action="APPROVE_PROPOSAL",
        previous_state="AWAITING_AUTHORITY", new_state="AUTHORIZED", origin="human",
        authentication_context="firebase_id_token", correlation_id=proposal.correlation_id,
    )
    auth = store.authorize(
        subject="firebase-uid-dispatch", proposal_id=proposal.id,
        authority_event_id=hae.id, scope={"tools": ["filesystem.list"]},
        constraints={"read_only": True, "repository_root": str(tmp_path), "network": False},
    )
    attempt = store.execution_attempt(
        subject="firebase-uid-dispatch", authorization_id=auth.id,
        tool_channel="filesystem.list", request_payload={"path": "."},
    )
    result = WeaverConsoleAdapter(store=store, repo_root=str(tmp_path)).dispatch(
        subject="firebase-uid-dispatch", authorization_id=auth.id,
        execution_attempt_id=attempt.id, tool_channel="filesystem.list",
        request_payload={"path": "."},
    )
    assert result["ok"] is True
    assert result["evidence"]["execution_attempt_id"] == attempt.id
    completed = store.complete_execution_attempt(
        subject="firebase-uid-dispatch", execution_attempt_id=attempt.id,
        result_status="SUCCEEDED",
    )
    assert completed.result_status == "SUCCEEDED"
