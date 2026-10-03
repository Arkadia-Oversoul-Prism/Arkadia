from __future__ import annotations

import asyncio


def test_console_authorization_creates_canonical_chain(tmp_path, monkeypatch):
    import solspire.proposal_manager as pm
    import solspire.workspace_manager as wm
    import weaver.enterprise_orchestration as ew
    from solspire.console_authority_router import authorize_proposal, AuthorizationRequest

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
            AuthorizationRequest(scope={"objective": proposal.objective}),
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
