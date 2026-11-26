"""Boundary guard: a change to `api/main.py` must execute the line-budget assertion.

`tests/architecture/test_layer_boundaries.py::test_api_main_line_count_within_budget`
holds `api/main.py` to 2600 lines. Measured at `main` `bb19aabd`: the file is **2597**
lines, so three added lines breach a stated architectural budget — and no workflow that
selects `api/**` executed the architecture suite. `provider-routing.yml` runs
`python -m pytest tests/architecture -q`, but its `paths` filter names
`tests/architecture/**`, `weaver/**` and `providers/**` and not `api/**`, so a commit
that grows the monolith reaches `main` with the assertion executed nowhere. This is the
same "a guard no gate executes is decoration" class already closed for
`test_baseline_fingerprint.py`, `test_boot_syntax_boundary.py` and
`test_solspire_route_composition.py`.

The invariant is stated over **every** workflow, not against one file:

1. A workflow that *mentions* the architecture suite — as a trigger path or in a
   command — must actually **execute** it. A path that appears only in prose, or a
   command that merely prints `pytest tests/architecture`, is not an execution.
2. Some workflow must both execute the suite and be selected by a change to
   `api/main.py`, so the budget is judged by the surface it constrains. Selecting the
   API surface is the load-bearing condition: executing the suite somewhere else does
   not judge an API commit.
3. Such a workflow must be dispatchable, so the budget can be checked against an exact
   revision on demand.
4. An executing step must be able to fail the run: no step- or job-level
   `continue-on-error`, and no `if: false`.

The detector is proven against each form it claims to catch (negative controls), so
rewriting a workflow cannot silently disarm the boundary.

Why this is a separate gate rather than a wider `provider-routing.yml`: that workflow
also runs the full suite, which carries pre-existing `main` debt, so widening its
filter to `api/**` would turn every API pull request red for debt it did not
introduce. `tests/test_ci_gate_trigger_coverage.py` records that widening as deferred
for exactly this reason; this guard takes the narrow route instead of the deferred one.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

# The assertion this gate exists to execute, and the surface whose change must select it.
_BUDGET_ASSERTION = "tests/architecture/test_layer_boundaries.py"
_ARCHITECTURE_DIR = "tests/architecture"
_API_SURFACE = "api/main.py"

_FALSEY_CONDITIONS = {"false", "${{ false }}", "0"}


# --------------------------------------------------------------------------- YAML


def _workflow_paths() -> list[Path]:
    return sorted(WORKFLOWS.glob("*.yml"))


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _trigger_block(workflow: dict) -> dict:
    """The `on:` mapping. PyYAML parses a bare `on` key as boolean True."""
    block = workflow.get(True, workflow.get("on"))
    return block if isinstance(block, dict) else {}


def _path_filter(trigger_block: dict, event: str) -> set[str] | None:
    event_block = trigger_block.get(event)
    if not isinstance(event_block, dict):
        return None
    paths = event_block.get("paths")
    return None if paths is None else set(paths)


def _steps(workflow: dict):
    for job_name, job in (workflow.get("jobs") or {}).items():
        for step in (job or {}).get("steps") or []:
            yield job_name, job or {}, step or {}


# ------------------------------------------------------------------- command parse


def _run_lines(step: dict) -> list[list[str]]:
    """Each effective shell command in a step's `run`, tokenised.

    Comment lines and inline comments are dropped, so a path that appears only in
    prose is not a command.
    """
    run = step.get("run")
    if not isinstance(run, str):
        return []
    commands: list[list[str]] = []
    for line in run.splitlines():
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


def _command_tokens(tokens: list[str]) -> list[str]:
    """The tokens from the invoked executable onward (leading `env`/`A=1` dropped)."""
    i = 0
    if tokens and tokens[0] == "env":
        i = 1
    while i < len(tokens):
        head = tokens[i].split("=", 1)[0]
        if "=" in tokens[i] and head.isidentifier():
            i += 1
            continue
        break
    return tokens[i:]


def _pytest_command_index(tokens: list[str]) -> int | None:
    """Index of the `pytest` word only when it is the invoked command.

    `pytest x` and `python -m pytest x` count; `echo pytest x` does not.
    """
    cmd = _command_tokens(tokens)
    for i, tok in enumerate(cmd):
        if tok == "pytest" or tok.endswith("/pytest"):
            if i == 0 or cmd[i - 1] == "-m":
                return i
    return None


def _pytest_runs_architecture(tokens: list[str]) -> bool:
    """Whether this command executes pytest over the architecture suite.

    The suite directory, a file inside it, a node-id on it, or the `tests` directory
    (which collects it) all count — the argument must reach the assertion.
    """
    idx = _pytest_command_index(tokens)
    if idx is None:
        return False
    for arg in _command_tokens(tokens)[idx + 1:]:
        if arg in (_ARCHITECTURE_DIR, _ARCHITECTURE_DIR + "/", "tests", "tests/"):
            return True
        if arg == _BUDGET_ASSERTION or arg.startswith(_BUDGET_ASSERTION + "::"):
            return True
        if arg.startswith(_ARCHITECTURE_DIR + "/"):
            return True
    return False


# ------------------------------------------------------------------ workflow audit


def _invocations(workflow: dict):
    """Steps that execute the architecture suite with pytest."""
    return [
        (name, job, step)
        for name, job, step in _steps(workflow)
        if any(_pytest_runs_architecture(cmd) for cmd in _run_lines(step))
    ]


def _is_falsey_condition(value: object) -> bool:
    return str(value).strip().lower() in _FALSEY_CONDITIONS


def _exemption(job: dict, step: dict) -> str | None:
    """Why an executing step could not fail the run, or None when it can."""
    if job.get("continue-on-error", False):
        return "job continue-on-error"
    if _is_falsey_condition(job.get("if", "")):
        return "job if: false"
    if _is_falsey_condition(step.get("if", "")):
        return "step if: false"
    if step.get("continue-on-error", False):
        return "step continue-on-error"
    return None


def _effective_invocations(workflow: dict):
    return [
        (name, job, step)
        for name, job, step in _invocations(workflow)
        if _exemption(job, step) is None
    ]


def _mentions_suite(workflow: dict) -> bool:
    """The suite appears as a trigger path or anywhere in a step's `run` text."""
    trigger = _trigger_block(workflow)
    for event in ("pull_request", "push"):
        if any(_ARCHITECTURE_DIR in p for p in (_path_filter(trigger, event) or set())):
            return True
    return any(_ARCHITECTURE_DIR in str(step.get("run", "")) for _, _, step in _steps(workflow))


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Translate a GitHub path filter glob into an anchored regex.

    `**` crosses separators, `*` does not, `?` matches one non-separator character.
    """
    out: list[str] = []
    i = 0
    while i < len(pattern):
        ch = pattern[i]
        if ch == "*":
            if pattern[i : i + 2] == "**":
                out.append(".*")
                i += 2
                continue
            out.append("[^/]*")
        elif ch == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(ch))
        i += 1
    return re.compile("^" + "".join(out) + "$")


def _selected(trigger_block: dict, concrete_path: str) -> bool:
    """Whether any declared `paths` filter selects the given concrete repository path."""
    for event in ("pull_request", "push"):
        for pattern in _path_filter(trigger_block, event) or set():
            if _glob_to_regex(pattern).match(concrete_path):
                return True
    return False


def _is_dispatchable(trigger_block: dict) -> bool:
    return "workflow_dispatch" in trigger_block


def _audit(workflow: dict) -> list[str]:
    """Defects that stop a workflow from judging the budget. Empty is a pass.

    A workflow that does not mention the suite is not a candidate and returns empty.
    """
    if not _mentions_suite(workflow):
        return []
    trigger = _trigger_block(workflow)
    defects: list[str] = []
    if not _effective_invocations(workflow):
        defects.append(
            "no effective step executes the architecture suite "
            "(a mention is not an execution; or the step is exempted by "
            "continue-on-error / if: false)"
        )
    if not _is_dispatchable(trigger):
        defects.append("no workflow_dispatch: budget not checkable on demand")
    if not _selected(trigger, _API_SURFACE):
        defects.append(f"paths filter does not select {_API_SURFACE}")
    if not _selected(trigger, _BUDGET_ASSERTION):
        defects.append(f"paths filter does not select {_BUDGET_ASSERTION}")
    return defects


def _candidates() -> list[tuple[Path, dict]]:
    out = []
    for path in _workflow_paths():
        workflow = _load(path)
        if _mentions_suite(workflow):
            out.append((path, workflow))
    return out


# ------------------------------------------------------------------------ tests


def test_the_suite_is_discovered():
    assert _candidates(), "no workflow mentions the architecture suite; the guard is vacuous"


@pytest.mark.parametrize("path,workflow", _candidates(), ids=lambda v: getattr(v, "name", ""))
def test_a_mention_is_an_execution(path: Path, workflow: dict):
    """A workflow that names the suite must run it, or the name is decoration."""
    assert _effective_invocations(workflow), (
        f"{path.name} mentions the architecture suite but no effective step executes it"
    )


def test_a_gate_selects_api_changes_and_executes_the_suite():
    """At least one workflow must execute the suite *and* be selected by an API change.

    This is the load-bearing assertion: executing the suite in a gate that `api/**`
    does not select leaves an API commit unjudged.
    """
    clean = [path.name for path, workflow in _candidates() if not _audit(workflow)]
    assert clean, (
        "no workflow both executes the architecture suite and is selected by "
        f"{_API_SURFACE}; defects per candidate: "
        + "; ".join(
            f"{path.name}: {_audit(workflow)}" for path, workflow in _candidates()
        )
    )


# ------------------------------------------------------------ negative controls


def _workflow(
    paths: list[str],
    run: str,
    *,
    dispatchable: bool = True,
    step_exempt: bool = False,
    job_exempt: bool = False,
) -> dict:
    """A minimal workflow shaped like the real one, for driving the detector."""
    trigger: dict = {
        "pull_request": {"paths": list(paths)},
        "push": {"branches": ["main"], "paths": list(paths)},
    }
    if dispatchable:
        trigger["workflow_dispatch"] = None
    step: dict = {"name": "suite", "run": run}
    if step_exempt:
        step["continue-on-error"] = True
    job: dict = {"runs-on": "ubuntu-latest", "steps": [step]}
    if job_exempt:
        job["continue-on-error"] = True
    return {"on": trigger, "jobs": {"suite": job}}


_GOOD_PATHS = [
    ".github/workflows/example.yml",
    "api/**",
    "tests/architecture/**",
]


def test_detector_is_silent_on_the_correct_shape():
    """Positive control: the invariant's own shape must audit clean."""
    assert _audit(_workflow(_GOOD_PATHS, "python -m pytest tests/architecture -q")) == []


