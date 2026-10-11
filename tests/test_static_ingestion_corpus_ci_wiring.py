"""Boundary guard: the static-ingestion corpus guard must be executed, not merely written.

`tests/test_static_ingestion_sources.py::test_adr_source_root_resolves_and_holds_the_records`
is the guard that keeps the declared ADR corpus honest. Measured on `main` it was
executed by **no** workflow — `grep -rn test_static_ingestion .github/workflows/`
returns 0 — so it held only when a human ran the suite by hand. That is the defect
class this repository already names: a guard no gate executes is decoration.

These tests state the invariant generically over the workflows that mention the guard:

1. Some workflow must **execute** the guard — a step whose command is a pytest
   invocation that targets the guard file (or a directory containing it). A step that
   merely *prints* or *comments* the path does not satisfy this.
2. Such a workflow must be dispatchable (`workflow_dispatch`), so the guard can be
   executed against an exact revision without a source change under the corpus.
3. Such a workflow's `paths` filter must name every input the guard reads — the guard
   file itself, the module that declares the source, and the corpus directory the
   declared root resolves to. The inputs are **derived** from the source by import, not
   restated here: a second hand-maintained copy drifts, and a drifted copy makes the
   coverage assertion vacuous.
4. An executing step must actually be able to fail the run: it must not be exempted by
   step- or job-level `continue-on-error`, nor by step- or job-level `if: false`.

The detector is proven against the forms it is meant to catch (negative controls),
including the *mention-without-executing* form and the *exempt* forms, so deleting or
disarming the wiring cannot silently pass.
"""

from __future__ import annotations

import shlex
from pathlib import Path

import pytest
import yaml

from knowledge.static_ingestion import _SOURCES

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

_GUARD_FILE = "tests/test_static_ingestion_corpus_ci_wiring.py"
_CONTRACT_FILE = "tests/test_static_ingestion_sources.py"
_DECLARING_MODULE = "knowledge/static_ingestion.py"
_CONTRACT_DIRS = {str(Path(_CONTRACT_FILE).parent), str(Path(_CONTRACT_FILE).parent) + "/"}

_FALSEY_CONDITIONS = {"false", "${{ false }}", "0"}


def _adr_root_relative() -> str:
    """The ADR corpus directory, derived from the declared source (not restated)."""
    entry = next(s for s in _SOURCES if s["source_provider"] == "static:adr")
    return entry["root"].relative_to(ROOT).as_posix()


_REQUIRED_SELECTORS = (
    _CONTRACT_FILE,
    _GUARD_FILE,
    _DECLARING_MODULE,
    f"{_adr_root_relative()}/**",
)


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
    event_block = trigger_block.get(event)
    if not isinstance(event_block, dict):
        return None
    paths = event_block.get("paths")
    return None if paths is None else set(paths)


def _steps(workflow: dict):
    for job_name, job in (workflow.get("jobs") or {}).items():
        for step in (job or {}).get("steps") or []:
            yield job_name, job, step


