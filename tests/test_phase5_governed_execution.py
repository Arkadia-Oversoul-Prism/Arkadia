"""Phase 5 — Governed execution dry-run and forbidden actions."""
from lab.execution import FORBIDDEN_ACTIONS, execute_governed


PROPOSAL = {
    "proposal_id": "EV-PHASE5-DRY-001",
    "title": "Document parallel execution path debt",
    "approval_required": True,
    "problem": {"description": "fixture", "evidence": ["pattern:parallel-execution-paths"]},
}


def test_forbidden_actions_include_merge_deploy():
    assert "merge" in FORBIDDEN_ACTIONS
    assert "deploy" in FORBIDDEN_ACTIONS


def test_dry_run_emits_events_no_pr():
    r = execute_governed(PROPOSAL, mode="dry_run")
    assert r.ok is True
    names = [e["event"] for e in r.events]
    assert "dry_run.completed" in names
    assert "pr.created" not in names
    d = r.to_dict()
    assert d["merge"] is False
    assert d["deploy"] is False


def test_rejects_auto_execution_flags():
    bad = {**PROPOSAL, "execution": True}
    r = execute_governed(bad, mode="dry_run")
    assert r.ok is False


def test_prepare_pr_requires_callables():
    r = execute_governed(PROPOSAL, mode="prepare_pr")
    assert r.ok is False
    assert r.ok is False and (any("callable" in e.lower() for e in r.errors) or any(e.get("event")=="prepare_pr.blocked" for e in r.events))


def test_prepare_pr_with_injected_callables():
    state = {"branch": None, "applied": False, "pr": None}

    def create_branch(b: str) -> None:
        state["branch"] = b

    def apply(_p: dict) -> None:
        state["applied"] = True

    def tests() -> tuple[bool, str]:
        return True, "ok"

    def open_pr(b: str, pid: str) -> str:
        state["pr"] = f"https://example.invalid/{b}/{pid}"
        return state["pr"]

    r = execute_governed(
        PROPOSAL,
        mode="prepare_pr",
        create_branch_fn=create_branch,
        apply_fn=apply,
        run_tests_fn=tests,
        open_pr_fn=open_pr,
    )
    assert r.ok is True
    assert state["branch"] and state["applied"] and state["pr"]
    assert r.pr_url == state["pr"]
    assert "pr.created" in [e["event"] for e in r.events]
    assert r.to_dict()["merge"] is False
