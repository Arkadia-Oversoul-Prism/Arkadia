"""Router truthfulness: an unrecognized move status must be named, never skipped.

`select_next_move` treats a move whose status it does not recognize as absent work
and moves on. When the skipped move *is* the frontier, the session reports
`NO_LEGAL_MOVE` with the fallback reason "all complete or dependencies unresolved"
— a claim that is false, and one that hides the real cause from the operator and
from the next wake.

Observed on `main` after PR #319 lifted `moves` to the top level of
`TRAJECTORY-CONSOLE-COMPLETION-01.yaml`: `G12-B` sits at `in_progress` (recognized)
but its siblings `G12-A`/`G12-C` sit at `merged_acceptance_pending`, which the
router did not know. The router silently dropped them and could not explain itself.

These tests pin the invariant on synthetic trajectories so they hold regardless of
the live trajectories' completion state. The negative control proves the guard can
detect the defect it claims to detect: a detector that always reported the
fallback message, or one that always reported "unrecognized", would fail here.
"""
from __future__ import annotations

import yaml

from weaver.engineering_router import (
    ACTIVE_STATUSES,
    TERMINAL_DONE,
    _load_yaml,
    select_next_move,
)


def _traj(moves: list[dict]) -> dict:
    return {
        "trajectory": {
            "id": "TEST-ROUTER-STATUS",
            "status": "authorized-for-review-gated-execution",
        },
        "moves": moves,
    }


def test_status_vocabularies_are_disjoint():
    """A status cannot be both active and terminal."""
    assert ACTIVE_STATUSES.isdisjoint(TERMINAL_DONE)


def test_unrecognized_status_is_reported_not_silently_skipped():
    move, blockers = select_next_move(
        _traj([{"id": "A", "status": "merged_acceptance_pending", "spec": "s.md"}])
    )
    assert move is None
    joined = " ".join(blockers)
    assert "unrecognized move status" in joined
    assert "A" in joined and "merged_acceptance_pending" in joined


def test_unrecognized_status_is_not_misreported_as_all_complete():
    """The load-bearing assertion: the fallback reason must not stand in for a defect.

    This is exactly the false claim the pre-fix router emitted for the live console
    trajectory. Reporting "all complete or dependencies unresolved" when a move was
    merely unrecognized is a truthfulness failure, not a cosmetic one.
    """
    _, blockers = select_next_move(
        _traj([{"id": "A", "status": "merged_acceptance_pending", "spec": "s.md"}])
    )
    assert not any("no legal pending move" in b for b in blockers)


def test_every_unrecognized_move_is_named():
    _, blockers = select_next_move(
        _traj(
            [
                {"id": "A", "status": "merged_acceptance_pending", "spec": "s.md"},
                {"id": "B", "status": "awaiting_sovereign", "spec": "s.md"},
            ]
        )
    )
    joined = " ".join(blockers)
    assert "A" in joined and "B" in joined


def test_negative_control_fallback_fires_only_for_genuinely_complete():
    """Positive control: a genuinely terminal-only trajectory keeps the fallback.

    Without this, `test_unrecognized_status_is_not_misreported_as_all_complete`
    would also pass if the router never emitted the fallback at all — the guard
    would be vacuous.
    """
    move, blockers = select_next_move(
        _traj([{"id": "A", "status": "completed", "spec": "s.md"}])
    )
    assert move is None
    assert any("no legal pending move" in b for b in blockers)
    assert not any("unrecognized" in b for b in blockers)


def test_recognized_active_move_is_still_selected():
    """The fix must not disturb ordinary routing."""
    move, blockers = select_next_move(
        _traj([{"id": "A", "status": "in_progress", "spec": "s.md", "depends_on": []}])
    )
    assert move is not None and move["id"] == "A"
    assert not any("unrecognized" in b for b in blockers)


def test_arbitrary_status_never_raises():
    """A malformed status is data, not an exception: the router must still decide."""
    move, blockers = select_next_move(
        _traj([{"id": "A", "status": "?? weird ??", "spec": "s.md"}])
    )
    assert move is None
    assert blockers


def test_guard_is_selected_and_executed_by_a_workflow():
    """A guard no workflow executes is decoration.

    `weaver/engineering_router.py` is not in any other workflow's path filter, so
    this file's workflow is the only surface that can judge the semantics. It must
    appear in both the `push` and `pull_request` filters (a guard absent from the
    pull_request filter is judged by nothing until after the merge) and be executed
    by a step, not merely triggered.
    """
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    workflow_path = root / ".github/workflows/weaver-mvp2-validation.yml"
    text = workflow_path.read_text(encoding="utf-8")
    workflow = yaml.safe_load(text)
    # PyYAML parses the bare key `on` as the boolean True.
    trigger = workflow.get(True, workflow.get("on"))
    assert isinstance(trigger, dict)

    name = "tests/test_engineering_router_status_truthfulness.py"
    for event in ("push", "pull_request"):
        paths = (trigger.get(event) or {}).get("paths") or []
        assert name in paths, f"{event} filter does not select this guard"

    push_paths = (trigger.get("push") or {}).get("paths") or []
    pr_paths = (trigger.get("pull_request") or {}).get("paths") or []
    assert set(push_paths) == set(pr_paths), (
        "push and pull_request filters must be identical, or a PR can introduce "
        "a surface the boundary only judges after merge"
    )

    # Executed, not merely triggered: the test file must be named in a run step.
    assert "Engineering-router status truthfulness guard" in text
    guard_step = text.split("Engineering-router status truthfulness guard", 1)[1]
    assert name in guard_step, "the guard step does not execute this file"


def test_live_scheduler_trajectory_never_silently_skips():
    """The trajectory the hourly scheduler routes to must not skip a move silently.

    Reads the path from the workflow, mirroring the scheduler's own env binding. On a
    revision whose trajectory does not load (the structural slip PR #319 repairs) the
    check skips rather than erroring — loadability is asserted by
    `tests/test_scheduler_trajectory_conformance.py`, not here.
    """
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/arkadia-engineering-scheduler.yml").read_text(
        encoding="utf-8"
    )
    match = re.search(
        r"^\s*ARKADIA_ENGINEERING_TRAJECTORY:\s*(\S+)\s*$", workflow, re.MULTILINE
    )
    assert match, "scheduler workflow does not set ARKADIA_ENGINEERING_TRAJECTORY"
    path = root / match.group(1)
    assert path.is_file(), f"scheduler targets a missing trajectory: {path}"

    try:
        data = _load_yaml(path)
    except ValueError as exc:  # structural slip — see test_scheduler_trajectory_conformance
        import pytest

        pytest.skip(f"live trajectory does not load yet: {exc}")

    move, blockers = select_next_move(data)
    if move is None:
        # Either every move is genuinely terminal, or a defect is named. What must
        # never happen is the fallback reason masking an unrecognized status.
        joined = " ".join(blockers)
        unrecognized_present = any(
            str(m.get("status", "pending")).lower()
            not in ACTIVE_STATUSES | TERMINAL_DONE
            for m in data["moves"]
            if str(m.get("status", "pending")).lower() not in TERMINAL_DONE
        )
        if unrecognized_present:
            assert "unrecognized move status" in joined
            assert not any("no legal pending move" in b for b in blockers)