def _run_lines(step: dict) -> list[list[str]]:
    """Each effective shell command in a step's `run`, tokenised.

    Comment lines and inline `#` comments are dropped, so a path that appears only in
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
    """The tokens from the invoked executable onward.

    Leading `env` and `NAME=value` assignments are dropped, so `FOO=1 pytest x` and
    `env pytest x` resolve to a `pytest` command word.
    """
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
    """Index of the `pytest` word **only when it is the invoked command**.

    `pytest x` and `python -m pytest x` count; `echo pytest x` does not — a word that
    merely appears as an argument is not an invocation.
    """
    cmd = _command_tokens(tokens)
    for i, tok in enumerate(cmd):
        if tok == "pytest" or tok.endswith("/pytest"):
            if i == 0 or cmd[i - 1] == "-m":
                return i
    return None


def _pytest_invokes(tokens: list[str]) -> bool:
    """Whether this command actually executes pytest against the contract."""
    idx = _pytest_command_index(tokens)
    if idx is None:
        return False
    arguments = _command_tokens(tokens)[idx + 1:]
    for arg in arguments:
        if arg == _CONTRACT_FILE or arg.startswith(_CONTRACT_FILE + "::"):
            return True
        if arg in _CONTRACT_DIRS:
            return True
    return False


def _invocations(workflow: dict):
    found = []
    for job_name, job, step in _steps(workflow):
        if any(_pytest_invokes(cmd) for cmd in _run_lines(step)):
            found.append((job_name, job, step))
    return found


def _mentions_contract(workflow: dict) -> bool:
    if any(_CONTRACT_FILE in str(step.get("run", "")) for _, _, step in _steps(workflow)):
        return True
    trigger = _trigger_block(workflow)
    for event in ("pull_request", "push"):
        if _CONTRACT_FILE in (_path_filter(trigger, event) or set()):
            return True
    return False


def _is_dispatchable(trigger_block: dict) -> bool:
    return "workflow_dispatch" in trigger_block


def _missing_filter_coverage(trigger_block: dict) -> list[str]:
    """Which required selectors the declared path filters omit."""
    filters: list[set[str]] = []
    for event in ("pull_request", "push"):
        f = _path_filter(trigger_block, event)
        if f is not None:
            filters.append(f)
    if not filters:
        return list(_REQUIRED_SELECTORS)
    covered = set().union(*filters)
    return [s for s in _REQUIRED_SELECTORS if s not in covered]


def _is_falsey_condition(value: object) -> bool:
    return str(value).strip().lower() in _FALSEY_CONDITIONS


def _exemption(job: dict, step: dict) -> str | None:
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


def _candidates() -> list[tuple[Path, dict]]:
    out = []
    for path in _workflow_paths():
        workflow = _load(path)
        if _mentions_contract(workflow):
            out.append((path, workflow))
    return out


_EXEMPTION_DEFECT = (
    "no effective step executes the contract "
    "(a mention is not an execution; or the step is exempted by "
    "continue-on-error / if: false)"
)


def _audit(workflow: dict) -> list[str]:
    if not _mentions_contract(workflow):
        return []
    trigger = _trigger_block(workflow)
    defects: list[str] = []
    if not _effective_invocations(workflow):
        defects.append(_EXEMPTION_DEFECT)
    if not _is_dispatchable(trigger):
        defects.append("no workflow_dispatch: contract not executable on demand")
    defects.extend(f"paths filter omits {sel}" for sel in _missing_filter_coverage(trigger))
    return defects


def test_some_workflow_executes_the_static_ingestion_corpus_guard():
    executed = [path for path, workflow in _candidates() if _effective_invocations(workflow)]
    assert executed, (
        f"no workflow executes {_CONTRACT_FILE} with pytest: the static-ingestion "
        "corpus guard is a guard that no gate executes"
    )


@pytest.mark.parametrize("path,workflow", _candidates(), ids=lambda v: getattr(v, "name", None))
def test_every_candidate_workflow_is_executable_and_can_fail(path: Path, workflow: dict):
    defects = _audit(workflow)
    assert not defects, f"{path.name}: " + "; ".join(defects)


# --- detector controls: prove the guard bites on the forms it names -----------------


def _minimal_workflow(run: str, **trigger) -> dict:
    return {
        True: trigger,
        "jobs": {"static-ingestion-corpus": {"steps": [{"run": run}]}},
    }


_WIRED_TRIGGER = dict(
    pull_request={"paths": list(_REQUIRED_SELECTORS)},
    push={"branches": ["main"], "paths": list(_REQUIRED_SELECTORS)},
    workflow_dispatch=None,
)


def test_positive_control_is_silent_on_the_wired_shape():
    wf = _minimal_workflow(f"python -m pytest {_CONTRACT_FILE} -q", **_WIRED_TRIGGER)
    assert _audit(wf) == []


def test_negative_control_mention_without_execution_is_caught():
    wf = _minimal_workflow(f"echo pytest {_CONTRACT_FILE}", **_WIRED_TRIGGER)
    assert _EXEMPTION_DEFECT in _audit(wf)


def test_negative_control_comment_only_is_caught():
    wf = _minimal_workflow(f"# pytest {_CONTRACT_FILE}", **_WIRED_TRIGGER)
    assert _EXEMPTION_DEFECT in _audit(wf)


def test_negative_control_incomplete_filter_is_caught():
    trigger = dict(_WIRED_TRIGGER)
    trigger["pull_request"] = {"paths": [_CONTRACT_FILE]}
    trigger["push"] = {"branches": ["main"], "paths": [_CONTRACT_FILE]}
    wf = _minimal_workflow(f"python -m pytest {_CONTRACT_FILE} -q", **trigger)
    defects = _audit(wf)
    assert any("paths filter omits" in d for d in defects)


def test_negative_control_undispatchable_is_caught():
    trigger = dict(_WIRED_TRIGGER)
    del trigger["workflow_dispatch"]
    wf = _minimal_workflow(f"python -m pytest {_CONTRACT_FILE} -q", **trigger)
    assert any("workflow_dispatch" in d for d in _audit(wf))


@pytest.mark.parametrize(
    "exempt",
    [
        {"step_continue_on_error": True},
        {"step_if": "false"},
        {"job_continue_on_error": True},
        {"job_if": "false"},
    ],
)
def test_negative_controls_exempted_steps_are_caught(exempt: dict):
    wf = _minimal_workflow(f"python -m pytest {_CONTRACT_FILE} -q", **_WIRED_TRIGGER)
    step = wf["jobs"]["static-ingestion-corpus"]["steps"][0]
    job = wf["jobs"]["static-ingestion-corpus"]
    if "step_continue_on_error" in exempt:
        step["continue-on-error"] = True
    if "step_if" in exempt:
        step["if"] = exempt["step_if"]
    if "job_continue_on_error" in exempt:
        job["continue-on-error"] = True
    if "job_if" in exempt:
        job["if"] = exempt["job_if"]
    assert _EXEMPTION_DEFECT in _audit(wf)


def test_derived_selectors_resolve_to_real_paths():
    """The derived filter inputs must name surfaces that exist in the repository."""
    assert (ROOT / _CONTRACT_FILE).is_file()
    assert (ROOT / _GUARD_FILE).is_file()
    assert (ROOT / _DECLARING_MODULE).is_file()
    assert (ROOT / _adr_root_relative()).is_dir()
