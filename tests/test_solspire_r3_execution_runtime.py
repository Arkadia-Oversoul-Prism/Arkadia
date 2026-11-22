"""R3 — SolSpire ExecutionRuntime boundary invariants."""
from __future__ import annotations

import pytest


def _plan(tool: str) -> object:
    from solspire.execution_runtime import Plan

    return Plan(
        id=f"r3-{tool}",
        request="R3 boundary test",
        intent="workflow",
        steps=[{"tool": tool, "payload": {}}],
    )


@pytest.mark.parametrize("tool", ["fs_write", "github_commit", "git_commit", "git_push"])
def test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools(tool):
    """Engineering mutation is refused *before* an execution starts.

    The canonical refusal is a raised ``PermissionError``, not a per-step
    ``MUTATION_DISABLED`` result envelope: ``execute()`` documents that a
    mutation tool is "blocked before a worker thread is created", and the
    production consumer ``solspire/voice_pipeline.py`` catches ``PermissionError``
    from ``execute()`` to convert it into ``EXECUTION_FAILED``. The
    ``MUTATION_DISABLED`` envelope belongs to the direct GitHub tool
    (``solspire/tools_github.commit_file``, pinned by R2), not to this runtime.

    The read-only counterpart is ``test_runtime_still_supports_read_only_workflow_steps``;
    without it a runtime that refused *every* tool would pass this test.
    """
    from solspire.execution_runtime import ExecutionRuntime

    runtime = ExecutionRuntime()
    with pytest.raises(PermissionError) as refusal:
        runtime.execute(_plan(tool), owner_uid="r3-user")

    message = str(refusal.value)
    assert tool in message
    assert "K15" in message
    assert "K3" in message
    # Pre-execution refusal: no execution record or worker thread was created.
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
