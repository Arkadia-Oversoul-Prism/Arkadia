"""Regression tests for truthful blocked-versus-clean-stop reporting."""
from __future__ import annotations

from pathlib import Path

from weaver.engineering_router import CLEAN_STOP_BLOCKER, EngineeringRouter, select_next_move


def test_schema_only_status_is_named_and_not_reported_as_clean_stop():
    trajectory = {
        "trajectory": {"id": "TEST", "status": "authorized-for-review-gated-execution"},
        "moves": [
            {"id": "G12-A", "name": "capture", "status": "merged_acceptance_pending", "depends_on": [], "spec": "spec-a.md"},
            {"id": "G12-B", "name": "queue", "status": "in_progress", "depends_on": ["G12-A"], "spec": "spec-b.md"},
        ],
    }

    move, blockers = select_next_move(trajectory)

    assert move is None
    joined = " ".join(blockers)
    assert "unrecognized move status" in joined
    assert "G12-A" in joined and "merged_acceptance_pending" in joined
    assert "dependency-blocked frontier" in joined and "G12-B" in joined
    assert "no legal pending move" not in joined


def test_clean_stop_and_blocked_route_have_distinct_statuses(tmp_path: Path):
    accepted = tmp_path / "accepted.yaml"
    accepted.write_text(
        "trajectory:\n  id: TEST\n  status: authorized-for-review-gated-execution\n"
        "moves:\n  - id: DONE\n    name: done\n    status: accepted\n    spec: spec.md\n",
        encoding="utf-8",
    )
    blocked = tmp_path / "blocked.yaml"
    blocked.write_text(
        "trajectory:\n  id: TEST\n  status: authorized-for-review-gated-execution\n"
        "moves:\n  - id: WAIT\n    name: wait\n    status: merged_acceptance_pending\n    spec: spec.md\n",
        encoding="utf-8",
    )

    clean_result = EngineeringRouter(repo_root=tmp_path, session_id="clean", dry_run=True, trajectory_path=accepted).run()
    blocked_result = EngineeringRouter(repo_root=tmp_path, session_id="blocked", dry_run=True, trajectory_path=blocked).run()

    assert clean_result["status"] == "NO_LEGAL_MOVE"
    assert clean_result["blockers"] == [CLEAN_STOP_BLOCKER]
    assert blocked_result["status"] == "BLOCKED"
    assert any("unrecognized move status" in item for item in blocked_result["blockers"])
