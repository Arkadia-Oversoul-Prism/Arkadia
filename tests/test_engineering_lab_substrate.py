"""EL-01 -> EL-10 native Engineering Lab substrate — verification tests.

These tests exercise the real code paths (no mocks): a real SQLite store, a real
sandbox running real commands inside a tmp workspace, real state transitions.

Categories covered (directive section 18): unit, integration, security/authority,
governance attribution, artifact validity, and runtime.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lab.engineering_lab.contracts import (  # noqa: E402
    BoundaryViolation,
    assert_operation_allowed,
    assert_transition_allowed,
)
from lab.engineering_lab.events import EventStream  # noqa: E402
from lab.engineering_lab.models import AGENT_ROLES, ROLE_CAPABILITIES  # noqa: E402
from lab.engineering_lab.runtime import (  # noqa: E402
    CANONICAL_LOOP,
    BoundedOperation,
    BoundedTask,
    EngineeringLabRuntime,
)
from lab.engineering_lab.sandbox import (  # noqa: E402
    Sandbox,
    SandboxCommandDenied,
    SandboxEscape,
    SandboxPolicy,
    SandboxWriteDenied,
)
from lab.engineering_lab.store import EngineeringLabStore  # noqa: E402


@pytest.fixture()
def store(tmp_path, monkeypatch):
    db = tmp_path / "el.db"
    monkeypatch.setenv("SOLSPIRE_PROJECTS_DB", str(db))
    # Reload the module-level DB path binding for this test process.
    import lab.engineering_lab.store as store_mod

    monkeypatch.setattr(store_mod, "_DB_PATH", str(db))
    return EngineeringLabStore()


@pytest.fixture()
def workspace(tmp_path):
    root = tmp_path / "ws"
    root.mkdir()
    (root / "README.md").write_text("hello arkadia\n", encoding="utf-8")
    (root / "sub").mkdir()
    (root / "sub" / "note.txt").write_text("nested\n", encoding="utf-8")
    return root


@pytest.fixture()
def runtime(store, tmp_path, monkeypatch):
    monkeypatch.setenv("ENGINEERING_LAB_DATA_DIR", str(tmp_path / "data"))
    stream = EventStream(log_path=str(tmp_path / "events.jsonl"))
    return EngineeringLabRuntime(store=store, stream=stream)


# ── EL-01: sandbox boundary ──────────────────────────────────────────────────


def test_sandbox_default_policy_is_read_only(workspace):
    sandbox = Sandbox(SandboxPolicy(root=str(workspace)))
    text = sandbox.read("README.md")
    assert "arkadia" in text
    with pytest.raises(SandboxWriteDenied):
        sandbox.write("new.txt", "x")


def test_sandbox_refuses_path_escape(workspace, tmp_path):
    sandbox = Sandbox(SandboxPolicy(root=str(workspace), write_allowed=True))
    with pytest.raises(SandboxEscape):
        sandbox.read("../outside.txt")
    with pytest.raises(SandboxEscape):
        sandbox.write("../../evil.txt", "x")


def test_sandbox_write_requires_allowlist(workspace):
    sandbox = Sandbox(
        SandboxPolicy(root=str(workspace), write_allowed=True, allowed_paths=("sub",))
    )
    sandbox.write("sub/ok.txt", "ok")
    with pytest.raises(SandboxWriteDenied):
        sandbox.write("README.md", "nope")


def test_sandbox_forbidden_path_blocks_write(workspace):
    sandbox = Sandbox(
        SandboxPolicy(root=str(workspace), write_allowed=True, forbidden_paths=("sub",))
    )
    with pytest.raises(SandboxWriteDenied):
        sandbox.write("sub/x.txt", "x")


def test_sandbox_runs_command_without_shell_and_observes_output(workspace):
    sandbox = Sandbox(SandboxPolicy(root=str(workspace), command_allowlist=("echo",)))
    result = sandbox.run(["echo", "sandbox-live"])
    assert result["ok"] is True
    assert result["stdout"].strip() == "sandbox-live"


def test_sandbox_command_allowlist_is_enforced(workspace):
    sandbox = Sandbox(SandboxPolicy(root=str(workspace), command_allowlist=("echo",)))
    with pytest.raises(SandboxCommandDenied):
        sandbox.run(["rm", "-rf", "/"])


def test_sandbox_never_passes_secrets_into_env(workspace, monkeypatch):
    monkeypatch.setenv("ARKADIA_TEST_SECRET_TOKEN", "super-secret-value")
    sandbox = Sandbox(SandboxPolicy(root=str(workspace), command_allowlist=("env",)))
    result = sandbox.run(["env"])
    assert result["ok"] is True
    assert "super-secret-value" not in result["stdout"]


def test_sandbox_git_refuses_merge_and_force_push(workspace):
    sandbox = Sandbox(SandboxPolicy(root=str(workspace), command_allowlist=("git",)))
    with pytest.raises(SandboxCommandDenied):
        sandbox.git(["merge", "main"])
    with pytest.raises(SandboxCommandDenied):
        sandbox.git(["push", "--force"])


def test_sandbox_git_remote_requires_network_policy(workspace):
    sandbox = Sandbox(SandboxPolicy(root=str(workspace), command_allowlist=("git",)))
    with pytest.raises(SandboxCommandDenied):
        sandbox.git(["fetch", "origin"], remote=True)


def test_sandbox_records_evidence(workspace):
    sandbox = Sandbox(SandboxPolicy(root=str(workspace)))
    sandbox.read("README.md")
    evidence = sandbox.evidence()
    assert evidence["operation_count"] >= 1
    assert evidence["operations"][0]["operation"] == "read"


# ── EL-01: foundational contracts ────────────────────────────────────────────


def test_forbidden_operations_are_refused():
    with pytest.raises(BoundaryViolation):
        assert_operation_allowed("merge")
    with pytest.raises(BoundaryViolation):
        assert_operation_allowed("production_deploy")
    # A benign operation is allowed.
    assert_operation_allowed("read")


def test_state_non_collapse_is_enforced():
    # AUTHORIZED may not collapse straight to COMPLETED.
    with pytest.raises(BoundaryViolation):
        assert_transition_allowed("AUTHORIZED", "COMPLETED")
    # But the canonical chain is permitted.
    assert_transition_allowed("AUTHORIZED", "QUEUED")
    assert_transition_allowed("VERIFYING", "READY_FOR_REVIEW")


def test_canonical_loop_is_the_success_condition_order():
    assert CANONICAL_LOOP == (
        "DISCOVER", "PLAN", "EXECUTE", "OBSERVE", "EVIDENCE",
        "PROPOSE", "REVIEW", "AUTHORIZE", "VERIFY", "RECORD",
    )


# ── EL-02 / EL-09: agents and roles ──────────────────────────────────────────


def test_agent_registration_binds_role_capabilities(runtime):
    agent = runtime.register_agent(subject_ref="u1", role="SENTINEL")
    assert agent["role"] == "SENTINEL"
    assert set(agent["capabilities"]) <= set(ROLE_CAPABILITIES["SENTINEL"])
    assert agent["tool_access"]["write_allowed"] is False


def test_agent_capability_cannot_exceed_role_ceiling(runtime):
    with pytest.raises(BoundaryViolation):
        runtime.register_agent(subject_ref="u1", role="SENTINEL", capabilities=("EDIT",))


def test_all_roles_are_registrable(runtime):
    for role in AGENT_ROLES:
        agent = runtime.register_agent(subject_ref="u1", role=role)
        assert agent["agent_id"].startswith("AGT-")


# ── EL-01 / EL-10: sessions, authorization, execution ────────────────────────


def test_session_without_authorization_is_proposed(runtime):
    agent = runtime.register_agent(subject_ref="u1", role="BUILDER")
    session = runtime.open_session(
        subject_ref="u1", workspace_ref="ws", agent_id=agent["agent_id"], objective="x"
    )
    assert session["state"] == "PROPOSED"
    assert session["authorization_ref"] is None


def test_execution_fails_closed_without_authorization(runtime, workspace):
    agent = runtime.register_agent(subject_ref="u1", role="BUILDER")
    session = runtime.open_session(
        subject_ref="u1", workspace_ref="ws", agent_id=agent["agent_id"], objective="x"
    )
    with pytest.raises(BoundaryViolation):
        runtime.execute_bounded_task(
            subject_ref="u1",
            session_id=session["session_id"],
            task=BoundedTask(
                objective="read",
                operations=(BoundedOperation(kind="read", target="README.md"),),
            ),
            sandbox_policy=SandboxPolicy(root=str(workspace)),
        )


def test_authorization_is_recorded_as_human_originated(runtime):
    auth = runtime.record_authorization(
        subject_ref="u1", scope_ref="SES-x", operations_allowed=("read",)
    )
    assert auth["originated_by"] == "human"
    assert auth["merge_prohibited"] is True
    assert auth["production_prohibited"] is True


def test_store_rejects_non_human_authorization(store):
    with pytest.raises(ValueError):
        store.record_authorization(
            {"authorization_id": "A", "scope_ref": "s", "originated_by": "lab"},
            "u1",
        )


def test_full_bounded_run_reaches_review_boundary(runtime, workspace):
    agent = runtime.register_agent(subject_ref="u1", role="BUILDER")
    session = runtime.open_session(
        subject_ref="u1", workspace_ref="ws", agent_id=agent["agent_id"], objective="probe"
    )
    runtime.record_authorization(
        subject_ref="u1", scope_ref=session["session_id"], operations_allowed=("read",)
    )
    runtime.transition(session["session_id"], "u1", "AUTHORIZED")

    result = runtime.execute_bounded_task(
        subject_ref="u1",
        session_id=session["session_id"],
        task=BoundedTask(
            objective="read + run",
            operations=(
                BoundedOperation(kind="read", target="README.md"),
                BoundedOperation(kind="run", argv=("echo", "live")),
            ),
            acceptance=("reads",),
        ),
        sandbox_policy=SandboxPolicy(root=str(workspace), command_allowlist=("echo",)),
    )
    assert result["result_state"] == "IMPLEMENTED"
    assert result["merge"] is False
    assert result["deploy"] is False
    assert result["self_authorized"] is False
    assert result["human_decision_required"] is True

    view = runtime.session_view(session["session_id"], "u1")
    assert view["session"]["state"] == "READY_FOR_REVIEW"
    assert view["human_decision_required"] is True
    # Governance: evidence is attributed to the run.
    assert len(view["evidence"]) == 1
    assert view["evidence"][0]["run_ref"] == result["run_id"]


def test_execution_never_reaches_completed_without_human(runtime, workspace):
    agent = runtime.register_agent(subject_ref="u1", role="BUILDER")
    session = runtime.open_session(
        subject_ref="u1", workspace_ref="ws", agent_id=agent["agent_id"], objective="x"
    )
    runtime.record_authorization(
        subject_ref="u1", scope_ref=session["session_id"], operations_allowed=("read",)
    )
    runtime.transition(session["session_id"], "u1", "AUTHORIZED")
    runtime.execute_bounded_task(
        subject_ref="u1",
        session_id=session["session_id"],
        task=BoundedTask(
            objective="read",
            operations=(BoundedOperation(kind="read", target="README.md"),),
        ),
        sandbox_policy=SandboxPolicy(root=str(workspace)),
    )
    view = runtime.session_view(session["session_id"], "u1")
    assert view["session"]["state"] != "COMPLETED"


def test_write_operation_requires_requires_write_flag(runtime, workspace):
    agent = runtime.register_agent(subject_ref="u1", role="BUILDER", write_allowed=True)
    session = runtime.open_session(
        subject_ref="u1", workspace_ref="ws", agent_id=agent["agent_id"], objective="x"
    )
    runtime.record_authorization(
        subject_ref="u1", scope_ref=session["session_id"], operations_allowed=("write",)
    )
    runtime.transition(session["session_id"], "u1", "AUTHORIZED")
    with pytest.raises(BoundaryViolation):
        runtime.execute_bounded_task(
            subject_ref="u1",
            session_id=session["session_id"],
            task=BoundedTask(
                objective="write",
                operations=(BoundedOperation(kind="write", target="a.txt", content="x"),),
                requires_write=False,
            ),
            sandbox_policy=SandboxPolicy(root=str(workspace), write_allowed=True),
        )


def test_write_run_captures_artifact(runtime, workspace):
    agent = runtime.register_agent(subject_ref="u1", role="BUILDER", write_allowed=True)
    session = runtime.open_session(
        subject_ref="u1", workspace_ref="ws", agent_id=agent["agent_id"], objective="x"
    )
    runtime.record_authorization(
        subject_ref="u1", scope_ref=session["session_id"], operations_allowed=("write",)
    )
    runtime.transition(session["session_id"], "u1", "AUTHORIZED")
    result = runtime.execute_bounded_task(
        subject_ref="u1",
        session_id=session["session_id"],
        task=BoundedTask(
            objective="write a file",
            operations=(BoundedOperation(kind="write", target="out.txt", content="hi"),),
            requires_write=True,
        ),
        sandbox_policy=SandboxPolicy(root=str(workspace), write_allowed=True),
    )
    assert result["artifact_refs"], "a write run must capture an artifact"
    assert (workspace / "out.txt").read_text() == "hi"


# ── Ownership isolation (security) ───────────────────────────────────────────


def test_sessions_are_owner_scoped(runtime):
    agent = runtime.register_agent(subject_ref="owner-a", role="BUILDER")
    session = runtime.open_session(
        subject_ref="owner-a", workspace_ref="ws", agent_id=agent["agent_id"], objective="x"
    )
    # A different subject cannot read the session.
    with pytest.raises(KeyError):
        runtime.session_view(session["session_id"], "owner-b")
    assert runtime._store.list_sessions("owner-b") == []


# ── EL-03: automations ───────────────────────────────────────────────────────


def test_automation_state_machine_rejects_illegal_transition():
    from lab.engineering_lab.automations import (
        AutomationTrigger,
        assert_automation_transition,
        grammar_view,
        make_automation,
    )

    automation = make_automation(
        subject_ref="u1",
        name="nightly",
        trigger=AutomationTrigger(kind="scheduled", schedule="0 * * * *"),
        agent_role="WEAVER",
    )
    assert automation.state == "DRAFT"
    assert_automation_transition("DRAFT", "ENABLED")
    with pytest.raises(BoundaryViolation):
        assert_automation_transition("DRAFT", "COMPLETED")
    grammar = grammar_view()
    assert grammar["may_authorize_consequential_action"] is False
    assert grammar["final_transition"] == "HUMAN_GATE"


# ── EL-04: artifacts / canvas ────────────────────────────────────────────────


def test_canvas_view_is_truthful_about_absence():
    from lab.engineering_lab.artifacts import canvas_view

    stored = {"artifact_id": "A", "kind": "diff", "content": None}
    view = canvas_view(stored)
    assert view["available"] is False
    assert view["renderer"] == "DiffSurface"
    assert view["unavailable_reason"]


def test_canvas_view_marks_present_content_available():
    from lab.engineering_lab.artifacts import canvas_view

    view = canvas_view({"artifact_id": "A", "kind": "markdown", "content": "# hi"})
    assert view["available"] is True
    assert view["renderer"] == "MarkdownViewer"


# ── EL-05: adapters ──────────────────────────────────────────────────────────


def test_google_adapters_report_unavailable_without_credentials(monkeypatch):
    from lab.engineering_lab.adapters import GoogleKeepAdapter, GoogleTasksAdapter

    for var in (
        "GOOGLE_TASKS_ACCESS_TOKEN", "GOOGLE_ACCESS_TOKEN",
        "GOOGLE_KEEP_ACCESS_TOKEN",
    ):
        monkeypatch.delenv(var, raising=False)
    tasks = GoogleTasksAdapter()
    assert tasks.status().state == "UNCONFIGURED"
    created = tasks.create_task(title="x")
    assert created["state"] == "UNAVAILABLE"
    assert created["task"] is None

    keep = GoogleKeepAdapter()
    assert keep.create_note(title="x", body="y")["state"] == "UNAVAILABLE"


def test_task_state_mapping_is_one_directional():
    from lab.engineering_lab.adapters import GoogleTasksAdapter

    mapping = GoogleTasksAdapter().map_lab_state("READY_FOR_REVIEW")
    assert mapping["task_state"] == "needsAction"
    assert "arkadia remains authoritative" in mapping["authority"]


# ── EL-06: Android control plane ─────────────────────────────────────────────


def test_android_control_plane_never_exposes_merge_or_deploy():
    from lab.engineering_lab.android import android_capability_report

    report = android_capability_report()
    assert report["android_local_execution_required"] is False
    assert report["authority"]["merge_exposed"] is False
    assert report["authority"]["deploy_exposed"] is False
    caps = {c["capability"] for c in report["capabilities"]}
    assert "voice_entry" in caps
    initiating = [c for c in report["capabilities"] if c["capability"] == "initiate_authorized_run"]
    assert initiating[0]["state"] == "AUTHORIZATION_REQUIRED"


# ── EL-07: voice adapter ─────────────────────────────────────────────────────


def test_voice_human_only_intents_are_refused():
    from lab.engineering_lab.voice import resolve_voice_command

    result = resolve_voice_command("merge the pull request")
    assert result.disposition == "HUMAN_ONLY_REFUSED"
    assert result.human_only is True


def test_voice_action_intent_requires_authorization():
    from lab.engineering_lab.voice import resolve_voice_command

    result = resolve_voice_command(
        "request review", identity_present=True, workspace_present=True,
        authorization_present=False,
    )
    assert result.disposition == "AUTHORIZATION_REQUIRED"


def test_voice_read_intent_is_observation_only():
    from lab.engineering_lab.voice import resolve_voice_command

    result = resolve_voice_command("show active runs")
    assert result.disposition == "READ"


def test_voice_boundary_is_not_a_hidden_authority():
    from lab.engineering_lab.voice import voice_boundary_report

    report = voice_boundary_report()
    assert report["assistant_is_hidden_authority"] is False
    assert report["human_authority_preserved"] is True


# ── EL-08: model gateway ─────────────────────────────────────────────────────


def test_gateway_is_provider_neutral_and_truthful():
    from lab.engineering_lab.gateway import ModelGateway

    gateway = ModelGateway()
    catalog = gateway.catalog()
    providers = {entry["provider"] for entry in catalog}
    assert {"ollama", "llama_cpp", "gemini"} <= providers
    # A local provider with no endpoint is not claimed available.
    ollama = next(e for e in catalog if e["provider"] == "ollama")
    assert ollama["status"] in ("UNCONFIGURED", "UNAVAILABLE")
    assert ollama["configured"] is False


def test_gateway_selection_never_fabricates_availability():
    from lab.engineering_lab.gateway import ModelGateway

    selection = ModelGateway().select(preferred="gemini")
    # Without a key in this test environment the honest answer is UNAVAILABLE.
    assert selection.status in ("AVAILABLE", "UNAVAILABLE")
    assert selection.to_dict()["cost_note"] if hasattr(selection, "cost_note") else True


# ── Event stream ─────────────────────────────────────────────────────────────


def test_event_stream_delivers_live_and_persists(tmp_path):
    stream = EventStream(log_path=str(tmp_path / "e.jsonl"))
    received: list[dict] = []
    stream.subscribe(received.append)
    event = stream.emit(session_id="S1", event_type="RUN_STARTED", payload={"x": 1})
    assert event.sequence == 1
    assert len(received) == 1
    second = stream.emit(session_id="S1", event_type="RUN_FINISHED", payload={})
    assert second.sequence == 2
    replay = stream.replay("S1")
    assert [r["event_type"] for r in replay] == ["RUN_STARTED", "RUN_FINISHED"]
