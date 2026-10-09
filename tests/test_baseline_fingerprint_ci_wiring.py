"""Boundary guard: the baseline-fingerprint guard must be executed in CI.

`tests/test_baseline_fingerprint.py` reconciles the recorded baseline node set with a
live measurement of `main` and fails when the two drift apart. Measured on `main` @
`24a00f85`, no workflow named it — `grep -rn baseline_fingerprint .github/workflows/`
returned 0 — so the reconciliation held only when a human invoked it by hand. That is
the defect class the repository already names elsewhere: a guard no workflow executes is
decoration.

These tests state the invariant once, generically over the workflows that run the guard:

1. Some workflow must run the fingerprint guard, and must be selected on `pull_request`
   by the guard file itself and by `tests/fixtures/**` (the guard's inputs), so a change
   to either is judged by the gate it changes.
2. Such a workflow must check out full history: the guard's node set is documented as
   clone-depth sensitive, so a shallow checkout can change its verdict.
3. Such a workflow must let the guard step fail the job (`continue-on-error` off).

The detector is proven against the forms it is meant to catch (negative controls), so
deleting the wiring cannot silently disarm the boundary.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

_GUARD_FILE = "tests/test_baseline_fingerprint.py"
_GUARD_FIXTURES = "tests/fixtures/**"
_GUARD_INPUTS = (_GUARD_FILE, _GUARD_FIXTURES)


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


def _run_scripts(workflow: dict) -> list[str]:
    scripts: list[str] = []
    for job in (workflow.get("jobs") or {}).values():
        for step in job.get("steps") or []:
            run = step.get("run")
            if isinstance(run, str):
                scripts.append(run)
    return scripts


def _runs_guard(workflow: dict) -> bool:
    return any(_GUARD_FILE in script for script in _run_scripts(workflow))


def _guard_workflows() -> list[str]:
    return [p.name for p in _workflow_paths() if _runs_guard(_load(p))]


def _guard_literal(module: Path, name: str) -> list[str]:
    """A module-level list-of-string literal, read from the guard's own source.

    The trigger filter must name every artifact the guard's verdict depends on. Those
    artifacts are declared *in the guard*, so they are read from there rather than
    duplicated here: a second copy would drift, and a drifted copy would make the
    boundary assertion below vacuous.
    """
    tree = ast.parse(module.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == name for t in node.targets
        ):
            return [e.value for e in node.value.elts]
    raise AssertionError(f"{name} is not declared in {module}")


def _guard_published_docs() -> list[str]:
    return _guard_literal(ROOT / _GUARD_FILE, "FINGERPRINT_DOCS")


def _checkout_steps(workflow: dict) -> list[dict]:
    steps: list[dict] = []
    for job in (workflow.get("jobs") or {}).values():
        for step in job.get("steps") or []:
            uses = step.get("uses")
            if isinstance(uses, str) and uses.startswith("actions/checkout@"):
                steps.append(step)
    return steps


# ---------------------------------------------------------------------------
# Detector negative controls
# ---------------------------------------------------------------------------


def test_detector_accepts_the_forms_the_workflow_uses():
    assert _runs_guard({"jobs": {"j": {"steps": [{"run": f"python -m pytest {_GUARD_FILE} -q"}]}}})
    assert not _runs_guard({"jobs": {"j": {"steps": [{"run": "python -m pytest tests/test_key_pool.py -q"}]}}})


def test_selector_rejects_unrelated_paths():
    # Negative control: a selector that matched everything would make the boundary
    # assertions vacuously green.
    assert not _selects_path({"weaver/**"}, _GUARD_FILE)
    assert not _selects_path({"tests/test_key_pool.py"}, "tests/fixtures/baseline_node_set.txt")
    # `*` does not cross a directory boundary.
    assert not _selects_path({"tests/*.txt"}, "tests/fixtures/baseline_node_set.txt")


def test_negative_control_flags_a_guard_workflow_that_does_not_select_itself():
    """The selection predicate must reject a guard that is not its own trigger."""
    synthetic = {"on": {"pull_request": {"paths": ["api/**"]}}}
    paths = _path_filter(_trigger_block(synthetic), "pull_request")
    assert paths is not None
    assert not _selects_path(paths, _GUARD_FILE), (
        "a workflow selected only by api/** must not count as selecting the guard"
    )


def test_negative_control_flags_a_workflow_that_omits_a_published_doc():
    """The input-coverage assertion must reject a filter missing one doc.

    Reproduces the measured defect: the filter named the guard and its fixtures but not
    the documents the guard also judges, so editing `.bootstrap/01_STATE.md` changed what
    the guard asserts without executing it.
    """
    docs = _guard_published_docs()
    assert docs, "the guard must publish the documents it reconciles"
    incomplete = set(_GUARD_INPUTS) | set(docs[:-1])
    omitted = docs[-1]
    assert not _selects_path(incomplete, omitted), (
        f"a filter omitting {omitted!r} must not count as covering the guard's inputs"
    )


def test_published_doc_list_is_read_from_the_guard_not_restated():
    """The input list is derived, not duplicated — a stale copy would be vacuous."""
    docs = _guard_published_docs()
    assert "MISSION.md" in docs
    source = (ROOT / _GUARD_FILE).read_text(encoding="utf-8")
    assert "FINGERPRINT_DOCS = [" in source, (
        "the guard must keep declaring FINGERPRINT_DOCS as a module-level literal; "
        "this test reads it by AST"
    )


# ---------------------------------------------------------------------------
# The invariants, over every workflow that runs the fingerprint guard
# ---------------------------------------------------------------------------


def test_a_workflow_executes_the_fingerprint_guard():
    """The reconciliation must be executed somewhere, not only invoked by hand."""
    assert _guard_workflows(), (
        f"no workflow runs {_GUARD_FILE}; the baseline reconciliation is decoration "
        f"and holds only when a human runs it by hand"
    )


@pytest.mark.parametrize("name", _guard_workflows())
def test_guard_workflow_is_selected_by_the_guard_and_its_fixtures(name: str):
    """A gate must be selected by the surfaces it judges."""
    workflow = _load(WORKFLOWS / name)
    paths = _path_filter(_trigger_block(workflow), "pull_request")
    if paths is None:
        # `pull_request` is undeclared or unfiltered; an unfiltered event already
        # selects every path, including the guard and its fixtures.
        return
    for surface in _GUARD_INPUTS:
        assert _selects_path(paths, surface), (
            f"{name} runs {_GUARD_FILE} on pull_request but is not selected by "
            f"{surface!r}; a change to what the guard asserts would not execute it"
        )
    # The guard's verdict also depends on the documents it reconciles against. Editing
    # one of them changes what the guard asserts, so it must execute the guard.
    for doc in _guard_published_docs():
        assert _selects_path(paths, doc), (
            f"{name} runs {_GUARD_FILE} on pull_request but is not selected by "
            f"{doc!r}; editing the document the guard judges would not execute it"
        )


@pytest.mark.parametrize("name", _guard_workflows())
def test_guard_workflow_checks_out_full_history(name: str):
    """The guard's node set is clone-depth sensitive, so history must be full."""
    workflow = _load(WORKFLOWS / name)
    checkouts = _checkout_steps(workflow)
    assert checkouts, f"{name} runs the fingerprint guard without an actions/checkout step"
    assert any(
        (step.get("with") or {}).get("fetch-depth") == 0 for step in checkouts
    ), (
        f"{name} runs {_GUARD_FILE} on a shallow checkout; the guard's node set "
        f"depends on repository history, so its verdict can differ from a full clone"
    )


@pytest.mark.parametrize("name", _guard_workflows())
def test_guard_workflow_judges_its_guard_step(name: str):
    """A step whose result cannot fail the job gates nothing."""
    workflow = _load(WORKFLOWS / name)
    for job in (workflow.get("jobs") or {}).values():
        for step in job.get("steps") or []:
            run = step.get("run")
            if isinstance(run, str) and _GUARD_FILE in run:
                assert step.get("continue-on-error") is not True, (
                    f"{name} runs {_GUARD_FILE} with continue-on-error, so the guard "
                    f"can fail without the job turning red"
                )
