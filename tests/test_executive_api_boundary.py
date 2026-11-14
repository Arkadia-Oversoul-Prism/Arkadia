"""Gate 1 API boundary tests — the two authentication surfaces must not cross.

A Firebase human token must not authenticate a machine route, and a broker
machine token must not authenticate a Founder control route. These tests drive
the real FastAPI app through TestClient.
"""
from __future__ import annotations

import time

import jwt
import pytest
from fastapi.testclient import TestClient

import executive_office.registry as registry_module
import weaver.authorization_revocation as revocation_module
import weaver.enterprise_orchestration as ew
from executive_office.broker import ExecutiveIdentityBroker
from executive_office.control import FounderDelegationControl
from executive_office.registry import DelegationRegistry

FOUNDER_UID = "founder-uid-api-001"
WORKSPACE_ID = "ws-api-001"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db = str(tmp_path / "executive.db")
    monkeypatch.setattr(registry_module, "_DB_PATH", db)
    monkeypatch.setattr(revocation_module, "_DB_PATH", db)
    monkeypatch.setattr(ew, "_DB_PATH", db)
    monkeypatch.setenv("EXECUTIVE_BROKER_KEY_DIR", str(tmp_path / "keys"))
    from api.main import app

    return TestClient(app)


@pytest.fixture()
def stores(tmp_path, monkeypatch):
    db = str(tmp_path / "executive.db")
    monkeypatch.setattr(registry_module, "_DB_PATH", db)
    monkeypatch.setattr(revocation_module, "_DB_PATH", db)
    monkeypatch.setattr(ew, "_DB_PATH", db)
    key_dir = str(tmp_path / "keys")
    monkeypatch.setenv("EXECUTIVE_BROKER_KEY_DIR", key_dir)
    registry = DelegationRegistry(db_path=db)
    return {
        "db": db,
        "registry": registry,
        "broker": ExecutiveIdentityBroker(registry=registry, key_dir=key_dir),
    }


def _grant(stores):
    control = FounderDelegationControl(registry=stores["registry"])
    return control.grant(
        founder={"uid": FOUNDER_UID, "access_level": 3},
        owner_uid=FOUNDER_UID,
        workspace_id=WORKSPACE_ID,
        capabilities=["read_project_metadata"],
        resources=["project-1"],
        expires_at=time.time() + 3600,
    )


# ── machine routes reject human tokens ──────────────────────────────────────

def test_machine_route_rejects_no_token(client):
    response = client.get("/solspire/executive/whoami")
    assert response.status_code == 401


def test_machine_route_rejects_a_firebase_human_token(client):
    human = jwt.encode(
        {"sub": FOUNDER_UID, "aud": "arkadia-console", "iss": "https://securetoken.google.com/arkadia"},
        "not-the-broker-key",
        algorithm="HS256",
    )
    response = client.get(
        "/solspire/executive/whoami", headers={"Authorization": f"Bearer {human}"}
    )
    assert response.status_code == 401


def test_machine_route_accepts_a_broker_token(client, stores):
    _grant(stores)
    token = stores["broker"].issue()["token"]
    response = client.get(
        "/solspire/executive/whoami", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    principal = response.json()["principal"]
    assert principal["owner_uid"] == FOUNDER_UID
    assert principal["workspace_id"] == WORKSPACE_ID
    assert principal["subject"] == "service:ARKADIA-CHIEF-001"


def test_machine_route_rejects_a_revoked_token(client, stores):
    delegation = _grant(stores)
    token = stores["broker"].issue()["token"]
    assert client.get(
        "/solspire/executive/whoami", headers={"Authorization": f"Bearer {token}"}
    ).status_code == 200

    stores["registry"].revoke(
        delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID, reason="api test"
    )
    response = client.get(
        "/solspire/executive/whoami", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


# ── Founder routes reject machine tokens ────────────────────────────────────

def test_founder_route_rejects_a_machine_token(client, stores):
    _grant(stores)
    token = stores["broker"].issue()["token"]
    response = client.get(
        "/solspire/executive/delegations", headers={"Authorization": f"Bearer {token}"}
    )
    # A broker token is not a Firebase identity: require_auth refuses it.
    assert response.status_code in (401, 403)


def test_founder_route_rejects_no_token(client):
    assert client.get("/solspire/executive/delegations").status_code in (401, 403)


# ── curated knowledge capability gate ───────────────────────────────────────

def test_curated_knowledge_requires_the_capability(client, stores):
    _grant(stores)  # capabilities: read_project_metadata only
    token = stores["broker"].issue()["token"]
    response = client.get(
        "/solspire/executive/knowledge/curated",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert "read_curated_knowledge" in response.json()["detail"]


def test_curated_knowledge_returns_nothing_without_a_collection(client, stores):
    control = FounderDelegationControl(registry=stores["registry"])
    control.grant(
        founder={"uid": FOUNDER_UID, "access_level": 3},
        owner_uid=FOUNDER_UID,
        workspace_id=WORKSPACE_ID,
        capabilities=["read_curated_knowledge"],
        resources=["project-1"],
        expires_at=time.time() + 3600,
        knowledge_collection=None,
    )
    token = stores["broker"].issue()["token"]
    response = client.get(
        "/solspire/executive/knowledge/curated",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    context = response.json()["context"]
    assert context["curated"] is True
    assert context["relevant_notes"] == []


# ── token issuance refuses when uncommissioned ──────────────────────────────

def test_token_route_requires_a_founder_session(client):
    """Issuance is not anonymous: an open route would let anyone mint tokens."""
    response = client.post("/solspire/executive/token")
    assert response.status_code in (401, 403)


def test_token_route_refuses_without_a_delegation(client, stores):
    """With a session but no delegation, the broker still refuses."""
    from executive_office.broker import BrokerUnavailable, ExecutiveIdentityBroker

    with pytest.raises(BrokerUnavailable, match="no active delegation"):
        ExecutiveIdentityBroker(registry=stores["registry"]).issue()


def test_token_issuance_never_returns_the_signing_key(stores):
    _grant(stores)
    body = stores["broker"].issue()
    assert "token" in body
    assert "PRIVATE KEY" not in str(body)
    assert set(body) >= {"token", "expires_in", "delegation_id", "credential_epoch"}
