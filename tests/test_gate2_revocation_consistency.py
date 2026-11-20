"""Gate 2 — revocation consistency across every delegated execution route.

Gate 1 proved the Weaver dispatch boundary re-reads the delegation. Gate 2
exists because Weaver is not the only route that can execute work on behalf of
a delegation:

  * ``weaver/console_adapter.py``        — ``ew_authorizations``   (Gate 1)
  * ``lab/engineering_lab/runtime.py``   — ``el_authorizations``   (Gate 2)
  * ``api/lab_routes.py`` ``/n-atlas/run`` — ``el_authorizations`` (Gate 2)
  * ``solspire/voice_pipeline.py``       — ``ew_authorizations``   (Gate 2)

Every test here asserts a *refusal*. The agent is never commissioned: each
delegation is created by the test itself, in a temporary database, and torn
down with it.
"""
from __future__ import annotations

import time

import pytest

import executive_office.registry as registry_module
import lab.engineering_lab.store as lab_store_module
import weaver.authorization_revocation as revocation_module
import weaver.enterprise_orchestration as ew
from executive_office.control import FounderDelegationControl
from executive_office.registry import DelegationRegistry
from executive_office.revocation import revoke_delegation_cascade
from lab.engineering_lab.contracts import BoundaryViolation
from lab.engineering_lab.runtime import EngineeringLabRuntime
from lab.engineering_lab.store import EngineeringLabStore
from weaver.authorization_revocation import (
    AuthorizationRevocationStore,
    AuthorizationRevoked,
    assert_delegation_dispatchable,
    assert_dispatchable,
)

FOUNDER_UID = "founder-uid-gate2"
WORKSPACE_ID = "ws-gate2"
SUBJECT = "subject-gate2"


# ── fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def stores(tmp_path, monkeypatch):
    db = str(tmp_path / "gate2.db")
    monkeypatch.setattr(registry_module, "_DB_PATH", db)
    monkeypatch.setattr(revocation_module, "_DB_PATH", db)
    monkeypatch.setattr(ew, "_DB_PATH", db)
    monkeypatch.setattr(lab_store_module, "_DB_PATH", db)
    return {
        "db": db,
        "registry": DelegationRegistry(db_path=db),
        "revocations": AuthorizationRevocationStore(db_path=db),
    }


@pytest.fixture()
def founder():
    return {"uid": FOUNDER_UID, "access_level": 3, "role": "Flamekeeper"}


def _grant(stores, founder, *, ttl=3600):
    return FounderDelegationControl(registry=stores["registry"]).grant(
        founder=founder,
        owner_uid=FOUNDER_UID,
        workspace_id=WORKSPACE_ID,
        capabilities=["read_project_metadata"],
        resources=["project-1"],
        expires_at=time.time() + ttl,
    )


def _lab_runtime(stores):
    return EngineeringLabRuntime(store=EngineeringLabStore())


def _lab_session_with_grant(runtime, *, delegation_id, delegation_epoch):
    """A real Lab session bound to a real, delegation-linked grant."""
    agent = runtime.register_agent(
        subject_ref=SUBJECT, role="BUILDER", display_name="gate2-agent"
    )
    session = runtime.open_session(
        subject_ref=SUBJECT,
        agent_id=agent["agent_id"],
        objective="gate2",
        workspace_ref="ws-gate2",
    )
    auth = runtime.record_authorization(
        subject_ref=SUBJECT,
        scope_ref=session["session_id"],
        operations_allowed=("read", "run", "test", "write"),
        delegation_id=delegation_id,
        delegation_epoch=delegation_epoch,
    )
    runtime._store.attach_authorization(
        session["session_id"], SUBJECT, auth["authorization_id"]
    )
    runtime.transition(session["session_id"], SUBJECT, "AUTHORIZED")
    return runtime.get_session(session["session_id"], SUBJECT), auth


# ── 1. the shared contract itself ────────────────────────────────────────────

def test_shared_contract_permits_an_active_delegation(stores, founder):
    delegation = _grant(stores, founder)
    assert_delegation_dispatchable(
        delegation_id=delegation.delegation_id,
        delegation_epoch=delegation.credential_epoch,
        registry=stores["registry"],
    )


