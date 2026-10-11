"""Boundary guard: the CI trigger-coverage contract must be executed in CI.

`tests/test_ci_gate_trigger_coverage.py` states the invariant that a CI gate must be
selected by the surfaces it judges, and carries its own negative controls. As of
`main` @ `36df0ea8` it was executed by *no* workflow: its only execution site was the
full-suite step inside `provider-routing.yml`, which is path-filtered to `weaver/**`,
`providers/**` and a handful of named files. A commit that changes only a workflow —
exactly the surface the guard judges — never ran it.

Measured on `main` @ `36df0ea8`: commit `7097d6a4` added
`openapi-security-metadata.yml` with `tests/test_forge_openapi_security_boundary.py`
in the `pull_request` filter but not in the `push` filter. The guard's node failed on
`main`, and that commit's only check-run was the secret scan. A guard no gate runs is
decoration; this module keeps it executed.

The invariant is stated generically over every workflow that runs the guard:

1. Some workflow must run the guard on ``pull_request``.
2. Its ``paths`` filter must select **every tracked workflow file**, because the
   guard's domain is the whole workflow corpus. A filter naming a handful of files is
   incomplete by construction: the next asymmetric filter is introduced in a workflow
   no entry selects, and the guard never runs on the pull request that introduces it.
3. The guard step must be able to fail the job (``continue-on-error`` off).

The covered domain is derived from ``git ls-files`` at test time, never restated, so a
new workflow is judged by the same rule without editing this file.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

_GUARD_FILE = "tests/test_ci_gate_trigger_coverage.py"
_WIRING_FILE = "tests/test_ci_gate_trigger_coverage_ci_wiring.py"
_WORKFLOW_FILE = ".github/workflows/ci-gate-trigger-coverage.yml"


def _tracked_workflow_paths() -> list[str]:
    """Every tracked workflow file, repo-relative — the guard's own domain."""
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", ".github/workflows/*.yml"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return sorted(p for p in result.stdout.split("\0") if p)


def _workflow_paths() -> list[Path]:
    return sorted(WORKFLOWS.glob("*.yml"))


def _load(path: Path | str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _trigger_block(workflow: dict) -> dict:
    """The ``on:`` mapping (PyYAML parses the bare key ``on`` as boolean True)."""
    block = workflow.get(True, workflow.get("on"))
    return block if isinstance(block, dict) else {}


def _path_filter(trigger_block: dict, event: str) -> set[str] | None:
    event_block = trigger_block.get(event)
    if not isinstance(event_block, dict):
        return None
    paths = event_block.get("paths")
    return None if paths is None else set(paths)


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Compile a GitHub ``paths`` glob to a whole-string regex.

    ``**/`` matches zero or more leading path segments, a remaining ``**`` matches
    anything including ``/``, and ``*``/``?`` match within a single path segment.
    Every other character is literal. Placeholders keep the single-``*`` rewrite from
    clobbering the ``**`` expansion.
    """
    placeholders = {"\x00": "**/", "\x01": "**", "\x02": "*", "\x03": "?"}
    tokens = {"\x00": "(?:.*/)?", "\x01": ".*", "\x02": "[^/]*", "\x03": "[^/]"}
    body = pattern
    for ph, token in placeholders.items():
        body = body.replace(token, ph)
    body = body.replace(".", r"\.")
    for ph, rx in tokens.items():
        body = body.replace(ph, rx)
    return re.compile("^" + body + "$")


def _selects_path(path_filter: set[str], path: str) -> bool:
    """Whether a ``paths`` filter selects a literal path, mirroring GitHub's globs."""
    return any(_glob_to_regex(pattern).match(path) for pattern in path_filter)


def _steps(workflow: dict) -> list[dict]:
    seen: list[dict] = []
    for job in (workflow.get("jobs") or {}).values():
        seen.extend(job.get("steps") or [])
    return seen


def _guard_steps(workflow: dict) -> list[dict]:
    """Steps whose ``run:`` command names the trigger-coverage guard file."""
    return [
        step
        for step in _steps(workflow)
        if isinstance(step.get("run"), str) and _GUARD_FILE in step["run"]
    ]


def _runs_guard(workflow: dict) -> bool:
    return bool(_guard_steps(workflow))


def _guard_workflows() -> list[str]:
    return [p.name for p in _workflow_paths() if _runs_guard(_load(p))]


# ---------------------------------------------------------------- detector controls


def test_runs_guard_detector_distinguishes_the_forms():
    runs = {"jobs": {"j": {"steps": [{"run": "python -m pytest tests/test_ci_gate_trigger_coverage.py -q"}]}}}
    other = {"jobs": {"j": {"steps": [{"run": "python -m py_compile api/main.py"}]}}}
    assert _runs_guard(runs)
    assert not _runs_guard(other)


def test_selector_accepts_the_forms_github_uses():
    assert _selects_path({".github/workflows/**"}, ".github/workflows/openapi-security-metadata.yml")
    assert _selects_path({".github/workflows/**"}, ".github/workflows/ci-gate-trigger-coverage.yml")
    assert _selects_path({"**"}, "anything/at/all.py")


def test_selector_rejects_an_incomplete_filter():
    # The incomplete shape the negative control below feeds to the invariant.
    assert not _selects_path({".github/workflows/boot-syntax.yml"}, ".github/workflows/openapi-security-metadata.yml")
    assert not _selects_path({"tests/ci_gate_trigger_coverage.py"}, "tests/test_ci_gate_trigger_coverage.py")


# ---------------------------------------------------------------- the invariant


def test_a_workflow_executes_the_trigger_coverage_guard():
    """A guard no gate runs is decoration, not a boundary."""
    assert _guard_workflows(), (
        "no workflow runs tests/test_ci_gate_trigger_coverage.py; the CI "
        "trigger-parity contract holds only when a human runs the suite by hand"
    )


@pytest.mark.parametrize("name", _guard_workflows())
def test_guard_workflow_is_selected_by_every_tracked_workflow(name: str):
    """The filter must cover the guard's whole domain, not a remembered subset."""
    workflow = _load(WORKFLOWS / name)
    paths = _path_filter(_trigger_block(workflow), "pull_request")
    assert paths is None or paths, f"{name} does not trigger on pull_request with paths"
    domain = _tracked_workflow_paths()
    assert domain, "git ls-files returned no workflow files; repository layout changed"
    omitted = [p for p in domain if not _selects_path(paths, p)]
    assert not omitted, (
        f"{name} runs the trigger-coverage guard but its pull_request paths filter "
        f"omits {len(omitted)} tracked workflow file(s), e.g. {omitted[:5]}"
    )


@pytest.mark.parametrize("name", _guard_workflows())
def test_guard_step_can_fail_the_job(name: str):
    """A guard step that cannot fail the job is not a gate."""
    workflow = _load(WORKFLOWS / name)
    for step in _guard_steps(workflow):
        assert not step.get("continue-on-error", False), (
            f"{name} runs the trigger-coverage guard with continue-on-error, so the "
            "job stays green when a workflow declares an asymmetric path filter"
        )


# ---------------------------------------------------------------- control workflow


def test_wiring_workflow_selects_its_own_file():
    """A gate that rejects the branch it watches is the omission class again."""
    workflow = _load(ROOT / _WORKFLOW_FILE)
    paths = _path_filter(_trigger_block(workflow), "pull_request")
    assert paths is not None
    assert _selects_path(paths, _WORKFLOW_FILE)
    assert _selects_path(paths, _WIRING_FILE)
