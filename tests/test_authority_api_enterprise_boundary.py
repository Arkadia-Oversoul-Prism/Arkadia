from __future__ import annotations

import sqlite3

import pytest


def _enterprise_store(tmp_path, monkeypatch):
    import weaver.enterprise_orchestration as ew

    db = tmp_path / "enterprise.db"
    monkeypatch.setattr(ew, "_DB_PATH", str(db))
    return ew.EnterpriseOrchestrationStore(), db


def _proposal(store):
    return store.proposal(
        subject="authorized-subject",
        enterprise_id="enterprise-01",
        objective="verify supplier",
        rationale="price is unknown",
        recommended_actions=["verify_price"],
        required_authority="human",
        tool_selections=["supplier_verification"],
    )


def _count(db, table: str) -> int:
    with sqlite3.connect(db) as conn:
        row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    return int(row[0])


def test_unauthorized_actor_cannot_create_enterprise_authority_or_authorization(
    tmp_path, monkeypatch
):
    from solspire.eden_ops import EdenOps

    store, db = _enterprise_store(tmp_path, monkeypatch)
    proposal = _proposal(store)
    ops = EdenOps(store=store)

    with pytest.raises(ValueError, match="subject mismatch"):
        ops.decide_proposal(
            subject="unauthorized-subject",
            proposal_id=proposal.id,
            action="APPROVE",
            actor="unauthorized-subject",
        )

    assert _count(db, "ew_authority_events") == 0
    assert _count(db, "ew_authorizations") == 0


def test_authorized_identity_is_the_control_case_and_creates_both_records(
    tmp_path, monkeypatch
):
    from solspire.eden_ops import EdenOps

    store, db = _enterprise_store(tmp_path, monkeypatch)
    proposal = _proposal(store)
    ops = EdenOps(store=store)

    result = ops.decide_proposal(
        subject="authorized-subject",
        proposal_id=proposal.id,
        action="APPROVE",
        actor="authorized-subject",
    )

    assert result["status"] == "AUTHORIZED"
    assert result["authority_event"].subject == "authorized-subject"
    assert result["authorization"].proposal_id == proposal.id
    assert result["authorization"].authority_event_id == result["authority_event"].id
    assert _count(db, "ew_authority_events") == 1
    assert _count(db, "ew_authorizations") == 1


@pytest.mark.asyncio
async def test_api_approval_does_not_create_enterprise_authorization_without_explicit_bridge(
    tmp_path, monkeypatch
):
    import api.approval_routes as approvals
    from solspire import eden_ops
    import weaver.enterprise_orchestration as ew

    db = tmp_path / "enterprise.db"
    monkeypatch.setattr(ew, "_DB_PATH", str(db))
    store = ew.EnterpriseOrchestrationStore()
    proposal = _proposal(store)

    class NoEnterpriseBridgeTool:
        def run(self, payload):
            assert payload["proposal_id"] == proposal.id
            return {"accepted": True}

    monkeypatch.setattr(
        "kernel.tools.get_tool",
        lambda name: NoEnterpriseBridgeTool() if name == "enterprise_proposal_review" else None,
    )

    approval_id = approvals.queue_approval(
        "enterprise_proposal_review",
        {"proposal_id": proposal.id},
        "Approve enterprise proposal",
    )

    result = await approvals.api_approve(approval_id)

    assert result["status"] == "approved"
    assert _count(db, "ew_authority_events") == 0
    assert _count(db, "ew_authorizations") == 0

    # Explicitly document the bridge boundary: EdenOps is the known path that
    # creates the enterprise authority + authorization pair.
    bridged = eden_ops.EdenOps(store=store).decide_proposal(
        subject="authorized-subject",
        proposal_id=proposal.id,
        action="APPROVE",
        actor="authorized-subject",
    )
    assert bridged["authorization"] is not None
    assert _count(db, "ew_authorizations") == 1
