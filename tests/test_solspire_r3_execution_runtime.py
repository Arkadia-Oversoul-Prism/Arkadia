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
    from solspire.execution_runtime import ExecutionRuntime

    runtime = ExecutionRuntime()
    execution = runtime.execute(_plan("fs_write"), owner_uid="r3-user")

    execution_thread_done = execution.completed_at is not None
    if not execution_thread_done:
        import time
        deadline = time.time() + 2
        while execution.completed_at is None and time.time() < deadline:
            time.sleep(0.01)

    assert execution.results[0]["ok"] is False
    assert execution.results[0]["code"] == "MUTATION_DISABLED"
    assert "K15" in execution.results[0]["error"]
    assert "K3" in execution.results[0]["error"]


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
