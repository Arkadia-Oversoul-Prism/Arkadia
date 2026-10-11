"""Boundary guard: the verdict-step integrity guard must be executed in CI.

`tests/test_ci_verdict_step_integrity.py` asserts that a CI verdict step can
report failure. Its domain is the whole workflow corpus, so a commit that
rewrites a workflow — exactly the surface the guard judges — must run it. A
guard no workflow executes is decoration; this module keeps it executed.

The invariant is stated generically over every workflow that runs the guard:

1. Some workflow must run the guard on ``pull_request``.
2. Its ``paths`` filter must select **every tracked workflow file**, because the
   guard's domain is the whole corpus; a filter naming a handful of files is
   incomplete by construction, and the next masked verdict step is introduced in
   a workflow no entry selects.
3. The guard step must be able to fail the job (``continue-on-error`` off, no
   ``if: false``), at the step *and* the job level.
4. The executing workflow must be dispatchable, so the contract can be run
   against an exact revision on demand rather than only when a path matches.

The covered domain is derived from ``git ls-files`` at test time, never
restated, so a new workflow is judged by the same rule without editing this
file. A detector that accepted a mere *mention* of the guard would be
self-satisfying, so the executor is identified by tokenising the command:
``pytest`` must be the invoked command word and the guard an argument to it.
"""

from __future__ import annotations

import re
import shlex
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

_GUARD_FILE = "tests/test_ci_verdict_step_integrity.py"
_WIRING_FILE = "tests/test_ci_verdict_step_integrity_ci_wiring.py"
_WORKFLOW_FILE = ".github/workflows/ci-verdict-step-integrity.yml"

# The guard's domain: every tracked workflow file.
_WORKFLOW_GLOB = ".github/workflows/**"

# `\` + newline is a line continuation: the shell parses the continuation as
# part of the same command, so an invocation folded across it must be tokenised
# as one line. Splitting physical lines left `pytest` with a `\` argument and
# the target on the next line, so a folded invocation read as *no* execution.
_CONTINUATION = re.compile(r"\\\r?\n")


# ---------------------------------------------------------------------------
# Workflow loading
# ---------------------------------------------------------------------------


