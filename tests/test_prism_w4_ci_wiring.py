"""Workstream 4 — the read-surface guards must actually execute in CI.

`tests/test_ci_suite_collection_continuation.py` established the class: a guard no
workflow executes is decoration. It repaired the *aborting* form (a bare
`pytest tests/` that interrupts at the CE-01 collection error, so the suite runs
zero tests). This module states the adjacent, still-open invariant for the
Workstream 4 read surfaces:

1. **Every Workstream 4 guard file is executed by some workflow, and by a step
   that can fail.** The `sg-02-fe-2-v.yml` `validate` job runs `pytest tests/ -q`
   in a `continue-on-error: true` step, which *interrupts* at the CE-01 collection
   error — measured in the live run `38145078942` log: `Interrupted: 1 error during
   collection`, `1 skipped, 1 error in 6.24s`. So that step executes **none** of
   these files. A dedicated judging step is what makes them execute.
2. **The workflow that executes them is selected by them.** A step that runs a
   file the trigger filter does not name is a step a change to that file never
   reaches.
3. **A step that executes the redaction guard must not be skippable by
   environment.** The `lab/overview` projection tests execute a real `.ts` module
   under Node and skip when Node cannot strip TypeScript. If CI's Node were too
   old, the credential-redaction guard would silently skip while the job stayed
   green. The workflow's Node version is therefore asserted, not assumed.

Detectors are proven against the forms they must catch (negative controls), so a
rewrite of the workflow cannot disarm the invariant without reddening a control.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
CP10 = WORKFLOWS / "sg-02-fe-2-v.yml"

# The Workstream 4 read-surface guards. Discovered, not restated: any test file
# matching these prefixes is in scope, so a new slice is judged by the same rule.
GUARD_GLOBS = (
    "tests/test_prism_w4_*.py",
    "tests/test_lab_run_trace_contract.py",
    "tests/test_lab_model_gateway_contract.py",
    "tests/test_lab_overview_contract.py",
)

# Native TypeScript stripping landed unflagged in node 23.6; 24.x is set up in CI.
MIN_NODE = (23, 6)

# The CE-01 collection error that makes a bare `pytest tests/` abort. Cited so the
# reason this wiring exists is legible at the point of failure.
COLLECTION_ABORT = "--continue-on-collection-errors"


def guard_files() -> list[Path]:
    found: set[Path] = set()
    for pattern in GUARD_GLOBS:
        found.update(ROOT.glob(pattern))
    return sorted(found)


def _workflow(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _triggers(path: Path) -> dict:
    workflow = _workflow(path)
    # PyYAML parses the bare key `on` as the boolean True.
    trigger = workflow.get(True, workflow.get("on")) or {}
    return trigger if isinstance(trigger, dict) else {}


def _steps(path: Path) -> list[dict]:
    steps: list[dict] = []
    for job in (_workflow(path).get("jobs") or {}).values():
        if isinstance(job, dict):
            steps.extend(s for s in (job.get("steps") or []) if isinstance(s, dict))
    return steps


def _judging_steps_running(path: Path, target: str) -> list[dict]:
    """Steps that invoke pytest on *target* and whose result can fail the job."""
    hits: list[dict] = []
    for step in _steps(path):
        run = step.get("run") or ""
        if "pytest" not in run or target not in run:
            continue
        if step.get("continue-on-error") is True:
            continue
        hits.append(step)
    return hits


def _workflows_running(target: str) -> list[Path]:
    return [p for p in sorted(WORKFLOWS.glob("*.yml")) if _judging_steps_running(p, target)]


# ---------------------------------------------------------------------------
# 1. Every guard file is executed by a judging step somewhere
# ---------------------------------------------------------------------------


def test_there_are_guard_files_to_wire():
    """Sanity: the discovery globs match the slice's own guards."""
    names = {p.name for p in guard_files()}
    assert "test_prism_w4_lab_overview.py" in names
    assert "test_lab_overview_contract.py" in names
    assert len(names) >= 6, f"expected the Workstream 4 guards, found {sorted(names)}"


@pytest.mark.parametrize("guard", guard_files(), ids=lambda p: p.name)
def test_guard_is_executed_by_a_judging_step(guard: Path):
    """A guard that no workflow executes cannot gate anything."""
    workflows = _workflows_running(guard.name)
    assert workflows, (
        f"{guard.name} is executed by no workflow step that can fail. The "
        f"sg-02-fe-2-v.yml `pytest tests/ -q` step runs under "
        f"continue-on-error and aborts at the CE-01 collection error "
        f"(run 38145078942: 'Interrupted: 1 error during collection'), so it "
        f"executes none of these files. Wire the guard into a judging step."
    )


def test_the_wired_step_is_a_judging_step_not_a_reporting_one():
    """The executing step must be able to fail, or it enforces nothing."""
    steps = _steps(CP10)
    wired = [s for s in steps if "test_prism_w4_lab_overview.py" in (s.get("run") or "")]
    assert wired, "the overview guard is not referenced by the CP10 workflow"
    for step in wired:
        assert step.get("continue-on-error") is not True, (
            f"step {step.get('name')!r} runs the redaction guard but cannot fail"
        )


