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


def test_console_dispatch_uses_authorized_repository_root(tmp_path, monkeypatch):
    import weaver.enterprise_orchestration as ew
    from weaver.console_adapter import WeaverConsoleAdapter

    db = str(tmp_path / "root-binding.db")
    monkeypatch.setattr(ew, "_DB_PATH", db)
    store = ew.EnterpriseOrchestrationStore()
    allowed = tmp_path / "allowed"
    other = tmp_path / "other"
    allowed.mkdir()
    other.mkdir()
    (allowed / "authorized.txt").write_text("inside", encoding="utf-8")
    (other / "unbound.txt").write_text("outside", encoding="utf-8")

    subject = "firebase-root-binding"
    proposal = store.proposal(
        subject=subject, enterprise_id="workspace-root",
        objective="Read authorized workspace", rationale="Console boundary",
        recommended_actions=["read"], required_authority="human",
        tool_selections=["filesystem.read"], correlation_id="root-binding-1",
    )
    hae = store.authority_event(
        subject=subject, actor=subject, authority_context="workspace-root",
        action="APPROVE_PROPOSAL", previous_state="AWAITING_AUTHORITY",
        new_state="AUTHORIZED", origin="human",
        authentication_context="firebase_id_token",
        correlation_id=proposal.correlation_id,
    )
    auth = store.authorize(
        subject=subject, proposal_id=proposal.id,
        authority_event_id=hae.id, scope={"tools": ["filesystem.read"]},
        constraints={"read_only": True, "repository_root": str(allowed), "network": False},
    )
    attempt = store.execution_attempt(
        subject=subject, authorization_id=auth.id,
        tool_channel="filesystem.read", request_payload={"path": "authorized.txt"},
    )
    result = WeaverConsoleAdapter(store=store, repo_root=str(other)).dispatch(
        subject=subject, authorization_id=auth.id,
        execution_attempt_id=attempt.id, tool_channel="filesystem.read",
        request_payload={"path": "authorized.txt"},
    )
    assert result["ok"] is True
    assert result["execution"]["observed"]["content"] == "inside"

    outside = store.execution_attempt(
        subject=subject, authorization_id=auth.id,
        tool_channel="filesystem.read", request_payload={"path": "../other/unbound.txt"},
    )
    try:
        WeaverConsoleAdapter(store=store, repo_root=str(other)).dispatch(
            subject=subject, authorization_id=auth.id,
            execution_attempt_id=outside.id, tool_channel="filesystem.read",
            request_payload={"path": "../other/unbound.txt"},
        )
    except RuntimeError as exc:
        assert "sandbox" in str(exc).lower() or "outside" in str(exc).lower()
    else:
        raise AssertionError("authorized repository root was not enforced")

def test_console_proposal_authorization_weaver_evidence_chain(tmp_path, monkeypatch):
    import asyncio
    import solspire.proposal_manager as pm
    import solspire.workspace_manager as wm
    import weaver.enterprise_orchestration as ew
    from solspire.console_authority_router import (
        authorize_proposal,
        create_execution_attempt,
        AuthorizationRequest,
        ExecutionRequest,
    )

    db = str(tmp_path / "console-full-chain.db")
    monkeypatch.setattr(pm, "_DB_PATH", db)
    monkeypatch.setattr(wm, "_DB_PATH", db)
    monkeypatch.setattr(ew, "_DB_PATH", db)

    subject = "firebase-console-full-chain"
    workspace = wm.WorkspaceManager().get_or_create(subject)
    proposal = pm.ProposalManager().create_proposal(
        subject_ref=subject,
        workspace_ref=workspace.id,
        objective="Inspect the authorized test workspace",
        scope="Read-only Console execution proof",
        requested_decision="inspect_workspace",
    )
    pm.ProposalManager().record_decision(
        proposal_id=proposal.proposal_id,
        subject_ref=subject,
        decision="ACCEPTED",
    )

    authorized = asyncio.run(
        authorize_proposal(
            proposal.proposal_id,
            AuthorizationRequest(
                scope={"tools": ["filesystem.list"]},
                constraints={
                    "read_only": True,
                    "repository_root": str(tmp_path),
                    "network": False,
                },
            ),
            user={"uid": subject, "role": "Flamekeeper", "access_level": 1},
        )
    )
    authorization_id = authorized["authorization"]["id"]
    assert authorized["human_authority_event"]["action"] == "APPROVE_PROPOSAL"
    assert authorized["execution_authorized"] is True
    assert authorized["solariun_proposal"]["authorization_ref"] == authorization_id

    executed = asyncio.run(
        create_execution_attempt(
            authorization_id,
            ExecutionRequest(
                tool_channel="filesystem.list",
                request_payload={"path": "."},
            ),
            user={"uid": subject},
        )
    )

    assert executed["ok"] is True
    assert executed["execution"]["tool_channel"] == "filesystem.list"
    assert executed["execution_attempt"]["result_status"] == "SUCCEEDED"
    evidence = executed["evidence"]
    assert evidence["execution_attempt_id"] == executed["execution_attempt"]["id"]
    assert evidence["evidence_type"] == "weaver_execution"
