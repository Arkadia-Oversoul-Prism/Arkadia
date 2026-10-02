"""Upstream causal continuity — identity/authority and API approval measurements.

These tests measure two independent boundaries without creating a bridge that
does not exist:

  * enterprise proposal approval requires an authenticated identity carrying
    Govern authority; an actor string alone cannot create authority evidence.
  * the API approval surface remains separate from ew_authorizations unless an
    explicit bridge is introduced.

The tests use isolated SQLite state and inspect durable enterprise records.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.approval_routes import APPROVAL_LOCK, PENDING_APPROVALS
from api.auth import require_auth
from api.main import app
from solspire.eden_ops import EdenOps
from weaver.enterprise_orchestration import EnterpriseOrchestrationStore


def _ops(tmp_path, monkeypatch):
    import solspire.eden_ops as eden_mod
    import weaver.enterprise_orchestration as ew_mod

    db = str(tmp_path / "upstream.db")
    monkeypatch.setattr(eden_mod, "_DB_PATH", db)
    monkeypatch.setattr(ew_mod, "_DB_PATH", db)
    store = EnterpriseOrchestrationStore()
    return EdenOps(store=store), db


def _proposal(ops):
    return ops.ingest_supplier_signal(
        subject="proposal-subject",
        enterprise_id="enterprise-01",
        message="Supplier signal",
        price="UNKNOWN",
    )["proposal"]


def _count(db, table):
    import sqlite3
    with sqlite3.connect(db) as conn:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_unauthorized_identity_cannot_create_authority_or_authorization(tmp_path, monkeypatch):
    ops, db = _ops(tmp_path, monkeypatch)
    proposal = _proposal(ops)

    try:
        ops.decide_proposal(
            subject="proposal-subject",
            proposal_id=proposal.id,
            action="APPROVE",
            actor="unauthorized",
            actor_identity={"uid": "unauthorized", "role": "Guest", "access_level": 0},
        )
    except ValueError as exc:
        assert "authority" in str(exc).lower()
    else:
        raise AssertionError("unauthorized enterprise approval must fail")

    assert _count(db, "ew_authority_events") == 0
    assert _count(db, "ew_authorizations") == 0


def test_authorized_identity_can_create_authority_and_authorization(tmp_path, monkeypatch):
    ops, db = _ops(tmp_path, monkeypatch)
    proposal = _proposal(ops)

    result = ops.decide_proposal(
        subject="proposal-subject",
        proposal_id=proposal.id,
        action="APPROVE",
        actor="sovereign",
        actor_identity={"uid": "sovereign", "role": "Flamekeeper", "access_level": 0},
    )

    assert result["status"] == "AUTHORIZED"
    assert result["authority_event"].actor == "sovereign"
    assert result["authorization"] is not None
    assert _count(db, "ew_authority_events") == 1
    assert _count(db, "ew_authorizations") == 1


def test_api_approval_does_not_create_enterprise_authorization(tmp_path, monkeypatch):
    import weaver.enterprise_orchestration as ew

    db = str(tmp_path / "api-approval.db")
    monkeypatch.setattr(ew, "_DB_PATH", db)
    EnterpriseOrchestrationStore()

    current = {"uid": "requester", "role": "Guest", "access_level": 0}
    app.dependency_overrides[require_auth] = lambda: {
        "uid": current["uid"],
        "email": "requester@example.com",
        "access_level": current["access_level"],
        "role": current["role"],
    }

    with APPROVAL_LOCK:
        PENDING_APPROVALS.clear()

    try:
        client = TestClient(app)
        requested = client.post(
            "/api/approvals/request",
            json={
                "tool_name": "execute_shell",
                "payload": {"command": "whoami"},
                "description": "upstream continuity measurement",
            },
        )
        assert requested.status_code == 200, requested.text
        approval_id = requested.json()["approval_id"]

        current.update({"uid": "sovereign", "role": "Flamekeeper", "access_level": 3})
        approved = client.post(f"/api/approvals/{approval_id}/approve")
        assert approved.status_code == 200, approved.text

        assert _count(db, "ew_authorizations") == 0
        assert _count(db, "ew_authority_events") == 0
    finally:
        app.dependency_overrides.pop(require_auth, None)
        with APPROVAL_LOCK:
            PENDING_APPROVALS.clear()
