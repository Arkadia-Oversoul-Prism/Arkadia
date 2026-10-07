"""A clean stop and a blocked frontier must not share one representation.

`select_next_move` signals "no move" with blockers in both cases, so downstream
salience cannot tell them apart from the status alone:

* a trajectory with nothing left to route is a **clean stop** — the scheduler treats
  `NO_LEGAL_MOVE` as success and the loop must stay quiet;
* a trajectory that still carries a frontier the session could not route (an
  unrecognized move status, a missing spec, an invalid authorization) is a **blocked
  frontier** — the stop must reach the sovereign.

Because the router returned a fallback string *as* a blocker for the clean stop, the
attention builder's non-empty-blockers test pushed it, turning every idle hourly
session into a HIGH `WEAVER_BLOCKED`. PR #329 recorded this as a strict xfail and
declared the router contract a separate bounded workstream; this file is that
workstream's guard.

The load-bearing distinction is `CLEAN_STOP_BLOCKER`: a clean stop is the sentinel and
nothing else. The negative control feeds the pre-fix rule (non-empty blockers) the
clean-stop result and asserts it *would* misfile it, so the guard cannot be satisfied
by a detector that flags nothing.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from weaver.attention_bus import _engineering_result_is_blocked
from weaver.engineering_router import CLEAN_STOP_BLOCKER, select_next_move

TRAJECTORY_ENV = "ARKADIA_ENGINEERING_TRAJECTORY"
CONTROL_PLANE = Path("docs/control-plane")


def _traj(moves: list[dict]) -> dict:
    return {
        "trajectory": {
            "id": "TEST-CLEAN-STOP",
            "status": "authorized-for-review-gated-execution",
        },
        "moves": moves,
    }


# ── router contract ─────────────────────────────────────────────────────────


def test_terminal_only_trajectory_reports_only_the_clean_stop_sentinel():
    """Nothing left to route is a clean stop, named by the sentinel and nothing else."""
    move, blockers = select_next_move(_traj([{"id": "DONE", "status": "completed"}]))
    assert move is None
    assert blockers == [CLEAN_STOP_BLOCKER]


def test_unrecognized_frontier_is_not_a_clean_stop():
    """An unrecognized move status is a defect, not an absence of work."""
    move, blockers = select_next_move(
        _traj([{"id": "A", "status": "merged_acceptance_pending", "spec": "s.md"}])
    )
    assert move is None
    joined = " ".join(blockers)
    assert "unrecognized move status" in joined
    assert CLEAN_STOP_BLOCKER not in blockers


def test_missing_spec_is_not_a_clean_stop():
    """A recognized active move with no spec is an unroutable frontier, not a clean stop."""
    _, blockers = select_next_move(_traj([{"id": "A", "status": "pending"}]))
    assert CLEAN_STOP_BLOCKER not in blockers
    assert any("scope/spec missing" in b for b in blockers)


def test_recognized_active_move_still_routes():
    """Positive control: the distinction must not disturb ordinary routing."""
    move, _ = select_next_move(
        _traj([{"id": "A", "status": "in_progress", "spec": "s.md", "depends_on": []}])
    )
    assert move is not None and move["id"] == "A"


# ── attention classification of the sentinel ────────────────────────────────


def test_clean_stop_result_is_classified_not_blocked():
    assert _engineering_result_is_blocked(
        {"status": "NO_LEGAL_MOVE", "blockers": [CLEAN_STOP_BLOCKER]}
    ) is False


def test_unroutable_result_is_classified_blocked():
    assert _engineering_result_is_blocked(
        {"status": "NO_LEGAL_MOVE", "blockers": ["unrecognized move status: A ('x')"]}
    ) is True


def test_mixed_blockers_are_blocked():
    """A sentinel alongside a real blocker is still a real boundary."""
    assert _engineering_result_is_blocked(
        {"status": "NO_LEGAL_MOVE", "blockers": [CLEAN_STOP_BLOCKER, "A: missing dependency B"]}
    ) is True


# ── the composition seam (worker → event), end to end ───────────────────────


def _write_trajectory(root: Path, moves: list[dict]) -> Path:
    spec = root / "spec.md"
    spec.write_text("# synthetic move spec\n", encoding="utf-8")
    for move in moves:
        move.setdefault("name", move["id"])
        move.setdefault("spec", "spec.md")
    path = root / "TRAJECTORY-SYNTHETIC.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "trajectory": {
                    "id": "TEST-CLEAN-STOP",
                    "status": "authorized-for-review-gated-execution",
                },
                "moves": moves,
            }
        ),
        encoding="utf-8",
    )
    return path


def _run_worker(monkeypatch: pytest.MonkeyPatch, root: Path, trajectory: Path) -> dict:
    from weaver.engineering_worker import EngineeringWorker

    monkeypatch.setenv(TRAJECTORY_ENV, str(trajectory))
    worker = EngineeringWorker(repo_root=str(root), session_id="clean-stop-test", dry_run=True)
    return worker.run()


def test_clean_completion_stays_quiet_through_the_worker(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The healthy end of the loop must not alert — the hourly loop runs every hour."""
    result = _run_worker(
        monkeypatch, tmp_path, _write_trajectory(tmp_path, [{"id": "DONE", "status": "completed"}])
    )
    assert result["status"] == "NO_LEGAL_MOVE"
    assert result["blockers"] == [CLEAN_STOP_BLOCKER]

    event = result["attention_event"]
    assert event["event_type"] == "WEAVER_STATE_CHANGED"
    assert event["severity"] == "INFO"
    assert event["action_required"] is False
    assert "push" not in result["attention_delivery_plan"]["channels"]


