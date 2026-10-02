"""GATE L1 — native agent runtime verification.

These exercise the real loop, real sandbox, real store, and real event stream.
Only *inference* is stubbed: the model is the external dependency, and the
directive makes the deterministic stub the CI acceptance path. The stub plays a
known four-turn sequence so termination is deterministic.

The hard invariant under test: the agent loop reasons and observes, but never
mutates the repository, and never crosses into the K15/K3 governed boundary.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lab.engineering_lab import gateway as gateway_mod  # noqa: E402
from lab.engineering_lab.agent_loop import TERMINAL_STATES, AgentLoop  # noqa: E402
from lab.engineering_lab.events import EventStream  # noqa: E402
from lab.engineering_lab.gateway import ModelAdapter, ModelGateway, ModelResponse  # noqa: E402
from lab.engineering_lab.runtime import EngineeringLabRuntime  # noqa: E402
from lab.engineering_lab.sandbox import Sandbox, SandboxPolicy  # noqa: E402
from lab.engineering_lab.store import EngineeringLabStore  # noqa: E402
from lab.engineering_lab.tools import ToolRegistry  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent


class ScriptedAdapter(ModelAdapter):
    """Deterministic stub: plays a fixed sequence of tool calls, then stops."""

    def __init__(self, provider: str, script: list[dict]) -> None:
        self.provider = provider
        self._script = script
        self._index = 0
        self.calls: list[list[dict]] = []

    def generate(self, *, model, messages, tools=None, **options) -> ModelResponse:
        self.calls.append(messages)
        if self._index >= len(self._script):
            return ModelResponse(self.provider, model, text="done", tool_calls=[])
        step = self._script[self._index]
        self._index += 1
        return ModelResponse(
            self.provider, model,
            text=step.get("text", ""),
            tool_calls=step.get("tool_calls", []),
        )


#: The directive's known sequence: list -> read -> run -> DONE.
KNOWN_SEQUENCE = [
    {"tool_calls": [{"name": "filesystem.list", "arguments": {"path": "."}}]},
    {"tool_calls": [{"name": "filesystem.read", "arguments": {"path": "README.md"}}]},
    {"tool_calls": [{"name": "terminal.run", "arguments": {"argv": ["git", "status", "--short"]}}]},
    {"text": "inspection complete", "tool_calls": []},
]


@pytest.fixture()
def store(tmp_path, monkeypatch):
    db = tmp_path / "el.db"
    import lab.engineering_lab.store as store_mod

    monkeypatch.setattr(store_mod, "_DB_PATH", str(db))
    return EngineeringLabStore()


@pytest.fixture()
def workspace(tmp_path):
    root = tmp_path / "ws"
    root.mkdir()
    (root / "README.md").write_text("# workspace\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "."],
                   cwd=root, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init"],
                   cwd=root, check=True)
    return root


@pytest.fixture()
def gateway():
    return ModelGateway()


@pytest.fixture()
def registry(workspace):
    sandbox = Sandbox(SandboxPolicy(root=str(workspace), command_allowlist=("git",)))
    return ToolRegistry(sandbox)


def _run_loop(gateway, registry, script, provider="ollama", max_turns=8, events=None):
    gateway.register_adapter(provider, ScriptedAdapter(provider, script))
    loop = AgentLoop(gateway=gateway, tools=registry, provider=provider,
                     model="stub-model", max_turns=max_turns)
    captured: list[tuple[str, dict]] = []

    def on_event(event_type, payload):
        captured.append((event_type, payload))
    result = loop.run(objective="inspect the workspace", on_event=on_event)
    if events is not None:
        events.extend(captured)
    return result


# -- the loop itself ---------------------------------------------------------


def test_loop_performs_multi_turn_tool_sequence(gateway, registry):
    result = _run_loop(gateway, registry, KNOWN_SEQUENCE)
    assert result.state == "DONE"
    tools_used = [t.tool_name for t in result.turns if t.tool_name]
    assert tools_used == ["filesystem.list", "filesystem.read", "terminal.run"]
    assert all(t.observation is not None for t in result.turns if t.tool_name)


def test_every_tool_call_produces_an_agent_event(gateway, registry):
    events: list[tuple[str, dict]] = []
    _run_loop(gateway, registry, KNOWN_SEQUENCE, events=events)
    kinds = [e[0] for e in events]
    assert kinds.count("MODEL_TURN") == 4
    assert kinds.count("TOOL_INTENT") == 3
    assert kinds.count("TOOL_OBSERVATION") == 3
    assert "AGENT_DECISION" in kinds
    assert kinds[-1] == "AGENT_DECISION"


def test_loop_termination_is_deterministic(gateway, registry):
    first = _run_loop(gateway, registry, KNOWN_SEQUENCE)
    second = _run_loop(gateway, registry, KNOWN_SEQUENCE)
    assert first.state == second.state == "DONE"
    assert [t.tool_name for t in first.turns] == [t.tool_name for t in second.turns]


def test_loop_terminates_allowed_states_only(gateway, registry):
    assert set(TERMINAL_STATES) == {
        "DONE", "BLOCKED", "ERROR", "HUMAN_AUTHORIZATION_REQUIRED"
    }


def test_loop_blocked_when_no_adapter_bound(registry):
    gateway = ModelGateway()  # no adapter registered
    loop = AgentLoop(gateway=gateway, tools=registry, provider="ollama", model="m")
    result = loop.run(objective="x")
    assert result.state == "BLOCKED"
    assert "no inference adapter" in result.reason


def test_loop_stops_at_human_authorization_on_turn_budget(gateway, registry):
    # A model that always requests a tool never terminates on its own.
    always = [{"tool_calls": [{"name": "filesystem.list", "arguments": {}}]}] * 3
    result = _run_loop(gateway, registry, always, max_turns=3)
    assert result.state == "HUMAN_AUTHORIZATION_REQUIRED"


def test_provider_swap_does_not_change_the_loop(registry):
    g1 = ModelGateway()
    r1 = _run_loop(g1, registry, KNOWN_SEQUENCE, provider="ollama")
    g2 = ModelGateway()
    r2 = _run_loop(g2, registry, KNOWN_SEQUENCE, provider="openai_compatible_local")
    assert r1.state == r2.state == "DONE"
    assert [t.tool_name for t in r1.turns] == [t.tool_name for t in r2.turns]


# -- the tool layer ----------------------------------------------------------


def test_tool_registry_exposes_no_mutating_tool(registry):
    specs = registry.available()
    assert specs, "expected read-only tools to be available"
    assert all(spec["mutating"] is False for spec in specs)
    names = " ".join(spec["name"] for spec in specs)
    for forbidden in ("write", "commit", "push", "merge", "create_pr"):
        assert forbidden not in names


def test_tool_registry_denies_ungranted_tool(registry):
    restricted = ToolRegistry(registry._sandbox, granted=("filesystem.list",))
    out = restricted.invoke("filesystem.read", {"path": "README.md"})
    assert out["ok"] is False
    assert "not granted" in out["error"]


def test_tool_failure_returns_observation_not_exception(registry):
    out = registry.invoke("filesystem.read", {"path": "does-not-exist.txt"})
    assert out["ok"] is False
    assert "error" in out


# -- runtime integration -----------------------------------------------------


def _runtime_fixture(tmp_path, store, monkeypatch, workspace):
    monkeypatch.setenv("ENGINEERING_LAB_DATA_DIR", str(tmp_path / "data"))
    stream = EventStream(log_path=str(tmp_path / "events.jsonl"))
    return EngineeringLabRuntime(store=store, stream=stream), stream


def test_runtime_agent_loop_records_evidence_and_review_boundary(
    tmp_path, store, monkeypatch, workspace, gateway
):
    runtime, _ = _runtime_fixture(tmp_path, store, monkeypatch, workspace)
    gateway.register_adapter("ollama", ScriptedAdapter("ollama", KNOWN_SEQUENCE))
    monkeypatch.setattr(gateway_mod, "get_gateway", lambda: gateway)

    agent = runtime.register_agent(subject_ref="architect", role="BUILDER",
                                   display_name="Builder")
    authorization = runtime.record_authorization(
        subject_ref="architect", scope_ref="inspect-workspace",
        operations_allowed=("list", "read", "run", "git_status"),
    )
    session = runtime.open_session(
        subject_ref="architect", agent_id=agent["agent_id"],
        workspace_ref="arkadia", objective="inspect workspace",
        authorization_ref=authorization["authorization_id"],
    )
    assert session["state"] == "AUTHORIZED"

    out = runtime.execute_agent_loop(
        subject_ref="architect", session_id=session["session_id"],
        objective="inspect the workspace", provider="ollama", model="stub-model",
        sandbox_policy=SandboxPolicy(root=str(workspace), command_allowlist=("git",)),
    )

    assert out["loop_state"] == "DONE"
    assert out["evidence_refs"], "evidence must reference the run"
    assert out["human_decision_required"] is True
    assert out["merge"] is False and out["deploy"] is False
    assert out["self_authorized"] is False
    # BUILDER (READ+OBSERVE+RUN) ∩ authorization(list,read,run,git_status) ⇒ these
    assert set(out["turns"][0].keys())  # shape sanity
    tools_used = [t["tool_name"] for t in out["turns"] if t["tool_name"]]
    assert "terminal.run" in tools_used

    evidence = store.list_evidence("architect", run_ref=out["run_id"])
    assert len(evidence) == 1
    assert evidence[0]["run_ref"] == out["run_id"]
    # BUILDER has no OBSERVE capability, so git.* is excluded even though the
    # authorization lists git_status: capability ceiling ∩ authorization.
    assert set(evidence[0]["provenance"]["effective_tools"]) == {
        "filesystem.list", "filesystem.read", "terminal.run",
    }
    assert evidence[0]["provenance"]["mutating_tools"] == []

    session_after = runtime.get_session(session["session_id"], "architect")
    assert session_after["state"] == "READY_FOR_REVIEW"


def test_weaver_ceiling_excludes_terminal_run(
    tmp_path, store, monkeypatch, workspace, gateway
):
    """Capability bound: WEAVER has no RUN, so terminal.run is not granted."""
    runtime, _ = _runtime_fixture(tmp_path, store, monkeypatch, workspace)
    gateway.register_adapter("ollama", ScriptedAdapter("ollama", KNOWN_SEQUENCE))
    monkeypatch.setattr(gateway_mod, "get_gateway", lambda: gateway)

    agent = runtime.register_agent(subject_ref="architect", role="WEAVER")
    authorization = runtime.record_authorization(
        subject_ref="architect", scope_ref="inspect",
        operations_allowed=("list", "read", "run", "git_status"),
    )
    session = runtime.open_session(subject_ref="architect", agent_id=agent["agent_id"],
                                   workspace_ref="arkadia", objective="inspect",
                                   authorization_ref=authorization["authorization_id"])
    out = runtime.execute_agent_loop(
        subject_ref="architect", session_id=session["session_id"],
        objective="inspect the workspace", provider="ollama", model="stub-model",
        sandbox_policy=SandboxPolicy(root=str(workspace), command_allowlist=("git",)),
    )
    evidence = store.list_evidence("architect", run_ref=out["run_id"])[0]
    effective = set(evidence["provenance"]["effective_tools"])
    assert "terminal.run" not in effective
    # WEAVER has OBSERVE, so the read-only git tools are granted.
    assert {"git.status", "git.diff"} <= effective
    # The stub still asks for terminal.run; it must be refused, not executed.
    terminal_turns = [t for t in out["turns"] if t["tool_name"] == "terminal.run"]
    assert terminal_turns and terminal_turns[0]["observation"]["ok"] is False


def test_authorization_narrows_capability(
    tmp_path, store, monkeypatch, workspace, gateway
):
    """A BUILDER authorized only to read must not receive terminal.run."""
    runtime, _ = _runtime_fixture(tmp_path, store, monkeypatch, workspace)
    gateway.register_adapter("ollama", ScriptedAdapter("ollama", KNOWN_SEQUENCE))
    monkeypatch.setattr(gateway_mod, "get_gateway", lambda: gateway)

    agent = runtime.register_agent(subject_ref="architect", role="BUILDER")
    authorization = runtime.record_authorization(
        subject_ref="architect", scope_ref="read-only",
        operations_allowed=("list", "read"),  # no run
    )
    session = runtime.open_session(subject_ref="architect", agent_id=agent["agent_id"],
                                   workspace_ref="arkadia", objective="inspect",
                                   authorization_ref=authorization["authorization_id"])
    out = runtime.execute_agent_loop(
        subject_ref="architect", session_id=session["session_id"],
        objective="inspect the workspace", provider="ollama", model="stub-model",
        sandbox_policy=SandboxPolicy(root=str(workspace), command_allowlist=("git",)),
    )
    evidence = store.list_evidence("architect", run_ref=out["run_id"])[0]
    effective = set(evidence["provenance"]["effective_tools"])
    assert "terminal.run" not in effective
    assert effective == {"filesystem.list", "filesystem.read"}


def test_agent_loop_does_not_mutate_repository(
    tmp_path, store, monkeypatch, workspace, gateway
):
    before = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT,
                            capture_output=True, text=True).stdout
    runtime, _ = _runtime_fixture(tmp_path, store, monkeypatch, workspace)
    gateway.register_adapter("ollama", ScriptedAdapter("ollama", KNOWN_SEQUENCE))
    monkeypatch.setattr(gateway_mod, "get_gateway", lambda: gateway)

    agent = runtime.register_agent(subject_ref="architect", role="BUILDER")
    authorization = runtime.record_authorization(
        subject_ref="architect", scope_ref="inspect",
        operations_allowed=("list", "read", "run", "git_status"),
    )
    session = runtime.open_session(subject_ref="architect",
                                   agent_id=agent["agent_id"],
                                   workspace_ref="arkadia", objective="inspect",
                                   authorization_ref=authorization["authorization_id"])
    runtime.execute_agent_loop(
        subject_ref="architect", session_id=session["session_id"],
        objective="inspect the workspace", provider="ollama", model="stub-model",
        sandbox_policy=SandboxPolicy(root=str(workspace), command_allowlist=("git",)),
    )
    after = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT,
                           capture_output=True, text=True).stdout
    assert before == after, "the agent loop must not mutate the repository"


def test_agent_loop_has_no_k15_k3_or_ew_coupling():
    """The L1 loop must not reach into the governed mutation boundary.

    Checked against code identifiers, not docstrings: the modules legitimately
    *document* the boundary they must not cross.
    """
    import ast

    forbidden = {"enterprise_orchestration", "transaction", "execute_patch",
                 "run_transaction", "PassSpec", "K15", "K3"}
    for module in ("agent_loop.py", "tools.py"):
        source = (REPO_ROOT / "lab" / "engineering_lab" / module).read_text(encoding="utf-8")
        tree = ast.parse(source)
        used: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used.add(node.id)
            elif isinstance(node, ast.Attribute):
                used.add(node.attr)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    used.add(alias.name.split(".")[-1])
        assert not (forbidden & used), f"{module} couples to {forbidden & used}"

    tools_source = (REPO_ROOT / "lab" / "engineering_lab" / "tools.py").read_text(encoding="utf-8")
    for forbidden_name in ("filesystem.write", "git.commit", "git.push", "create_pr"):
        assert forbidden_name not in tools_source


# -- L1.1 boundary hardening: negative mutation tests ------------------------

MUTATING_GIT_COMMANDS = (
    ["git", "commit", "--allow-empty", "-m", "agent"],
    ["git", "-c", "user.email=a@b.c", "commit", "--allow-empty", "-m", "agent"],
    ["git", "add", "-A"],
    ["git", "reset", "--hard", "HEAD"],
    ["git", "checkout", "-b", "agent-branch"],
    ["git", "branch", "agent-branch"],
    ["git", "tag", "agent-tag"],
    ["git", "stash"],
    ["git", "config", "user.name", "agent"],
    ["git", "merge", "main"],
    ["git", "push", "origin", "main"],
)

READONLY_GIT_COMMANDS = (
    ["git", "status", "--short"],
    ["git", "diff"],
    ["git", "log", "--oneline"],
    ["git", "rev-parse", "HEAD"],
)


@pytest.mark.parametrize("argv", MUTATING_GIT_COMMANDS)
def test_git_mutation_is_refused_through_terminal_run(workspace, argv):
    """terminal.run must not be a mutation capability (GATE L1.1)."""
    from lab.engineering_lab.sandbox import SandboxCommandDenied

    sandbox = Sandbox(SandboxPolicy(root=str(workspace), write_allowed=False,
                                    command_allowlist=("git",), enforce_git_read_only=True))
    registry = ToolRegistry(sandbox)
    before = subprocess.run(["git", "status", "--porcelain"], cwd=workspace,
                            capture_output=True, text=True).stdout
    out = registry.invoke("terminal.run", {"argv": argv})
    after = subprocess.run(["git", "status", "--porcelain"], cwd=workspace,
                           capture_output=True, text=True).stdout
    assert out["ok"] is False, f"{argv} must be refused"
    assert before == after, f"{argv} must not change repository state"


@pytest.mark.parametrize("argv", READONLY_GIT_COMMANDS)
def test_git_reads_still_work_under_hardening(workspace, argv):
    sandbox = Sandbox(SandboxPolicy(root=str(workspace), write_allowed=False,
                                    command_allowlist=("git",), enforce_git_read_only=True))
    registry = ToolRegistry(sandbox)
    out = registry.invoke("terminal.run", {"argv": argv})
    assert out["ok"] is True, f"{argv} should be permitted"


def test_git_read_only_guard_blocks_real_commit(workspace):
    """Direct sandbox proof: a commit that would succeed before hardening."""
    from lab.engineering_lab.sandbox import SandboxCommandDenied

    sandbox = Sandbox(SandboxPolicy(root=str(workspace), command_allowlist=("git",),
                                    enforce_git_read_only=True))
    log_before = subprocess.run(["git", "log", "--oneline"], cwd=workspace,
                                capture_output=True, text=True).stdout
    with pytest.raises(SandboxCommandDenied):
        sandbox.run(["git", "-c", "user.email=a@b.c", "-c", "user.name=t",
                     "commit", "--allow-empty", "-m", "AGENT COMMIT"])
    log_after = subprocess.run(["git", "log", "--oneline"], cwd=workspace,
                               capture_output=True, text=True).stdout
    assert log_before == log_after
    assert "AGENT COMMIT" not in log_after


def test_git_subcommand_parser_skips_global_options():
    from lab.engineering_lab.sandbox import _git_subcommand

    assert _git_subcommand(["git", "commit", "-m", "x"]) == "commit"
    assert _git_subcommand(["git", "-c", "user.email=a", "commit"]) == "commit"
    assert _git_subcommand(["git", "--no-pager", "log"]) == "log"
    assert _git_subcommand(["git", "--git-dir=/x", "status"]) == "status"
    assert _git_subcommand(["git"]) == ""


# -- L1.1 follow-up: caller allow-list and git path redirection ---------------

GIT_PATH_REDIRECT_COMMANDS = (
    ["git", "-C", "/tmp/outside", "status"],
    ["git", "-C/tmp/outside", "status"],
    ["git", "-C../outside", "status"],
    ["git", "--git-dir=/tmp/outside/.git", "status"],
    ["git", "--work-tree", "/tmp/outside", "status"],
)


@pytest.mark.parametrize("argv", GIT_PATH_REDIRECT_COMMANDS)
def test_git_path_redirect_is_refused(workspace, argv):
    """Git path options must not escape the sandbox root (GATE L1.1)."""
    from lab.engineering_lab.sandbox import SandboxCommandDenied

    sandbox = Sandbox(SandboxPolicy(root=str(workspace), command_allowlist=("git",),
                                    enforce_git_read_only=True, enforce_command_grammar=True))
    with pytest.raises(SandboxCommandDenied):
        sandbox.run(argv)


def test_git_config_override_is_not_treated_as_path_escape(workspace):
    """``-c`` is a config override, not a path redirect; it must not be denied."""
    from lab.engineering_lab.sandbox import SandboxCommandDenied, _git_path_redirect

    assert _git_path_redirect(["git", "-c", "core.pager=cat", "status"]) == ""
    assert _git_path_redirect(["git", "--git-dir=/x", "status"]) == "--git-dir"
    assert _git_path_redirect(["git", "-C", "/x", "status"]) == "-C"
    sandbox = Sandbox(SandboxPolicy(root=str(workspace), command_allowlist=("git",),
                                    enforce_git_read_only=True, enforce_command_grammar=True))
    try:
        sandbox.run(["git", "-c", "core.pager=cat", "status"])
    except SandboxCommandDenied:  # pragma: no cover
        pytest.fail("git -c is a config override and must not be denied")


def test_caller_allowlist_cannot_widen_terminal_grammar(workspace):
    """A caller-supplied allow-list must not reintroduce mutation (GATE L1.1)."""
    from lab.engineering_lab.sandbox import SandboxCommandDenied

    sandbox = Sandbox(SandboxPolicy(root=str(workspace), write_allowed=False,
                                    command_allowlist=("python", "sh", "rm"),
                                    enforce_git_read_only=True, enforce_command_grammar=True))
    before = sorted(p.name for p in workspace.iterdir())
    for argv in (["python", "-c", "open('injected.txt','w').write('x')"],
                 ["sh", "-c", "echo x > injected.txt"],
                 ["rm", "-rf", "."]):
        with pytest.raises(SandboxCommandDenied):
            sandbox.run(argv)
    assert sorted(p.name for p in workspace.iterdir()) == before


def test_l1_terminal_binaries_still_run_under_grammar(workspace):
    sandbox = Sandbox(SandboxPolicy(root=str(workspace), write_allowed=False,
                                    command_allowlist=("git", "echo", "pwd", "true"),
                                    enforce_git_read_only=True, enforce_command_grammar=True))
    for argv in (["echo", "hi"], ["pwd"], ["true"]):
        assert sandbox.run(argv)["ok"] is True


def test_runtime_forces_closed_grammar_on_caller_policy(
    tmp_path, store, monkeypatch, workspace, gateway
):
    """Even when the caller supplies command_allowlist=('python','git'), the
    runtime must force the closed grammar onto the effective policy."""
    import lab.engineering_lab.runtime as runtime_mod
    from lab.engineering_lab.sandbox import SandboxCommandDenied

    runtime, _ = _runtime_fixture(tmp_path, store, monkeypatch, workspace)
    gateway.register_adapter("ollama", ScriptedAdapter("ollama", KNOWN_SEQUENCE))
    monkeypatch.setattr(gateway_mod, "get_gateway", lambda: gateway)

    captured: list = []
    real_sandbox = runtime_mod.Sandbox

    class RecordingSandbox(real_sandbox):
        def __init__(self, policy):
            captured.append(policy)
            super().__init__(policy)

    monkeypatch.setattr(runtime_mod, "Sandbox", RecordingSandbox)

    agent = runtime.register_agent(subject_ref="architect", role="BUILDER")
    authorization = runtime.record_authorization(
        subject_ref="architect", scope_ref="inspect",
        operations_allowed=("list", "read", "run", "git_status"),
    )
    session = runtime.open_session(subject_ref="architect", agent_id=agent["agent_id"],
                                   workspace_ref="arkadia", objective="inspect",
                                   authorization_ref=authorization["authorization_id"])
    runtime.execute_agent_loop(
        subject_ref="architect", session_id=session["session_id"],
        objective="inspect", provider="ollama", model="stub-model",
        sandbox_policy=SandboxPolicy(root=str(workspace),
                                     command_allowlist=("python", "git")),
    )
    assert captured, "the runtime must construct a sandbox"
    effective = captured[0]
    assert effective.enforce_command_grammar is True
    assert effective.enforce_git_read_only is True
    with pytest.raises(SandboxCommandDenied):
        effective and real_sandbox(effective).run(["python", "-c", "print(1)"])


def test_agent_loop_uses_git_read_only_policy_by_default(
    tmp_path, store, monkeypatch, workspace, gateway
):
    """The runtime's own default policy must enforce git read-only."""
    runtime, _ = _runtime_fixture(tmp_path, store, monkeypatch, workspace)
    gateway.register_adapter("ollama", ScriptedAdapter("ollama", KNOWN_SEQUENCE))
    monkeypatch.setattr(gateway_mod, "get_gateway", lambda: gateway)
    monkeypatch.setenv("ENGINEERING_LAB_WORKSPACE_ROOT", str(workspace))

    agent = runtime.register_agent(subject_ref="architect", role="BUILDER")
    authorization = runtime.record_authorization(
        subject_ref="architect", scope_ref="inspect",
        operations_allowed=("list", "read", "run", "git_status"),
    )
    session = runtime.open_session(subject_ref="architect", agent_id=agent["agent_id"],
                                   workspace_ref="arkadia", objective="inspect",
                                   authorization_ref=authorization["authorization_id"])
    # No sandbox_policy passed -> the runtime builds its default (enforce_git_read_only=True)
    out = runtime.execute_agent_loop(
        subject_ref="architect", session_id=session["session_id"],
        objective="inspect", provider="ollama", model="stub-model",
    )
    assert out["loop_state"] in TERMINAL_STATES


