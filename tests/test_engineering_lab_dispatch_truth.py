"""P0.5 — dispatch truth for the Engineering Lab's native agent runtime.

Three rules this file pins, each with a negative control:

* **Provider independence.** Adapters are bound from configuration, never
  hard-wired. Swapping providers must not require redesigning the Lab, and a
  provider that is *described* as available is not thereby *dispatchable* —
  `AVAILABLE` and `dispatchable` are separate facts.
* **Observable execution.** A dispatch reports its real terminal state, the
  reason it stopped, the tool envelope actually granted, and stores its events
  against the run so the mission workspace can attribute them.
* **Honest availability.** With no configured provider the dispatch is
  `BLOCKED` with a reason — never a fabricated worker, never `IMPLEMENTED`.

Plus the boundary the directive calls out by name: the `test` operation is
never granted to `run-agent` just because both capabilities now exist.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import lab.engineering_lab.gateway as gateway_mod  # noqa: E402
from lab.engineering_lab.events import EventStream  # noqa: E402
from lab.engineering_lab.gateway import (  # noqa: E402
    ModelUnavailable,
    ModelGateway,
    get_gateway,
)
from lab.engineering_lab.runtime import (  # noqa: E402
    OPERATION_TOOLS,
    EngineeringLabRuntime,
)
from lab.engineering_lab.store import EngineeringLabStore  # noqa: E402
from lab.engineering_lab.tools import ToolRegistry, _specs  # noqa: E402

SUBJECT = "operator-1"

#: Every provider credential/endpoint variable the gateway reads. Cleared so a
#: dispatch test measures this environment, not the developer's shell.
_PROVIDER_VARS = (
    "N_ATLAS_BASE_URL",
    "N_ATLAS_PROTOCOL",
    "OLLAMA_BASE_URL",
    "OLLAMA_HOST",
    "LLAMA_CPP_BASE_URL",
    "LOCAL_MODEL_BASE_URL",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "ANTHROPIC_API_KEY",
    "OLLAMA_MODEL",
    "N_ATLAS_MODEL",
)


@pytest.fixture(autouse=True)
def clean_provider_env(monkeypatch):
    for var in _PROVIDER_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(gateway_mod, "_GLOBAL_GATEWAY", None)
    yield


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
    (root / "README.md").write_text("hello\n", encoding="utf-8")
    return root


@pytest.fixture()
def runtime(store, tmp_path, monkeypatch):
    monkeypatch.setenv("ENGINEERING_LAB_DATA_DIR", str(tmp_path / "data"))
    stream = EventStream(log_path=str(tmp_path / "events.jsonl"))
    return EngineeringLabRuntime(store=store, stream=stream)


def _authorized_session(runtime, *, operations=("read", "test", "run")):
    agent = runtime.register_agent(subject_ref=SUBJECT, role="BUILDER")
    authorization = runtime.record_authorization(
        subject_ref=SUBJECT, scope_ref="dispatch", operations_allowed=tuple(operations)
    )
    session = runtime.open_session(
        subject_ref=SUBJECT,
        workspace_ref="ws-1",
        agent_id=agent["agent_id"],
        objective="dispatch a worker",
        authorization_ref=authorization["authorization_id"],
    )
    return session


# ---------------------------------------------------------------------------
# Provider independence: availability and dispatchability are different facts
# ---------------------------------------------------------------------------


def test_availability_and_dispatchability_are_reported_separately(monkeypatch):
    """A configured key with no adapter must not read as dispatchable.

    This is the exact failure mode the directive names: a *connected* provider
    reported as a *functioning* worker. Without the split, `describe()` would
    say AVAILABLE while every dispatch dies on `ModelUnavailable`.
    """
    monkeypatch.setenv("OPENAI_API_KEY", "present-but-never-sent")
    gateway = ModelGateway()

    descriptor = gateway.describe("openai_compatible")
    assert descriptor.status == "AVAILABLE"          # configuration truth
    assert descriptor.adapter_bound is False         # dispatch truth
    assert descriptor.dispatchable is False          # the honest conjunction

    gateway.register_adapter("openai_compatible", object())
    bound = gateway.describe("openai_compatible")
    assert bound.status == "AVAILABLE"
    assert bound.adapter_bound is True
    assert bound.dispatchable is True


def test_gateway_catalog_carries_the_dispatch_fields_the_surface_reads():
    gateway = ModelGateway()
    entry = next(e for e in gateway.to_dict()["catalog"] if e["provider"] == "ollama")
    assert entry["status"] == "UNCONFIGURED"
    assert entry["adapter_bound"] is False
    assert entry["dispatchable"] is False


def test_unconfigured_provider_is_never_reported_available_or_dispatchable():
    gateway = ModelGateway()
    for provider in ("ollama", "n_atlas", "gemini", "openai_compatible"):
        descriptor = gateway.describe(provider)
        assert descriptor.status == "UNCONFIGURED"
        assert descriptor.dispatchable is False


def test_ollama_adapter_is_bound_from_configuration_not_hard_wired(monkeypatch):
    """Configured endpoint => bound adapter; absent configuration => none."""
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    gateway_mod._GLOBAL_GATEWAY = None
    bound = get_gateway()
    assert "ollama" in bound._adapters, "a configured provider must be callable"

    monkeypatch.delenv("OLLAMA_BASE_URL")
    gateway_mod._GLOBAL_GATEWAY = None
    unbound = get_gateway()
    assert "ollama" not in unbound._adapters
    # n_atlas stays bound (the Lab's own adapter) but is not dispatchable
    # without its endpoint.
    n_atlas = unbound.describe("n_atlas")
    assert n_atlas.adapter_bound is True
    assert n_atlas.dispatchable is False


def test_generation_without_a_bound_adapter_fails_closed():
    gateway = ModelGateway()
    with pytest.raises(ModelUnavailable) as excinfo:
        gateway.generate(
            provider="ollama",
            model="llama3",
            messages=[{"role": "user", "content": "hi"}],
        )
    assert "no inference adapter bound" in str(excinfo.value)


# ---------------------------------------------------------------------------
# Honest availability: a dispatch with nothing configured is BLOCKED
# ---------------------------------------------------------------------------


def test_dispatch_without_a_provider_is_blocked_with_a_reason(runtime, workspace, monkeypatch):
    """No configured provider => BLOCKED + reason, never a simulated worker."""
    session = _authorized_session(runtime)
    monkeypatch.setattr(gateway_mod, "_GLOBAL_GATEWAY", None)

    result = runtime.execute_agent_loop(
        subject_ref=SUBJECT,
        session_id=session["session_id"],
        objective="read README.md and summarise",
        provider="ollama",
        model=None,
        sandbox_policy=None,
        max_turns=3,
    )

    assert result["loop_state"] == "BLOCKED"
    assert "no inference adapter bound" in result["loop_reason"]
    assert result["result_state"] == "BLOCKED"
    assert result["turns"] == [], "no model turn happened; inventing one would be a fabrication"
    assert result["merge"] is False and result["deploy"] is False
    assert result["self_authorized"] is False

    evidence = runtime._store.list_evidence(SUBJECT, run_ref=result["run_id"])
    assert evidence and evidence[0]["state"] == "BLOCKED"
    assert "BLOCKED" in evidence[0]["summary"]


def test_dispatch_reports_the_tool_envelope_it_actually_granted(runtime, workspace):
    """Permissions must be observable, not assumed."""
    session = _authorized_session(runtime, operations=("read", "test", "run"))
    result = runtime.execute_agent_loop(
        subject_ref=SUBJECT,
        session_id=session["session_id"],
        objective="inspect",
        provider="ollama",
        sandbox_policy=None,
        max_turns=2,
    )
    granted = result["effective_tools"]
    assert isinstance(granted, list)
    assert granted, "the read/run authorization should reach the loop"
    assert set(granted) <= {
        "filesystem.list", "filesystem.read", "filesystem.propose_edit",
        "terminal.run", "git.status", "git.diff",
    }


def test_dispatch_events_are_stored_and_attributable_to_the_run(runtime, workspace):
    session = _authorized_session(runtime)
    result = runtime.execute_agent_loop(
        subject_ref=SUBJECT,
        session_id=session["session_id"],
        objective="inspect",
        provider="ollama",
        sandbox_policy=None,
        max_turns=2,
    )
    view = runtime.session_view(session["session_id"], SUBJECT)
    run_ids = {r["run_id"] for r in view["runs"]}
    assert result["run_id"] in run_ids

    event_types = {e["event_type"] for e in view["events"]}
    assert "RUN_STARTED" in event_types
    assert "EVIDENCE_RECORDED" in event_types
    assert "RUN_FINISHED" in event_types
    # every event is attributable: either this run or session-scoped
    for event in view["events"]:
        assert event["session_id"] == session["session_id"]
        assert event.get("run_id") in (None, result["run_id"])


# ---------------------------------------------------------------------------
# The named boundary: `test` never rides along with run-agent
# ---------------------------------------------------------------------------


def test_the_test_operation_is_not_a_loop_tool(monkeypatch):
    """`test` exists as an operation kind, never as a model-facing tool."""
    assert "test" not in OPERATION_TOOLS
    assert "test" not in _specs(), "no tool spec may be named 'test'"
    from lab.engineering_lab.runtime import CAPABILITY_OPERATIONS

    assert "test" not in CAPABILITY_OPERATIONS.get("RUN", ())
    assert "test" not in CAPABILITY_OPERATIONS.get("READ", ())


def test_authorizing_test_does_not_grant_the_loop_a_test_tool(runtime, workspace):
    """The explicit-independence rule: both capabilities exist, neither implies
    the other. Authorizing `test` for the session must not widen the loop."""
    session = _authorized_session(runtime, operations=("read", "test", "run", "git_status"))
    result = runtime.execute_agent_loop(
        subject_ref=SUBJECT,
        session_id=session["session_id"],
        objective="inspect",
        provider="ollama",
        sandbox_policy=None,
        max_turns=2,
    )
    granted = set(result["effective_tools"])
    assert "test" not in granted
    assert not any(name.startswith("test") for name in granted)


def test_every_loop_tool_is_non_mutating():
    """Defence in depth: the registry cannot expose a mutating tool in L1."""
    for spec in _specs().values():
        assert spec.mutating is False, f"{spec.name} must not be mutating"
    registry = ToolRegistry(sandbox=None, granted=None)
    for spec in registry.available():
        assert spec["mutating"] is False


def test_a_grant_cannot_smuggle_a_tool_outside_the_registry(runtime, workspace):
    """A granted name that is not a tool grants nothing."""
    from lab.engineering_lab.sandbox import Sandbox, SandboxPolicy

    sandbox = Sandbox(SandboxPolicy(root=str(workspace)))
    registry = ToolRegistry(sandbox, granted=("test", "shell.exec", "filesystem.read"))
    names = {spec["name"] for spec in registry.available()}
    assert names == {"filesystem.read"}
    observation = registry.invoke("shell.exec", {"cmd": "id"})
    assert observation["ok"] is False
    assert "unknown tool" in observation["error"]
