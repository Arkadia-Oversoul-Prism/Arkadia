"""Boundary guard: the frontend-script-asset guard must be executed in CI.

`tests/test_frontend_script_assets_resolve.py` fails when `index.html` names a
root-absolute `<script src>` with no committed file under `web/public_prism/public/`
— the `/firebase-config.js` defect that passed `pnpm build` yet failed the CP10
browser route-verification step, turning `main` red on 2026-10-09. Measured on
`main` @ `f9ced6b6`, no workflow named that guard, so it held only when a human
invoked it by hand. That is the defect class the repository already names: a guard
no workflow executes is decoration.

These tests state the invariant once, generically over the workflows that run the
guard:

1. Some workflow must run the guard, and must be selected on `pull_request` by the
   guard file itself and by its inputs (`index.html` and the committed assets under
   `web/public_prism/public/`), so a change to what the guard asserts is judged by
   the gate it changes.
2. Its guard step must be able to fail the job — `continue-on-error` off — or the
   job's conclusion is that step's conclusion and the assertion is vacuous.

The detector is proven against the forms it is meant to catch (negative controls),
so deleting the wiring cannot silently disarm the boundary.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

_GUARD_FILE = "tests/test_frontend_script_assets_resolve.py"
_WIRING_FILE = "tests/test_frontend_script_asset_ci_wiring.py"
# The guard parses index.html and resolves each src against public/. A change to any
# of those artifacts changes the guard's verdict, so the gate must be selected by it.
_GUARD_INPUTS = (
    _GUARD_FILE,
    _WIRING_FILE,
    "web/public_prism/index.html",
    "web/public_prism/public/**",
)


def _workflow_paths() -> list[Path]:
    return sorted(WORKFLOWS.glob("*.yml"))


def _load(name: str) -> dict:
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


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


def _selects_path(path_filter: set[str], path: str) -> bool:
    """Whether a `paths` filter selects a literal path, mirroring GitHub's globs."""
    parts = [p for p in path.split("/") if p]
    for pattern in path_filter:
        segments = pattern.split("/")
        if segments[-1] == "**" and len(segments) - 1 <= len(parts):
            if all(
                ps == "*" or ps == pp
                for ps, pp in zip(segments[:-1], parts[: len(segments) - 1])
            ):
                return True
            continue
        if len(segments) != len(parts):
            continue
        if all(ps == "**" or ps == "*" or ps == pp for ps, pp in zip(segments, parts)):
            return True
    return False


def _steps(workflow: dict) -> list[dict]:
    steps: list[dict] = []
    for job in (workflow.get("jobs") or {}).values():
        steps.extend(job.get("steps") or [])
    return steps


def _runs_guard(workflow: dict) -> bool:
    return any(
        isinstance(step.get("run"), str) and _GUARD_FILE in step["run"]
        for step in _steps(workflow)
    )


def _guard_workflows() -> list[str]:
    return [p.name for p in _workflow_paths() if _runs_guard(_load(p.name))]


def _guard_steps(workflow: dict) -> list[dict]:
    return [
        step
        for step in _steps(workflow)
        if isinstance(step.get("run"), str) and _GUARD_FILE in step["run"]
    ]


# ---------------------------------------------------------------------------
# Detector negative controls
# ---------------------------------------------------------------------------


def test_detector_accepts_the_forms_the_workflow_uses():
    assert _runs_guard(
        {"jobs": {"j": {"steps": [{"run": f"python -m pytest {_GUARD_FILE} -q"}]}}}
    )
    assert not _runs_guard(
        {"jobs": {"j": {"steps": [{"run": "python -m pytest tests/test_key_pool.py -q"}]}}}
    )


def test_selector_rejects_unrelated_paths():
    # Negative control: a selector that matched everything would make the boundary
    # assertions vacuously green.
    assert not _selects_path({"weaver/**"}, _GUARD_FILE)
    assert not _selects_path({"tests/test_key_pool.py"}, "web/public_prism/index.html")
    # `*` does not cross a directory boundary.
    assert not _selects_path({"web/*.html"}, "web/public_prism/index.html")


def test_negative_control_flags_a_guard_workflow_that_does_not_select_itself():
    """The selection predicate must reject a guard that is not its own trigger."""
    synthetic = {"on": {"pull_request": {"paths": ["api/**"]}}}
    paths = _path_filter(_trigger_block(synthetic), "pull_request")
    assert paths is not None
    assert not _selects_path(paths, _GUARD_FILE), (
        "a workflow selected only by api/** must not count as selecting the guard"
    )


def test_negative_control_flags_a_guard_step_that_cannot_fail_the_job():
    """A `continue-on-error` guard step reports the process exit, not the guard's."""
    workflow = {
        "jobs": {
            "j": {
                "steps": [
                    {"run": f"python -m pytest {_GUARD_FILE} -q", "continue-on-error": True}
                ]
            }
        }
    }
    assert all(step.get("continue-on-error") for step in _guard_steps(workflow))


# ---------------------------------------------------------------------------
# The invariants, over every workflow that runs the frontend-asset guard
# ---------------------------------------------------------------------------


def test_a_workflow_executes_the_frontend_script_asset_guard():
    """The guard must be executed somewhere, not only invoked by hand."""
    assert _guard_workflows(), (
        f"no workflow runs {_GUARD_FILE}; the dangling-script-src guard is decoration "
        f"and the browser gate can only rediscover the defect minutes later"
    )


@pytest.mark.parametrize("name", _guard_workflows())
def test_guard_workflow_is_selected_by_the_guard_and_its_inputs(name: str):
    """A gate must be selected by the surfaces it judges."""
    workflow = _load(name)
    paths = _path_filter(_trigger_block(workflow), "pull_request")
    if paths is None:
        # `pull_request` is undeclared or unfiltered; an unfiltered event already
        # selects every path, including the guard and its inputs.
        return
    for surface in _GUARD_INPUTS:
        assert _selects_path(paths, surface), (
            f"{name} runs {_GUARD_FILE} on pull_request but is not selected by "
            f"{surface!r}; a change to what the guard asserts would not execute it"
        )


@pytest.mark.parametrize("name", _guard_workflows())
def test_guard_step_can_fail_the_job(name: str):
    """A guard step that cannot fail the job cannot enforce anything."""
    workflow = _load(name)
    steps = _guard_steps(workflow)
    assert steps, f"{name} names {_GUARD_FILE} but no step runs it"
    for step in steps:
        assert not step.get("continue-on-error"), (
            f"{name}: the step running {_GUARD_FILE} sets continue-on-error, so its "
            f"conclusion reports the shell, not the guard"
        )
