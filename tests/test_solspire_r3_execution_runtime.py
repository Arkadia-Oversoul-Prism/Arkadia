"""R3 — SolSpire ExecutionRuntime boundary invariants."""
from __future__ import annotations


def _plan(tool: str) -> object:
    from solspire.execution_runtime import Plan

    return Plan(
        id=f"r3-{tool}",
        request="R3 boundary test",
        intent="workflow",
        steps=[{"tool": tool, "payload": {}}],
    )


def test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools():
    """The runtime must refuse engineering mutation and name the Weaver path.

    Pre-repair expectation, retained verbatim so the drift stays reconstructable:
    this node previously called `runtime.execute(_plan("fs_write"), ...)` and
    asserted `execution.results[0]["code"] == "MUTATION_DISABLED"` — the per-step
    result-dict refusal. The runtime was later converged to reject the plan
    *before* a worker thread exists, so the per-step branch is unreachable for
    engineering tools and no `Execution` is ever returned. The boundary is
    unchanged; only the shape of the refusal drifted.
    """
    import pytest

    from solspire.execution_runtime import ExecutionRuntime, _ENGINEERING_MUTATION_TOOLS

    # Guard against a vacuous pass: an emptied tool set would satisfy the loop.
    assert {"fs_write", "github_commit"} <= _ENGINEERING_MUTATION_TOOLS

    runtime = ExecutionRuntime()
    for tool in sorted(_ENGINEERING_MUTATION_TOOLS):
        with pytest.raises(PermissionError) as excinfo:
            runtime.execute(_plan(tool), owner_uid="r3-user")

        message = str(excinfo.value)
        assert "K15" in message
        assert "K3" in message
        assert tool in message

    # Refusal must precede execution: no plan carrying a mutation tool may be
    # recorded as a started run.
    assert runtime._executions == {}


def test_runtime_still_supports_read_only_workflow_steps():
    from solspire.execution_runtime import ExecutionRuntime

    runtime = ExecutionRuntime()
    execution = runtime.execute(_plan("fs_list"), owner_uid="r3-user")

    import time
    deadline = time.time() + 2
    while execution.completed_at is None and time.time() < deadline:
        time.sleep(0.01)

    assert execution.status.value in {"completed", "failed"}
    assert execution.results
    assert execution.results[0]["tool"] == "fs_list"


def test_project_creation_preserves_authenticated_owner_context(monkeypatch):
    from solspire.execution_runtime import ExecutionRuntime

    class Project:
        def to_dict(self):
            return {"owner_uid": "r3-user"}

    class Manager:
        def __init__(self):
            self.owner_uid = None

        def create(self, name, metadata=None, owner_uid=None):
            self.owner_uid = owner_uid
            return Project()

    manager = Manager()
    monkeypatch.setattr("solspire.project_manager.get_project_manager", lambda: manager)

    runtime = ExecutionRuntime()
    execution = runtime.execute(_plan("project_create"), owner_uid="r3-user")

    import time
    deadline = time.time() + 2
    while execution.completed_at is None and time.time() < deadline:
        time.sleep(0.01)

    assert manager.owner_uid == "r3-user"
    assert execution.results[0]["ok"] is True
