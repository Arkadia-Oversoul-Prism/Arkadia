"""Execution-boundary regression tests (Lane 4 / Engineering Lab).

Each test asserts a *refusal*. The negative controls at the bottom prove the
tests actually detect the pre-fix behaviour: they re-introduce the old shape
in-process and assert the guard fails.
"""
from __future__ import annotations

import pytest

from lab.engineering_lab.contracts import BoundaryViolation
from lab.engineering_lab.runtime import (
    BoundedOperation,
    BoundedTask,
    EngineeringLabRuntime,
    effective_tools,
)
from lab.engineering_lab.sandbox import SandboxPolicy

SUBJECT = "u-boundary"


@pytest.fixture()
def store(tmp_path, monkeypatch):
    from lab.engineering_lab.store import EngineeringLabStore
    import lab.engineering_lab.store as store_mod

    db = tmp_path / "el.db"
    monkeypatch.setenv("SOLSPIRE_PROJECTS_DB", str(db))
    monkeypatch.setattr(store_mod, "_DB_PATH", str(db))
    return EngineeringLabStore()


@pytest.fixture()
def workspace(tmp_path):
    root = tmp_path / "ws"
    root.mkdir()
    (root / "README.md").write_text("hello\n", encoding="utf-8")
    return root


@pytest.fixture()
def runtime(store, tmp_path, monkeypatch):
    from lab.engineering_lab.events import EventStream

    monkeypatch.setenv("ENGINEERING_LAB_DATA_DIR", str(tmp_path / "data"))
    return EngineeringLabRuntime(
        store=store, stream=EventStream(log_path=str(tmp_path / "events.jsonl"))
    )


def _agent(runtime, *, write_allowed=True):
    return runtime.register_agent(
        subject_ref=SUBJECT, role="BUILDER", capabilities=("READ", "EDIT", "RUN"),
        write_allowed=write_allowed,
    )


def _session(runtime, agent, *, authorization_ref=None):
    return runtime.open_session(
        subject_ref=SUBJECT, workspace_ref="ws", agent_id=agent["agent_id"],
        objective="boundary probe", authorization_ref=authorization_ref,
    )


def _authorized_session(runtime, agent, operations):
    """Record a grant, link it to the session, and move to AUTHORIZED."""
    session = _session(runtime, agent)
    auth = runtime.record_authorization(
        subject_ref=SUBJECT, scope_ref=session["session_id"],
        operations_allowed=tuple(operations),
    )
    runtime._store.attach_authorization(
        session["session_id"], SUBJECT, auth["authorization_id"]
    )
    runtime.transition(session["session_id"], SUBJECT, "AUTHORIZED")
    return runtime.get_session(session["session_id"], SUBJECT), auth


def _write_task():
    return BoundedTask(
        objective="write", operations=(BoundedOperation(kind="write", target="x.txt", content="x"),),
        requires_write=True,
    )


# ── 1. no grant at all ───────────────────────────────────────────────────────

def test_write_with_no_authorization_is_refused(runtime, workspace):
    agent = _agent(runtime)
    session = _session(runtime, agent)
    runtime.transition(session["session_id"], SUBJECT, "AUTHORIZED")
    with pytest.raises(BoundaryViolation, match="requires a linked human authorization"):
        runtime.execute_bounded_task(
            subject_ref=SUBJECT, session_id=session["session_id"], task=_write_task(),
            sandbox_policy=SandboxPolicy(root=str(workspace), write_allowed=True),
        )
    assert not (workspace / "x.txt").exists()


# ── 2. explicitly empty grant ────────────────────────────────────────────────

def test_write_with_empty_grant_is_refused(runtime, workspace):
    agent = _agent(runtime)
    session, _ = _authorized_session(runtime, agent, operations=())
    with pytest.raises(BoundaryViolation, match="does not permit 'write'"):
        runtime.execute_bounded_task(
            subject_ref=SUBJECT, session_id=session["session_id"], task=_write_task(),
            sandbox_policy=SandboxPolicy(root=str(workspace), write_allowed=True),
        )
    assert not (workspace / "x.txt").exists()


