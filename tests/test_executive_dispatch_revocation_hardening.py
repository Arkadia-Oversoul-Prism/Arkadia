"""Gate 1 security reconciliation — dispatch-time delegation re-read.

The Gate 1C cascade revokes the delegation *first*, then writes authorization
revocations. If that second write fails, the revocation ledger has no record
and an unexpired authorization would otherwise look clean. These tests prove
the dispatch guard closes that window by independently re-reading the linked
delegation and failing closed on status, expiry, epoch, or any read error.

Every test asserts a *refusal*. The agent is never commissioned.
"""
from __future__ import annotations

import sqlite3
import time

import pytest

import executive_office.registry as registry_module
import weaver.authorization_revocation as revocation_module
import weaver.enterprise_orchestration as ew
from executive_office.control import FounderDelegationControl
from executive_office.registry import DelegationRegistry
from executive_office.revocation import revoke_delegation_cascade
from weaver.authorization_revocation import (
    AuthorizationRevocationStore,
    AuthorizationRevoked,
    assert_dispatchable,
)

FOUNDER_UID = "founder-uid-001"
WORKSPACE_ID = "ws-canonical-001"


# ── fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def stores(tmp_path, monkeypatch):
    db = str(tmp_path / "executive.db")
    monkeypatch.setattr(registry_module, "_DB_PATH", db)
    monkeypatch.setattr(revocation_module, "_DB_PATH", db)
    monkeypatch.setattr(ew, "_DB_PATH", db)
    registry = DelegationRegistry(db_path=db)
    revocations = AuthorizationRevocationStore(db_path=db)
    return {"db": db, "registry": registry, "revocations": revocations}


@pytest.fixture()
def founder():
    return {"uid": FOUNDER_UID, "access_level": 3, "role": "Flamekeeper"}


def _grant(stores, founder, *, ttl=3600):
    control = FounderDelegationControl(registry=stores["registry"])
    return control.grant(
        founder=founder,
        owner_uid=FOUNDER_UID,
        workspace_id=WORKSPACE_ID,
        capabilities=["read_project_metadata"],
        resources=["project-1"],
        expires_at=time.time() + ttl,
    )


def _authorization(*, delegation_id=None, delegation_epoch=None, expires_at=None):
    """Mint a real authorization through the real store."""
    store = ew.EnterpriseOrchestrationStore()
    proposal = store.proposal(
        subject=FOUNDER_UID,
        enterprise_id="ent-1",
        objective="read a file",
        rationale="test",
        recommended_actions=["read"],
        required_authority="human",
        tool_selections=["filesystem.read"],
    )
    authority = store.authority_event(
        subject=FOUNDER_UID,
        actor=FOUNDER_UID,
        authority_context="founder",
        action="AUTHORIZE",
        previous_state={"status": "PROPOSED"},
        new_state={"status": "AUTHORIZED"},
        origin="test",
        authentication_context="firebase",
        correlation_id=proposal.correlation_id,
    )
    return store.authorize(
        subject=FOUNDER_UID,
        proposal_id=proposal.id,
        authority_event_id=authority.id,
        scope={"tools": ["filesystem.read"]},
        constraints={"read_only": True, "repository_root": ".", "network": False},
        expires_at=expires_at if expires_at is not None else time.time() + 3600,
        delegation_id=delegation_id,
        delegation_epoch=delegation_epoch,
    )


# ── 2. linkage is persisted and read back ────────────────────────────────────

def test_authorization_persists_delegation_id(stores, founder):
    delegation = _grant(stores, founder)
    auth = _authorization(delegation_id=delegation.delegation_id)
    assert auth.delegation_id == delegation.delegation_id
    # And it survives a fresh read from the store, not just the in-memory row.
    reloaded = ew.EnterpriseOrchestrationStore().authorization(
        subject=FOUNDER_UID, authorization_id=auth.id
    )
    assert reloaded.delegation_id == delegation.delegation_id


def test_authorization_auto_stamps_current_epoch(stores, founder):
    delegation = _grant(stores, founder)
    auth = _authorization(delegation_id=delegation.delegation_id)
    assert auth.delegation_epoch == delegation.credential_epoch


def test_authorization_without_delegation_has_null_linkage(stores):
    auth = _authorization()
    assert auth.delegation_id is None
    assert auth.delegation_epoch is None


def test_unresolvable_delegation_refuses_authorization(stores):
    with pytest.raises(ValueError, match="delegation could not be resolved"):
        _authorization(delegation_id="eodlg-does-not-exist")


# ── 1. the critical gap: cascade partially fails ─────────────────────────────

def test_revoked_delegation_denies_even_when_revocation_write_fails(
    stores, founder, monkeypatch
):
    """The exact failure path: delegation REVOKED, authorization revocation lost."""
    delegation = _grant(stores, founder)
    auth = _authorization(delegation_id=delegation.delegation_id)

    # Valid before revocation.
    assert_dispatchable(
        authorization=auth, revocations=stores["revocations"], registry=stores["registry"]
    )

    # Simulate the cascade's second step failing: the delegation is revoked,
    # but the authorization revocation is never written.
    def _boom(*args, **kwargs):
        raise sqlite3.OperationalError("revocation store unavailable")

    monkeypatch.setattr(stores["revocations"], "revoke_for_delegation", _boom)
    with pytest.raises(sqlite3.OperationalError):
        revoke_delegation_cascade(
            delegation_id=delegation.delegation_id,
            founder_uid=FOUNDER_UID,
            reason="founder revoked",
            registry=stores["registry"],
            revocations=stores["revocations"],
        )

    # The ledger has no record — the old guard would have allowed this.
    assert stores["revocations"].is_revoked(auth.id) is False

    # The new guard re-reads the delegation and refuses anyway.
    with pytest.raises(AuthorizationRevoked, match="delegation is revoked"):
        assert_dispatchable(
            authorization=auth,
            revocations=stores["revocations"],
            registry=stores["registry"],
        )


