"""WS2 — independent security review of the execution boundary (Lane 4 / Lab).

The WS1 gate made authorization a *dispatch-point* check. This file is the
adversarial follow-up: it asks whether the gate can be walked around, and it
records the answer as a test rather than a claim.

Four questions, one section each:

A. **Atomic consumption** — can two concurrent callers both consume one grant?
B. **Revocation during execution** — is the grant re-resolved at each
   consequential dispatch, or only once when the run starts?
C. **Both execution paths** — do ``execute_bounded_task`` and
   ``execute_agent_loop`` enforce equivalently, with no bypass?
D. **Filesystem boundary** — does refusing a client-supplied ``sandbox_root``
   leave a second route to a caller-chosen root?

Findings that were *gaps* are marked as such and carry the regression test that
closes them. Findings that were already sound are recorded as measured
properties, so a future change that breaks them reddens here.
"""
from __future__ import annotations

import threading

import pytest

from lab.engineering_lab.contracts import BoundaryViolation
from lab.engineering_lab.runtime import (
    BoundedOperation,
    BoundedTask,
    EngineeringLabRuntime,
    effective_tools,
)
from lab.engineering_lab.sandbox import Sandbox, SandboxPolicy

SUBJECT = "u-ws2"


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


def _authorized_session(runtime, agent, operations):
    session = runtime.open_session(
        subject_ref=SUBJECT, workspace_ref="ws", agent_id=agent["agent_id"],
        objective="ws2 probe",
    )
    auth = runtime.record_authorization(
        subject_ref=SUBJECT, scope_ref=session["session_id"],
        operations_allowed=tuple(operations),
    )
    runtime._store.attach_authorization(
        session["session_id"], SUBJECT, auth["authorization_id"]
    )
    runtime.transition(session["session_id"], SUBJECT, "AUTHORIZED")
    return runtime.get_session(session["session_id"], SUBJECT), auth


def _write_task(target: str = "x.txt"):
    return BoundedTask(
        objective="write",
        operations=(BoundedOperation(kind="write", target=target, content="x"),),
        requires_write=True,
    )


# ── A. atomic consumption ────────────────────────────────────────────────────
# Finding: SOUND. The conditional UPDATE is guarded by
# ``json_extract(payload,'$.consumed_at') IS NULL`` inside one transaction, so
# the loser's rowcount is 0 and it returns None. Measured under real thread
# contention below rather than argued from the SQL.

