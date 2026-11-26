"""A guard no gate executes is decoration -- so the GOV-04 oracle must be wired.

``scripts/gov04_platform_preconditions.py`` is the only surface that decides whether
GOV-04's condition 2 is backed by a platform control. That makes it a governance
input: if it silently stops running, or its own gate can be rewritten without being
judged, the precondition goes back to being unmeasured while every document still
claims it is checked.

The invariant is stated over **every workflow that names the guard**, not against one
filename, so a second wiring is judged by the same rule and deleting the current
workflow cannot make these assertions vacuous. A broad-suite step (``pytest tests/``)
is not counted as wiring: it also reaches the guard, but only a *file-targeted* gate
guarantees that a change to the guard re-runs it deterministically. Six properties:

1. some workflow names each guard file as a pytest target;
2. that workflow's ``pull_request`` filter names its own file;
3. its ``push`` and ``pull_request`` path filters are identical;
4. it is dispatchable, so the guard can be re-run against an exact revision;
5. the executing step can actually fail (no step- or job-level
   ``continue-on-error``, no ``if: false``);
6. the filter names every input the guards read -- both guard files *and* the
   classifier script, which the guards import.

Each detector has a negative control that feeds it the defect it is meant to catch,
built from a deep copy of the real workflow, so a rewrite cannot silently disarm the
boundary.
"""

from __future__ import annotations

import copy
import shlex
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

GUARDS = (
    "tests/test_gov04_platform_preconditions.py",
    "tests/test_gov04_platform_preconditions_ci_wiring.py",
)
INPUTS = GUARDS + ("scripts/gov04_platform_preconditions.py",)


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _trigger_block(workflow: dict) -> dict:
    # PyYAML parses the bare key `on` as the boolean `True`.
    block = workflow.get(True, workflow.get("on"))
    return block if isinstance(block, dict) else {}


def _paths(workflow: dict, event: str) -> list[str] | None:
    trigger = _trigger_block(workflow).get(event)
    if not isinstance(trigger, dict):
        return None
    paths = trigger.get("paths")
    return list(paths) if isinstance(paths, list) else None


def _pytest_targets(step: dict) -> list[str] | None:
    """The argument tokens of a real pytest invocation, else ``None``.

    ``pytest`` must be the invoked command word -- ``pytest x`` or ``python -m
    pytest x``. A ``pytest`` token that is merely an argument to another command
    (``echo pytest x``) or that sits inside a comment is not an execution.
    """
    command = step.get("run")
    if not isinstance(command, str):
        return None
    tokens: list[str] = []
    for line in command.splitlines():
        try:
            tokens.extend(shlex.split(line.split("#", 1)[0]))
        except ValueError:
            continue
    if "pytest" not in tokens:
        return None
    index = tokens.index("pytest")
    if index > 0 and tokens[index - 1] != "-m":
        return None
    return tokens[index + 1 :]


def _executing_steps(workflow: dict):
    for job in (workflow.get("jobs") or {}).values():
        if not isinstance(job, dict):
            continue
        for step in job.get("steps") or []:
            if not isinstance(step, dict):
                continue
            targets = _pytest_targets(step)
            if targets is not None:
                yield step, targets


def names_as_target(workflow: dict, guard: str) -> bool:
    """True when a pytest invocation names ``guard`` as an explicit target."""
    for _step, targets in _executing_steps(workflow):
        if guard in [t for t in targets if not t.startswith("-")]:
            return True
    return False


def exemptions(workflow: dict) -> list[str]:
    """Every place the workflow declares itself unable to fail."""
    found: list[str] = []
    for job_name, job in (workflow.get("jobs") or {}).items():
        if not isinstance(job, dict):
            continue
        if job.get("continue-on-error") is True:
            found.append(f"{job_name}: job-level continue-on-error")
        if job.get("if") in (False, "false", "${{ false }}"):
            found.append(f"{job_name}: job-level if-false")
        for index, step in enumerate(job.get("steps") or []):
            if not isinstance(step, dict):
                continue
            if step.get("continue-on-error") is True:
                found.append(f"{job_name}[{index}]: step-level continue-on-error")
            if step.get("if") in (False, "false", "${{ false }}"):
                found.append(f"{job_name}[{index}]: step-level if-false")
    return found


def filter_omissions(workflow: dict) -> list[str]:
    """Inputs the guards read that the pull_request filter does not select."""
    paths = _paths(workflow, "pull_request") or []
    return [item for item in INPUTS if item not in paths]


def self_selection_omissions(workflow: dict, workflow_name: str) -> list[str]:
    paths = _paths(workflow, "pull_request") or []
    if workflow_name in paths or f".github/workflows/{workflow_name}" in paths:
        return []
    return [workflow_name]


def _workflow_files() -> list[Path]:
    return sorted(WORKFLOWS.glob("*.yml"))