# ── 3. adversarial matrix ────────────────────────────────────────────────────

def test_suspended_delegation_denies_unexpired_authorization(stores, founder):
    delegation = _grant(stores, founder)
    auth = _authorization(delegation_id=delegation.delegation_id)
    stores["registry"].suspend(
        delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID, reason="pause"
    )
    with pytest.raises(AuthorizationRevoked, match="delegation is suspended"):
        assert_dispatchable(
            authorization=auth, revocations=stores["revocations"], registry=stores["registry"]
        )


def test_delegation_expiring_before_authorization_denies(stores, founder):
    delegation = _grant(stores, founder, ttl=60)
    # Authorization outlives the delegation.
    auth = _authorization(
        delegation_id=delegation.delegation_id, expires_at=time.time() + 7200
    )
    # Dispatch after the delegation expired but before the authorization did.
    with pytest.raises(AuthorizationRevoked, match="delegation has expired"):
        assert_dispatchable(
            authorization=auth,
            revocations=stores["revocations"],
            registry=stores["registry"],
            now=time.time() + 120,
        )


def test_credential_epoch_supersession_denies(stores, founder):
    delegation = _grant(stores, founder)
    auth = _authorization(delegation_id=delegation.delegation_id)
    # Suspend then reactivate: the epoch advances, the authorization's own
    # expiry is untouched, and the delegation is ACTIVE again.
    stores["registry"].suspend(
        delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID, reason="pause"
    )
    stores["registry"].reactivate(
        delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID, reason="resume"
    )
    current = stores["registry"].get(delegation.delegation_id)
    assert current.status == "ACTIVE"
    assert current.credential_epoch > auth.delegation_epoch

    with pytest.raises(AuthorizationRevoked, match="credential epoch superseded"):
        assert_dispatchable(
            authorization=auth, revocations=stores["revocations"], registry=stores["registry"]
        )


def test_revocation_racing_queued_dispatch_denies(stores, founder):
    """A dispatch that read the authorization before revocation still refuses."""
    delegation = _grant(stores, founder)
    auth = _authorization(delegation_id=delegation.delegation_id)
    # The dispatcher has already loaded the authorization object...
    revoke_delegation_cascade(
        delegation_id=delegation.delegation_id,
        founder_uid=FOUNDER_UID,
        reason="race",
        registry=stores["registry"],
        revocations=stores["revocations"],
    )
    # ...and now reaches the gate. The stale object must not pass.
    with pytest.raises(AuthorizationRevoked):
        assert_dispatchable(
            authorization=auth, revocations=stores["revocations"], registry=stores["registry"]
        )


def test_registry_unavailable_denies(stores, founder, monkeypatch):
    delegation = _grant(stores, founder)
    auth = _authorization(delegation_id=delegation.delegation_id)

    def _unreadable(*args, **kwargs):
        raise sqlite3.OperationalError("registry unavailable")

    monkeypatch.setattr(stores["registry"], "get", _unreadable)
    with pytest.raises(AuthorizationRevoked, match="delegation could not be verified"):
        assert_dispatchable(
            authorization=auth, revocations=stores["revocations"], registry=stores["registry"]
        )


def test_missing_delegation_record_denies(stores, founder):
    delegation = _grant(stores, founder)
    auth = _authorization(delegation_id=delegation.delegation_id)
    # Delete the delegation row out from under the authorization.
    with sqlite3.connect(stores["db"]) as conn:
        conn.execute("DELETE FROM eo_delegations WHERE delegation_id=?", (delegation.delegation_id,))
    with pytest.raises(AuthorizationRevoked, match="delegation could not be verified"):
        assert_dispatchable(
            authorization=auth, revocations=stores["revocations"], registry=stores["registry"]
        )


def test_revocation_store_unavailable_denies(stores, founder, monkeypatch):
    delegation = _grant(stores, founder)
    auth = _authorization(delegation_id=delegation.delegation_id)

    def _unreadable(*args, **kwargs):
        raise sqlite3.OperationalError("revocation store unavailable")

    monkeypatch.setattr(stores["revocations"], "is_revoked", _unreadable)
    with pytest.raises(sqlite3.OperationalError):
        assert_dispatchable(
            authorization=auth, revocations=stores["revocations"], registry=stores["registry"]
        )


# ── 4. the happy path still works ────────────────────────────────────────────

def test_active_delegation_permits_dispatch(stores, founder):
    delegation = _grant(stores, founder)
    auth = _authorization(delegation_id=delegation.delegation_id)
    assert_dispatchable(
        authorization=auth, revocations=stores["revocations"], registry=stores["registry"]
    )


def test_non_agent_authorization_unaffected_by_registry(stores, monkeypatch):
    """An authorization with no delegation must not require a registry read."""
    auth = _authorization()

    def _must_not_be_called(*args, **kwargs):
        raise AssertionError("registry must not be read for a non-agent authorization")

    monkeypatch.setattr(stores["registry"], "get", _must_not_be_called)
    assert_dispatchable(
        authorization=auth, revocations=stores["revocations"], registry=stores["registry"]
    )