def _tracked_workflow_paths() -> list[str]:
    """Every tracked workflow file, repo-relative — the guard's own domain."""
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", ".github/workflows/*.yml"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [p for p in result.stdout.decode().split("\0") if p]


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _trigger_block(workflow: dict) -> dict:
    """The `on:` mapping. PyYAML parses bare `on` as boolean True."""
    block = workflow.get(True, workflow.get("on"))
    return block if isinstance(block, dict) else {}


def _path_filter(trigger_block: dict, event: str) -> set[str] | None:
    """The `paths` filter for one event, or None when it is unfiltered/undeclared."""
    event_block = trigger_block.get(event)
    if not isinstance(event_block, dict):
        return None
    paths = event_block.get("paths")
    return None if paths is None else set(paths)


def _jobs(workflow: dict) -> dict:
    return workflow.get("jobs") or {}


def _steps(job: dict) -> list[dict]:
    return [s for s in (job.get("steps") or []) if isinstance(s, dict)]


def _selects_path(path_filter: set[str] | None, path: str) -> bool:
    """Whether a `paths` filter selects a path, mirroring GitHub's glob syntax."""
    if path_filter is None:
        return True
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


# ---------------------------------------------------------------------------
# Executor detection — execution, not mention
# ---------------------------------------------------------------------------


def _tokenised_commands(run: str) -> list[list[str]]:
    """The command words of every non-comment line, with shell comments dropped."""
    commands: list[list[str]] = []
    for line in _CONTINUATION.sub(" ", run).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            tokens = shlex.split(stripped, comments=True)
        except ValueError:
            tokens = stripped.split()
        if tokens:
            commands.append(tokens)
    return commands


def _invokes_pytest_with(tokens: list[str], targets: set[str]) -> bool:
    """Whether these tokens invoke pytest with one of `targets` as an argument.

    ``pytest`` must be the invoked command word — ``pytest x`` directly, or
    ``python -m pytest x``. A token appearing *after* another command word
    (``echo pytest x``) is a mention, not an execution, so it does not count.
    """
    for index, token in enumerate(tokens):
        base = token.rsplit("/", 1)[-1]
        invoked = base == "pytest" and (index == 0 or tokens[index - 1] == "-m")
        if not invoked:
            continue
        for argument in tokens[index + 1 :]:
            for target in targets:
                if argument == target or argument.startswith(target + "::"):
                    return True
                # A directory argument (`pytest tests/`) executes the target too.
                if target.startswith(argument.rstrip("/") + "/"):
                    return True
    return False


def _guard_targets() -> set[str]:
    """The guard file and its containing directory."""
    return {_GUARD_FILE, _GUARD_FILE.rsplit("/", 1)[0]}


def _names_the_guard_file(tokens: list[str]) -> bool:
    """Whether pytest is invoked on the guard *file*, not merely its directory.

    A full-suite step (`pytest tests/`) executes the guard incidentally; a gate
    that *dedicates* a step to the guard names the file. Only the latter is the
    guard's execution surface, and only the latter is held to the whole-corpus
    selection invariant. The directory-expansion rule of
    ``_invokes_pytest_with`` is deliberately excluded here: `pytest tests/`
    matches by that rule, which is exactly the incidental case this excludes.
    """
    for index, token in enumerate(tokens):
        base = token.rsplit("/", 1)[-1]
        if not (base == "pytest" and (index == 0 or tokens[index - 1] == "-m")):
            continue
        for argument in tokens[index + 1 :]:
            if argument == _GUARD_FILE or argument.startswith(_GUARD_FILE + "::"):
                return True
    return False


def _workflows_matching(predicate) -> list[str]:
    found: list[str] = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        workflow = _load(path)
        for job in _jobs(workflow).values():
            if not isinstance(job, dict):
                continue
            for step in _steps(job):
                run = step.get("run")
                if isinstance(run, str) and predicate(run):
                    found.append(path.name)
                    break
    return found


def _executing_workflows() -> list[str]:
    """Workflow files that invoke pytest on the guard, file or directory."""
    return _workflows_matching(
        lambda run: any(
            _invokes_pytest_with(c, _guard_targets())
            for c in _tokenised_commands(run)
        )
    )


def _dedicated_executing_workflows() -> list[str]:
    """Workflow files that name the guard file in a pytest invocation."""
    return _workflows_matching(
        lambda run: any(
            _names_the_guard_file(c) for c in _tokenised_commands(run)
        )
    )


def _is_dispatchable(workflow: dict) -> bool:
    return "workflow_dispatch" in _trigger_block(workflow)


def _step_can_fail(job: dict, step: dict) -> bool:
    """Whether a failing guard actually fails the job."""
    if step.get("continue-on-error") is True or job.get("continue-on-error") is True:
        return False
    for holder in (step, job):
        condition = holder.get("if")
        if isinstance(condition, str) and condition.strip() in {"false", "${{ false }}"}:
            return False
    return True


# ---------------------------------------------------------------------------
# Detector negative controls
# ---------------------------------------------------------------------------


def test_detector_accepts_a_real_pytest_invocation():
    assert _invokes_pytest_with(
        ["python", "-m", "pytest", _GUARD_FILE, "-q"], _guard_targets()
    )
    assert _invokes_pytest_with(["pytest", _GUARD_FILE], _guard_targets())
    assert _invokes_pytest_with(["pytest", "tests/", "-q"], _guard_targets())


def test_detector_rejects_a_mention_without_execution():
    # Negative control: the echo-mention hole. A detector that matched the word
    # `pytest` anywhere would pass this and be self-satisfying.
    assert not _invokes_pytest_with(
        ["echo", "pytest", _GUARD_FILE], _guard_targets()
    )
    assert not _invokes_pytest_with(["echo", _GUARD_FILE], _guard_targets())
    # A comment is dropped before tokenising.
    assert not any(
        _invokes_pytest_with(c, _guard_targets())
        for c in _tokenised_commands(f"# pytest {_GUARD_FILE}\necho done")
    )


def test_detector_rejects_an_unrelated_target():
    assert not _invokes_pytest_with(
        ["python", "-m", "pytest", "tests/test_other.py", "-q"], _guard_targets()
    )


def test_detector_accepts_an_invocation_folded_across_a_continuation():
    # Negative control: `\` + newline is a line continuation, so the shell runs
    # this as one command. Splitting physical lines gave pytest a `\` argument
    # and stranded the target on the next line, so a folded invocation of the
    # guard read as *no* execution — the gate looked unwired.
    folded = f"python -m pytest \\\n  {_GUARD_FILE} -q"
    assert any(
        _invokes_pytest_with(c, _guard_targets())
        for c in _tokenised_commands(folded)
    ), _tokenised_commands(folded)
    assert any(
        _names_the_guard_file(c) for c in _tokenised_commands(folded)
    ), _tokenised_commands(folded)


def test_step_can_fail_detector_sees_both_exemption_levels():
    assert _step_can_fail({}, {"run": "pytest x"})
    assert not _step_can_fail({}, {"run": "pytest x", "continue-on-error": True})
    assert not _step_can_fail({"continue-on-error": True}, {"run": "pytest x"})
    assert not _step_can_fail({}, {"run": "pytest x", "if": "false"})


# ---------------------------------------------------------------------------
# The invariants, over the live tracked workflow corpus
# ---------------------------------------------------------------------------


def test_some_workflow_executes_the_guard():
    """The guard must not be decoration: something must run it."""
    assert _executing_workflows(), (
        f"no workflow invokes pytest on {_GUARD_FILE}; the guard runs only when "
        "a human calls it by hand"
    )


@pytest.mark.parametrize("name", sorted(set(_dedicated_executing_workflows())))
def test_executing_workflow_selects_the_whole_corpus(name: str):
    """The filter must select every tracked workflow, the guard's own domain."""
    workflow = _load(WORKFLOWS / name)
    paths = _path_filter(_trigger_block(workflow), "pull_request")
    missing = [
        p for p in _tracked_workflow_paths() if not _selects_path(paths, p)
    ]
    assert not missing, (
        f"{name} executes {_GUARD_FILE} but its pull_request filter does not "
        f"select {len(missing)} tracked workflow file(s): {missing[:5]}. The "
        "guard judges the whole corpus, so an unselected workflow is judged by "
        "nothing."
    )


@pytest.mark.parametrize("name", sorted(set(_dedicated_executing_workflows())))
def test_executing_workflow_selects_itself_and_the_guard(name: str):
    workflow = _load(WORKFLOWS / name)
    paths = _path_filter(_trigger_block(workflow), "pull_request")
    assert _selects_path(paths, f".github/workflows/{name}"), (
        f"{name} does not select its own file; its wiring can be rewritten "
        "without being judged"
    )
    assert _selects_path(paths, _GUARD_FILE), (
        f"{name} does not select {_GUARD_FILE}"
    )


@pytest.mark.parametrize("name", sorted(set(_dedicated_executing_workflows())))
def test_executing_workflow_step_can_fail(name: str):
    workflow = _load(WORKFLOWS / name)
    found = False
    for job in _jobs(workflow).values():
        if not isinstance(job, dict):
            continue
        for step in _steps(job):
            run = step.get("run")
            if not isinstance(run, str):
                continue
            if not any(
                _invokes_pytest_with(c, _guard_targets())
                for c in _tokenised_commands(run)
            ):
                continue
            found = True
            assert _step_can_fail(job, step), (
                f"{name} runs the guard in a step that cannot fail the job; the "
                "guard would be reported as passing whatever it found"
            )
    assert found


@pytest.mark.parametrize("name", sorted(set(_dedicated_executing_workflows())))
def test_executing_workflow_is_dispatchable(name: str):
    """An exact revision must be checkable on demand, not only when a path matches."""
    assert _is_dispatchable(_load(WORKFLOWS / name)), (
        f"{name} executes the guard but carries no workflow_dispatch; a revision "
        "that touches none of its paths has no guard execution and cannot be "
        "checked against an exact revision"
    )


def test_the_dedicated_workflow_exists():
    """The recorded execution surface is the dedicated workflow."""
    assert (WORKFLOWS / Path(_WORKFLOW_FILE).name).is_file()


def test_wiring_file_is_selected_by_the_workflow_it_guards():
    """The wiring guard is itself an input whose edit must run the gate."""
    paths = _path_filter(
        _trigger_block(_load(WORKFLOWS / Path(_WORKFLOW_FILE).name)), "pull_request"
    )
    assert _selects_path(paths, _WIRING_FILE), (
        f"{_WORKFLOW_FILE} does not select {_WIRING_FILE}; this guard can be "
        "changed without being executed"
    )
