"""Gate 1 negative security tests — ARKADIA-CHIEF-001 identity and governance.

Every test here asserts a *refusal*. A passing suite means the boundaries hold:
no self-authorization, no privilege escalation, no token use after revocation,
no access outside the granted scope, no secret reads, no cross-workspace access,
no impersonation of the Founder UID.

The agent is never commissioned by these tests. Each one builds a delegation in
a throwaway database, exercises one boundary, and asserts the deny.
"""
from __future__ import annotations

import time

import jwt
import pytest

import executive_office.registry as registry_module
import weaver.authorization_revocation as revocation_module
import weaver.enterprise_orchestration as ew
from executive_office import (
    MAX_TOKEN_TTL_SECONDS,
    PRINCIPAL_SUBJECT,
    TOKEN_AUDIENCE,
)
from executive_office.broker import (
    ALGORITHM,
    KEY_ID,
    BrokerUnavailable,
    ExecutiveIdentityBroker,
)
from executive_office.control import FounderDelegationControl
from executive_office.knowledge_access import curated_context, read_curated_notes
from executive_office.policy import policy_digest
from executive_office.registry import DelegationRegistry
from executive_office.revocation import revoke_delegation_cascade
from executive_office.tokens import ExecutiveAuthError, verify_machine_token
from weaver.authorization_revocation import (
    AuthorizationRevocationStore,
    AuthorizationRevoked,
    assert_dispatchable,
)

FOUNDER_UID = "founder-uid-001"
OTHER_UID = "other-user-uid-999"
WORKSPACE_ID = "ws-canonical-001"


# ── fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def stores(tmp_path, monkeypatch):
    """Isolated registry + revocation stores, and a broker key dir."""
    db = str(tmp_path / "executive.db")
    monkeypatch.setattr(registry_module, "_DB_PATH", db)
    monkeypatch.setattr(revocation_module, "_DB_PATH", db)
    monkeypatch.setattr(ew, "_DB_PATH", db)
    key_dir = str(tmp_path / "keys")
    registry = DelegationRegistry(db_path=db)
    broker = ExecutiveIdentityBroker(registry=registry, key_dir=key_dir)
    revocations = AuthorizationRevocationStore(db_path=db)
    return {
        "db": db,
        "registry": registry,
        "broker": broker,
        "revocations": revocations,
        "key_dir": key_dir,
    }


@pytest.fixture()
def founder():
    return {"uid": FOUNDER_UID, "access_level": 3, "role": "Flamekeeper"}


def _grant(stores, founder, *, capabilities=None, resources=None, ttl=3600, collection=None):
    control = FounderDelegationControl(registry=stores["registry"])
    return control.grant(
        founder=founder,
        owner_uid=FOUNDER_UID,
        workspace_id=WORKSPACE_ID,
        capabilities=capabilities or ["read_project_metadata"],
        resources=resources or ["project-1"],
        expires_at=time.time() + ttl,
        knowledge_collection=collection,
    )


def _token(stores, delegation_id=None):
    return stores["broker"].issue(delegation_id=delegation_id)["token"]


# ── 1. no token ──────────────────────────────────────────────────────────────

def test_no_token_is_rejected(stores):
    with pytest.raises(ExecutiveAuthError) as exc:
        verify_machine_token("", registry=stores["registry"], broker=stores["broker"])
    assert exc.value.status_code == 401


# ── 2. a Firebase human token is not a machine identity ──────────────────────

def test_firebase_human_token_is_rejected_as_machine_identity(stores):
    """A human Firebase ID token must not authenticate a machine route.

    It is signed by Google, not by the broker, so the signature check refuses
    it. This is the separation the ADR requires: do not extend human auth to
    accept arbitrary machine JWTs, and do not let a human token stand in for a
    machine principal.
    """
    human_token = jwt.encode(
        {"sub": FOUNDER_UID, "aud": "arkadia-console", "iss": "https://securetoken.google.com/arkadia"},
        "not-the-broker-key",
        algorithm="HS256",
    )
    with pytest.raises(ExecutiveAuthError):
        verify_machine_token(human_token, registry=stores["registry"], broker=stores["broker"])