def test_a_concurrent_consumption_admits_exactly_one_winner(runtime):
    """Twelve threads race one grant; exactly one may consume it.

    A read-then-write without the conditional guard would let several callers
    observe ``consumed_at`` as unset and all "win". The barrier maximises the
    overlap so the race is actually exercised.
    """
    agent = _agent(runtime)
    _, auth = _authorized_session(runtime, agent, operations=("write",))

    workers = 12
    barrier = threading.Barrier(workers)
    outcomes: list[str] = []
    lock = threading.Lock()

    def consume() -> None:
        barrier.wait()
        try:
            record = runtime._store.consume_authorization(
                auth["authorization_id"], SUBJECT
            )
            verdict = "CONSUMED" if record else "REFUSED"
        except Exception as exc:  # pragma: no cover - surfaced as a failure
            verdict = f"ERROR:{type(exc).__name__}"
        with lock:
            outcomes.append(verdict)

    threads = [threading.Thread(target=consume) for _ in range(workers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert outcomes.count("CONSUMED") == 1, (
        f"exactly one consumer may win; got {sorted(outcomes)}"
    )
    assert outcomes.count("REFUSED") == workers - 1


def test_a_consumed_grant_is_then_unusable_for_dispatch(runtime, workspace):
    """Consumption is not merely a counter: the grant stops authorizing work."""
    agent = _agent(runtime)
    session, auth = _authorized_session(runtime, agent, operations=("write",))
    assert runtime._store.consume_authorization(auth["authorization_id"], SUBJECT)

    with pytest.raises(BoundaryViolation, match="revoked, expired or already consumed"):
        runtime.execute_bounded_task(
            subject_ref=SUBJECT, session_id=session["session_id"], task=_write_task(),
            sandbox_policy=SandboxPolicy(root=str(workspace), write_allowed=True),
        )


# ── B. revocation during execution ───────────────────────────────────────────
# Finding: GAP, now closed. The pre-flight gate ran once before the run record
# existed, so a grant revoked *after* the run started still let every remaining
# operation execute. ``_recheck_authorization_for`` re-resolves the grant at
# each consequential dispatch. The test below is the regression test for it.

def test_b_revocation_mid_run_stops_the_next_protected_operation(runtime, workspace):
    """A grant revoked between two writes must refuse the second write.

    The first write is dispatched while the grant is live; the grant is then
    revoked; the second write must be refused. Before the re-check, both writes
    executed because authorization was resolved only once, at run start.
    """
    agent = _agent(runtime)
    session, auth = _authorized_session(runtime, agent, operations=("write",))

    task = BoundedTask(
        objective="two writes",
        operations=(
            BoundedOperation(kind="write", target="first.txt", content="1"),
            BoundedOperation(kind="write", target="second.txt", content="2"),
        ),
        requires_write=True,
    )

    original = runtime._run_operation
    revoked = {"done": False}

    def revoke_after_first(sandbox, op):
        result = original(sandbox, op)
        if not revoked["done"]:
            revoked["done"] = True
            runtime._store.revoke_authorization(
                auth["authorization_id"], SUBJECT, reason="mid-run revocation"
            )
        return result

    runtime._run_operation = revoke_after_first  # type: ignore[assignment]
    try:
        with pytest.raises(BoundaryViolation, match="revoked, expired or already consumed"):
            runtime.execute_bounded_task(
                subject_ref=SUBJECT, session_id=session["session_id"], task=task,
                sandbox_policy=SandboxPolicy(root=str(workspace), write_allowed=True),
            )
    finally:
        runtime._run_operation = original  # type: ignore[assignment]

    assert (workspace / "first.txt").exists(), "the first write ran while authorized"
    assert not (workspace / "second.txt").exists(), (
        "the second write must be refused once revocation is recognised"
    )


def test_b_negative_control_start_only_check_would_allow_the_second_write(
    runtime, workspace
):
    """Negative control: without the re-check, both writes execute.

    This reproduces the pre-fix shape in-process — resolve the grant once, then
    run every operation — and asserts it writes the file the guarded path
    refuses. If the re-check is ever removed, the test above stops detecting.
    """
    agent = _agent(runtime)
    session, auth = _authorized_session(runtime, agent, operations=("write",))
    sandbox = Sandbox(SandboxPolicy(root=str(workspace), write_allowed=True))

    # The old shape: one authorization resolution, then unconditional dispatch.
    assert runtime._authorization_operations(session, SUBJECT) == {"write"}
    runtime._store.revoke_authorization(auth["authorization_id"], SUBJECT, reason="old")
    runtime._run_operation(
        sandbox, BoundedOperation(kind="write", target="old-second.txt", content="2")
    )
    assert (workspace / "old-second.txt").exists(), (
        "the start-only shape must write after revocation; this is the defect"
    )


# ── C. both execution paths ──────────────────────────────────────────────────
# Finding: SOUND, with one asymmetry worth stating. ``execute_bounded_task``
# gates each consequential operation at dispatch. ``execute_agent_loop`` has no
# per-operation dispatch to gate — it is read-only by construction, and its
# enforcement is the *tool envelope*: effective_tools() intersects the grant, so
# a missing/empty/revoked grant yields no tools at all. Both paths therefore
# fail closed, by the mechanism each actually has.

def test_c_both_paths_fail_closed_without_a_grant(runtime, workspace):
    """Neither path may execute consequential work on an unlinked session."""
    agent = _agent(runtime)
    session = runtime.open_session(
        subject_ref=SUBJECT, workspace_ref="ws", agent_id=agent["agent_id"],
        objective="no grant",
    )
    runtime.transition(session["session_id"], SUBJECT, "AUTHORIZED")
    live = runtime.get_session(session["session_id"], SUBJECT)

    # Path 1: bounded task — refused at dispatch.
    with pytest.raises(BoundaryViolation, match="requires a linked human authorization"):
        runtime.execute_bounded_task(
            subject_ref=SUBJECT, session_id=live["session_id"], task=_write_task(),
            sandbox_policy=SandboxPolicy(root=str(workspace), write_allowed=True),
        )

    # Path 2: agent loop — the same resolution yields no operations, so the
    # envelope is empty. This is the loop's equivalent of a refusal.
    assert runtime._authorization_operations(live, SUBJECT) is None
    assert effective_tools(
        capabilities=("READ", "EDIT", "RUN"),
        agent_tools=("read", "list", "write", "run"),
        authorization_operations=runtime._authorization_operations(live, SUBJECT),
    ) == ()


def test_c_agent_loop_envelope_is_empty_for_a_revoked_grant(runtime):
    """A revoked grant must not leave the loop with a usable envelope."""
    agent = _agent(runtime)
    session, auth = _authorized_session(runtime, agent, operations=("read", "run"))
    runtime._store.revoke_authorization(auth["authorization_id"], SUBJECT, reason="ws2")

    live = runtime.get_session(session["session_id"], SUBJECT)
    assert runtime._authorization_operations(live, SUBJECT) is None
    assert effective_tools(
        capabilities=("READ", "EDIT", "RUN"),
        agent_tools=("read", "list", "write", "run"),
        authorization_operations=runtime._authorization_operations(live, SUBJECT),
    ) == ()


def test_c_no_second_registry_construction_can_widen_the_envelope():
    """The loop's only registry is built from the intersected envelope.

    ``ToolRegistry(sandbox, granted=None)`` means *unrestricted* — so a second
    construction site that forgot to pass ``granted`` would silently widen the
    loop. This pins the single construction site and its argument.
    """
    import inspect

    from lab.engineering_lab import runtime as runtime_mod

    source = inspect.getsource(runtime_mod)
    assert source.count("ToolRegistry(") == 1, (
        "exactly one ToolRegistry construction is expected in the runtime; a "
        "second site could omit `granted` and widen the loop"
    )
    assert "ToolRegistry(sandbox, granted=effective)" in source


# ── D. filesystem boundary ───────────────────────────────────────────────────
# Finding: SOUND. Every SandboxPolicy in the request path is server-derived:
# the project branch builds it from a disposable snapshot, and the no-project
# branch refuses a client root outright. The tests below measure the refusal and
# the confinement that backs it.

def test_d_client_supplied_sandbox_root_is_refused_over_http(monkeypatch, tmp_path):
    """The route must answer 409 for a caller-chosen root, not honour it."""
    from fastapi.testclient import TestClient

    from api.auth import require_auth
    from api.lab_routes import require_lab_auth
    from api.main import app
    from lab.engineering_lab import runtime as runtime_mod
    from lab.engineering_lab import store as store_mod
    from lab.engineering_lab.events import EventStream

    monkeypatch.setattr(store_mod, "_DB_PATH", str(tmp_path / "lab.db"))
    monkeypatch.setattr(store_mod, "_GLOBAL_STORE", None)
    runtime = EngineeringLabRuntime(
        store=store_mod.get_store(),
        stream=EventStream(log_path=str(tmp_path / "events.jsonl")),
    )
    monkeypatch.setattr(runtime_mod, "_GLOBAL_RUNTIME", runtime)

    # The Lab router authenticates twice: a router-level ``require_lab_auth``
    # and the endpoint's own ``Depends(require_auth)``. Both must be overridden
    # or the request is refused 401 before the body is ever inspected.
    app.dependency_overrides[require_lab_auth] = lambda: None
    app.dependency_overrides[require_auth] = lambda: {"uid": SUBJECT}
    try:
        client = TestClient(app)
        agent = runtime.register_agent(
            subject_ref=SUBJECT, role="BUILDER", write_allowed=True
        )
        session = runtime.open_session(
            subject_ref=SUBJECT, workspace_ref="ws", agent_id=agent["agent_id"],
            objective="root probe",
        )
        response = client.post(
            f"/api/lab/engineering/sessions/{session['session_id']}/execute",
            json={
                "objective": "escape attempt",
                "operations": [{"kind": "read", "target": "README.md"}],
                "sandbox_root": str(tmp_path / "attacker-chosen"),
            },
        )
        assert response.status_code == 409, response.text
        assert "server-managed" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(require_lab_auth, None)
        app.dependency_overrides.pop(require_auth, None)


def test_d_sandbox_confinement_refuses_traversal_and_symlink_escape(tmp_path):
    """The refusal is backed by confinement: no second route out of the root."""
    from lab.engineering_lab.sandbox import SandboxEscape

    root = tmp_path / "root"
    root.mkdir()
    (root / "inside.txt").write_text("in\n", encoding="utf-8")
    outside = tmp_path / "outside.txt"
    outside.write_text("secret\n", encoding="utf-8")
    (root / "link.txt").symlink_to(outside)

    sandbox = Sandbox(SandboxPolicy(root=str(root), write_allowed=False))

    with pytest.raises(SandboxEscape):
        sandbox.read("../outside.txt")
    with pytest.raises(SandboxEscape):
        sandbox.read("link.txt")
    # The legitimate path still works, so the guard is not trivially refusing.
    assert sandbox.read("inside.txt") == "in\n"


def test_d_no_policy_in_the_request_path_is_built_from_a_client_root():
    """A source-level guard: the route module must not pass a body field as root.

    ``_project_canvas_policy`` derives its root from a disposable snapshot and
    the no-project branch refuses a client root. This asserts the route module
    contains no ``root=body.`` construction, so a future edit cannot quietly
    reintroduce one.
    """
    import inspect

    from api import lab_routes

    source = inspect.getsource(lab_routes)
    assert "root=body." not in source, (
        "a SandboxPolicy root must never be taken from the request body"
    )
    assert "sandbox_root is server-managed" in source
