"""Gate 2e — runtime recovery assurance.

Gates 1, 2, 2b, 2c and 2d prove that *withdrawal* of authority is enforced while
a process is running. None of them answers the recovery question: what happens
when the runtime is restarted?

That matters because authority is durable state, not process memory. Three
things can go wrong across a restart and only one of them is obvious:

  1. Persisted authority is **lost** on restart, so a legitimately delegated
     agent silently cannot act. This is a availability failure, and it is the
     failure mode this file's first two tests pin: an ACTIVE delegation, its
     status and its credential epoch must be re-read from the durable store by a
     *new* runtime instance and must be unchanged.
  2. Persisted authority is **reloaded but stale**, so credentials issued before
     a revocation keep working because the process died before it could act on
     the revocation. This is the dangerous one. Restart must not launder a
     withdrawal: the old token must still fail, and the old credential epoch
     must still be superseded.
  3. Queued work **resumes** under authority that no longer exists, because the
     queue was durable and the revocation never reached it.

Every test here constructs a genuinely new runtime object bound to the same
durable stores — that is what "restart" means in-process. No test asserts on
mocked behaviour where a real store will do: the delegation registry, the
revocation ledger and the Lab store are the same SQLite files before and after
the restart, and only the consuming objects are rebuilt.

The agent is never commissioned. Each delegation is created inside a temporary
database owned by the test and torn down with it.
"""
from __future__ import annotations

import time

import pytest

import executive_office.registry as registry_module
import lab.engineering_lab.gateway as gateway_mod
import lab.engineering_lab.store as lab_store_module
import weaver.authorization_revocation as revocation_module
import weaver.enterprise_orchestration as ew
from executive_office.control import FounderDelegationControl
from executive_office.registry import DelegationRegistry
from executive_office.revocation import revoke_delegation_cascade
from lab.engineering_lab.events import EventStream
from lab.engineering_lab.gateway import ModelAdapter, ModelGateway, ModelResponse
from lab.engineering_lab.runtime import EngineeringLabRuntime
from lab.engineering_lab.sandbox import SandboxPolicy
from lab.engineering_lab.store import EngineeringLabStore

FOUNDER_UID = "founder-uid-gate2e"
WORKSPACE_ID = "ws-gate2e"
SUBJECT = "subject-gate2e"


# ── fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture()
def stores(tmp_path, monkeypatch):
    """One durable database shared by every store the guard consults.

    The paths are module-level globals in the production modules, exactly as a
    real deployment reads them from the environment. A "restart" below rebuilds
    the *objects* but deliberately leaves these paths alone, so the second
    runtime sees the first runtime's writes.
    """
    db = str(tmp_path / "gate2e.db")
    monkeypatch.setattr(registry_module, "_DB_PATH", db)
    monkeypatch.setattr(revocation_module, "_DB_PATH", db)
    monkeypatch.setattr(ew, "_DB_PATH", db)
    monkeypatch.setattr(lab_store_module, "_DB_PATH", db)
    monkeypatch.setenv("ENGINEERING_LAB_DATA_DIR", str(tmp_path / "data"))
    return {"db": db, "tmp_path": tmp_path}


@pytest.fixture()
def founder():
    return {"uid": FOUNDER_UID, "access_level": 3, "role": "Flamekeeper"}


@pytest.fixture()
def workspace(tmp_path):
    root = tmp_path / "ws"
    root.mkdir()
    (root / "README.md").write_text("# workspace\n", encoding="utf-8")
    return root


class ScriptedAdapter(ModelAdapter):
    """Deterministic stub: one tool call, then stop."""

    def __init__(self, provider: str, script: list[dict]) -> None:
        self.provider = provider
        self._script = script
        self._index = 0

    def generate(self, *, model, messages, tools=None, **options) -> ModelResponse:
        if self._index >= len(self._script):
            return ModelResponse(self.provider, model, text="done", tool_calls=[])
        step = self._script[self._index]
        self._index += 1
        return ModelResponse(
            self.provider,
            model,
            text=step.get("text", ""),
            tool_calls=step.get("tool_calls", []),
        )