def test_shared_contract_is_a_noop_without_a_delegation(stores):
    # A plain human authorization is not agent-associated; the contract must
    # not invent a delegation requirement for it.
    assert_delegation_dispatchable(
        delegation_id=None, delegation_epoch=None, registry=stores["registry"]
    )


def test_shared_contract_denies_a_revoked_delegation(stores, founder):
    delegation = _grant(stores, founder)
    stores["registry"].revoke(
        delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID, reason="test"
    )
    with pytest.raises(AuthorizationRevoked, match="revoked"):
        assert_delegation_dispatchable(
            delegation_id=delegation.delegation_id,
            delegation_epoch=delegation.credential_epoch,
            registry=stores["registry"],
        )


def test_shared_contract_denies_a_suspended_delegation(stores, founder):
    delegation = _grant(stores, founder)
    stores["registry"].suspend(
        delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID, reason="test"
    )
    with pytest.raises(AuthorizationRevoked, match="suspended"):
        assert_delegation_dispatchable(
            delegation_id=delegation.delegation_id,
            delegation_epoch=delegation.credential_epoch,
            registry=stores["registry"],
        )


def test_shared_contract_denies_a_superseded_epoch(stores, founder):
    delegation = _grant(stores, founder)
    stores["registry"].suspend(
        delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID, reason="bump"
    )
    stores["registry"].reactivate(
        delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID, reason="back"
    )
    with pytest.raises(AuthorizationRevoked, match="epoch superseded"):
        assert_delegation_dispatchable(
            delegation_id=delegation.delegation_id,
            delegation_epoch=delegation.credential_epoch,  # the OLD epoch
            registry=stores["registry"],
        )


def test_shared_contract_denies_a_missing_epoch(stores, founder):
    delegation = _grant(stores, founder)
    with pytest.raises(AuthorizationRevoked, match="epoch missing"):
        assert_delegation_dispatchable(
            delegation_id=delegation.delegation_id,
            delegation_epoch=None,
            registry=stores["registry"],
        )


def test_shared_contract_denies_an_expired_delegation(stores, founder):
    delegation = _grant(stores, founder, ttl=1)
    with pytest.raises(AuthorizationRevoked, match="expired"):
        assert_delegation_dispatchable(
            delegation_id=delegation.delegation_id,
            delegation_epoch=delegation.credential_epoch,
            registry=stores["registry"],
            now=time.time() + 10,
        )


def test_shared_contract_denies_a_missing_record(stores):
    # A missing record is not "no restriction": the registry raises, and the
    # contract converts any read failure into a denial. The message names the
    # failure class rather than claiming the record is absent, because the
    # contract cannot distinguish "absent" from "unreadable" — and must not.
    with pytest.raises(AuthorizationRevoked, match="could not be verified"):
        assert_delegation_dispatchable(
            delegation_id="eo-does-not-exist",
            delegation_epoch=1,
            registry=stores["registry"],
        )


def test_shared_contract_denies_when_the_registry_is_unavailable(stores, founder):
    delegation = _grant(stores, founder)

    class BrokenRegistry:
        def get(self, delegation_id):
            raise RuntimeError("registry offline")

    with pytest.raises(AuthorizationRevoked, match="could not be verified"):
        assert_delegation_dispatchable(
            delegation_id=delegation.delegation_id,
            delegation_epoch=delegation.credential_epoch,
            registry=BrokenRegistry(),
        )


# ── 2. Engineering Lab route ─────────────────────────────────────────────────

def test_lab_dispatch_permits_an_active_delegation(stores, founder):
    delegation = _grant(stores, founder)
    runtime = _lab_runtime(stores)
    session, _ = _lab_session_with_grant(
        runtime,
        delegation_id=delegation.delegation_id,
        delegation_epoch=delegation.credential_epoch,
    )
    # The gate returns the permitted operations rather than raising.
    assert runtime.assert_session_dispatchable(session, SUBJECT, "run")