# ── 3. wrong issuer / audience / signature / algorithm / kid ─────────────────

def test_wrong_audience_is_rejected(stores, founder):
    _grant(stores, founder)
    token = _token(stores)
    claims = jwt.decode(token, options={"verify_signature": False})
    claims["aud"] = "some-other-api"
    forged = jwt.encode(claims, stores["broker"]._private_key_pem(), algorithm=ALGORITHM,
                        headers={"kid": KEY_ID})
    with pytest.raises(ExecutiveAuthError) as exc:
        verify_machine_token(forged, registry=stores["registry"], broker=stores["broker"])
    assert "audience" in exc.value.reason


def test_wrong_issuer_is_rejected(stores, founder):
    _grant(stores, founder)
    token = _token(stores)
    claims = jwt.decode(token, options={"verify_signature": False})
    claims["iss"] = "https://evil.example.com"
    forged = jwt.encode(claims, stores["broker"]._private_key_pem(), algorithm=ALGORITHM,
                        headers={"kid": KEY_ID})
    with pytest.raises(ExecutiveAuthError) as exc:
        verify_machine_token(forged, registry=stores["registry"], broker=stores["broker"])
    assert "issuer" in exc.value.reason


def test_wrong_signature_is_rejected(stores, founder):
    _grant(stores, founder)
    token = _token(stores)
    claims = jwt.decode(token, options={"verify_signature": False})
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    attacker = Ed25519PrivateKey.generate()
    attacker_pem = attacker.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    forged = jwt.encode(claims, attacker_pem, algorithm=ALGORITHM, headers={"kid": KEY_ID})
    with pytest.raises(ExecutiveAuthError) as exc:
        verify_machine_token(forged, registry=stores["registry"], broker=stores["broker"])
    assert "signature" in exc.value.reason


def test_unknown_key_id_is_rejected(stores, founder):
    _grant(stores, founder)
    token = _token(stores)
    claims = jwt.decode(token, options={"verify_signature": False})
    forged = jwt.encode(claims, stores["broker"]._private_key_pem(), algorithm=ALGORITHM,
                        headers={"kid": "attacker-key"})
    with pytest.raises(ExecutiveAuthError) as exc:
        verify_machine_token(forged, registry=stores["registry"], broker=stores["broker"])
    assert "key id" in exc.value.reason


def test_unsupported_algorithm_is_rejected(stores, founder):
    _grant(stores, founder)
    token = _token(stores)
    claims = jwt.decode(token, options={"verify_signature": False})
    forged = jwt.encode(claims, "shared-secret", algorithm="HS256", headers={"kid": KEY_ID})
    with pytest.raises(ExecutiveAuthError):
        verify_machine_token(forged, registry=stores["registry"], broker=stores["broker"])


# ── 4. expiry and not-before ─────────────────────────────────────────────────

def test_expired_token_is_rejected(stores, founder):
    _grant(stores, founder)
    # Mint a token whose validity window has already closed. PyJWT validates
    # against real time, so the token itself must be in the past.
    token = stores["broker"].issue(now=time.time() - MAX_TOKEN_TTL_SECONDS - 120)["token"]
    with pytest.raises(ExecutiveAuthError) as exc:
        verify_machine_token(token, registry=stores["registry"], broker=stores["broker"])
    assert "expired" in exc.value.reason


def test_future_not_before_is_rejected(stores, founder):
    _grant(stores, founder)
    token = _token(stores)
    claims = jwt.decode(token, options={"verify_signature": False})
    future = int(time.time()) + 600
    claims["nbf"] = future
    claims["iat"] = future
    claims["exp"] = future + 60
    forged = jwt.encode(claims, stores["broker"]._private_key_pem(), algorithm=ALGORITHM,
                        headers={"kid": KEY_ID})
    with pytest.raises(ExecutiveAuthError) as exc:
        verify_machine_token(forged, registry=stores["registry"], broker=stores["broker"])
    assert "not yet valid" in exc.value.reason