READ_SCRIPT = [
    {"tool_calls": [{"name": "filesystem.read", "arguments": {"path": "README.md"}}]},
    {"text": "done", "tool_calls": []},
]


# ── helpers ─────────────────────────────────────────────────────────────────

def _grant(stores, founder, *, ttl=3600):
    return FounderDelegationControl(registry=DelegationRegistry(db_path=stores["db"])).grant(
        founder=founder,
        owner_uid=FOUNDER_UID,
        workspace_id=WORKSPACE_ID,
        capabilities=["read_project_metadata"],
        resources=["project-1"],
        expires_at=time.time() + ttl,
    )


def _registry(stores) -> DelegationRegistry:
    return DelegationRegistry(db_path=stores["db"])


def _runtime(stores) -> EngineeringLabRuntime:
    """A fresh runtime over the *durable* stores.

    This is the restart primitive. ``EngineeringLabStore()`` reads the
    monkeypatched module path, so the new object opens the same database the
    previous runtime wrote to. Nothing is carried over in memory.
    """
    stream = EventStream(log_path=str(stores["tmp_path"] / "events.jsonl"))
    return EngineeringLabRuntime(store=EngineeringLabStore(), stream=stream)


def _authorize_and_attach(runtime, *, delegation_id, delegation_epoch, operations=("read",)):
    """Open a real session and attach a real grant scoped to it.

    Mirrors the API route: the session is opened first, the authorization is
    recorded against that session id, and only then is it attached and the
    session transitioned to AUTHORIZED.
    """
    agent = runtime.register_agent(
        subject_ref=SUBJECT, role="BUILDER", display_name="gate2e-agent"
    )
    session = runtime.open_session(
        subject_ref=SUBJECT,
        agent_id=agent["agent_id"],
        workspace_ref=WORKSPACE_ID,
        objective="gate2e",
    )
    auth = runtime.record_authorization(
        subject_ref=SUBJECT,
        scope_ref=session["session_id"],
        operations_allowed=operations,
        delegation_id=delegation_id,
        delegation_epoch=delegation_epoch,
    )
    runtime._store.attach_authorization(
        session["session_id"], SUBJECT, auth["authorization_id"]
    )
    runtime.transition(session["session_id"], SUBJECT, "AUTHORIZED")
    return runtime.get_session(session["session_id"], SUBJECT), auth


def _run(runtime, session, workspace, monkeypatch, script=None):
    gateway = ModelGateway()
    gateway.register_adapter("ollama", ScriptedAdapter("ollama", script or READ_SCRIPT))
    monkeypatch.setattr(gateway_mod, "get_gateway", lambda: gateway)
    return runtime.execute_agent_loop(
        subject_ref=SUBJECT,
        session_id=session["session_id"],
        objective="read the readme",
        provider="ollama",
        model="stub-model",
        sandbox_policy=SandboxPolicy(root=str(workspace), command_allowlist=("git",)),
    )


def _executed(out) -> bool:
    """Did any tool actually run and succeed?"""
    return any(
        t["tool_name"] and (t["observation"] or {}).get("ok") for t in out["turns"]
    )


# ── 1. restart with an existing active delegation ───────────────────────────

def test_restart_with_active_delegation_still_dispatches(
    stores, founder, workspace, monkeypatch
):
    """Persisted authority is reloaded, not lost.

    A delegated agent that was legitimate before the restart must still be
    legitimate after it. If this fails, the registry has become process-local
    and every restart silently de-authorises the agent.
    """
    delegation = _grant(stores, founder)
    runtime_a = _runtime(stores)
    _authorize_and_attach(
        runtime_a,
        delegation_id=delegation.delegation_id,
        delegation_epoch=delegation.credential_epoch,
    )

    # ── restart: a brand-new runtime over the same durable stores ──
    runtime_b = _runtime(stores)
    assert runtime_b is not runtime_a
    session = runtime_b.get_session(
        _session_id_for(runtime_b), SUBJECT
    )

    out = _run(runtime_b, session, workspace, monkeypatch)
    assert out["loop_state"] == "DONE", out.get("loop_reason")
    assert _executed(out), "a delegation that survived the restart must still dispatch"


