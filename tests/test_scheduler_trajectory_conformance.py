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


# --- PR-safety invariants for the scheduler workflow -------------------------------
#
# The follow-on gave the scheduler a `pull_request` trigger, which widened the
# workflow's blast radius. The two safety properties the workflow documents in
# comments must be enforced, not merely stated: the token stays read-only, and a PR
# is never routed as a live engineering session. Each property has a pure detector
# with a negative control, so the guard cannot be disarmed by editing the workflow
# without reddening a control.


def _non_read_scopes(perms) -> set[str]:
    """Scopes that grant more than read. An unset token defaults to write."""
    if not isinstance(perms, dict):
        return {"<unset: defaults to write>"}
    return {f"{key}: {value}" for key, value in perms.items() if value != "read"}


def _session_steps(workflow):
    for job in (workflow.get("jobs") or {}).values():
        if not isinstance(job, dict):
            continue
        for step in job.get("steps") or []:
            if "EngineeringWorker" in (step.get("run") or ""):
                yield step


def _ungated_session_steps(workflow) -> list:
    return [
        step
        for step in _session_steps(workflow)
        if step.get("if") != "github.event_name != 'pull_request'"
    ]


def test_scheduler_pr_trigger_holds_a_read_only_token():
    """A `pull_request`-triggered job must not hold a write token."""
    workflow = yaml.safe_load(SCHEDULER_WORKFLOW.read_text(encoding="utf-8"))
    for job_name, job in (workflow.get("jobs") or {}).items():
        assert not _non_read_scopes(job.get("permissions")), (
            f"job {job_name!r} holds a non-read token but the workflow runs on "
            f"pull_request; a PR-triggered job must stay read-only"
        )


def test_scheduler_session_is_not_routed_on_pull_request():
    """The EngineeringWorker must never run for a `pull_request` event."""
    workflow = yaml.safe_load(SCHEDULER_WORKFLOW.read_text(encoding="utf-8"))
    steps = list(_session_steps(workflow))
    assert len(steps) == 1, "expected exactly one session step to gate"
    assert not _ungated_session_steps(workflow), (
        "the session step is not gated to non-pull_request events; a PR could be "
        "routed as a live engineering session"
    )


def test_negative_control_read_only_detector_flags_write():
    assert _non_read_scopes({"contents": "write"}) == {"contents: write"}
    assert _non_read_scopes(None)  # unset defaults to write
    assert _non_read_scopes({"contents": "read", "actions": "read"}) == set()


def test_negative_control_session_gate_detector_flags_ungated():
    ungated = {
        "jobs": {
            "engineering-scheduler": {
                "steps": [
                    {
                        "name": "Session",
                        "run": "from weaver.engineering_worker import EngineeringWorker",
                    }
                ]
            }
        }
    }
    assert _ungated_session_steps(ungated), "detector failed to flag an ungated session"
    gated = {
        "jobs": {
            "engineering-scheduler": {
                "steps": [
                    {
                        "name": "Session",
                        "if": "github.event_name != 'pull_request'",
                        "run": "from weaver.engineering_worker import EngineeringWorker",
                    }
                ]
            }
        }
    }
    assert not _ungated_session_steps(gated)


# --- the session's failure path must still report the outcome -----------------------
#
# `Session + Engineering Runner` writes `status`/`move` to `$GITHUB_OUTPUT` *after* the
# `sys.exit(1)` guard, so on a `FAILED` orientation the job dies before those outputs are
# written. The `if: always()` "Session report" step then interpolates `steps.runner.outputs.*`
# — which are empty — and prints `Status:` / `Move:` with nothing after them.
#
# Observed in the live hourly session (`run 37379043890`, `main` @ `451e41a3`, 2026-10-05):
# the report step printed the repository SHA and the `FORBIDDEN` lines, but `Status:` and
# `Move:` were blank, while the failure itself was real (`invalid trajectory structure`).
# The one step whose job is to summarise the session was silent about why it stopped — the
# same "the stop must be visible" defect class the worker→attention seam guard pins one
# layer up.
#
# These tests assert the ordering invariant (nothing may exit before the outputs are
# written) and pin a negative control for the detector, so a reordering that reintroduces
# the silent failure reddens CI instead of shipping.


def _session_step(workflow):
    steps = list(_session_steps(workflow))
    assert len(steps) == 1, "expected exactly one session step"
    return steps[0]


def _reports_status_before_exiting(script: str) -> bool:
    """Whether every `$GITHUB_OUTPUT` write precedes the earliest failure exit.

    A `run:` block executes with `bash -e`, so an `exit 1` aborts the step; any
    `$GITHUB_OUTPUT` write after it never lands, and the `if: always()` report step
    interpolates an empty value. Two things keep the detector measuring the decision
    rather than the prose around it: comments are dropped (a comment mentioning
    `exit 1` is not a failure path), and the anchor is the output write itself, not a
    `status=` substring that also appears in a `::notice::` print.
    """
    code = "\n".join(
        line for line in script.splitlines() if not line.lstrip().startswith("#")
    )
    output_writes = [m.start() for m in re.finditer(r"GITHUB_OUTPUT", code)]
    exits = [m.start() for m in re.finditer(r"\bexit\s*\(?\s*1\s*\)?", code)]
    if not output_writes:
        return False
    if not exits:
        return True
    return min(exits) >= max(output_writes)


def test_negative_control_output_ordering_detector_flags_exit_before_write():
    silent = (
        'if bad:\n    sys.exit(1)\n'
        'with open(os.environ["GITHUB_OUTPUT"], "a") as fh:\n    fh.write(f"status=X\\n")\n'
    )
    assert not _reports_status_before_exiting(silent)
    ordered = (
        'with open(os.environ["GITHUB_OUTPUT"], "a") as fh:\n    fh.write(f"status=X\\n")\n'
        'if bad:\n    sys.exit(1)\n'
    )
    assert _reports_status_before_exiting(ordered)
    assert not _reports_status_before_exiting("print('no outputs written at all')\n")


def test_negative_control_output_ordering_detector_ignores_comments():
    """A comment mentioning `exit 1` is not a failure path."""
    prose = (
        "# an exit 1 here would abort the step\n"
        'with open(os.environ["GITHUB_OUTPUT"], "a") as fh:\n    fh.write("status=X\\n")\n'
    )
    assert _reports_status_before_exiting(prose)


def test_session_reports_status_and_move_before_any_failure_exit():
    """A failing session must still publish `status`/`move` for the report step."""
    workflow = yaml.safe_load(SCHEDULER_WORKFLOW.read_text(encoding="utf-8"))
    script = _session_step(workflow)["run"]
    assert _reports_status_before_exiting(script), (
        "the session step exits before writing status/move to $GITHUB_OUTPUT; on a FAILED "
        "orientation the `if: always()` report step interpolates empty values and prints a "
        "blank Status/Move, hiding the reason the hourly session stopped"
    )
    assert "status=" in script and "move=" in script

