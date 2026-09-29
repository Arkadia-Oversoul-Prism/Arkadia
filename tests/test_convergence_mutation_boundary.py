"""Convergence tests: SolSpire cannot become a second engineering mutation authority."""

import pytest

from solspire.execution_runtime import ExecutionRuntime, Plan
from solspire.tools_fs import write_file
from solspire.tools_github import commit_file


@pytest.mark.parametrize("tool", ["fs_write", "github_commit", "git_commit", "git_push"])
def test_generic_execution_runtime_rejects_engineering_mutation(tool: str) -> None:
    runtime = ExecutionRuntime()
    plan = Plan(
        id="convergence-test",
        request="test",
        intent="engineering",
        steps=[{"tool": tool, "payload": {}}],
    )

    with pytest.raises(PermissionError, match="Weaver K15 → K3"):
        runtime.execute(plan, owner_uid="test-user")


def test_direct_filesystem_write_fails_closed() -> None:
    result = write_file("convergence-test.txt", "must not be written")

    assert result["ok"] is False
    assert result["status"] == "BLOCKED"
    assert "Weaver K15 → K3" in result["error"]


def test_direct_github_commit_fails_closed_without_network_call() -> None:
    result = commit_file(
        "Arkadia-Oversoul-Prism",
        "Arkadia",
        "convergence-test.txt",
        "must not be committed",
        "test",
    )

    assert result["ok"] is False
    assert result["status"] == "BLOCKED"
    assert "Weaver K15 → K3" in result["error"]