def _session_id_for(runtime) -> str:
    """The single session this test opened, read back from the durable store."""
    sessions = runtime._store.list_sessions(SUBJECT)
    assert len(sessions) == 1, f"expected one persisted session, found {len(sessions)}"
    return sessions[0]["session_id"]


# ── 2. persisted authority and credential epochs are reloaded unchanged ─────

def test_restart_reloads_persisted_status_and_credential_epoch(stores, founder):
    """The reloaded record must equal the written one, field for field.

    Status and credential epoch are the two fields the dispatch guard and the
    token validator both key on. A restart that reloaded either differently
    would either grant access the Founder withdrew, or deny access the Founder
    granted.
    """
    delegation = _grant(stores, founder)

    before = _registry(stores).get(delegation.delegation_id)
    after_restart = _registry(stores).get(delegation.delegation_id)

    assert after_restart.delegation_id == before.delegation_id
    assert after_restart.status == "ACTIVE"
    assert after_restart.credential_epoch == before.credential_epoch == 1
    assert after_restart.policy_digest == before.policy_digest
    assert after_restart.owner_uid == before.owner_uid
    assert after_restart.workspace_id == before.workspace_id

    # The append-only history is durable too: the GRANTED event survives.
    events = _registry(stores).events(delegation.delegation_id)
    assert [e["event_type"] for e in events] == ["GRANTED"]
    assert events[0]["credential_epoch"] == 1


def test_restart_after_suspension_reloads_the_bumped_epoch(stores, founder):
    """A suspend bumps the epoch; the restarted process must see the new one.

    Reloading the pre-suspension epoch would re-validate credentials the
    suspension invalidated.
    """
    delegation = _grant(stores, founder)
    _registry(stores).suspend(
        delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID, reason="test"
    )

    reloaded = _registry(stores).get(delegation.delegation_id)
    assert reloaded.status == "SUSPENDED"
    assert reloaded.credential_epoch == 2
    assert _registry(stores).active_for_principal() is None


# ── 3. restart after revocation: old credentials stay unusable ──────────────

def test_restart_after_revocation_keeps_old_credentials_unusable(
    stores, founder, workspace, monkeypatch
):
    """Restart must not launder a revocation.

    The delegation is revoked, then the process is replaced. A credential
    minted before the revocation must still be refused afterwards, and the
    guard must still refuse the pre-revocation epoch.
    """
    delegation = _grant(stores, founder)
    runtime_a = _runtime(stores)
    _authorize_and_attach(
        runtime_a,
        delegation_id=delegation.delegation_id,
        delegation_epoch=delegation.credential_epoch,
    )
    old_epoch = delegation.credential_epoch

    cascade = revoke_delegation_cascade(
        delegation_id=delegation.delegation_id,
        founder_uid=FOUNDER_UID,
        reason="gate2e restart",
        registry=_registry(stores),
    )
    assert cascade["delegation"]["status"] == "REVOKED"

    # ── restart ──
    registry = _registry(stores)
    assert registry.active_for_principal() is None, (
        "a revoked delegation must not be reported active after a restart"
    )

    reloaded = registry.get(delegation.delegation_id)
    assert reloaded.status == "REVOKED"
    assert reloaded.credential_epoch == old_epoch + 1, "revocation must bump the epoch"

    # The pre-revocation credential epoch is superseded by the durable record,
    # not by anything held in the dead process's memory.
    from weaver.authorization_revocation import AuthorizationRevoked, assert_delegation_dispatchable

    with pytest.raises(AuthorizationRevoked, match="delegation is revoked"):
        assert_delegation_dispatchable(
            delegation_id=delegation.delegation_id,
            delegation_epoch=old_epoch,
            registry=registry,
        )

    runtime_b = _runtime(stores)
    session = runtime_b.get_session(_session_id_for(runtime_b), SUBJECT)
    out = _run(runtime_b, session, workspace, monkeypatch)
    assert out["loop_state"] == "BLOCKED"
    assert not _executed(out), "a revoked delegation must not execute after a restart"
    # The full cascade also revokes the Lab grant, and the guard checks the
    # grant before the delegation, so the refusal names the grant. Both are
    # denials; the delegation-only variant below proves the delegation path on
    # its own.
    assert "revoked, expired or already consumed" in out["loop_reason"]


