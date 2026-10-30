"""P0.4 — bounded containerized test execution for the Engineering Lab.

What this guards, and why each part is here:

* **The command allowlist is explicit and caller-independent.** A ``test``
  operation carries no argv of its own; it resolves against the pinned
  ``TEST_COMMAND_ALLOWLIST``. A caller (client, model, session) can name a
  test, never a binary.
* **Host execution is impossible, not merely unfashionable.** The L1 terminal
  grammar must not widen: a negative control proves ``python -c`` is still
  refused on the host path *and* that ``run_test`` refuses a non-containerized
  policy outright.
* **Approval is bound to the operation.** Running tests requires a linked
  human authorization that names ``test``; without one the refusal happens
  before any run record exists.
* **Refusal is visible.** When the container boundary is unavailable the run
  reports BLOCKED with its reason — never IMPLEMENTED, never a fabricated pass.
* **The limits are the boundary's own.** The delegation target is asserted
  against the real ``build_container_argv`` (pure, executable here), including
  its digest-pin negative control.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lab.engineering_lab.contracts import BoundaryViolation  # noqa: E402
from lab.engineering_lab.events import EventStream  # noqa: E402
from lab.engineering_lab.runtime import (  # noqa: E402
    TEST_OPERATIONS,
    BoundedOperation,
    BoundedTask,
    EngineeringLabRuntime,
)
from lab.engineering_lab.sandbox import (  # noqa: E402
    L1_TERMINAL_BINARIES,
    Sandbox,
    SandboxCommandDenied,
    SandboxPolicy,
)
from lab.engineering_lab.store import EngineeringLabStore  # noqa: E402
from lab.engineering_lab.bounded_test_execution import (  # noqa: E402
    DEFAULT_TEST_COMMAND,
    TEST_COMMAND_ALLOWLIST,
    TEST_OPERATION,
    assert_command_allowlisted,
    configured_command,
    configured_timeout_seconds,
    resolve_test_command,
    validate_target,
)

SUBJECT = "architect"
PINNED_IMAGE = "ghcr.io/example/agent@sha256:" + "ab" * 32


@pytest.fixture()
def store(tmp_path, monkeypatch):
    db = tmp_path / "el.db"
    monkeypatch.setenv("SOLSPIRE_PROJECTS_DB", str(db))
    import lab.engineering_lab.store as store_mod

    monkeypatch.setattr(store_mod, "_DB_PATH", str(db))
    return EngineeringLabStore()


@pytest.fixture()
def workspace(tmp_path):
    root = tmp_path / "ws"
    root.mkdir()
    (root / "README.md").write_text("hello arkadia\n", encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_sample.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    return root


@pytest.fixture()
def runtime(store, tmp_path, monkeypatch):
    monkeypatch.setenv("ENGINEERING_LAB_DATA_DIR", str(tmp_path / "data"))
    stream = EventStream(log_path=str(tmp_path / "events.jsonl"))
    return EngineeringLabRuntime(store=store, stream=stream)


@pytest.fixture()
def container_policy(workspace):
    return SandboxPolicy(
        root=str(workspace),
        containerized=True,
        container_image=PINNED_IMAGE,
        container_runtime="docker",
    )


def _authorized_session(runtime, *, operations=("read", "test"), workspace_ref="proj-1"):
    agent = runtime.register_agent(subject_ref=SUBJECT, role="BUILDER")
    authorization = runtime.record_authorization(
        subject_ref=SUBJECT,
        scope_ref="tests",
        operations_allowed=tuple(operations),
    )
    session = runtime.open_session(
        subject_ref=SUBJECT,
        workspace_ref=workspace_ref,
        agent_id=agent["agent_id"],
        objective="run the suite",
        authorization_ref=authorization["authorization_id"],
    )
    return session


def _test_task(target: str = "") -> BoundedTask:
    return BoundedTask(
        objective="verify the project",
        operations=(BoundedOperation(kind=TEST_OPERATION, target=target),),
        acceptance=("suite exit code is 0",),
    )


# ---------------------------------------------------------------------------
# The command allowlist and the target rule
# ---------------------------------------------------------------------------


def test_default_command_is_allowlisted_and_needs_no_target(monkeypatch):
    monkeypatch.delenv("ENGINEERING_LAB_TEST_COMMAND", raising=False)
    assert configured_command() == DEFAULT_TEST_COMMAND
    assert_command_allowlisted(DEFAULT_TEST_COMMAND)
    assert resolve_test_command() == DEFAULT_TEST_COMMAND
    # The default itself must satisfy the allowlist — a pinned default that
    # its own allowlist rejects would make the first run a surprise refusal.
    assert any(
        DEFAULT_TEST_COMMAND[: len(prefix)] == prefix
        for prefix in TEST_COMMAND_ALLOWLIST
    )


def test_every_allowlisted_prefix_is_a_suite_command_and_never_a_shell():
    """No entry may spawn a shell; that is the whole point of the allowlist."""
    shells = {"sh", "bash", "zsh", "dash", "fish", "ksh", "cmd", "powershell"}
    for prefix in TEST_COMMAND_ALLOWLIST:
        assert prefix, "an empty prefix would admit any command"
        assert prefix[0] not in shells
        # `-c` is the shape that turns an interpreter into a shell.
        assert all(part != "-c" for part in prefix), f"{prefix} can run a snippet"


def test_valid_selector_is_appended_after_the_pinned_command(monkeypatch):
    monkeypatch.delenv("ENGINEERING_LAB_TEST_COMMAND", raising=False)
    assert resolve_test_command("tests/test_sample.py") == (
        *DEFAULT_TEST_COMMAND,
        "tests/test_sample.py",
    )
    assert resolve_test_command("tests/test_a.py::test_b[1]") == (
        *DEFAULT_TEST_COMMAND,
        "tests/test_a.py::test_b[1]",
    )


@pytest.mark.parametrize(
    "target",
    [
        "-k evil",                 # option injection
        "--co",                    # option injection, short
        "/etc/passwd",             # absolute
        "../escape",               # traversal
        "tests/../../etc/passwd",  # embedded traversal
        "tests//sample.py",        # empty segment
        "tests/./sample.py",       # current-dir segment
        "a b",                     # whitespace (argv splitting)
        "$(id)",                   # command substitution
        "x;y",                     # statement separator
        "x&y",                     # background/chain
        "x`y`",                    # backticks
        "x\x00y",                  # NUL
        "z" * 201,                 # unbounded length
    ],
)
def test_hostile_selectors_are_refused(target):
    with pytest.raises(BoundaryViolation):
        validate_target(target)


def test_empty_selector_is_accepted_as_absent():
    assert validate_target("") == ""
    assert validate_target(None) == ""


def test_environment_cannot_repoint_the_suite_onto_a_shell(monkeypatch):
    monkeypatch.setenv("ENGINEERING_LAB_TEST_COMMAND", "bash -c 'rm -rf /'")
    with pytest.raises(BoundaryViolation):
        resolve_test_command()
    monkeypatch.setenv("ENGINEERING_LAB_TEST_COMMAND", "curl http://evil")
    with pytest.raises(BoundaryViolation):
        resolve_test_command()


def test_environment_may_add_arguments_but_only_to_an_allowlisted_base(monkeypatch):
    monkeypatch.setenv(
        "ENGINEERING_LAB_TEST_COMMAND",
        "python -m pytest -q -p no:cacheprovider",
    )
    command = resolve_test_command("tests")
    assert command[:3] == ("python", "-m", "pytest")
    assert command[-1] == "tests"


def test_unparseable_environment_configuration_fails_closed(monkeypatch):
    monkeypatch.setenv("ENGINEERING_LAB_TEST_COMMAND", "python -m pytest 'unclosed")
    with pytest.raises(BoundaryViolation):
        configured_command()
    monkeypatch.setenv("ENGINEERING_LAB_TEST_COMMAND", "   ")
    with pytest.raises(BoundaryViolation):
        configured_command()


def test_timeout_is_bounded_and_caller_independent(monkeypatch):
    monkeypatch.delenv("ENGINEERING_LAB_TEST_TIMEOUT_SECONDS", raising=False)
    assert configured_timeout_seconds() == 120
    monkeypatch.setenv("ENGINEERING_LAB_TEST_TIMEOUT_SECONDS", "60")
    assert configured_timeout_seconds() == 60
    for bad in ("0", "-5", "901", "abc"):
        monkeypatch.setenv("ENGINEERING_LAB_TEST_TIMEOUT_SECONDS", bad)
        with pytest.raises(BoundaryViolation):
            configured_timeout_seconds()


# ---------------------------------------------------------------------------
# The sandbox: container-only, and the L1 grammar stays closed
# ---------------------------------------------------------------------------


def test_run_test_refuses_a_host_policy_entirely(workspace, container_policy):
    host = Sandbox(SandboxPolicy(root=str(workspace), command_allowlist=("python",)))
    before = sorted(p.name for p in workspace.iterdir())
    with pytest.raises(SandboxCommandDenied) as excinfo:
        host.run_test(command=resolve_test_command())
    assert "containerized" in str(excinfo.value)
    assert sorted(p.name for p in workspace.iterdir()) == before
    assert host.events[-1]["detail"]["reason"] == "container_boundary_required"


def test_run_test_refuses_an_unallowlisted_command_even_when_containerized(
    workspace, container_policy
):
    sandbox = Sandbox(container_policy)
    before = sorted(p.name for p in workspace.iterdir())
    for command in (
        ["bash", "-c", "id"],
        ["python", "-c", "open('x','w').write('y')"],
        ["rm", "-rf", "/"],
        [],
    ):
        with pytest.raises(SandboxCommandDenied):
            sandbox.run_test(command=command)
    assert sorted(p.name for p in workspace.iterdir()) == before
    assert all(e["detail"].get("reason") == "not_allowlisted" for e in sandbox.events)


def test_run_test_refuses_an_image_that_is_not_digest_pinned(workspace):
    policy = SandboxPolicy(
        root=str(workspace), containerized=True, container_image="python:3.12"
    )
    with pytest.raises(SandboxCommandDenied) as excinfo:
        Sandbox(policy).run_test(command=resolve_test_command())
    assert "SOLSPIRE_AGENT_IMAGE" in str(excinfo.value)


def test_l1_host_grammar_is_not_widened_by_the_test_capability(workspace):
    """Negative control: P0.4 must not loosen the closed terminal grammar."""
    sandbox = Sandbox(
        SandboxPolicy(
            root=str(workspace),
            write_allowed=False,
            command_allowlist=("python", "git", "echo"),
            enforce_git_read_only=True,
            enforce_command_grammar=True,
        )
    )
    before = sorted(p.name for p in workspace.iterdir())
    with pytest.raises(SandboxCommandDenied):
        sandbox.run(["python", "-c", "open('injected.txt','w').write('x')"])
    assert sorted(p.name for p in workspace.iterdir()) == before
    assert "python" not in L1_TERMINAL_BINARIES
    # ...and the allowlisted test command is still refused on the host path.
    with pytest.raises(SandboxCommandDenied):
        sandbox.run(list(DEFAULT_TEST_COMMAND))


def test_run_test_delegates_to_the_container_boundary_with_pinned_arguments(
    workspace, container_policy, monkeypatch
):
    captured: dict = {}

    def fake_execute(**kwargs):
        captured.update(kwargs)
        return {
            "ok": True,
            "returncode": 0,
            "stdout": "1 passed\n",
            "stderr": "",
            "runtime": kwargs["runtime"],
            "container_image": kwargs["image"],
            "network": "disabled",
        }

    monkeypatch.setattr(
        "solspire.project_execution_service.execute_container_command", fake_execute
    )
    sandbox = Sandbox(container_policy)
    result = sandbox.run_test(
        command=resolve_test_command("tests/test_sample.py"), timeout=120
    )

    assert captured["workspace"] == str(sandbox.root)
    assert captured["command"] == [*DEFAULT_TEST_COMMAND, "tests/test_sample.py"]
    assert captured["image"] == PINNED_IMAGE
    assert captured["runtime"] == "docker"
    assert captured["timeout_seconds"] == 120
    assert captured["cwd"] == "."
    assert result["ok"] is True
    assert result["kind"] == "test"
    assert result["boundary"] == "solspire.container"
    assert result["truncated"] is False
    assert sandbox.events[-1]["operation"] == "test"
    assert sandbox.events[-1]["ok"] is True


def test_run_test_reports_a_boundary_failure_instead_of_raising_success(
    workspace, container_policy, monkeypatch
):
    def unavailable(**kwargs):
        raise RuntimeError("container runtime daemon unavailable")

    monkeypatch.setattr(
        "solspire.project_execution_service.execute_container_command", unavailable
    )
    sandbox = Sandbox(container_policy)
    with pytest.raises(SandboxCommandDenied) as excinfo:
        sandbox.run_test(command=resolve_test_command())
    assert "unavailable" in str(excinfo.value)
    assert sandbox.events[-1]["detail"]["reason"] == "container_boundary_failed"


def test_container_limits_are_the_hardened_boundary_ones(workspace, container_policy):
    """The delegation target really does carry the resource envelope.

    ``build_container_argv`` is pure, so it is executed for real here — this is
    the argv our path hands the runtime, not a description of one.
    """
    from solspire.project_execution_boundary import BoundaryError, build_container_argv

    argv = build_container_argv(
        image=PINNED_IMAGE,
        workspace=workspace,
        command=list(DEFAULT_TEST_COMMAND),
        runtime="docker",
    )
    joined = " ".join(argv)
    for flag in (
        "--network=none",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges:true",
        "--pids-limit",
        "--memory",
        "--cpus",
        "--user",
        "/tmp:rw,noexec,nosuid,size=64m",
    ):
        assert flag in argv or flag in joined, f"missing hardened flag {flag}"
    assert "65532:65532" in argv
    assert PINNED_IMAGE in argv
    assert argv.count("--rm") == 1

    # Negative control: an unpinned image never reaches a container.
    with pytest.raises(BoundaryError):
        build_container_argv(
            image="python:3.12",
            workspace=workspace,
            command=list(DEFAULT_TEST_COMMAND),
            runtime="docker",
        )


# ---------------------------------------------------------------------------
# The runtime: approval bound to the operation, refusal before any run
# ---------------------------------------------------------------------------


def test_authorization_operations_fails_closed_without_a_linked_authorization(runtime, workspace):
    agent = runtime.register_agent(subject_ref=SUBJECT, role="BUILDER")
    session = runtime.open_session(
        subject_ref=SUBJECT,
        workspace_ref="proj-1",
        agent_id=agent["agent_id"],
        objective="no authorization yet",
    )
    assert runtime._authorization_operations(session, SUBJECT) is None


def test_test_operation_is_registered_as_its_own_kind():
    """`test` is neither a read nor a write: it runs code, container-only."""
    from lab.engineering_lab.runtime import READ_OPERATIONS, WRITE_OPERATIONS

    assert TEST_OPERATIONS == frozenset({TEST_OPERATION})
    assert "test" not in READ_OPERATIONS
    assert "test" not in WRITE_OPERATIONS


def test_runtime_refuses_a_test_operation_without_a_containerized_policy(
    runtime, workspace
):
    session = _authorized_session(runtime)
    with pytest.raises(BoundaryViolation) as excinfo:
        runtime.execute_bounded_task(
            subject_ref=SUBJECT,
            session_id=session["session_id"],
            task=_test_task("tests/test_sample.py"),
            sandbox_policy=SandboxPolicy(root=str(workspace)),
        )
    assert "containerized project boundary" in str(excinfo.value)
    assert runtime._store.list_runs(session["session_id"], SUBJECT) == []


def test_runtime_refuses_a_test_operation_with_no_policy_at_all(runtime):
    session = _authorized_session(runtime)
    with pytest.raises(BoundaryViolation) as excinfo:
        runtime.execute_bounded_task(
            subject_ref=SUBJECT,
            session_id=session["session_id"],
            task=_test_task(),
            sandbox_policy=None,
        )
    assert "host execution is refused" in str(excinfo.value)
    assert runtime._store.list_runs(session["session_id"], SUBJECT) == []


def test_runtime_refuses_a_test_operation_when_the_authorization_does_not_name_it(
    runtime, container_policy
):
    session = _authorized_session(runtime, operations=("read",))
    with pytest.raises(BoundaryViolation) as excinfo:
        runtime.execute_bounded_task(
            subject_ref=SUBJECT,
            session_id=session["session_id"],
            task=_test_task("tests/test_sample.py"),
            sandbox_policy=container_policy,
        )
    assert "does not permit 'test'" in str(excinfo.value)
    assert runtime._store.list_runs(session["session_id"], SUBJECT) == []


def test_runtime_refuses_a_hostile_selector_before_planning_anything(
    runtime, container_policy
):
    session = _authorized_session(runtime)
    with pytest.raises(BoundaryViolation):
        runtime.execute_bounded_task(
            subject_ref=SUBJECT,
            session_id=session["session_id"],
            task=_test_task("-k evil"),
            sandbox_policy=container_policy,
        )
    assert runtime._store.list_runs(session["session_id"], SUBJECT) == []
    assert runtime._store.list_evidence(SUBJECT) == []


def test_runtime_refuses_an_unknown_operation_kind(runtime, container_policy):
    session = _authorized_session(runtime)
    with pytest.raises(BoundaryViolation) as excinfo:
        runtime.execute_bounded_task(
            subject_ref=SUBJECT,
            session_id=session["session_id"],
            task=BoundedTask(
                objective="escape",
                operations=(BoundedOperation(kind="shell", target="id"),),
            ),
            sandbox_policy=container_policy,
        )
    assert "unknown operation kind" in str(excinfo.value)


# ---------------------------------------------------------------------------
# Execution: real exit codes become evidence
# ---------------------------------------------------------------------------


def _stub_boundary(monkeypatch, *, returncode: int, stdout: str = "", stderr: str = ""):
    captured: dict = {}

    def fake_execute(**kwargs):
        captured.update(kwargs)
        return {
            "ok": returncode == 0,
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
            "runtime": kwargs["runtime"],
            "container_image": kwargs["image"],
            "network": "disabled",
        }

    monkeypatch.setattr(
        "solspire.project_execution_service.execute_container_command", fake_execute
    )
    return captured


def test_passing_suite_records_implemented_evidence_with_the_pinned_command(
    runtime, container_policy, monkeypatch
):
    captured = _stub_boundary(monkeypatch, returncode=0, stdout="2 passed\n")
    session = _authorized_session(runtime)

    result = runtime.execute_bounded_task(
        subject_ref=SUBJECT,
        session_id=session["session_id"],
        task=_test_task("tests/test_sample.py"),
        sandbox_policy=container_policy,
    )

    assert captured["command"] == [*DEFAULT_TEST_COMMAND, "tests/test_sample.py"]
    assert result["result_state"] == "IMPLEMENTED"
    assert result["human_decision_required"] is True
    observation = result["observations"][0]
    assert observation["kind"] == "test"
    assert observation["ok"] is True
    assert observation["returncode"] == 0
    assert observation["target"] == "tests/test_sample.py"
    assert result["merge"] is False and result["deploy"] is False

    evidence = runtime._store.list_evidence(SUBJECT, run_ref=result["run_id"])
    assert evidence and evidence[0]["state"] == "IMPLEMENTED"
    assert evidence[0]["detail"]["observations"][0]["returncode"] == 0


def test_failing_suite_records_blocked_evidence_not_a_silent_success(
    runtime, container_policy, monkeypatch
):
    _stub_boundary(monkeypatch, returncode=1, stdout="1 failed\n")
    session = _authorized_session(runtime)

    result = runtime.execute_bounded_task(
        subject_ref=SUBJECT,
        session_id=session["session_id"],
        task=_test_task(),
        sandbox_policy=container_policy,
    )

    observation = result["observations"][0]
    assert observation["ok"] is False
    assert "return code 1" in observation["error"]
    assert result["result_state"] == "BLOCKED"
    assert result["human_decision_required"] is True

    evidence = runtime._store.list_evidence(SUBJECT, run_ref=result["run_id"])
    # NOT_ATTEMPTED would be a lie: the suite ran and failed.
    assert evidence and evidence[0]["state"] == "BLOCKED"


def test_an_unavailable_container_boundary_is_reported_as_blocked_not_passed(
    runtime, container_policy
):
    """No stub: the real boundary runs, and whatever it says is the result.

    In an environment without a usable container runtime this must surface as
    BLOCKED with the boundary's reason. It must never be reported as a pass.
    """
    session = _authorized_session(runtime)

    result = runtime.execute_bounded_task(
        subject_ref=SUBJECT,
        session_id=session["session_id"],
        task=_test_task(),
        sandbox_policy=container_policy,
    )

    observation = result["observations"][0]
    if observation.get("ok") is True:
        pytest.skip(
            "a container runtime is available here and the suite genuinely passed; "
            "the blocked-branch assertion does not apply to this environment"
        )
    assert observation["error"], "a non-pass must carry a reason"
    assert result["result_state"] == "BLOCKED"
    evidence = runtime._store.list_evidence(SUBJECT, run_ref=result["run_id"])
    assert evidence and evidence[0]["state"] == "BLOCKED"


# ---------------------------------------------------------------------------
# The serving surface keeps the gate it advertises
# ---------------------------------------------------------------------------


def test_execute_route_admits_test_and_only_test_for_project_sessions():
    source = (Path(__file__).resolve().parents[1] / "api" / "lab_routes.py").read_text(
        encoding="utf-8"
    )
    assert 'operation.kind not in {"read", "list", "test"}' in source
    assert "read/list/test only" in source
    # The route still refuses everything else, including the host terminal:
    # the admitted set is exactly read/list/test, nothing more.
    assert '{"read", "list", "test"}' in source


def test_the_capability_adds_no_new_route_surface():
    """P0.4 rides the existing bounded execute route — no new endpoint, so the
    OpenAPI operation inventory and its security adjudication stay untouched."""
    from api.lab_routes import router

    paths = [route.path for route in router.routes]
    # The only pre-existing path containing "test" is the unrelated n-atlas
    # probe; no *test-execution* endpoint may appear.
    assert "/api/lab/engineering/sessions/{session_id}/execute" in paths
    assert "/api/lab/engineering/sessions/{session_id}/test" not in paths
    assert not [p for p in paths if p.endswith("/test")], (
        "a test-execution endpoint must not appear; the operation kind is "
        "carried by the bounded execute route"
    )