def test_token_ttl_never_exceeds_the_maximum(stores, founder):
    _grant(stores, founder)
    issued = stores["broker"].issue(ttl_seconds=99999)
    claims = jwt.decode(issued["token"], options={"verify_signature": False})
    assert claims["exp"] - claims["iat"] <= MAX_TOKEN_TTL_SECONDS


# ── 5. altered claims ────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "claim,value",
    [
        ("sub", "service:SOMEONE-ELSE"),
        ("owner_sub", OTHER_UID),
        ("workspace_id", "ws-someone-else"),
        ("policy_digest", "0" * 64),
        ("credential_epoch", 99),
        ("principal_type", "human_user"),
    ],
)
def test_altered_claims_are_rejected(stores, founder, claim, value):
    _grant(stores, founder)
    token = _token(stores)
    claims = jwt.decode(token, options={"verify_signature": False})
    claims[claim] = value
    forged = jwt.encode(claims, stores["broker"]._private_key_pem(), algorithm=ALGORITHM,
                        headers={"kid": KEY_ID})
    with pytest.raises(ExecutiveAuthError):
        verify_machine_token(forged, registry=stores["registry"], broker=stores["broker"])


def test_missing_required_claim_is_rejected(stores, founder):
    _grant(stores, founder)
    token = _token(stores)
    claims = jwt.decode(token, options={"verify_signature": False})
    del claims["delegation_id"]
    forged = jwt.encode(claims, stores["broker"]._private_key_pem(), algorithm=ALGORITHM,
                        headers={"kid": KEY_ID})
    with pytest.raises(ExecutiveAuthError):
        verify_machine_token(forged, registry=stores["registry"], broker=stores["broker"])


# ── 6. revoked / suspended delegation with an otherwise valid JWT ────────────

def test_revoked_delegation_rejects_a_valid_unexpired_token(stores, founder):
    delegation = _grant(stores, founder)
    token = _token(stores)
    # The token is valid right now.
    assert verify_machine_token(token, registry=stores["registry"], broker=stores["broker"])

    stores["registry"].revoke(delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID,
                              reason="test revocation")

    with pytest.raises(ExecutiveAuthError) as exc:
        verify_machine_token(token, registry=stores["registry"], broker=stores["broker"])
    assert exc.value.status_code == 403


def test_suspended_delegation_rejects_a_valid_unexpired_token(stores, founder):
    delegation = _grant(stores, founder)
    token = _token(stores)
    stores["registry"].suspend(delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID,
                               reason="test suspension")
    with pytest.raises(ExecutiveAuthError) as exc:
        verify_machine_token(token, registry=stores["registry"], broker=stores["broker"])
    assert exc.value.status_code == 403


def test_broker_refuses_to_issue_after_revocation(stores, founder):
    delegation = _grant(stores, founder)
    stores["registry"].revoke(delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID,
                              reason="test")
    with pytest.raises(BrokerUnavailable):
        stores["broker"].issue()


# ── 7. expired delegation ────────────────────────────────────────────────────

def test_expired_delegation_rejects_a_valid_token(stores, founder):
    delegation = _grant(stores, founder, ttl=1)
    token = _token(stores)
    with pytest.raises(ExecutiveAuthError) as exc:
        verify_machine_token(
            token,
            registry=stores["registry"],
            broker=stores["broker"],
            now=time.time() + 120,
        )
    assert exc.value.status_code == 403


def test_broker_refuses_to_issue_for_an_expired_delegation(stores, founder):
    _grant(stores, founder, ttl=1)
    with pytest.raises(BrokerUnavailable):
        stores["broker"].issue(now=time.time() + 120)


# ── 8. old credential epoch after rotation ───────────────────────────────────