def test_detector_flags_a_gate_that_does_not_select_api_changes():
    """Negative control: the measured pre-repair shape must be reported."""
    shape = _workflow(
        [".github/workflows/example.yml", "tests/architecture/**"],
        "python -m pytest tests/architecture -q",
    )
    defects = _audit(shape)
    assert any(_API_SURFACE in d for d in defects), defects


def test_detector_does_not_count_a_mention_as_an_execution():
    """Negative control: printing the command is not running it."""
    shape = _workflow(_GOOD_PATHS, "echo pytest tests/architecture -q")
    defects = _audit(shape)
    assert any("no effective step executes" in d for d in defects), defects


def test_detector_flags_an_exempted_executing_step():
    """Negative control: a step that cannot fail the run is not a gate."""
    shape = _workflow(_GOOD_PATHS, "python -m pytest tests/architecture -q", step_exempt=True)
    defects = _audit(shape)
    assert any("no effective step executes" in d for d in defects), defects


def test_detector_flags_an_undispatchable_gate():
    shape = _workflow(
        _GOOD_PATHS, "python -m pytest tests/architecture -q", dispatchable=False
    )
    defects = _audit(shape)
    assert any("workflow_dispatch" in d for d in defects), defects


def test_detector_flags_a_gate_that_does_not_select_the_budget_assertion():
    shape = _workflow(
        [".github/workflows/example.yml", "api/**"],
        "python -m pytest tests/architecture -q",
    )
    defects = _audit(shape)
    assert any(_BUDGET_ASSERTION in d for d in defects), defects


def test_glob_matching_covers_the_concrete_paths_the_invariant_names():
    """The selector is a real glob translation, not a substring test."""
    trigger = {"pull_request": {"paths": ["api/**"]}}
    assert _selected(trigger, "api/main.py")
    assert _selected(trigger, "api/nested/deep.py")
    assert not _selected(trigger, "apis/main.py")
    exact = {"pull_request": {"paths": ["api/main.py"]}}
    assert _selected(exact, "api/main.py")
    assert not _selected(exact, "api/other.py")