def test_the_enforcement_step_asserts_the_wired_step():
    """A judging step that nothing asserts is still advisory.

    The `Enforce CP10 executable gates` step tests each step's outcome. The new
    step must be among them, and the assertion must name a step that exists.
    """
    enforce = [
        s for s in _steps(CP10) if "Enforce" in (s.get("name") or "")
    ]
    assert enforce, "the CP10 enforcement step is gone"
    run = "\n".join(s.get("run") or "" for s in enforce)

    ids = {s.get("id") for s in _steps(CP10) if s.get("id")}
    asserted = set(re.findall(r"steps\.([A-Za-z0-9_]+)\.outcome", run))
    missing = asserted - ids
    assert not missing, f"the enforcement step asserts non-existent step ids: {sorted(missing)}"

    wired_ids = {
        s.get("id")
        for s in _steps(CP10)
        if "test_prism_w4_lab_overview.py" in (s.get("run") or "")
    }
    assert wired_ids, "the wired step has no id, so its outcome cannot be asserted"
    assert wired_ids <= asserted, (
        f"the step(s) {sorted(wired_ids)} run the guards but no enforcement "
        f"assertion references them; the step's failure would not fail the job"
    )


# ---------------------------------------------------------------------------
# 2. The executing workflow is selected by the files it executes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("guard", guard_files(), ids=lambda p: p.name)
def test_the_executing_workflow_is_triggered_by_that_guard(guard: Path):
    """A change to a guard must reach the workflow that judges it."""
    rel = guard.relative_to(ROOT).as_posix()
    directory = guard.parent.relative_to(ROOT).as_posix()
    for path in _workflows_running(guard.name):
        triggers = _triggers(path)
        for event in ("push", "pull_request"):
            paths = (triggers.get(event) or {}).get("paths") or []
            assert any(
                entry in (rel, guard.name, directory, f"{directory}/**")
                for entry in paths
            ), (
                f"{path.name} runs {guard.name} on {event} but its {event} path "
                f"filter does not select it; a change to the guard would not run "
                f"the workflow that judges it"
            )


def test_cp10_trigger_filters_stay_symmetric():
    """An asymmetric filter lets a PR introduce a surface unjudged."""
    triggers = _triggers(CP10)
    push = set((triggers.get("push") or {}).get("paths") or [])
    pull = set((triggers.get("pull_request") or {}).get("paths") or [])
    assert push == pull, f"filters diverge; only in one: {sorted(push ^ pull)}"


# ---------------------------------------------------------------------------
# 3. The redaction guard cannot be skipped by the environment
# ---------------------------------------------------------------------------


def test_the_ci_node_version_can_strip_typescript():
    """Otherwise the projection tests skip and the redaction guard is unenforced.

    `labOverview.ts` is executed directly as a module, which needs native
    TypeScript stripping. `_node()` skips below that version rather than reporting
    a false defect, so the workflow's Node version is the thing that decides
    whether the guard runs at all.
    """
    versions = [
        str(step["with"]["node-version"])
        for step in _steps(CP10)
        if "setup-node" in str(step.get("uses", ""))
    ]
    assert versions, "the CP10 job no longer sets up Node"
    majors = []
    for version in versions:
        match = re.match(r"(\d+)", version)
        assert match, f"unparsed node version {version!r}"
        majors.append(int(match.group(1)))
    assert min(majors) >= MIN_NODE[0], (
        f"CP10 sets up node {versions}; below {MIN_NODE[0]}.{MIN_NODE[1]} the "
        f"projection tests skip and the credential-redaction guard never runs"
    )


def test_the_projection_guard_states_its_node_requirement():
    """The skip must name its requirement, not fail opaquely."""
    source = (ROOT / "tests" / "test_prism_w4_lab_overview.py").read_text(encoding="utf-8")
    assert "23.6" in source or "23, 6" in source, (
        "the node version requirement is not stated in the guard that depends on it"
    )


# ---------------------------------------------------------------------------
# Negative controls — the detectors must fire on the forms they exist to catch
# ---------------------------------------------------------------------------


def test_negative_control_a_continue_on_error_step_is_not_counted_as_judging():
    """The reporting step must not satisfy the invariant."""
    polluted = {
        "jobs": {
            "j": {
                "steps": [
                    {
                        "name": "CP10-B broader backend regression",
                        "continue-on-error": True,
                        "run": "python -m pytest tests/ -q 2>&1 | tee cp10-backend.log",
                    }
                ]
            }
        }
    }
    # Re-use the real predicate against a synthetic workflow, via a temp file.
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "synthetic.yml"
        path.write_text(yaml.safe_dump(polluted), encoding="utf-8")
        assert _judging_steps_running(path, "tests/") == []
        assert _judging_steps_running(path, "test_prism_w4_lab_overview.py") == []


def test_negative_control_an_unwired_guard_is_reported():
    """A guard named by no workflow must be reported, not silently accepted."""
    assert _workflows_running("test_prism_w4_definitely_not_wired.py") == []


def test_negative_control_the_enforcement_assertion_detector_sees_a_missing_id():
    """The step-id detector must flag an assertion naming a step that does not exist."""
    ids = {"backend", "w4_surfaces"}
    run = "test '${{ steps.nonexistent_step.outcome }}' = success"
    asserted = set(re.findall(r"steps\.([A-Za-z0-9_]+)\.outcome", run))
    assert asserted - ids == {"nonexistent_step"}
