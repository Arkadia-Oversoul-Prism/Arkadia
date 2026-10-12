"""Regression tests for merged-but-not-accepted trajectory states."""
from __future__ import annotations

from weaver.engineering_router import select_next_move


def test_merged_acceptance_pending_is_a_named_human_gate_not_unknown_status():
    trajectory = {
        "trajectory": {"id": "TEST", "status": "authorized-for-review-gated-execution"},
        "moves": [
            {"id": "G12-A", "name": "capture", "status": "merged_acceptance_pending", "depends_on": [], "spec": "spec-a.md"},
            {"id": "G12-B", "name": "queue", "status": "in_progress", "depends_on": ["G12-A"], "spec": "spec-b.md"},
        ],
    }

    move, blockers = select_next_move(trajectory)

    assert move is None
    assert any("G12-A: merged work awaits human acceptance evidence" in item for item in blockers)
    assert any("dependency-blocked frontier" in item and "G12-B" in item for item in blockers)
    assert not any("unrecognized move status" in item for item in blockers)


def test_clean_stop_is_distinct_from_a_human_acceptance_blocker():
    from weaver.engineering_router import CLEAN_STOP_BLOCKER

    clean, clean_blockers = select_next_move({
        "trajectory": {"id": "TEST", "status": "authorized-for-review-gated-execution"},
        "moves": [
            {"id": "DONE", "name": "done", "status": "accepted", "depends_on": [], "spec": "spec.md"}
        ],
    })
    blocked, blocked_blockers = select_next_move({
        "trajectory": {"id": "TEST", "status": "authorized-for-review-gated-execution"},
        "moves": [
            {"id": "WAIT", "name": "wait", "status": "merged_acceptance_pending", "depends_on": [], "spec": "spec.md"}
        ],
    })

    assert clean is None
    assert clean_blockers == [CLEAN_STOP_BLOCKER]
    assert blocked is None
    assert any("human acceptance evidence" in item for item in blocked_blockers)
    assert blocked_blockers != [CLEAN_STOP_BLOCKER]