# ── 3. read-only grant cannot escalate to write ──────────────────────────────

def test_read_only_grant_cannot_escalate_to_write(runtime, workspace):
    agent = _agent(runtime)
    session, _ = _authorized_session(runtime, agent, operations=("read", "list"))
    with pytest.raises(BoundaryViolation, match="does not permit 'write'"):
        runtime.execute_bounded_task(
            subject_ref=SUBJECT, session_id=session["session_id"], task=_write_task(),
            sandbox_policy=SandboxPolicy(root=str(workspace), write_allowed=True),
        )
    assert not (workspace / "x.txt").exists()


# ── 4. run is consequential too ──────────────────────────────────────────────

def test_run_without_grant_is_refused(runtime, workspace):
    agent = _agent(runtime)
    session, _ = _authorized_session(runtime, agent, operations=("read",))
    task = BoundedTask(
        objective="run", operations=(BoundedOperation(kind="run", argv=("echo", "hi")),),
    )
    with pytest.raises(BoundaryViolation, match="does not permit 'run'"):
        runtime.execute_bounded_task(
            subject_ref=SUBJECT, session_id=session["session_id"], task=task,
            sandbox_policy=SandboxPolicy(root=str(workspace), command_allowlist=("echo",)),
        )


# ── 5. grant scoped to a different session is refused ────────────────────────

def test_grant_scoped_to_another_session_is_refused(runtime, workspace):
    agent = _agent(runtime)
    other = _session(runtime, agent)
    auth = runtime.record_authorization(
        subject_ref=SUBJECT, scope_ref=other["session_id"], operations_allowed=("write",),
    )
    session = _session(runtime, agent)
    # Force the foreign grant onto this session, bypassing attach's scope check.
    from lab.engineering_lab.store import _db

    with _db() as conn:
        conn.execute(
            "UPDATE el_sessions SET authorization_ref = ? WHERE session_id = ?",
            (auth["authorization_id"], session["session_id"]),
        )
    runtime.transition(session["session_id"], SUBJECT, "AUTHORIZED")
    with pytest.raises(BoundaryViolation, match="not scoped to this session"):
        runtime.execute_bounded_task(
            subject_ref=SUBJECT, session_id=session["session_id"], task=_write_task(),
            sandbox_policy=SandboxPolicy(root=str(workspace), write_allowed=True),
        )


# ── 6. revoked grant is refused ──────────────────────────────────────────────

def test_revoked_grant_is_refused(runtime, workspace):
    agent = _agent(runtime)
    session, auth = _authorized_session(runtime, agent, operations=("write",))
    runtime._store.revoke_authorization(auth["authorization_id"], SUBJECT, reason="test")
    with pytest.raises(BoundaryViolation, match="revoked, expired or already consumed"):
        runtime.execute_bounded_task(
            subject_ref=SUBJECT, session_id=session["session_id"], task=_write_task(),
            sandbox_policy=SandboxPolicy(root=str(workspace), write_allowed=True),
        )


# ── 7. expired grant is refused ──────────────────────────────────────────────

def test_expired_grant_is_refused(runtime, workspace):
    agent = _agent(runtime)
    session = _session(runtime, agent)
    auth = runtime.record_authorization(
        subject_ref=SUBJECT, scope_ref=session["session_id"],
        operations_allowed=("write",), duration_minutes=0,
    )
    runtime._store.attach_authorization(
        session["session_id"], SUBJECT, auth["authorization_id"]
    )
    runtime.transition(session["session_id"], SUBJECT, "AUTHORIZED")
    with pytest.raises(BoundaryViolation, match="revoked, expired or already consumed"):
        runtime.execute_bounded_task(
            subject_ref=SUBJECT, session_id=session["session_id"], task=_write_task(),
            sandbox_policy=SandboxPolicy(root=str(workspace), write_allowed=True),
        )


# ── 8. single-use consumption is atomic ──────────────────────────────────────

def test_single_use_consumption_is_atomic(runtime):
    agent = _agent(runtime)
    session, auth = _authorized_session(runtime, agent, operations=("write",))
    first = runtime._store.consume_authorization(auth["authorization_id"], SUBJECT)
    second = runtime._store.consume_authorization(auth["authorization_id"], SUBJECT)
    assert first is not None, "the first consumption must succeed"
    assert second is None, "a second consumption must be refused"