def _guard_workflows() -> list[Path]:
    """Workflows that name a guard as an explicit pytest target."""
    return [
        path
        for path in _workflow_files()
        if any(names_as_target(_load(path), guard) for guard in GUARDS)
    ]


def _the_workflow() -> tuple[str, dict]:
    """The real wiring, as a deep copy the negative controls can mutate."""
    candidates = _guard_workflows()
    assert candidates, "no workflow names the GOV-04 platform-precondition guard"
    return candidates[0].name, copy.deepcopy(_load(candidates[0]))


# --- the six properties -----------------------------------------------------

def test_a_workflow_names_each_guard_as_a_target():
    for guard in GUARDS:
        assert any(names_as_target(_load(p), guard) for p in _workflow_files()), (
            f"no workflow names {guard} as a pytest target"
        )


@pytest.mark.parametrize("workflow_path", _guard_workflows(), ids=lambda p: p.name)
def test_the_executing_workflow_selects_itself(workflow_path: Path):
    assert self_selection_omissions(_load(workflow_path), workflow_path.name) == []


@pytest.mark.parametrize("workflow_path", _guard_workflows(), ids=lambda p: p.name)
def test_push_and_pull_request_filters_are_identical(workflow_path: Path):
    workflow = _load(workflow_path)
    pull = _paths(workflow, "pull_request")
    push = _paths(workflow, "push")
    if pull is None or push is None:
        pytest.skip("workflow does not declare both path filters")
    assert sorted(pull) == sorted(push)


@pytest.mark.parametrize("workflow_path", _guard_workflows(), ids=lambda p: p.name)
def test_the_workflow_is_dispatchable(workflow_path: Path):
    assert "workflow_dispatch" in _trigger_block(_load(workflow_path))


@pytest.mark.parametrize("workflow_path", _guard_workflows(), ids=lambda p: p.name)
def test_the_executing_workflow_can_fail(workflow_path: Path):
    assert exemptions(_load(workflow_path)) == []


@pytest.mark.parametrize("workflow_path", _guard_workflows(), ids=lambda p: p.name)
def test_the_filter_names_every_input_the_guards_read(workflow_path: Path):
    assert filter_omissions(_load(workflow_path)) == []


# --- negative controls ------------------------------------------------------

def test_positive_control_the_real_workflow_passes_every_detector():
    name, workflow = _the_workflow()
    for guard in GUARDS:
        assert names_as_target(workflow, guard)
    assert exemptions(workflow) == []
    assert filter_omissions(workflow) == []
    assert self_selection_omissions(workflow, name) == []


def test_negative_control_a_mention_is_not_an_execution():
    _name, workflow = _the_workflow()
    for job in workflow["jobs"].values():
        for step in job.get("steps") or []:
            if _pytest_targets(step) is not None:
                step["run"] = "echo pytest " + " ".join(GUARDS)
    for guard in GUARDS:
        assert not names_as_target(workflow, guard), (
            "an `echo pytest ...` line was read as an execution"
        )


def test_negative_control_a_directory_target_does_not_count_as_wiring():
    """`pytest tests/` reaches the guard, but does not re-run it deterministically."""
    _name, workflow = _the_workflow()
    for job in workflow["jobs"].values():
        for step in job.get("steps") or []:
            if _pytest_targets(step) is not None:
                step["run"] = "python -m pytest -q tests/"
    for guard in GUARDS:
        assert not names_as_target(workflow, guard)


def test_negative_control_a_job_level_continue_on_error_is_flagged():
    _name, workflow = _the_workflow()
    next(iter(workflow["jobs"].values()))["continue-on-error"] = True
    assert any("job-level continue-on-error" in f for f in exemptions(workflow))


def test_negative_control_a_step_level_if_false_is_flagged():
    _name, workflow = _the_workflow()
    for job in workflow["jobs"].values():
        for step in job.get("steps") or []:
            if _pytest_targets(step) is not None:
                step["if"] = False
    assert any("step-level if-false" in f for f in exemptions(workflow))


def test_negative_control_a_filter_omitting_the_classifier_is_flagged():
    _name, workflow = _the_workflow()
    for event in ("pull_request", "push"):
        trigger = _trigger_block(workflow).get(event)
        if isinstance(trigger, dict) and isinstance(trigger.get("paths"), list):
            trigger["paths"] = [p for p in trigger["paths"] if p != INPUTS[-1]]
    assert "scripts/gov04_platform_preconditions.py" in filter_omissions(workflow)


def test_negative_control_a_filter_omitting_its_own_file_is_flagged():
    name, workflow = _the_workflow()
    assert self_selection_omissions(workflow, name) == [], "control is vacuous"
    for event in ("pull_request", "push"):
        trigger = _trigger_block(workflow).get(event)
        if isinstance(trigger, dict) and isinstance(trigger.get("paths"), list):
            trigger["paths"] = [p for p in trigger["paths"] if not p.endswith(".yml")]
    assert self_selection_omissions(workflow, name) == [name]