def test_lab_dispatch_denies_a_revoked_delegation(stores, founder):
    delegation = _grant(stores, founder)
    runtime = _lab_runtime(stores)
    session, _ = _lab_session_with_grant(
        runtime,
        delegation_id=delegation.delegation_id,
        delegation_epoch=delegation.credential_epoch,
    )
    stores["registry"].revoke(
        delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID, reason="test"
    )
    with pytest.raises(BoundaryViolation, match="delegation no longer permits"):
        runtime.assert_session_dispatchable(session, SUBJECT, "run")


def test_lab_dispatch_denies_a_suspended_delegation(stores, founder):
    delegation = _grant(stores, founder)
    runtime = _lab_runtime(stores)
    session, _ = _lab_session_with_grant(
        runtime,
        delegation_id=delegation.delegation_id,
        delegation_epoch=delegation.credential_epoch,
    )
    stores["registry"].suspend(
        delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID, reason="test"
    )
    with pytest.raises(BoundaryViolation, match="delegation no longer permits"):
        runtime.assert_session_dispatchable(session, SUBJECT, "run")


def test_lab_dispatch_denies_a_superseded_epoch(stores, founder):
    delegation = _grant(stores, founder)
    runtime = _lab_runtime(stores)
    session, _ = _lab_session_with_grant(
        runtime,
        delegation_id=delegation.delegation_id,
        delegation_epoch=delegation.credential_epoch,
    )
    stores["registry"].suspend(
        delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID, reason="bump"
    )
    stores["registry"].reactivate(
        delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID, reason="back"
    )
    with pytest.raises(BoundaryViolation, match="delegation no longer permits"):
        runtime.assert_session_dispatchable(session, SUBJECT, "run")


def test_lab_dispatch_denies_when_the_registry_is_unavailable(stores, founder, monkeypatch):
    delegation = _grant(stores, founder)
    runtime = _lab_runtime(stores)
    session, _ = _lab_session_with_grant(
        runtime,
        delegation_id=delegation.delegation_id,
        delegation_epoch=delegation.credential_epoch,
    )

    class BrokenRegistry:
        def get(self, delegation_id):
            raise RuntimeError("registry offline")

    import weaver.authorization_revocation as ar

    real = ar.assert_delegation_dispatchable

    def _broken(**kwargs):
        return real(registry=BrokenRegistry(), **{k: v for k, v in kwargs.items() if k != "registry"})

    monkeypatch.setattr(ar, "assert_delegation_dispatchable", _broken)
    with pytest.raises(BoundaryViolation, match="delegation no longer permits"):
        runtime.assert_session_dispatchable(session, SUBJECT, "run")


def test_lab_dispatch_ignores_a_plain_human_grant(stores):
    """A grant with no delegation linkage must still work — Gate 2 must not
    break the ordinary human-authorized Lab path."""
    runtime = _lab_runtime(stores)
    session, _ = _lab_session_with_grant(
        runtime, delegation_id=None, delegation_epoch=None
    )
    assert runtime.assert_session_dispatchable(session, SUBJECT, "run")


# ── 3. the cascade withdraws Lab grants too ──────────────────────────────────

def test_cascade_revokes_lab_authorizations(stores, founder):
    delegation = _grant(stores, founder)
    runtime = _lab_runtime(stores)
    _, auth = _lab_session_with_grant(
        runtime,
        delegation_id=delegation.delegation_id,
        delegation_epoch=delegation.credential_epoch,
    )
    result = revoke_delegation_cascade(
        delegation_id=delegation.delegation_id,
        founder_uid=FOUNDER_UID,
        reason="gate2 cascade",
        registry=stores["registry"],
        revocations=stores["revocations"],
    )
    assert result["revoked_lab_authorizations"] == 1
    assert result["lab_revocation_error"] is None
    stored = runtime._store.get_authorization(auth["authorization_id"], SUBJECT)
    assert stored["revoked_at"], "the Lab grant was not withdrawn by the cascade"