# ── 9. both execution paths agree ────────────────────────────────────────────

def test_agent_loop_yields_no_tools_without_grant(runtime):
    agent = _agent(runtime)
    session = _session(runtime, agent)
    runtime.transition(session["session_id"], SUBJECT, "AUTHORIZED")
    # The loop path resolves the same usable-grant set; with none, no tools.
    assert runtime._authorization_operations(
        runtime.get_session(session["session_id"], SUBJECT), SUBJECT
    ) is None
    assert effective_tools(
        capabilities=("READ", "EDIT", "RUN"),
        agent_tools=("read", "list", "write", "run"),
        authorization_operations=None,
    ) == ()


# ── 10. effective_tools never widens on a missing grant ──────────────────────

def test_effective_tools_missing_grant_is_empty_not_unrestricted():
    assert effective_tools(
        capabilities=("READ", "EDIT"), agent_tools=("read", "list", "write"),
        authorization_operations=None,
    ) == ()
    assert effective_tools(
        capabilities=("READ", "EDIT"), agent_tools=("read", "list", "write"),
        authorization_operations=set(),
    ) == ()


# ── NEGATIVE CONTROLS ────────────────────────────────────────────────────────
# These prove the guards above detect the pre-fix behaviour rather than
# passing vacuously.

def test_negative_control_old_effective_tools_would_widen():
    """The pre-fix shape: only intersect when the grant is not None."""
    def old_effective_tools(*, capabilities, agent_tools, authorization_operations):
        from lab.engineering_lab.runtime import _capability_operations, OPERATION_TOOLS
        allowed = _capability_operations(capabilities) & set(agent_tools)
        if authorization_operations is not None:
            allowed &= authorization_operations
        return tuple(
            t for op, tools in OPERATION_TOOLS.items() if op in allowed for t in tools
        )

    widened = old_effective_tools(
        capabilities=("READ", "EDIT"), agent_tools=("read", "list", "write"),
        authorization_operations=None,
    )
    assert widened != (), "the old shape must widen on a missing grant"
    # ...and the shipped function must not.
    assert effective_tools(
        capabilities=("READ", "EDIT"), agent_tools=("read", "list", "write"),
        authorization_operations=None,
    ) == ()


def test_negative_control_old_dispatch_would_allow_the_write(runtime, workspace):
    """The pre-fix dispatch: no per-operation authorization gate at all."""
    agent = _agent(runtime)
    session = _session(runtime, agent)
    runtime.transition(session["session_id"], SUBJECT, "AUTHORIZED")

    # Simulate the old dispatch by calling the operation runner directly,
    # which is exactly what the old loop did without a gate.
    from lab.engineering_lab.sandbox import Sandbox

    sandbox = Sandbox(SandboxPolicy(root=str(workspace), write_allowed=True))
    runtime._run_operation(sandbox, BoundedOperation(kind="write", target="old.txt", content="x"))
    assert (workspace / "old.txt").exists(), (
        "the old dispatch path must write; this is the defect the gate closes"
    )


# ── CONTAINMENT: PENDING_APPROVALS is process-local ──────────────────────────

def test_pending_approvals_is_explicitly_process_local():
    """Containment, not a fix: the tool-approval queue is in-memory.

    This test pins the limitation so it cannot be silently assumed durable.
    A restart drops every pending approval; the Lab authorization path (which
    *is* durable, in ``el_authorizations``) is the one that survives.
    """
    from api.approval_routes import PENDING_APPROVALS

    assert isinstance(PENDING_APPROVALS, dict), (
        "PENDING_APPROVALS is a process-local dict; durability is NOT provided. "
        "Do not treat a queued approval as surviving a restart."
    )
    # The durable counterpart exists and is a real table.
    from lab.engineering_lab.store import EngineeringLabStore  # noqa: F401

    assert hasattr(EngineeringLabStore, "consume_authorization")
    assert hasattr(EngineeringLabStore, "revoke_authorization")