def test_restart_after_delegation_only_revocation_denies_on_the_delegation(
    stores, founder, workspace, monkeypatch
):
    """Revoke the delegation alone, leaving the Lab grant intact and live.

    This isolates the delegation re-read. If the guard consulted the grant
    alone, this run would succeed: the grant is unrevoked, unexpired and
    unconsumed. The refusal can therefore only come from the delegation, which
    a restarted process has to re-read from durable state.
    """
    delegation = _grant(stores, founder)
    runtime_a = _runtime(stores)
    _authorize_and_attach(
        runtime_a,
        delegation_id=delegation.delegation_id,
        delegation_epoch=delegation.credential_epoch,
    )
    session_id = _session_id_for(runtime_a)

    # Deliberately NOT the cascade: no authorization revocation is written.
    _registry(stores).revoke(
        delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID, reason="test"
    )

    runtime_b = _runtime(stores)
    session = runtime_b.get_session(session_id, SUBJECT)
    assert session["authorization_ref"], "the grant must still be attached and live"

    out = _run(runtime_b, session, workspace, monkeypatch)
    assert out["loop_state"] == "BLOCKED"
    assert not _executed(out)
    assert "delegation is revoked" in out["loop_reason"], (
        "with the grant still live, the refusal must come from the delegation"
    )


def test_restart_after_revocation_refuses_a_token_minted_before_it(stores, founder):
    """The token surface, not only the Lab guard, must refuse across a restart.

    ``verify_machine_token`` re-reads the delegation on every call, so a token
    that was valid when it was minted is refused once the durable record says
    the delegation is revoked — even though the signature still verifies and the
    token has not expired.
    """
    delegation = _grant(stores, founder)

    from executive_office.broker import ExecutiveIdentityBroker
    from executive_office.tokens import ExecutiveAuthError, verify_machine_token

    key_dir = str(stores["tmp_path"] / "keys")
    minting_broker = ExecutiveIdentityBroker(
        registry=_registry(stores), key_dir=key_dir
    )
    minted = minting_broker.issue(delegation_id=delegation.delegation_id, ttl_seconds=300)

    # Sanity: the token is genuinely usable before revocation. Verified through a
    # *separate* broker over the same key directory, so this is already the
    # restart shape.
    principal = verify_machine_token(
        minted["token"],
        broker=ExecutiveIdentityBroker(registry=_registry(stores), key_dir=key_dir),
    )
    assert principal.delegation_id == delegation.delegation_id

    revoke_delegation_cascade(
        delegation_id=delegation.delegation_id,
        founder_uid=FOUNDER_UID,
        reason="gate2e restart",
        registry=_registry(stores),
    )

    # ── restart: a new broker and a new registry over the durable state ──
    restarted = ExecutiveIdentityBroker(registry=_registry(stores), key_dir=key_dir)
    with pytest.raises(ExecutiveAuthError, match="not serviceable"):
        verify_machine_token(minted["token"], broker=restarted)


# ── 4. queued work cannot resume under revoked authority ────────────────────

def test_queued_work_cannot_resume_after_revocation(stores, founder):
    """A durable queue plus a revoked delegation must not equal resumed work.

    The queue outlives the process, so a restart alone would happily resume it.
    The revocation must have reached the queue: the job is cancelled, and the
    dispatch predicate refuses it on its own terms.
    """
    delegation = _grant(stores, founder)
    job = _registry(stores).enqueue_work(
        delegation_id=delegation.delegation_id, description="gate2e queued work"
    )
    assert _registry(stores).job_is_dispatchable(job) is True, (
        "the job must be dispatchable before the revocation, or the test proves nothing"
    )

    cascade = revoke_delegation_cascade(
        delegation_id=delegation.delegation_id,
        founder_uid=FOUNDER_UID,
        reason="gate2e queue",
        registry=_registry(stores),
    )
    assert cascade["cancelled_jobs"] == 1

    # ── restart ──
    registry = _registry(stores)
    assert registry.job_is_dispatchable(job) is False, (
        "queued work must not become dispatchable again after a restart"
    )
    rows = registry.queued_work(delegation.delegation_id)
    assert [r["status"] for r in rows] == ["CANCELLED"]
    assert rows[0]["cancel_reason"]


