"""Gate 2b — the native agent loop is bound to the delegation dispatch contract.

Gate 2 proved that every *route* into delegated execution consults the
delegation. It did not cover the native agent loop's *tool boundary*:
``execute_agent_loop`` derived its tool envelope once, through
``_authorization_operations``, which checks the local grant's usability but
never re-reads the executive delegation. Authority was therefore a snapshot
taken before the run started.

That is a real gap, not a theoretical one. Reproduced before the fix: a
delegation revoked (status REVOKED, epoch 1 -> 2) *before* the loop ran still
let ``filesystem.read`` execute and return file content, because the envelope
had already been computed from a grant that was still locally usable.

The fix binds a per-call guard to ``ToolRegistry``. Every test here asserts a
*refusal*: the tool does not run, the loop ends BLOCKED, and the denial is
recorded as evidence. The agent is never commissioned — each delegation is
created by the test in a temporary database and torn down with it.
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
from lab.engineering_lab.events import EventStream
from lab.engineering_lab.gateway import ModelAdapter, ModelGateway, ModelResponse
from lab.engineering_lab.runtime import EngineeringLabRuntime, _tool_operation_kind
from lab.engineering_lab.sandbox import SandboxPolicy
from lab.engineering_lab.store import EngineeringLabStore
from lab.engineering_lab.tools import ToolDenied, ToolRegistry

FOUNDER_UID = "founder-uid-gate2b"
WORKSPACE_ID = "ws-gate2b"
SUBJECT = "subject-gate2b"


# ── fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture()
def stores(tmp_path, monkeypatch):
    db = str(tmp_path / "gate2b.db")
    monkeypatch.setattr(registry_module, "_DB_PATH", db)
    monkeypatch.setattr(revocation_module, "_DB_PATH", db)
    monkeypatch.setattr(ew, "_DB_PATH", db)
    monkeypatch.setattr(lab_store_module, "_DB_PATH", db)
    return {"db": db, "registry": DelegationRegistry(db_path=db)}


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
        return ModelResponse(self.provider, model, text=step.get("text", ""),
                             tool_calls=step.get("tool_calls", []))


READ_SCRIPT = [
    {"tool_calls": [{"name": "filesystem.read", "arguments": {"path": "README.md"}}]},
    {"text": "done", "tool_calls": []},
]


def _grant(stores, founder, *, ttl=3600):
    return FounderDelegationControl(registry=stores["registry"]).grant(
        founder=founder,
        owner_uid=FOUNDER_UID,
        workspace_id=WORKSPACE_ID,
        capabilities=["read_project_metadata"],
        resources=["project-1"],
        expires_at=time.time() + ttl,
    )


def _runtime(tmp_path, monkeypatch):
    monkeypatch.setenv("ENGINEERING_LAB_DATA_DIR", str(tmp_path / "data"))
    stream = EventStream(log_path=str(tmp_path / "events.jsonl"))
    return EngineeringLabRuntime(store=EngineeringLabStore(), stream=stream)


def _session(runtime, *, delegation_id, delegation_epoch, operations=("read",)):
    """A real Lab session bound to a real grant scoped to that session.

    The grant's ``scope_ref`` must equal the session id — the dispatch gate
    refuses a grant scoped elsewhere — so the session is opened first and the
    authorization recorded against it, exactly as the API route does.
    """
    agent = runtime.register_agent(subject_ref=SUBJECT, role="BUILDER",
                                   display_name="gate2b-agent")
    session = runtime.open_session(
        subject_ref=SUBJECT,
        agent_id=agent["agent_id"],
        workspace_ref=WORKSPACE_ID,
        objective="gate2b",
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


# ── 1. the reproduction, now refused ────────────────────────────────────────

def test_revoked_delegation_cannot_execute_through_the_agent_loop(
    tmp_path, stores, founder, workspace, monkeypatch
):
    """The exact pre-fix reproduction: revoke before the run, tool must not run.

    Before the fix this returned ``loop_state=DONE`` with the file's content in
    the observation. The envelope was computed from a grant that was still
    locally usable, and nothing re-read the delegation at the tool boundary.
    """
    delegation = _grant(stores, founder)
    runtime = _runtime(tmp_path, monkeypatch)
    session, _ = _session(runtime, delegation_id=delegation.delegation_id,
                          delegation_epoch=delegation.credential_epoch)

    stores["registry"].revoke(
        delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID, reason="test"
    )

    out = _run(runtime, session, workspace, monkeypatch)

    assert out["loop_state"] == "BLOCKED"
    assert out["result_state"] == "BLOCKED"
    assert not _executed(out), "a revoked delegation must not execute a tool"
    assert "delegation is revoked" in out["loop_reason"]
    # The denial is a recorded turn, not a silent stop.
    denied = [t for t in out["turns"] if t["decision"] == "DENIED"]
    assert denied and denied[0]["observation"]["denied"] is True


def test_suspended_delegation_cannot_execute_through_the_agent_loop(
    tmp_path, stores, founder, workspace, monkeypatch
):
    delegation = _grant(stores, founder)
    runtime = _runtime(tmp_path, monkeypatch)
    session, _ = _session(runtime, delegation_id=delegation.delegation_id,
                          delegation_epoch=delegation.credential_epoch)

    stores["registry"].suspend(
        delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID, reason="test"
    )

    out = _run(runtime, session, workspace, monkeypatch)
    assert out["loop_state"] == "BLOCKED"
    assert not _executed(out)
    assert "delegation is suspended" in out["loop_reason"]


def test_expired_delegation_cannot_execute_through_the_agent_loop(
    tmp_path, stores, founder, workspace, monkeypatch
):
    """The delegation expires while the authorization is still unexpired."""
    delegation = _grant(stores, founder, ttl=1)
    runtime = _runtime(tmp_path, monkeypatch)
    session, _ = _session(runtime, delegation_id=delegation.delegation_id,
                          delegation_epoch=delegation.credential_epoch)

    time.sleep(1.1)  # delegation expires; the grant's 60-minute window does not

    out = _run(runtime, session, workspace, monkeypatch)
    assert out["loop_state"] == "BLOCKED"
    assert not _executed(out)
    assert "delegation has expired" in out["loop_reason"]


def test_superseded_credential_epoch_cannot_execute_through_the_agent_loop(
    tmp_path, stores, founder, workspace, monkeypatch
):
    """Suspend + reactivate bumps the epoch; the old grant is dead."""
    delegation = _grant(stores, founder)
    runtime = _runtime(tmp_path, monkeypatch)
    session, _ = _session(runtime, delegation_id=delegation.delegation_id,
                          delegation_epoch=delegation.credential_epoch)

    stores["registry"].suspend(
        delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID, reason="bump"
    )
    stores["registry"].reactivate(
        delegation_id=delegation.delegation_id, founder_uid=FOUNDER_UID, reason="back"
    )
    # The delegation is ACTIVE again, but under a new epoch.
    assert stores["registry"].get(delegation.delegation_id).status == "ACTIVE"

    out = _run(runtime, session, workspace, monkeypatch)
    assert out["loop_state"] == "BLOCKED"
    assert not _executed(out)
    assert "credential epoch superseded" in out["loop_reason"]


def test_missing_delegation_record_cannot_execute_through_the_agent_loop(
    tmp_path, stores, founder, workspace, monkeypatch
):
    """An authorization naming a delegation that does not exist is not usable.

    Finding: ``DelegationRegistry.get`` raises ``ValueError("unknown
    delegation")`` for an absent row rather than returning ``None``, so this
    surfaces as "could not be verified" rather than the more specific
    "delegation record is missing". Both are denials and both are fail-closed;
    the ``delegation is None`` branch in the contract remains as a guard for a
    registry implementation that returns ``None`` instead of raising. The
    existing hardening suite pins the same wording, so this is the established
    contract, not a regression introduced here.
    """
    runtime = _runtime(tmp_path, monkeypatch)
    session, _ = _session(runtime, delegation_id="eodel-does-not-exist",
                          delegation_epoch=1)

    out = _run(runtime, session, workspace, monkeypatch)
    assert out["loop_state"] == "BLOCKED"
    assert not _executed(out)
    assert "could not be verified" in out["loop_reason"]


def test_unverifiable_registry_cannot_execute_through_the_agent_loop(
    tmp_path, stores, founder, workspace, monkeypatch
):
    """The registry becomes unavailable at the tool boundary, not at load time.

    The session and grant load fine; the failure is injected only when the
    guard re-reads the delegation, which is the moment that matters.
    """
    delegation = _grant(stores, founder)
    runtime = _runtime(tmp_path, monkeypatch)
    session, _ = _session(runtime, delegation_id=delegation.delegation_id,
                          delegation_epoch=delegation.credential_epoch)

    class BrokenRegistry:
        def get(self, delegation_id):
            raise RuntimeError("registry offline")

    import weaver.authorization_revocation as ar

    real = ar.assert_delegation_dispatchable

    def _broken(**kwargs):
        return real(registry=BrokenRegistry(),
                    **{k: v for k, v in kwargs.items() if k != "registry"})

    monkeypatch.setattr(ar, "assert_delegation_dispatchable", _broken)

    out = _run(runtime, session, workspace, monkeypatch)
    assert out["loop_state"] == "BLOCKED"
    assert not _executed(out)
    assert "could not be verified" in out["loop_reason"]


# ── 2. the boundary is per-call, not per-run ────────────────────────────────

def test_revocation_between_two_turns_stops_the_second_tool_call(
    tmp_path, stores, founder, workspace, monkeypatch
):
    """The decisive test: authority withdrawn *mid-run*.

    A start-of-run check cannot pass this. The first tool call succeeds; the
    delegation is then revoked; the second tool call must be refused. This is
    what "at the actual tool execution boundary" means.
    """
    delegation = _grant(stores, founder)
    runtime = _runtime(tmp_path, monkeypatch)
    session, _ = _session(runtime, delegation_id=delegation.delegation_id,
                          delegation_epoch=delegation.credential_epoch)

    registry = stores["registry"]
    calls: list[str] = []

    class RevokingAdapter(ModelAdapter):
        """Revokes the delegation after the first tool call is observed."""

        provider = "ollama"

        def __init__(self):
            self._index = 0

        def generate(self, *, model, messages, tools=None, **options):
            self._index += 1
            if self._index == 1:
                return ModelResponse("ollama", model, text="first",
                                     tool_calls=[{"name": "filesystem.read",
                                                  "arguments": {"path": "README.md"}}])
            if self._index == 2:
                # The first call has completed; withdraw authority now.
                registry.revoke(delegation_id=delegation.delegation_id,
                                founder_uid=FOUNDER_UID, reason="mid-run")
                return ModelResponse("ollama", model, text="second",
                                     tool_calls=[{"name": "filesystem.read",
                                                  "arguments": {"path": "README.md"}}])
            return ModelResponse("ollama", model, text="done", tool_calls=[])

    gateway = ModelGateway()
    gateway.register_adapter("ollama", RevokingAdapter())
    monkeypatch.setattr(gateway_mod, "get_gateway", lambda: gateway)

    out = runtime.execute_agent_loop(
        subject_ref=SUBJECT,
        session_id=session["session_id"],
        objective="read twice",
        provider="ollama",
        model="stub-model",
        sandbox_policy=SandboxPolicy(root=str(workspace), command_allowlist=("git",)),
    )

    tool_turns = [t for t in out["turns"] if t["tool_name"]]
    assert len(tool_turns) == 2, "both attempts must be recorded"
    assert tool_turns[0]["observation"]["ok"] is True, "the first call was authorized"
    assert tool_turns[1]["decision"] == "DENIED", "the second call must be refused"
    assert tool_turns[1]["observation"]["ok"] is False
    assert out["loop_state"] == "BLOCKED"
    assert "delegation is revoked" in out["loop_reason"]


def test_denial_is_not_offered_back_to_the_model_as_a_retry(
    tmp_path, stores, founder, workspace, monkeypatch
):
    """A denial ends the run; it is not a tool error the model may route around.

    If the denial were fed back as an ordinary observation, the model could try
    a different tool and keep going. Withdrawn authority must terminate.
    """
    delegation = _grant(stores, founder)
    runtime = _runtime(tmp_path, monkeypatch)
    session, _ = _session(runtime, delegation_id=delegation.delegation_id,
                          delegation_epoch=delegation.credential_epoch)
    stores["registry"].revoke(delegation_id=delegation.delegation_id,
                              founder_uid=FOUNDER_UID, reason="test")

    # A script that would keep trying other tools if it were allowed to.
    script = [
        {"tool_calls": [{"name": "filesystem.read", "arguments": {"path": "README.md"}}]},
        {"tool_calls": [{"name": "filesystem.list", "arguments": {"path": "."}}]},
        {"tool_calls": [{"name": "git.status", "arguments": {}}]},
        {"text": "done", "tool_calls": []},
    ]
    out = _run(runtime, session, workspace, monkeypatch, script=script)

    assert out["loop_state"] == "BLOCKED"
    assert len(out["turns"]) == 1, "the run must stop at the first denial"
    assert not _executed(out)


def test_grant_revoked_mid_run_stops_the_next_tool_call(
    tmp_path, stores, founder, workspace, monkeypatch
):
    """The grant itself, not only the delegation, is re-read per call.

    Mutation testing found this uncovered: removing the grant-usability check
    from the guard reddened nothing, because every other test withdraws the
    *delegation*. A grant revoked mid-run must stop the run for the same reason
    — the envelope was derived from a grant that no longer exists.
    """
    delegation = _grant(stores, founder)
    runtime = _runtime(tmp_path, monkeypatch)
    session, auth = _session(runtime, delegation_id=delegation.delegation_id,
                             delegation_epoch=delegation.credential_epoch)

    class RevokingGrantAdapter(ModelAdapter):
        provider = "ollama"

        def __init__(self):
            self._index = 0

        def generate(self, *, model, messages, tools=None, **options):
            self._index += 1
            if self._index == 1:
                return ModelResponse("ollama", model, text="first",
                                     tool_calls=[{"name": "filesystem.read",
                                                  "arguments": {"path": "README.md"}}])
            if self._index == 2:
                runtime._store.revoke_authorization(
                    auth["authorization_id"], SUBJECT, reason="mid-run"
                )
                return ModelResponse("ollama", model, text="second",
                                     tool_calls=[{"name": "filesystem.read",
                                                  "arguments": {"path": "README.md"}}])
            return ModelResponse("ollama", model, text="done", tool_calls=[])

    gateway = ModelGateway()
    gateway.register_adapter("ollama", RevokingGrantAdapter())
    monkeypatch.setattr(gateway_mod, "get_gateway", lambda: gateway)

    out = runtime.execute_agent_loop(
        subject_ref=SUBJECT,
        session_id=session["session_id"],
        objective="read twice",
        provider="ollama",
        model="stub-model",
        sandbox_policy=SandboxPolicy(root=str(workspace), command_allowlist=("git",)),
    )

    tool_turns = [t for t in out["turns"] if t["tool_name"]]
    assert len(tool_turns) == 2
    assert tool_turns[0]["observation"]["ok"] is True
    assert tool_turns[1]["decision"] == "DENIED"
    assert out["loop_state"] == "BLOCKED"
    assert "revoked, expired or already consumed" in out["loop_reason"]


# ── 3. the guard is total and the ordinary path still works ────────────────

def test_every_registered_tool_maps_to_an_authorized_operation():
    """No tool can be invoked that the guard has no opinion about."""
    from lab.engineering_lab.tools import _specs

    for name in _specs():
        assert _tool_operation_kind(name) is not None, (
            f"tool '{name}' has no operation mapping, so the per-call guard "
            "would silently skip it"
        )


def test_plain_human_grant_still_executes_through_the_agent_loop(
    tmp_path, stores, workspace, monkeypatch
):
    """Gate 2b must not break the ordinary human-authorized Lab path."""
    runtime = _runtime(tmp_path, monkeypatch)
    session, _ = _session(runtime, delegation_id=None, delegation_epoch=None)

    out = _run(runtime, session, workspace, monkeypatch)
    assert out["loop_state"] == "DONE"
    assert _executed(out)


def test_active_delegation_still_executes_through_the_agent_loop(
    tmp_path, stores, founder, workspace, monkeypatch
):
    """A live delegation must not be refused — the guard is not a blanket deny."""
    delegation = _grant(stores, founder)
    runtime = _runtime(tmp_path, monkeypatch)
    session, _ = _session(runtime, delegation_id=delegation.delegation_id,
                          delegation_epoch=delegation.credential_epoch)

    out = _run(runtime, session, workspace, monkeypatch)
    assert out["loop_state"] == "DONE"
    assert _executed(out)


def test_denial_is_recorded_as_evidence(tmp_path, stores, founder, workspace, monkeypatch):
    """The refusal must be legible in the evidence trail, not only in the return."""
    delegation = _grant(stores, founder)
    runtime = _runtime(tmp_path, monkeypatch)
    session, _ = _session(runtime, delegation_id=delegation.delegation_id,
                          delegation_epoch=delegation.credential_epoch)
    stores["registry"].revoke(delegation_id=delegation.delegation_id,
                              founder_uid=FOUNDER_UID, reason="test")

    out = _run(runtime, session, workspace, monkeypatch)
    evidence = runtime._store.list_evidence(SUBJECT, run_ref=out["run_id"])
    assert evidence and evidence[0]["state"] == "BLOCKED"
    assert "delegation is revoked" in evidence[0]["summary"]

    events = runtime._store.list_events(session["session_id"], SUBJECT)
    assert any(e["event_type"] == "TOOL_DENIED" for e in events), (
        "the denial must appear on the live event stream"
    )


# ── 4. the registry-level guard itself ─────────────────────────────────────

def test_tool_registry_denies_when_the_guard_raises(workspace):
    """A guard that raises denies; the sandbox is never touched."""
    from lab.engineering_lab.sandbox import Sandbox

    sandbox = Sandbox(SandboxPolicy(root=str(workspace), command_allowlist=("git",)))

    def _guard(name):
        raise ToolDenied(f"refused {name}", tool_name=name)

    registry = ToolRegistry(sandbox, granted=("filesystem.read",), dispatch_guard=_guard)
    with pytest.raises(ToolDenied):
        registry.invoke("filesystem.read", {"path": "README.md"})


def test_tool_registry_denies_when_the_guard_itself_fails(workspace):
    """A guard that crashes also denies — unverifiable is not permission."""
    from lab.engineering_lab.sandbox import Sandbox

    sandbox = Sandbox(SandboxPolicy(root=str(workspace), command_allowlist=("git",)))

    def _guard(name):
        raise RuntimeError("guard exploded")

    registry = ToolRegistry(sandbox, granted=("filesystem.read",), dispatch_guard=_guard)
    with pytest.raises(ToolDenied, match="guard exploded"):
        registry.invoke("filesystem.read", {"path": "README.md"})


def test_tool_registry_without_a_guard_is_unchanged(workspace):
    """The guard is additive: a registry built without one behaves as before."""
    from lab.engineering_lab.sandbox import Sandbox

    sandbox = Sandbox(SandboxPolicy(root=str(workspace), command_allowlist=("git",)))
    registry = ToolRegistry(sandbox, granted=("filesystem.read",))
    out = registry.invoke("filesystem.read", {"path": "README.md"})
    assert out["ok"] is True