def test_unroutable_frontier_reaches_the_sovereign_through_the_worker(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The unroutable stop must be composed into a pushed HIGH block, not filed as INFO."""
    result = _run_worker(
        monkeypatch,
        tmp_path,
        _write_trajectory(
            tmp_path, [{"id": "F-A", "status": "merged_acceptance_pending"}]
        ),
    )
    assert result["status"] == "NO_LEGAL_MOVE"
    assert any("unrecognized move status" in b for b in result["blockers"])

    event = result["attention_event"]
    assert event["event_type"] == "WEAVER_BLOCKED"
    assert event["severity"] == "HIGH"
    assert event["action_required"] is True
    assert "push" in result["attention_delivery_plan"]["channels"]


# ── negative control ────────────────────────────────────────────────────────


def test_negative_control_nonempty_blockers_rule_would_misfile_the_clean_stop():
    """The pre-fix rule (non-empty blockers) classified the clean stop as blocked.

    If this ever stops holding, the repair has been reverted and every idle hourly
    session pushes a false alert.
    """
    clean_stop = {"status": "NO_LEGAL_MOVE", "blockers": [CLEAN_STOP_BLOCKER]}
    pre_fix_is_blocked = bool(clean_stop["blockers"])  # the rule before this change
    assert pre_fix_is_blocked is True
    assert _engineering_result_is_blocked(clean_stop) is False


def test_guard_is_selected_by_a_workflow_that_runs_the_whole_suite():
    """A guard no workflow executes is decoration.

    `weaver/engineering_router.py` and `weaver/attention_bus.py` are judged by any
    workflow that runs the whole suite and is selected by a `weaver/**` path filter.
    """
    workflows = Path(__file__).resolve().parents[1] / ".github" / "workflows"
    for path in sorted(workflows.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        if "pytest tests/ -q" not in text:
            continue
        workflow = yaml.safe_load(text)
        # PyYAML parses the bare key `on` as the boolean True.
        trigger = workflow.get(True, workflow.get("on")) or {}
        pr_paths = set((trigger.get("pull_request") or {}).get("paths") or [])
        if "weaver/**" in pr_paths:
            return
    pytest.fail(
        "no workflow runs the whole test suite and is selected by 'weaver/**'; a "
        "change to weaver/engineering_router.py would not execute this guard"
    )