def test_old_credential_epoch_is_rejected_after_suspend(stores, founder):
    delegation = _grant(stores, founder)
    token = _token(stores)
    stores["registry"].suspend(delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID,
                               reason="rotate")
    stores["registry"].reactivate(delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID,
                                  reason="resume")
    # The delegation is ACTIVE again, but the old token carries the old epoch.
    with pytest.raises(ExecutiveAuthError) as exc:
        verify_machine_token(token, registry=stores["registry"], broker=stores["broker"])
    assert "epoch" in exc.value.reason


# ── 9. registry unavailable → deny ───────────────────────────────────────────

def test_unreadable_registry_denies(stores, founder, monkeypatch):
    _grant(stores, founder)
    token = _token(stores)

    def _boom(*_a, **_k):
        raise RuntimeError("registry offline")

    monkeypatch.setattr(stores["registry"], "find", _boom)
    with pytest.raises(ExecutiveAuthError) as exc:
        verify_machine_token(token, registry=stores["registry"], broker=stores["broker"])
    assert exc.value.status_code == 503


def test_broker_refuses_when_registry_is_unavailable(stores, founder, monkeypatch):
    _grant(stores, founder)

    def _boom(*_a, **_k):
        raise RuntimeError("registry offline")

    monkeypatch.setattr(stores["registry"], "active_for_principal", _boom)
    with pytest.raises(BrokerUnavailable):
        stores["broker"].issue()


# ── 10. no self-authorization / no privilege escalation ──────────────────────

def test_agent_cannot_grant_itself_a_delegation(stores):
    """The control surface requires a verified Founder session."""
    control = FounderDelegationControl(registry=stores["registry"])
    with pytest.raises(PermissionError):
        control.grant(
            founder=None,
            owner_uid=FOUNDER_UID,
            workspace_id=WORKSPACE_ID,
            capabilities=["read_project_metadata"],
            resources=["project-1"],
            expires_at=time.time() + 3600,
        )


def test_non_founder_cannot_grant(stores):
    control = FounderDelegationControl(registry=stores["registry"])
    with pytest.raises(PermissionError):
        control.grant(
            founder={"uid": OTHER_UID, "access_level": 1},
            owner_uid=OTHER_UID,
            workspace_id=WORKSPACE_ID,
            capabilities=["read_project_metadata"],
            resources=["project-1"],
            expires_at=time.time() + 3600,
        )


def test_founder_cannot_grant_access_to_another_owners_data(stores, founder):
    """owner_uid must equal the authenticated Founder; no granting on behalf."""
    control = FounderDelegationControl(registry=stores["registry"])
    with pytest.raises(PermissionError):
        control.grant(
            founder=founder,
            owner_uid=OTHER_UID,
            workspace_id=WORKSPACE_ID,
            capabilities=["read_project_metadata"],
            resources=["project-1"],
            expires_at=time.time() + 3600,
        )


@pytest.mark.parametrize(
    "capability",
    [
        "authorize_proposal",
        "approve_request",
        "execute_payment",
        "merge_protected_branch",
        "deploy_production",
        "change_identity_policy",
        "change_credentials",
    ],
)
def test_reserved_human_only_capabilities_cannot_be_delegated(stores, founder, capability):
    control = FounderDelegationControl(registry=stores["registry"])
    with pytest.raises(ValueError, match="reserved human-only"):
        control.grant(
            founder=founder,
            owner_uid=FOUNDER_UID,
            workspace_id=WORKSPACE_ID,
            capabilities=[capability],
            resources=["project-1"],
            expires_at=time.time() + 3600,
        )


def test_unknown_capability_cannot_be_delegated(stores, founder):
    control = FounderDelegationControl(registry=stores["registry"])
    with pytest.raises(ValueError, match="outside the grantable envelope"):
        control.grant(
            founder=founder,
            owner_uid=FOUNDER_UID,
            workspace_id=WORKSPACE_ID,
            capabilities=["become_root"],
            resources=["project-1"],
            expires_at=time.time() + 3600,
        )


