"""Every trajectory the hourly scheduler may target must be router-loadable.

The scheduler (`.github/workflows/arkadia-engineering-scheduler.yml`) runs the
EngineeringWorker against the trajectory named in `ARKADIA_ENGINEERING_TRAJECTORY`
and fails the job (exit 1) on `FAILED`. A trajectory that does not conform to the
canonical structure (`docs/control-plane/trajectory.schema.json`: top-level
`trajectory` + `moves`) therefore turns the hourly session into a hard failure
instead of a truthful clean stop (`NO_LEGAL_MOVE`). This guard loads every
candidate trajectory through the router's own loader, so a structural slip fails
CI rather than the scheduler.

The negative control proves the check can detect the defect it claims to detect:
a trajectory that nests `moves` under `trajectory` must be rejected.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from weaver.engineering_router import _load_yaml, select_next_move


ROOT = Path(__file__).resolve().parents[1]
CONTROL_PLANE = ROOT / "docs/control-plane"
SCHEDULER_WORKFLOW = ROOT / ".github/workflows/arkadia-engineering-scheduler.yml"
TRAJECTORY_ENV_RE = re.compile(
    r"^\s*ARKADIA_ENGINEERING_TRAJECTORY:\s*(\S+)\s*$", re.MULTILINE
)


def _scheduler_trajectory() -> Path:
    """The trajectory the live scheduler actually routes to, read from the workflow."""
    text = SCHEDULER_WORKFLOW.read_text(encoding="utf-8")
    match = TRAJECTORY_ENV_RE.search(text)
    assert match, "scheduler workflow does not set ARKADIA_ENGINEERING_TRAJECTORY"
    return ROOT / match.group(1)


def _candidate_trajectories() -> list[Path]:
    return sorted(CONTROL_PLANE.glob("TRAJECTORY-*.yaml"))


def test_scheduler_names_a_tracked_trajectory():
    traj = _scheduler_trajectory()
    assert traj.is_file(), f"scheduler targets a missing trajectory: {traj}"


def test_candidates_are_discovered():
    assert _candidate_trajectories(), "no TRAJECTORY-*.yaml found to validate"


@pytest.mark.parametrize("path", _candidate_trajectories(), ids=lambda p: p.name)
def test_candidate_trajectory_is_router_loadable(path: Path):
    # _load_yaml raises ValueError('invalid trajectory structure') on a structural
    # slip; the router must never receive a trajectory it cannot load.
    data = _load_yaml(path)
    assert isinstance(data.get("trajectory"), dict)
    assert isinstance(data.get("moves"), list) and data["moves"]


@pytest.mark.parametrize("path", _candidate_trajectories(), ids=lambda p: p.name)
def test_candidate_moves_carry_required_fields(path: Path):
    data = _load_yaml(path)
    for move in data["moves"]:
        assert move.get("id"), f"{path.name}: move missing id"
        assert move.get("name"), f"{path.name}: {move.get('id')} missing name"
        assert move.get("status"), f"{path.name}: {move.get('id')} missing status"
        spec = move.get("spec")
        assert spec, f"{path.name}: {move.get('id')} missing spec"
        assert (ROOT / spec).is_file(), f"{path.name}: spec not found: {spec}"


@pytest.mark.parametrize("path", _candidate_trajectories(), ids=lambda p: p.name)
def test_router_never_fails_on_candidate(path: Path):
    """The router must return a decision, not raise, for a scheduled trajectory."""
    data = _load_yaml(path)
    move, blockers = select_next_move(data)
    assert move is None or move.get("id")
    assert isinstance(blockers, list)


def test_scheduler_trajectory_resolves_without_structural_failure():
    """The live scheduler target must load and route (clean stop allowed)."""
    data = _load_yaml(_scheduler_trajectory())
    move, _ = select_next_move(data)
    if move is not None:
        assert move.get("id")


def test_negative_control_nested_moves_is_rejected(tmp_path: Path):
    """A trajectory nesting `moves` under `trajectory` must be rejected."""
    nested = tmp_path / "TRAJECTORY-NESTED.yaml"
    nested.write_text(
        yaml.safe_dump(
            {
                "trajectory": {
                    "id": "NEGATIVE-CONTROL",
                    "status": "authorized-for-review-gated-execution",
                    "moves": [
                        {"id": "X", "name": "x", "status": "pending", "spec": "x.md"}
                    ],
                }
            }
        )
    )
    with pytest.raises(ValueError, match="invalid trajectory structure"):
        _load_yaml(nested)


def test_scheduler_workflow_selects_this_guard():
    """The guard must be selected by the workflow it protects.

    A guard no workflow executes is decoration: the structural slip it detects
    reaches `main` unjudged. The workflow's `pull_request` paths filter must name
    this test file. The guard step itself runs on every event, so removing the
    trigger fails the next hourly session instead of silently disabling the guard.
    """
    workflow = yaml.safe_load(SCHEDULER_WORKFLOW.read_text(encoding="utf-8"))
    # PyYAML parses the bare key `on` as the boolean True.
    trigger = workflow.get(True, workflow.get("on"))
    assert isinstance(trigger, dict) and "pull_request" in trigger, (
        "scheduler workflow has no pull_request trigger; the trajectory-routing "
        "conformance guard would run nowhere and a structural slip would reach "
        "main unjudged"
    )
    paths = (trigger.get("pull_request") or {}).get("paths") or []
    assert "tests/test_scheduler_trajectory_conformance.py" in paths, (
        "the scheduler workflow does not select this guard in its pull_request "
        "paths filter"
    )


def test_scheduler_workflow_executes_the_guard():
    """The guard must be executed by a step, not merely triggered."""
    text = SCHEDULER_WORKFLOW.read_text(encoding="utf-8")
    assert "pytest tests/test_scheduler_trajectory_conformance.py" in text, (
        "scheduler workflow does not execute the trajectory-routing guard"
    )
