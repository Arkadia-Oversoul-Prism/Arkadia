"""Boundary guard: the boot-syntax boundary must be executed in CI.

`tests/test_boot_syntax_boundary.py` proves that ``api/main.py`` (the P1-A boot
surface) and every tracked Python file parse. As introduced by #297, no workflow ran
it — `grep -rn test_boot_syntax .github/workflows/` returned 0 — so the boundary held
only when a human invoked the suite by hand. A guard no workflow executes is
decoration; this module keeps it executed.

The invariant is stated generically over every workflow that runs the guard:

1. Some workflow must run the guard on ``pull_request``.
2. Its ``paths`` filter must select **every tracked Python file**, because the guard's
   domain is the whole tracked Python corpus. A filter naming a handful of files is
   incomplete by construction: the next boot-broken module is added at a path no entry
   selects, and the guard never runs on the pull request that introduces it.
3. The guard step must be able to fail the job (``continue-on-error`` off).

The covered domain is derived from ``git ls-files`` at test time, never restated, so a
new tracked module is judged by the same rule without editing this file.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

_GUARD_FILE = "tests/test_boot_syntax_boundary.py"
_WIRING_FILE = "tests/test_boot_syntax_ci_wiring.py"
_WORKFLOW_FILE = ".github/workflows/boot-syntax.yml"


def _tracked_python_paths() -> list[str]:
    """Every tracked ``.py`` file, repo-relative — the guard's own domain."""
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", "*.py"],
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

    ``**/`` matches zero or more leading path segments (so ``**/*.py`` selects
    ``weaver.py`` as well as ``api/main.py``), a remaining ``**`` matches anything
    including ``/``, and ``*``/``?`` match within a single path segment. Every other
    character is literal. Placeholders keep the single-``*`` rewrite from clobbering
    the ``**`` expansion.
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
    """Steps whose ``run:`` command names the boot-syntax guard file."""
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
    runs = {"jobs": {"j": {"steps": [{"run": "python -m pytest tests/test_boot_syntax_boundary.py -q"}]}}}
    other = {"jobs": {"j": {"steps": [{"run": "python -m py_compile api/main.py"}]}}}
    assert _runs_guard(runs)
    assert not _runs_guard(other)


def test_selector_accepts_the_forms_github_uses():
    filt = {".github/workflows/boot-syntax.yml", "**/*.py", "*.py"}
    assert _selects_path(filt, "api/main.py")
    assert _selects_path(filt, "weaver.py")
    assert _selects_path(filt, "lab/engineering_lab/substrate.py")


def test_selector_rejects_an_incomplete_filter():
    # The incomplete shape the negative control below feeds to the invariant.
    filt = {".github/workflows/boot-syntax.yml", "api/main.py"}
    assert _selects_path(filt, "api/main.py")
    assert not _selects_path(filt, "kernel/tts.py")


# ---------------------------------------------------------------- the invariant


def test_a_workflow_executes_the_boot_syntax_guard():
    """A guard no gate runs is decoration, not a boundary."""
    assert _guard_workflows(), (
        "no workflow runs tests/test_boot_syntax_boundary.py; the P1-A boot boundary "
        "holds only when a human runs the suite by hand"
    )


@pytest.mark.parametrize("name", _guard_workflows())
def test_guard_workflow_is_selected_by_every_tracked_python_file(name: str):
    """The filter must cover the guard's whole domain, not a remembered subset."""
    workflow = _load(WORKFLOWS / name)
    paths = _path_filter(_trigger_block(workflow), "pull_request")
    assert paths is None or paths, f"{name} does not trigger on pull_request with paths"
    domain = _tracked_python_paths()
    assert domain, "git ls-files returned no Python files; repository layout changed"
    omitted = [p for p in domain if not _selects_path(paths, p)]
    assert not omitted, (
        f"{name} runs the boot-syntax guard but its pull_request paths filter omits "
        f"{len(omitted)} tracked Python file(s), e.g. {omitted[:5]}"
    )


@pytest.mark.parametrize("name", _guard_workflows())
def test_guard_step_can_fail_the_job(name: str):
    """A guard step that cannot fail the job is not a gate."""
    workflow = _load(WORKFLOWS / name)
    for step in _guard_steps(workflow):
        assert not step.get("continue-on-error", False), (
            f"{name} runs the boot-syntax guard with continue-on-error, so the job "
            "stays green when a tracked Python file stops parsing"
        )


# ---------------------------------------------------------------- control workflow


def test_wiring_workflow_selects_its_own_file():
    """A gate that rejects the branch it watches is the omission class again."""
    workflow = _load(ROOT / _WORKFLOW_FILE)
    paths = _path_filter(_trigger_block(workflow), "pull_request")
    assert paths is not None
    assert _selects_path(paths, _WORKFLOW_FILE)
    assert _selects_path(paths, _WIRING_FILE)