# -- local provider adapter (opportunistic) ----------------------------------


def _ollama_reachable() -> bool:
    from lab.engineering_lab.gateway import _probe_local

    base = os.environ.get("OLLAMA_BASE_URL") or os.environ.get("OLLAMA_HOST")
    if not base:
        return False
    return _probe_local(base)[0]


@pytest.mark.skipif(not _ollama_reachable(), reason="no local Ollama endpoint configured")
def test_ollama_adapter_calls_a_real_local_model(registry):
    """Exercises the real adapter only when a local endpoint is actually up.

    The deterministic stub remains the CI truth; this proves the same loop runs
    against a real local model without any change to the loop.
    """
    gateway = ModelGateway()
    gateway.register_adapter("ollama", gateway_mod.OllamaAdapter())
    model = os.environ.get("OLLAMA_MODEL", "llama3")
    loop = AgentLoop(gateway=gateway, tools=registry, provider="ollama", model=model,
                     max_turns=2)
    result = loop.run(objective="List the files in the workspace, then stop.")
    assert result.state in TERMINAL_STATES


def test_git_path_overrides_are_removed_from_sandbox_environment(monkeypatch):
    """Ambient Git path overrides must not redirect a sandbox outside its root."""
    from lab.engineering_lab.sandbox import _sanitised_env

    monkeypatch.setenv("GIT_DIR", "/tmp/outside/.git")
    monkeypatch.setenv("GIT_WORK_TREE", "/tmp/outside")
    monkeypatch.setenv("GIT_INDEX_FILE", "/tmp/outside/index")
    env = _sanitised_env()
    assert "GIT_DIR" not in env
    assert "GIT_WORK_TREE" not in env
    assert "GIT_INDEX_FILE" not in env