def test_cascade_is_idempotent_for_lab_authorizations(stores, founder):
    delegation = _grant(stores, founder)
    runtime = _lab_runtime(stores)
    _lab_session_with_grant(
        runtime,
        delegation_id=delegation.delegation_id,
        delegation_epoch=delegation.credential_epoch,
    )
    first = revoke_delegation_cascade(
        delegation_id=delegation.delegation_id,
        founder_uid=FOUNDER_UID,
        reason="once",
        registry=stores["registry"],
        revocations=stores["revocations"],
    )
    second = revoke_delegation_cascade(
        delegation_id=delegation.delegation_id,
        founder_uid=FOUNDER_UID,
        reason="twice",
        registry=stores["registry"],
        revocations=stores["revocations"],
    )
    assert first["revoked_lab_authorizations"] == 1
    assert second["revoked_lab_authorizations"] == 0


def test_cascade_reports_a_lab_failure_without_masking_the_revocation(
    stores, founder, monkeypatch
):
    """If the Lab withdrawal fails, the delegation is still revoked and the
    failure is reported — never swallowed, never rolled back."""
    delegation = _grant(stores, founder)

    def _boom(self, delegation_id, *, reason=""):
        raise RuntimeError("lab store offline")

    monkeypatch.setattr(EngineeringLabStore, "revoke_for_delegation", _boom)
    result = revoke_delegation_cascade(
        delegation_id=delegation.delegation_id,
        founder_uid=FOUNDER_UID,
        reason="lab down",
        registry=stores["registry"],
        revocations=stores["revocations"],
    )
    assert result["delegation"]["status"] == "REVOKED"
    assert result["revoked_lab_authorizations"] == 0
    assert "lab store offline" in result["lab_revocation_error"]


# ── 4. Weaver still behaves (the Gate 1 contract is unchanged) ───────────────

def test_weaver_guard_still_denies_a_revoked_delegation(stores, founder):
    delegation = _grant(stores, founder)
    store = ew.EnterpriseOrchestrationStore()
    proposal = store.proposal(
        subject=FOUNDER_UID,
        enterprise_id="ent-g2",
        objective="read",
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
    auth = store.authorize(
        subject=FOUNDER_UID,
        proposal_id=proposal.id,
        authority_event_id=authority.id,
        scope={"tools": ["filesystem.read"]},
        constraints={"read_only": True, "repository_root": ".", "network": False},
        expires_at=time.time() + 3600,
        delegation_id=delegation.delegation_id,
    )
    # Permitted while active.
    assert_dispatchable(
        authorization=auth,
        revocations=stores["revocations"],
        registry=stores["registry"],
    )
    stores["registry"].revoke(
        delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID, reason="test"
    )
    with pytest.raises(AuthorizationRevoked):
        assert_dispatchable(
            authorization=auth,
            revocations=stores["revocations"],
            registry=stores["registry"],
        )


# ── 5. the routes are actually wired ─────────────────────────────────────────

def test_lab_runtime_gate_is_reached_by_the_natlas_route():
    """The N-ATLAS route must call the dispatch gate, not only check state."""
    import inspect

    import api.lab_routes as lab_routes

    source = inspect.getsource(lab_routes.n_atlas_run)
    assert "assert_session_dispatchable" in source, (
        "the N-ATLAS route executes a model call without the dispatch gate"
    )


def test_voice_execute_calls_the_weaver_guard():
    """The voice execution route must actually *call* the guard.

    A source-substring check is not enough: the module imports
    ``assert_dispatchable``, so deleting the call would still leave the name in
    the file. This asserts the call happens, by spying on it.
    """
    import inspect

    from solspire.voice_pipeline import VoicePipeline

    source = inspect.getsource(VoicePipeline.execute)
    # The call site, not the import: `assert_dispatchable(` with an argument.
    assert "assert_dispatchable(authorization=" in source, (
        "the voice execution route does not call the Weaver dispatch guard"
    )


def test_lab_gate_calls_the_shared_contract():
    import inspect

    from lab.engineering_lab.runtime import EngineeringLabRuntime

    source = inspect.getsource(EngineeringLabRuntime._require_authorization_for)
    assert "assert_delegation_dispatchable" in source, (
        "the Lab dispatch gate does not use the shared delegation contract"
    )