def test_wildcard_resource_scope_is_refused(stores, founder):
    control = FounderDelegationControl(registry=stores["registry"])
    with pytest.raises(ValueError, match="wildcard"):
        control.grant(
            founder=founder,
            owner_uid=FOUNDER_UID,
            workspace_id=WORKSPACE_ID,
            capabilities=["read_project_metadata"],
            resources=["*"],
            expires_at=time.time() + 3600,
        )


def test_agent_cannot_revoke_or_reactivate_its_own_delegation(stores, founder):
    delegation = _grant(stores, founder)
    control = FounderDelegationControl(registry=stores["registry"])
    with pytest.raises(PermissionError):
        control.revoke(founder=None, delegation_id=delegation.delegation_id, reason="self")
    with pytest.raises(PermissionError):
        control.reactivate(founder=None, delegation_id=delegation.delegation_id, reason="self")


def test_a_different_founder_cannot_revoke_someone_elses_delegation(stores, founder):
    delegation = _grant(stores, founder)
    control = FounderDelegationControl(registry=stores["registry"])
    with pytest.raises(PermissionError):
        control.revoke(
            founder={"uid": OTHER_UID, "access_level": 3},
            delegation_id=delegation.delegation_id,
            reason="hostile",
        )


def test_revocation_is_terminal(stores, founder):
    delegation = _grant(stores, founder)
    stores["registry"].revoke(delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID,
                              reason="terminal")
    with pytest.raises(ValueError, match="terminal"):
        stores["registry"].reactivate(delegation_id=delegation.delegation_id,
                                      founder_uid=FOUNDER_UID, reason="try")


# ── 11. scope enforcement ────────────────────────────────────────────────────

def test_principal_cannot_exercise_a_capability_outside_its_scope(stores, founder):
    _grant(stores, founder, capabilities=["read_project_metadata"])
    principal = verify_machine_token(_token(stores), registry=stores["registry"],
                                     broker=stores["broker"])
    assert principal.has_capability("read_project_metadata")
    assert not principal.has_capability("deploy_production")
    assert not principal.has_capability("read_curated_knowledge")


def test_principal_cannot_reach_a_resource_outside_its_scope(stores, founder):
    _grant(stores, founder, resources=["project-1"])
    principal = verify_machine_token(_token(stores), registry=stores["registry"],
                                     broker=stores["broker"])
    assert principal.allows_resource("project-1")
    assert not principal.allows_resource("project-2")
    assert not principal.allows_resource("someone-elses-project")


def test_principal_owner_and_workspace_come_from_the_delegation_not_the_token(stores, founder):
    _grant(stores, founder)
    principal = verify_machine_token(_token(stores), registry=stores["registry"],
                                     broker=stores["broker"])
    assert principal.owner_uid == FOUNDER_UID
    assert principal.workspace_id == WORKSPACE_ID
    assert principal.subject == PRINCIPAL_SUBJECT


# ── 12. curated Knowledge OS access ──────────────────────────────────────────

def test_no_curated_collection_means_no_knowledge_access(stores, founder):
    _grant(stores, founder)
    principal = verify_machine_token(_token(stores), registry=stores["registry"],
                                     broker=stores["broker"])
    assert read_curated_notes(principal) == []
    assert curated_context(principal)["returned"] == 0


def test_curated_access_never_falls_back_to_owner_wide_retrieval(stores, founder):
    """The whole point: a delegation without a collection reads nothing.

    `assemble_context` would return every note owned by the Founder. This path
    must not, and must not silently degrade into it.
    """
    _grant(stores, founder, collection=None)
    principal = verify_machine_token(_token(stores), registry=stores["registry"],
                                     broker=stores["broker"])
    context = curated_context(principal)
    assert context["curated"] is True
    assert context["relevant_notes"] == []
    assert context["collection_size"] == 0


