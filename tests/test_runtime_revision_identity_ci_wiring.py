"""Boundary guard: the revision-identity gate must keep identifying `main`.

`scripts/version_reconciliation.py` compares the revision a deployment reports at
`GET /api/version` against an intended source revision. Measured at `main`
`bb19aabd`, `grep -rn "api/version" .github/workflows/` named only
`canonical-render-runtime-probe.yml` and `canonical-render-acceptance.yml` -- both
path-filtered (build inputs only, and itself only respectively). A push to `main`
touching anything else still deploys a new revision that no workflow identifies.

`.github/workflows/runtime-revision-identity.yml` is that missing surface. This
module pins the properties that make it one, and it pins them over the *real*
file, so a rewrite of the gate is judged by the gate's own judge:

1. `push` is **not** path-filtered. A filter here would re-create the gap: the
   commits that most need identifying are the ones a filter omits.
2. The `pull_request` filter names this workflow file and every input the guard
   reads, so a change to any of them executes the judge.
3. A pull request cannot probe production. A PR is not deployed, so a probe from
   one measures a different revision and reports a false drift.
4. No `continue-on-error` on any job: the probe's exit status is the verdict.
5. The probe passes the pushed SHA through `env:`, never interpolated into the
   shell body.

Each detector has a negative control built from the pre-repair shape, so the
guard cannot be disarmed by editing the workflow without reddening a control.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "runtime-revision-identity.yml"
SELF_PATH = ".github/workflows/runtime-revision-identity.yml"
SCRIPT = "scripts/version_reconciliation.py"

# Every input the guard reads. A change to one of these can change what the gate
# asserts without executing the gate, so each must select it.
REQUIRED_PULL_REQUEST_PATHS = (
    SELF_PATH,
    SCRIPT,
    "kernel/revision_identity.py",
    "tests/test_version_reconciliation.py",
    "tests/test_runtime_revision_identity_ci_wiring.py",
)


def _load(path: Path = WORKFLOW) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _events(workflow: dict) -> dict:
    """PyYAML parses a bare `on` key as the boolean `True`; read both spellings."""
    block = workflow.get("on", workflow.get(True))
    return block if isinstance(block, dict) else {}


def _push_is_unfiltered(workflow: dict) -> bool:
    push = _events(workflow).get("push")
    return isinstance(push, dict) and "paths" not in push and "paths-ignore" not in push


def _missing_pull_request_paths(workflow: dict, required=REQUIRED_PULL_REQUEST_PATHS) -> list[str]:
    pull = _events(workflow).get("pull_request")
    if not isinstance(pull, dict):
        return list(required)
    declared = set(pull.get("paths") or [])
    return sorted(p for p in required if p not in declared)


def _probe_jobs(workflow: dict) -> list[str]:
    """Jobs whose steps invoke the reconciliation script."""
    names = []
    for name, job in (workflow.get("jobs") or {}).items():
        for step in job.get("steps") or []:
            if SCRIPT in (step.get("run") or ""):
                names.append(name)
                break
    return names


def _unreachable_probe_jobs(workflow: dict) -> list[str]:
    """Probe jobs that are not confined to non-pull-request events."""
    confined = "github.event_name != 'pull_request'"
    return [name for name in _probe_jobs(workflow) if (workflow["jobs"][name].get("if") or "") != confined]


def _masked_jobs(workflow: dict) -> list[str]:
    return [name for name, job in (workflow.get("jobs") or {}).items() if job.get("continue-on-error")]


def _interpolated_probe(workflow: dict) -> list[str]:
    """Steps that put `${{ }}` directly into the shell body of the probe."""
    offending = []
    for job in (workflow.get("jobs") or {}).values():
        for step in job.get("steps") or []:
            run = step.get("run") or ""
            if "${{" in run:
                offending.append(run.splitlines()[0])
    return offending


# ---------------------------------------------------------------------------
# The gate as it exists
# ---------------------------------------------------------------------------


def test_the_gate_exists_and_runs_the_reconciliation_script():
    workflow = _load()
    assert _probe_jobs(workflow), "no job invokes scripts/version_reconciliation.py"


def test_push_is_not_path_filtered():
    """Every commit that lands on main is deployed, so every one is checked."""
    assert _push_is_unfiltered(_load())


def test_pull_request_selects_the_gate_and_every_input_it_reads():
    assert _missing_pull_request_paths(_load()) == []


def test_a_pull_request_cannot_probe_production():
    assert _unreachable_probe_jobs(_load()) == []


def test_no_job_can_mask_the_probe_verdict():
    assert _masked_jobs(_load()) == []


def test_the_pushed_sha_is_passed_through_the_environment():
    assert _interpolated_probe(_load()) == []


def test_the_gate_executes_the_guard_it_enforces():
    """A gate that runs only the probe leaves the oracle's own tests unexecuted."""
    workflow = _load()
    executed = [
        step.get("run") or ""
        for job in (workflow.get("jobs") or {}).values()
        for step in job.get("steps") or []
        if "pytest" in (step.get("run") or "")
    ]
    assert any("tests/test_version_reconciliation.py" in run for run in executed)


# ---------------------------------------------------------------------------
# Detector negative controls
# ---------------------------------------------------------------------------


def test_negative_control_a_path_filtered_push_is_reported():
    """The pre-repair shape: the gate would run only on build inputs."""
    workflow = _load()
    workflow[_events_key(workflow)]["push"]["paths"] = ["api/**"]
    assert _push_is_unfiltered(workflow) is False


def test_negative_control_a_dropped_input_is_reported():
    workflow = _load()
    pull = _events(workflow)["pull_request"]
    pull["paths"] = [p for p in pull["paths"] if p != SCRIPT]
    assert _missing_pull_request_paths(workflow) == [SCRIPT]


def test_negative_control_an_unguarded_probe_is_reported():
    """A probe reachable from a pull request measures someone else's revision."""
    workflow = _load()
    for name in _probe_jobs(workflow):
        workflow["jobs"][name]["if"] = "github.event_name == 'push'"
    assert _unreachable_probe_jobs(workflow)


def test_negative_control_a_masked_job_is_reported():
    workflow = _load()
    for name in _probe_jobs(workflow):
        workflow["jobs"][name]["continue-on-error"] = True
    assert _masked_jobs(workflow)


def test_negative_control_an_interpolated_sha_is_reported():
    workflow = _load()
    for job in workflow["jobs"].values():
        for step in job.get("steps") or []:
            if SCRIPT in (step.get("run") or ""):
                step["run"] = 'python ' + SCRIPT + ' --expected "${{ github.sha }}"'
    assert _interpolated_probe(workflow)


def _events_key(workflow: dict) -> object:
    return "on" if "on" in workflow else True


@pytest.mark.parametrize("name", REQUIRED_PULL_REQUEST_PATHS)
def test_every_required_input_is_named(name: str):
    """The required set is not vacuous: each entry is a real repository path."""
    assert (ROOT / name).exists(), f"{name} is named by the filter but is not a tracked path"
