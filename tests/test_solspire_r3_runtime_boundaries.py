"""R3 — SolSpire ExecutionRuntime boundary invariants."""
from __future__ import annotations

import time


def test_unknown_runtime_tool_fails_closed_instead_of_falling_through_to_llm():
    from solspire.execution_runtime import ExecutionRuntime, Plan

    runtime = ExecutionRuntime()
    execution = runtime.execute(
        Plan(
            id="r3-unknown-tool",
            request="test",
            intent="boundary",
            steps=[{"tool": "github_commit", "payload": {}}],
        )
    )

    deadline = time.time() + 2
    while execution.status.value == "running" and time.time() < deadline:
        time.sleep(0.01)

    assert execution.status.value == "failed"
    assert execution.results[0]["status"] == "NOT_AVAILABLE"
    assert execution.results[0]["mutation_path"] == "NONE"
    assert "Unknown execution tool" in execution.results[0]["error"]


def test_runtime_still_supports_explicit_llm_tool(monkeypatch):
    from solspire.execution_runtime import ExecutionRuntime, Plan
    import solspire.provider_manager as provider_manager

    class FakeManager:
        def invoke_model(self, prompt, context):
            return "fixture-result"

    monkeypatch.setattr(provider_manager, "get_manager", lambda: FakeManager())

    runtime = ExecutionRuntime()
    execution = runtime.execute(
        Plan(
            id="r3-llm",
            request="test",
            intent="boundary",
            steps=[{"tool": "llm", "payload": {"prompt": "fixture"}}],
        )
    )

    deadline = time.time() + 2
    while execution.status.value == "running" and time.time() < deadline:
        time.sleep(0.01)

    assert execution.status.value == "completed"
    assert execution.results[0]["result"] == "fixture-result"


def test_runtime_contains_no_direct_weaver_transaction_import():
    from pathlib import Path

    source = Path("solspire/execution_runtime.py").read_text(encoding="utf-8")
    assert "run_transaction" not in source
    assert "execute_patch" not in source
    assert "subprocess" not in source
