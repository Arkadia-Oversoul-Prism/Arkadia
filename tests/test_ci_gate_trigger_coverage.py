"""Boundary guard: a CI gate must be selected by the surfaces it judges.

`tests/test_m02a_ci_gate_integrity.py` already pins this for the CP10 mutation
boundary: its own contract surfaces must appear in the workflow's trigger filter,
and the `push` and `pull_request` filters must be identical, because a surface
judged on `push` but not on `pull_request` reaches `main` unjudged and turns the
gate red at the merge.

That lesson was never generalised. `provider-routing.yml` ran
`python -m pytest tests/architecture -q` on every pull request but triggered on
neither `tests/architecture/**` (the assertions themselves) nor its own workflow
file — so the gate that judges a change could itself be changed without being
judged. Measured on `main` @ `4550531`: the same architecture failure that
`provider-routing` reported on PR #294 is present on `main` and could be reached
without the gate running at all.

These tests state the invariant once, generically, over every workflow that runs
pytest:

1. A workflow that runs pytest on `pull_request` must name its own file in that
   trigger filter — otherwise its gate logic can be rewritten unjudged.
2. A workflow that declares both `push` and `pull_request` path filters must make
   them identical — an asymmetric filter is a masking hole.
3. A workflow that runs the architecture fitness suite must be triggered by a
   change to the architecture tests themselves.

The detector is proven against the forms it is meant to catch (negative controls),
so a rewrite of a workflow cannot silently disarm the boundary.

A wider trigger is *not* asserted here. The architecture suite also asserts a
line budget for `api/main.py`, so `api/**` arguably belongs in the filter of any
workflow that runs it; `provider-routing.yml` also runs the full suite, which
carries pre-existing `main` failures, so widening its filter to `api/**` would
turn every API pull request red with debt it did not introduce. That widening is
therefore recorded as proposed work, not performed here — a gate must stop being
baseline-red before its blast radius is expanded.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

# A workflow that runs the architecture fitness suite must be selected by the
# assertions it executes.
_ARCHITECTURE_TEST_SURFACE = "tests/architecture/test_layer_boundaries.py"

_PYTEST = re.compile(r"\bpytest\b")
_ARCHITECTURE_RUN = re.compile(r"tests/architecture(?:/|\s|$|\\)")


def _workflow_paths() -> list[Path]:
    return sorted(WORKFLOWS.glob("*.yml"))


def _trigger_block(workflow: dict) -> dict:
    """The `on:` mapping.

    PyYAML parses the bare key `on` as the boolean `True`, so both spellings are
    read.
    """
    block = workflow.get(True, workflow.get("on"))
    return block if isinstance(block, dict) else {}


def _path_filter(trigger_block: dict, event: str) -> set[str] | None:
    """The `paths` filter for one event, or None when the event is not declared.

    An event declared without a `paths` filter (e.g. a bare `pull_request:`)
    selects every path, so it is returned as None to mean "unfiltered" rather
    than as an empty set.
    """
    event_block = trigger_block.get(event)
    if not isinstance(event_block, dict):
        return None
    paths = event_block.get("paths")
    if paths is None:
        return None
    return set(paths)


def _run_scripts(workflow: dict) -> list[str]:
    scripts: list[str] = []
    for job in (workflow.get("jobs") or {}).values():
        for step in job.get("steps") or []:
            run = step.get("run")
            if isinstance(run, str):
                scripts.append(run)
    return scripts


def _runs_pytest(workflow: dict) -> bool:
    return any(_PYTEST.search(script) for script in _run_scripts(workflow))


def _runs_architecture_suite(workflow: dict) -> bool:
    return any(_ARCHITECTURE_RUN.search(script) for script in _run_scripts(workflow))


def _selects_path(path_filter: set[str], path: str) -> bool:
    """Whether a `paths` filter selects a literal path.

    GitHub's filter syntax is glob-like: `**` spans directories, `*` does not.
    This mirrors that for the literal paths these tests probe.
    """
    parts = [p for p in path.split("/") if p]
    for pattern in path_filter:
        segments = pattern.split("/")
        # A trailing `/**` matches the directory and everything beneath it.
        if segments[-1] == "**" and len(segments) - 1 <= len(parts):
            if all(
                ps == "*" or ps == pp
                for ps, pp in zip(segments[:-1], parts[: len(segments) - 1])
            ):
                return True
            continue
        if len(segments) != len(parts):
            continue
        if all(
            ps == "**" or ps == "*" or ps == pp for ps, pp in zip(segments, parts)
        ):
            return True
    return False


def _load(name: str) -> dict:
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


def _pytest_workflows() -> list[str]:
    return [p.name for p in _workflow_paths() if _runs_pytest(_load(p.name))]


# ---------------------------------------------------------------------------
# Detector negative controls
# ---------------------------------------------------------------------------


def test_selector_accepts_the_forms_github_uses():
    assert _selects_path({"api/**"}, "api/main.py")
    assert _selects_path({"api/**"}, "api/lab_routes.py")
    assert _selects_path({"tests/architecture/**"}, "tests/architecture/test_layer_boundaries.py")
    assert _selects_path({"tests/architecture/test_layer_boundaries.py"}, "tests/architecture/test_layer_boundaries.py")
    assert _selects_path({"**"}, "anything/at/all.py")


def test_selector_rejects_unrelated_paths():
    # Negative control: a selector that matched everything would make the
    # boundary assertions vacuously green.
    assert not _selects_path({"weaver/**", "providers/**"}, "api/main.py")
    assert not _selects_path({"tests/test_key_pool.py"}, "tests/architecture/test_layer_boundaries.py")
    # `*` does not cross a directory boundary.
    assert not _selects_path({"api/*.py"}, "api/sub/module.py")


def test_runs_pytest_detector_distinguishes_the_forms():
    assert _runs_pytest({"jobs": {"j": {"steps": [{"run": "python -m pytest tests/ -q"}]}}})
    assert not _runs_pytest({"jobs": {"j": {"steps": [{"run": "python -m py_compile api/main.py"}]}}})


# ---------------------------------------------------------------------------
# The invariants, over every workflow that runs pytest
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", _pytest_workflows())
def test_pr_pytest_workflow_is_selected_by_its_own_file(name: str):
    """A gate that runs on PRs must be triggered by changes to itself."""
    workflow = _load(name)
    paths = _path_filter(_trigger_block(workflow), "pull_request")
    if paths is None:
        # `pull_request` is either undeclared or unfiltered; an unfiltered event
        # already selects the workflow file.
        return
    self_path = f".github/workflows/{name}"
    assert _selects_path(paths, self_path), (
        f"{name} runs pytest on pull_request but does not trigger on its own "
        f"file ({self_path}); its gate logic can be rewritten without being judged"
    )


@pytest.mark.parametrize("name", _pytest_workflows())
def test_push_and_pull_request_filters_are_identical(name: str):
    """An asymmetric path filter is a masking hole, not a convenience."""
    trigger_block = _trigger_block(_load(name))
    push = _path_filter(trigger_block, "push")
    pull = _path_filter(trigger_block, "pull_request")
    if push is None or pull is None:
        return
    assert push == pull, (
        f"{name} declares asymmetric push/pull_request filters; surfaces present "
        f"in only one: {sorted(push ^ pull)}"
    )


@pytest.mark.parametrize("name", _pytest_workflows())
def test_architecture_fitness_is_selected_by_the_surfaces_it_judges(name: str):
    """A workflow running `tests/architecture` must be selected by those tests."""
    workflow = _load(name)
    if not _runs_architecture_suite(workflow):
        return
    paths = _path_filter(_trigger_block(workflow), "pull_request")
    if paths is None:
        return
    assert _selects_path(paths, _ARCHITECTURE_TEST_SURFACE), (
        f"{name} runs the architecture fitness suite on pull_request but does not "
        "trigger on tests/architecture/**; the assertions themselves can be "
        "changed without the gate that executes them running"
    )
