"""A judging CI step must run the suite, not abort before reaching it.

`provider-routing.yml` is the only workflow selected by `weaver/**` that runs the
whole suite, so it is the sole CI surface that can execute a `weaver/**` guard
(for example `tests/test_attention_truthfulness.py`, PR #323). Its "Broader test
suite" step ran a bare `python -m pytest tests/ -q`. The known CE-01
`weaver.autonomy` module-vs-package collision makes a bare `tests/` run
*interrupt* — "Interrupted: 1 error during collection" — so pytest exits before
executing any test. Measured on the live PR #323 run `37395288765`: the step died
at the collection error and `test_attention_truthfulness.py` executed **zero**
times. The guard passed locally and in no CI job; a regression it was written to
catch would have reached `main` unjudged.

The repair is the documented reproducibility flag: `--continue-on-collection-errors`.
It does not hide debt — the collection error and the pre-existing failures are
still reported — it only stops the session from aborting before the suite runs.

These tests read the workflows as text and as YAML. Each detector has a negative
control, so the guard cannot be disarmed by rewriting a workflow without
reddening a control.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

CONTINUE_FLAG = "--continue-on-collection-errors"

# `pytest` followed by a directory target (`tests/` or `tests`) and no explicit
# test node. A file-targeted invocation (`pytest tests/test_x.py`) is already
# immune to unrelated collection errors and is not a broad-suite step.
_PYTEST_INVOCATION = re.compile(r"pytest\s+(?P<targets>[^\n|&]*)")
_NODE = re.compile(r"\S+\.py(?:::\S+)?")


def _broad_suite_invocations(text: str) -> list[str]:
    """Return pytest invocations that run a whole test directory."""
    found: list[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        for match in _PYTEST_INVOCATION.finditer(line):
            targets = match.group("targets")
            tokens = targets.split()
            if any(token in {"tests", "tests/"} for token in tokens) and not _NODE.search(
                targets
            ):
                found.append(match.group(0).strip())
    return found


def _workflow_files() -> list[Path]:
    return sorted(WORKFLOWS.glob("*.yml"))


def _steps(path: Path) -> list[dict]:
    workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
    steps: list[dict] = []
    for job in (workflow.get("jobs") or {}).values():
        if isinstance(job, dict):
            steps.extend(step for step in (job.get("steps") or []) if isinstance(step, dict))
    return steps


def _broad_suite_steps(path: Path) -> list[dict]:
    return [step for step in _steps(path) if _broad_suite_invocations(step.get("run") or "")]


def _judging_broad_suite_steps(path: Path) -> list[dict]:
    """Broad-suite steps whose result can fail the job (not `continue-on-error`)."""
    return [step for step in _broad_suite_steps(path) if step.get("continue-on-error") is not True]


def _workflow_triggers(path: Path) -> dict:
    workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
    # PyYAML parses the bare key `on` as the boolean True.
    trigger = workflow.get(True, workflow.get("on")) or {}
    return trigger if isinstance(trigger, dict) else {}


def test_detector_finds_the_known_broad_suite_workflows():
    """Sanity: the detector actually matches the workflows that run the suite."""
    hits = {p.name for p in _workflow_files() if _broad_suite_steps(p)}
    assert {"provider-routing.yml", "sg-02-fe-2-v.yml"} <= hits


@pytest.mark.parametrize("path", _workflow_files(), ids=lambda p: p.name)
def test_judging_broad_suite_steps_continue_past_collection_errors(path: Path):
    """A step that can fail the job must actually run the suite.

    A judging step that aborts at the CE-01 collection error executes zero tests
    and reports nothing, so every guard it collects goes unjudged while the job
    still turns red for an unrelated reason. `continue-on-error` steps are out of
    scope: they do not gate anything, and this repair is bounded to the surface
    that does.
    """
    for step in _judging_broad_suite_steps(path):
        run = step.get("run") or ""
        assert CONTINUE_FLAG in run, (
            f"{path.name}: judging step {step.get('name')!r} runs the whole suite "
            f"without {CONTINUE_FLAG}; the known collection error interrupts the "
            f"session and no test executes"
        )


def test_a_judging_broad_suite_surface_exists():
    """The suite must be *judged* somewhere, not only reported."""
    judged = [
        (path.name, step.get("name"))
        for path in _workflow_files()
        for step in _judging_broad_suite_steps(path)
    ]
    assert judged, (
        "no workflow judges a broad-suite run; the suite result cannot gate anything"
    )


def test_provider_routing_remains_the_weaver_guard_surface():
    """The judging surface for `weaver/**` must stay selected by `weaver/**`."""
    triggers = _workflow_triggers(WORKFLOWS / "provider-routing.yml")
    pr_paths = set((triggers.get("pull_request") or {}).get("paths") or [])
    assert "weaver/**" in pr_paths, (
        "provider-routing.yml is no longer selected by weaver/**; a change to a "
        "weaver guard would then be judged by no workflow"
    )
    judging = _judging_broad_suite_steps(WORKFLOWS / "provider-routing.yml")
    assert judging, "provider-routing.yml no longer judges a broad-suite run"
    assert all(CONTINUE_FLAG in (step.get("run") or "") for step in judging)


def test_weaver_guard_is_reachable_in_ci():
    """Reachability, not selection: a `weaver/**` workflow must reach a whole-suite run.

    A guard under `weaver/**` (for example `tests/test_attention_truthfulness.py`,
    PR #323) is auto-collected by a broad-suite run, but only if a workflow that is
    selected by `weaver/**` actually reaches the suite. This asserts the workflow
    property, not a specific file, so it holds whether or not a given guard is
    present on the revision.
    """
    reachable = []
    for path in _workflow_files():
        triggers = _workflow_triggers(path)
        pr_paths = set((triggers.get("pull_request") or {}).get("paths") or [])
        if "weaver/**" not in pr_paths:
            continue
        text = path.read_text(encoding="utf-8")
        if "pytest tests/" in text and CONTINUE_FLAG in text:
            reachable.append(path.name)
    assert reachable, (
        "no workflow selected by weaver/** reaches a whole-suite run past the "
        "collection error; a weaver guard would execute zero times in CI"
    )


def test_this_guard_is_selected_by_its_workflow():
    """The guard must be selected by the workflow it audits, or it is decoration."""
    triggers = _workflow_triggers(WORKFLOWS / "provider-routing.yml")
    paths = set((triggers.get("pull_request") or {}).get("paths") or [])
    assert "tests/test_ci_suite_collection_continuation.py" in paths, (
        "provider-routing.yml does not select this guard; the workflow it audits "
        "could be edited without executing it"
    )


def test_negative_control_detector_flags_the_pre_fix_invocation():
    """The detector must flag the exact pre-fix line, or it proves nothing."""
    pre_fix = "          python -m pytest tests/ -q"
    found = _broad_suite_invocations(pre_fix)
    assert found, "detector failed to flag a bare broad-suite invocation"
    assert CONTINUE_FLAG not in found[0]


def test_negative_control_detector_ignores_file_targeted_invocations():
    """A file-targeted step is already immune and must not be flagged."""
    targeted = "          python -m pytest tests/test_attention_truthfulness.py -q"
    assert _broad_suite_invocations(targeted) == []


def test_negative_control_continue_on_error_step_is_not_a_judging_surface():
    """`continue-on-error` must disqualify a step from being a judging surface."""
    step = {
        "name": "Broader test suite",
        "run": "python -m pytest tests/ -q 2>&1 | tee cp10-backend.log",
        "continue-on-error": True,
    }
    assert _broad_suite_invocations(step["run"]), "flagged invocation must be detected"
    assert not (
        step.get("continue-on-error") is not True
        and bool(_broad_suite_invocations(step["run"]))
    ), "a continue-on-error step must not count as a judging surface"


# ---------------------------------------------------------------------------
# Reachability, independent of gating
#
# The judging-surface invariant above is scoped to `continue-on-error: false`, so
# it is silent on a non-gating broad-suite step. The CP10-B step in
# `sg-02-fe-2-v.yml` is exactly that shape, and it is the *only* broad-suite
# surface selected by `lab/**` and `spiral_grove/**`. Measured at `main`
# `26521e24` (run `38240790826`), it died at
# `Interrupted: 1 error during collection` — `1 skipped, 1 error in 10.05s` —
# so 177 tests reachable only through a broad-suite run executed zero times,
# while the step's name still read like coverage.
#
# Gating and reaching are different properties. A step that never reaches the
# suite cannot report, gate, or cover anything; the flag that makes it reach is
# orthogonal to `continue-on-error`, so this invariant is stated over *every*
# broad-suite step rather than only the judging ones.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", _workflow_files(), ids=lambda p: p.name)
def test_every_broad_suite_step_reaches_the_suite(path: Path):
    """Every broad-suite step — gating or not — must run the suite.

    A bare `pytest tests/` aborts at the CE-01 collision, so such a step reports
    nothing and the guards it collects go unexecuted. This is the defect measured
    on the CP10-B step; it is *not* about the step's gating status.
    """
    for step in _broad_suite_steps(path):
        run = step.get("run") or ""
        assert CONTINUE_FLAG in run, (
            f"{path.name}: broad-suite step {step.get('name')!r} runs the whole "
            f"suite without {CONTINUE_FLAG}; the known collection error interrupts "
            f"the session and zero tests execute, so the step reports nothing"
        )


def test_the_cp10b_step_is_a_broad_suite_reachability_instance():
    """Pin the repaired surface so a rewrite of it is a visible change."""
    steps = _broad_suite_steps(WORKFLOWS / "sg-02-fe-2-v.yml")
    assert steps, "sg-02-fe-2-v.yml no longer has a broad-suite step"
    backend = [s for s in steps if s.get("id") == "backend"]
    assert backend, "the CP10-B broad-suite step (`id: backend`) is gone"
    assert CONTINUE_FLAG in (backend[0].get("run") or ""), (
        "the CP10-B step must continue past collection errors, or it runs zero tests"
    )


def test_negative_control_reachability_detector_flags_the_pre_fix_step():
    """The reachability detector must flag the exact pre-fix CP10-B line."""
    pre_fix = {
        "name": "CP10-B broader backend regression",
        "id": "backend",
        "continue-on-error": True,
        "run": "python -m pytest tests/ -q 2>&1 | tee cp10-backend.log",
    }
    assert _broad_suite_invocations(pre_fix["run"]), "the shape must be recognised"
    assert CONTINUE_FLAG not in pre_fix["run"], (
        "the pre-fix shape must lack the flag, or this control proves nothing"
    )


def test_positive_control_reachability_detector_accepts_the_repaired_step():
    repaired = {
        "name": "CP10-B broader backend regression",
        "id": "backend",
        "continue-on-error": True,
        "run": "python -m pytest tests/ -q --continue-on-collection-errors 2>&1 | tee cp10-backend.log",
    }
    assert _broad_suite_invocations(repaired["run"]), "still a broad-suite step"
    assert CONTINUE_FLAG in repaired["run"]
