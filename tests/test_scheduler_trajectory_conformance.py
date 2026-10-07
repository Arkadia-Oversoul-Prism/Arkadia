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

import json
import re
import subprocess
import sys
import textwrap
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


# --- session report truthfulness ----------------------------------------------------
#
# The hourly stop must be legible, not merely non-blank. `Status: NO_LEGAL_MOVE` with
# an empty `Move:` says the session did not proceed; the router's `blockers` say why
# (e.g. "unrecognized move status: G12-A ('merged_acceptance_pending')"). Those live
# only in `engineering-session-result.json`, and with attention delivery unconfigured
# the run log is the sole human-readable artifact. Observed live: run 37523927861
# reported a clean stop while its session result named two unroutable frontier moves,
# so a live frontier read as "nothing to do".
#
# The detector is pure and the negative control feeds it the pre-fix report body, so
# the guard cannot be disarmed by reverting the report step to echo-only.


def _report_step(workflow):
    for job in (workflow.get("jobs") or {}).values():
        if not isinstance(job, dict):
            continue
        for step in job.get("steps") or []:
            if step.get("name") == "Session report":
                yield step


_REPORT_HEREDOC_RE = re.compile(
    r"python - << 'PY'\n(.*?)\n\s*PY\s*$", re.DOTALL | re.MULTILINE
)


def _report_program(script: str) -> str | None:
    """The blockers program embedded in the report step, or None if absent."""
    match = _REPORT_HEREDOC_RE.search(script)
    if not match:
        return None
    return textwrap.dedent(match.group(1))


def _report_names_blockers(script: str) -> bool:
    """True iff the report step reads the session result and prints its blockers."""
    program = _report_program(script)
    if program is None:
        return False
    return "engineering-session-result.json" in program and "blockers" in program


def _live_report_step() -> dict:
    workflow = yaml.safe_load(SCHEDULER_WORKFLOW.read_text(encoding="utf-8"))
    steps = list(_report_step(workflow))
    assert len(steps) == 1, "expected exactly one 'Session report' step"
    return steps[0]


def _run_report_program(program: str, cwd: Path) -> str:
    proc = subprocess.run(
        [sys.executable, "-c", program], cwd=cwd, capture_output=True, text=True
    )
    assert proc.returncode == 0, f"report program failed:\n{proc.stderr}"
    return proc.stdout


def test_session_report_runs_even_after_a_failure_exit():
    """The report must execute on the FAILED orientation it exists to explain."""
    step = _live_report_step()
    assert step.get("if") == "always()", (
        "the session report is not gated on always(); a FAILED session aborts the "
        "runner step and the report would not run to name the cause"
    )


def test_session_report_surfaces_router_blockers(tmp_path: Path):
    """The report must print the router's blockers, not just the status."""
    step = _live_report_step()
    program = _report_program(step.get("run") or "")
    assert program, "the session report no longer embeds a blockers program"

    blocker = (
        "unrecognized move status: G12-A ('merged_acceptance_pending'), "
        "G12-C ('merged_acceptance_pending') \u2014 cannot route"
    )
    (tmp_path / "engineering-session-result.json").write_text(
        json.dumps({"status": "NO_LEGAL_MOVE", "blockers": [blocker]}),
        encoding="utf-8",
    )

    out = _run_report_program(program, tmp_path)
    assert blocker in out, f"report did not name the blocker:\n{out}"
    assert "Blockers:" in out


def test_session_report_states_an_absent_session_result(tmp_path: Path):
    """On a pull_request the runner step is skipped; the report must still run."""
    step = _live_report_step()
    program = _report_program(step.get("run") or "")
    out = _run_report_program(program, tmp_path)  # no session result written
    assert "unavailable" in out.lower(), out


def test_negative_control_pre_fix_report_is_silent():
    """The pre-fix echo-only report must be reported as not naming blockers."""
    pre_fix = (
        'echo "=== ARKADIA ENGINEERING SESSION ==="\n'
        'echo "SHA:    ${{ steps.sha.outputs.sha }}"\n'
        'echo "Status: ${{ steps.runner.outputs.status }}"\n'
        'echo "Move:   ${{ steps.runner.outputs.move }}"\n'
        'echo "Merge:  FORBIDDEN"\n'
    )
    assert not _report_names_blockers(pre_fix), (
        "the detector does not flag the pre-fix echo-only report; it cannot detect "
        "the silent-stop defect it claims to detect"
    )
    assert _report_names_blockers(_live_report_step().get("run") or "")


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