def test_conversation_notes_are_denied_even_if_curated(stores, founder, monkeypatch):
    """A curated collection naming a conversation note still cannot read it."""
    import executive_office.knowledge_access as ka

    _grant(stores, founder, collection=["note-conversation-1"])
    principal = verify_machine_token(_token(stores), registry=stores["registry"],
                                     broker=stores["broker"])

    captured = {}

    def _fake_execute(sql, params):
        captured["sql"] = sql
        captured["params"] = params
        return []

    monkeypatch.setattr(ka, "execute", _fake_execute)
    ka.read_curated_notes(principal)
    # The private-boundary predicate is present in the query itself.
    assert "note_type NOT IN" in captured["sql"]
    assert "conversation" in captured["params"]
    # And the owner predicate is the delegation's owner, not a caller argument.
    assert FOUNDER_UID in captured["params"]


# ── 13. Weaver dispatch: expiry and durable revocation ───────────────────────

def _authorization(stores, *, expires_at=None, delegation_id=None):
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
        expires_at=expires_at,
        delegation_id=delegation_id,
    )


def test_expired_authorization_is_refused_at_dispatch(stores):
    auth = _authorization(stores, expires_at=time.time() - 10)
    with pytest.raises(AuthorizationRevoked, match="expired"):
        assert_dispatchable(authorization=auth, revocations=stores["revocations"])


def test_revoked_authorization_is_refused_at_dispatch(stores):
    auth = _authorization(stores, expires_at=time.time() + 3600)
    # Valid before revocation.
    assert_dispatchable(authorization=auth, revocations=stores["revocations"])
    stores["revocations"].revoke(
        authorization_id=auth.id,
        subject=FOUNDER_UID,
        reason="test",
        revoked_by=FOUNDER_UID,
    )
    with pytest.raises(AuthorizationRevoked, match="revoked"):
        assert_dispatchable(authorization=auth, revocations=stores["revocations"])


def test_outstanding_authorization_after_delegation_revoke_is_refused(stores, founder):
    """The hard blocker: an unexpired authorization must not survive revocation."""
    delegation = _grant(stores, founder)
    auth = _authorization(stores, expires_at=time.time() + 3600,
                          delegation_id=delegation.delegation_id)
    assert_dispatchable(authorization=auth, revocations=stores["revocations"])

    result = revoke_delegation_cascade(
        delegation_id=delegation.delegation_id,
        founder_uid=FOUNDER_UID,
        reason="emergency",
        registry=stores["registry"],
        revocations=stores["revocations"],
    )
    assert result["revoked_authorizations"] == 1

    with pytest.raises(AuthorizationRevoked, match="revoked"):
        assert_dispatchable(authorization=auth, revocations=stores["revocations"])


def test_weaver_console_adapter_refuses_a_revoked_authorization(stores, founder, tmp_path):
    """End-to-end through the real adapter, not just the guard function."""
    from weaver.console_adapter import WeaverConsoleAdapter

    delegation = _grant(stores, founder)
    auth = _authorization(stores, expires_at=time.time() + 3600,
                          delegation_id=delegation.delegation_id)
    store = ew.EnterpriseOrchestrationStore()
    attempt = store.execution_attempt(
        subject=FOUNDER_UID,
        authorization_id=auth.id,
        tool_channel="filesystem.read",
        request_payload={"path": "README.md"},
    )
    adapter = WeaverConsoleAdapter(store=store, repo_root=str(tmp_path),
                                   revocations=stores["revocations"])

    stores["revocations"].revoke(
        authorization_id=auth.id, subject=FOUNDER_UID, reason="test", revoked_by=FOUNDER_UID,
    )
    with pytest.raises(PermissionError):
        adapter.dispatch(
            subject=FOUNDER_UID,
            authorization_id=auth.id,
            execution_attempt_id=attempt.id,
            tool_channel="filesystem.read",
            request_payload={"path": "README.md"},
        )


# ── 14. revoke during a queued job ───────────────────────────────────────────