def test_queued_work_for_a_suspended_delegation_is_not_dispatchable(
    stores, founder, workspace, monkeypatch
):
    """Suspension withdraws service, so the queued job cannot execute.

    The job row itself is untouched by a suspension — only a revocation cancels
    it — so this asserts the *guard* is what stops it, which is the behaviour
    that must hold across a restart.
    """
    delegation = _grant(stores, founder)
    runtime = _runtime(stores)
    _authorize_and_attach(
        runtime,
        delegation_id=delegation.delegation_id,
        delegation_epoch=delegation.credential_epoch,
    )
    _registry(stores).enqueue_work(
        delegation_id=delegation.delegation_id, description="gate2e queued work"
    )
    _registry(stores).suspend(
        delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID, reason="test"
    )

    runtime_b = _runtime(stores)
    session = runtime_b.get_session(_session_id_for(runtime_b), SUBJECT)
    out = _run(runtime_b, session, workspace, monkeypatch)

    assert out["loop_state"] == "BLOCKED"
    assert not _executed(out)
    assert "delegation is suspended" in out["loop_reason"]


# ── 5. the registry being unavailable stays closed ──────────────────────────

def test_restart_with_unavailable_registry_denies_dispatch(
    stores, founder, workspace, monkeypatch
):
    """An unreadable registry must deny, not fall through to "no restriction".

    This is the recovery path that matters most: on startup a dependency may be
    down. Fail-closed means the agent cannot act, not that it acts unguarded.
    """
    delegation = _grant(stores, founder)
    runtime_a = _runtime(stores)
    _authorize_and_attach(
        runtime_a,
        delegation_id=delegation.delegation_id,
        delegation_epoch=delegation.credential_epoch,
    )
    session_id = _session_id_for(runtime_a)

    class UnavailableRegistry:
        def get(self, delegation_id):
            raise RuntimeError("registry offline")

        def active_for_principal(self, principal_id=None):
            raise RuntimeError("registry offline")

    import weaver.authorization_revocation as ar

    real = ar.assert_delegation_dispatchable

    def _unavailable(**kwargs):
        return real(
            registry=UnavailableRegistry(),
            **{k: v for k, v in kwargs.items() if k != "registry"},
        )

    monkeypatch.setattr(ar, "assert_delegation_dispatchable", _unavailable)

    runtime_b = _runtime(stores)
    session = runtime_b.get_session(session_id, SUBJECT)
    out = _run(runtime_b, session, workspace, monkeypatch)

    assert out["loop_state"] == "BLOCKED", (
        "an unreadable registry must block execution, not permit it"
    )
    assert not _executed(out)
    assert "could not be verified" in out["loop_reason"]


def test_registry_read_error_is_reported_as_no_active_delegation(stores, founder):
    """The registry's own recovery read is fail-closed by construction.

    ``active_for_principal`` swallows a store error and reports "no active
    delegation", so a caller that treats it as the startup answer denies rather
    than crashing into an unhandled state.
    """
    delegation = _grant(stores, founder)
    registry = _registry(stores)
    assert registry.active_for_principal() is not None

    class Broken(DelegationRegistry):
        def _connect(self):
            raise registry_module.sqlite3.OperationalError("disk unavailable")

    assert Broken(db_path=stores["db"]).active_for_principal() is None


def test_broker_refuses_issuance_when_the_registry_is_unavailable(stores):
    """No token can be minted across a restart while the registry is down."""
    from executive_office.broker import BrokerUnavailable, ExecutiveIdentityBroker

    class UnavailableRegistry:
        def active_for_principal(self, principal_id=None):
            raise RuntimeError("registry offline")

        def get(self, delegation_id):
            raise RuntimeError("registry offline")

    broker = ExecutiveIdentityBroker(
        registry=UnavailableRegistry(),
        key_dir=str(stores["tmp_path"] / "keys"),
    )
    with pytest.raises(BrokerUnavailable, match="unavailable"):
        broker.issue()