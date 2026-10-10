"""Boundary guard: the composed-route contract must be executable in CI on demand.

`tests/test_solspire_route_composition.py` pins the EDEN-OPS-02 routes at the paths
they actually compose to under the SolSpire parent router. Measured on `main` @
`3b74c19d`, the gate that runs it (`.github/workflows/solspire-route-composition.yml`)
is path-filtered to `solspire/**` and carries **no** `workflow_dispatch`, so it executes
only when a change touches SolSpire — the only run on record is at `73fbb51a`. A revision
that changes nothing under `solspire/**` therefore has no route-composition execution,
and the contract cannot be re-run against an exact revision on demand.

These tests state the invariant generically over the workflows that run the contract:

1. Some workflow must run `tests/test_solspire_route_composition.py`.
2. Such a workflow must be dispatchable (`workflow_dispatch`), so the contract can be
   executed against an exact revision without a source change under `solspire/**`.
3. Such a workflow's `paths` filter must name the contract file and the surface it
   exercises (`solspire/**`), so a change to either is judged by the gate it changes.
4. Such a workflow's contract step must be able to fail the job.

The detector is proven against the forms it is meant to catch (negative controls), so
deleting the wiring cannot silently disarm the boundary.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

_CONTRACT_FILE = "tests/test_solspire_route_composition.py"
_COMPOSITION_SURFACE = "solspire/**"


def _workflow_paths() -> list[Path]:
    return sorted(WORKFLOWS.glob("*.yml"))


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _trigger_block(workflow: dict) -> dict:
    """The `on:` mapping.

    PyYAML parses the bare key `on` as the boolean `True`, so both spellings are read.
    """
    block = workflow.get(True, workflow.get("on"))
    return block if isinstance(block, dict) else {}


def _path_filter(trigger_block: dict, event: str) -> set[str] | None:
    """The `paths` filter for one event, or None when the event is not declared."""
    event_block = trigger_block.get(event)
    if not isinstance(event_block, dict):
        return None
    paths = event_block.get("paths")
    return None if paths is None else set(paths)


def _runs_contract(workflow: dict) -> bool:
    for job in (workflow.get("jobs") or {}).values():
        for step in job.get("steps") or []:
            if _CONTRACT_FILE in str(step.get("run", "")):
                return True
    return False


def _contract_steps(workflow: dict) -> list[dict]:
    steps = []
    for job in (workflow.get("jobs") or {}).values():
        for step in job.get("steps") or []:
            if _CONTRACT_FILE in str(step.get("run", "")):
                steps.append(step)
    return steps


def _is_dispatchable(trigger_block: dict) -> bool:
    return "workflow_dispatch" in trigger_block


def _missing_filter_coverage(trigger_block: dict) -> list[str]:
    """Which required selectors the declared path filters omit.

    A selector is covered when *any* declared event's `paths` filter names it; the
    contract must be re-judged by a change to itself and to the surface it exercises.
    """
    filters: list[set[str]] = []
    for event in ("pull_request", "push"):
        f = _path_filter(trigger_block, event)
        if f is not None:
            filters.append(f)
    if not filters:
        return [_CONTRACT_FILE, _COMPOSITION_SURFACE]
    covered = set().union(*filters)
    required = (_CONTRACT_FILE, _COMPOSITION_SURFACE)
    return [selector for selector in required if selector not in covered]


def _step_can_fail(step: dict) -> bool:
    return not step.get("continue-on-error", False)


def _audit(workflow: dict) -> list[str]:
    """Defects that make a workflow unable to satisfy the invariant. Empty is a pass."""
    trigger = _trigger_block(workflow)
    defects: list[str] = []
    if not _runs_contract(workflow):
        return defects
    if not _is_dispatchable(trigger):
        defects.append("no workflow_dispatch: contract not executable on demand")
    defects.extend(
        f"paths filter omits {sel}" for sel in _missing_filter_coverage(trigger)
    )
    if not all(_step_can_fail(step) for step in _contract_steps(workflow)):
        defects.append("contract step cannot fail the job")
    return defects


def _wired() -> list[tuple[Path, dict]]:
    wired = []
    for path in _workflow_paths():
        workflow = _load(path)
        if _runs_contract(workflow):
            wired.append((path, workflow))
    return wired


def test_some_workflow_runs_the_composed_route_contract():
    assert _wired(), (
        f"no workflow runs {_CONTRACT_FILE}: the composed-route contract is a guard "
        "that no gate executes"
    )


@pytest.mark.parametrize("path,workflow", _wired(), ids=lambda v: getattr(v, "name", None))
def test_every_contract_workflow_is_executable_and_can_fail(path: Path, workflow: dict):
    defects = _audit(workflow)
    assert not defects, f"{path.name}: " + "; ".join(defects)


# --- detector controls: prove the guard bites on the forms it names -----------------


def _minimal_workflow(**trigger) -> dict:
    return {
        True: trigger,
        "jobs": {
            "router-composition": {
                "steps": [{"run": f"python -m pytest {_CONTRACT_FILE} -q"}],
            }
        },
    }


def test_negative_control_flags_the_pre_fix_shape():
    """The measured pre-fix workflow (path-filtered, no dispatch) must be flagged."""
    pre_fix = _minimal_workflow(
        pull_request={"paths": [_COMPOSITION_SURFACE, _CONTRACT_FILE]},
        push={"branches": ["main"], "paths": [_COMPOSITION_SURFACE, _CONTRACT_FILE]},
    )
    assert _audit(pre_fix) == [
        "no workflow_dispatch: contract not executable on demand"
    ]


def test_negative_control_flags_incomplete_filter():
    incomplete = _minimal_workflow(
        pull_request={"paths": [_CONTRACT_FILE]},
        workflow_dispatch=None,
    )
    assert _audit(incomplete) == [f"paths filter omits {_COMPOSITION_SURFACE}"]


def test_negative_control_flags_a_step_that_cannot_fail():
    workflow = _minimal_workflow(pull_request={"paths": [_COMPOSITION_SURFACE, _CONTRACT_FILE]}, workflow_dispatch=None)
    workflow["jobs"]["router-composition"]["steps"][0]["continue-on-error"] = True
    assert _audit(workflow) == ["contract step cannot fail the job"]


def test_positive_control_is_silent_on_the_wired_shape():
    wired = _minimal_workflow(
        pull_request={"paths": [_COMPOSITION_SURFACE, _CONTRACT_FILE]},
        push={"branches": ["main"], "paths": [_COMPOSITION_SURFACE, _CONTRACT_FILE]},
        workflow_dispatch=None,
    )
    assert _audit(wired) == []


def test_detector_ignores_workflows_that_do_not_run_the_contract():
    unrelated = _minimal_workflow(workflow_dispatch=None)
    unrelated["jobs"]["router-composition"]["steps"] = [{"run": "echo unrelated"}]
    assert _audit(unrelated) == []