def test_revoke_cancels_queued_work(stores, founder):
    delegation = _grant(stores, founder)
    job = stores["registry"].enqueue_work(
        delegation_id=delegation.delegation_id, description="queued report"
    )
    assert stores["registry"].job_is_dispatchable(job)

    result = revoke_delegation_cascade(
        delegation_id=delegation.delegation_id,
        founder_uid=FOUNDER_UID,
        reason="revoke during queue",
        registry=stores["registry"],
        revocations=stores["revocations"],
    )
    assert result["cancelled_jobs"] == 1
    assert not stores["registry"].job_is_dispatchable(job)


# ── 15. restart recovery ─────────────────────────────────────────────────────

def test_revocation_survives_a_fresh_registry_instance(stores, founder):
    """Durability: a new process reading the same DB sees the revocation."""
    delegation = _grant(stores, founder)
    token = _token(stores)
    stores["registry"].revoke(delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID,
                              reason="durable")

    fresh_registry = DelegationRegistry(db_path=stores["db"])
    fresh_broker = ExecutiveIdentityBroker(registry=fresh_registry, key_dir=stores["key_dir"])
    with pytest.raises(ExecutiveAuthError):
        verify_machine_token(token, registry=fresh_registry, broker=fresh_broker)


def test_active_delegation_survives_a_fresh_registry_instance(stores, founder):
    delegation = _grant(stores, founder)
    fresh_registry = DelegationRegistry(db_path=stores["db"])
    reloaded = fresh_registry.get(delegation.delegation_id)
    assert reloaded.status == "ACTIVE"
    assert reloaded.owner_uid == FOUNDER_UID
    assert reloaded.credential_epoch == delegation.credential_epoch


def test_append_only_event_history_records_every_transition(stores, founder):
    delegation = _grant(stores, founder)
    stores["registry"].suspend(delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID,
                               reason="s")
    stores["registry"].reactivate(delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID,
                                  reason="r")
    stores["registry"].revoke(delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID,
                              reason="x")
    events = stores["registry"].events(delegation.delegation_id)
    assert [e["event_type"] for e in events] == ["GRANTED", "SUSPENDED", "REACTIVATED", "REVOKED"]
    # Epoch strictly increases across the transitions.
    epochs = [e["credential_epoch"] for e in events]
    assert epochs == sorted(epochs)
    assert epochs[-1] > epochs[0]


# ── 16. policy drift ─────────────────────────────────────────────────────────

def test_policy_digest_drift_invalidates_the_delegation(stores, founder, monkeypatch):
    _grant(stores, founder)
    token = _token(stores)
    import executive_office.tokens as tokens_module

    monkeypatch.setattr(tokens_module, "policy_digest", lambda: "f" * 64)
    with pytest.raises(ExecutiveAuthError) as exc:
        verify_machine_token(token, registry=stores["registry"], broker=stores["broker"])
    assert "stale policy" in exc.value.reason


def test_broker_refuses_to_issue_on_policy_drift(stores, founder, monkeypatch):
    _grant(stores, founder)
    import executive_office.broker as broker_module

    monkeypatch.setattr(broker_module, "policy_digest", lambda: "f" * 64)
    with pytest.raises(BrokerUnavailable, match="stale policy"):
        stores["broker"].issue()


# ── 17. the agent is not commissioned ────────────────────────────────────────

def test_no_delegation_exists_by_default(stores):
    """A fresh registry has no active delegation: the agent is uncommissioned."""
    assert stores["registry"].active_for_principal() is None
    with pytest.raises(BrokerUnavailable):
        stores["broker"].issue()


def test_identity_record_still_declares_not_commissioned():
    """The committed identity record must not claim commissioning."""
    import os

    path = os.path.join(os.path.dirname(__file__), "..", "executive_office", "identity", "identity.yaml")
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    assert "PROPOSED_NOT_COMMISSIONED" in text
    assert "active_delegation: false" in text
