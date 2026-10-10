"""Boundary guard: the composed-route contract must be executed (not merely mentioned).

`tests/test_solspire_route_composition.py` pins the EDEN-OPS-02 routes at the paths
they actually compose to under the SolSpire parent router. Measured on `main` @
`3b74c19d`, the gate that runs it (`.github/workflows/solspire-route-composition.yml`)
is path-filtered to `solspire/**` and carries **no** `workflow_dispatch`, so it executes
only when a change touches SolSpire.

These tests state the invariant generically over the workflows that mention the contract:

1. Some workflow must **execute** the contract — a step whose command is a pytest
   invocation that targets the contract file (or a directory containing it). A step
   that merely *prints* or *comments* the path does not satisfy this.
2. Such a workflow must be dispatchable (`workflow_dispatch`), so the contract can be
   executed against an exact revision without a source change under `solspire/**`.
3. Such a workflow's `paths` filter must name the contract file and the surface it
   exercises (`solspire/**`), so a change to either is judged by the gate it changes.
4. An executing step must actually be able to fail the run: it must not be exempted by
   step-level `continue-on-error`, nor by step- or job-level `if: false`, nor by
   job-level `continue-on-error`.

The detector is proven against the forms it is meant to catch (negative controls),
including the *mention-without-executing* form and the *exempt* forms, so deleting or
disarming the wiring cannot silently pass.
"""

from __future__ import annotations

import shlex
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

_CONTRACT_FILE = "tests/test_solspire_route_composition.py"
_COMPOSITION_SURFACE = "solspire/**"
# Directory form: a pytest invocation over a directory that contains the contract
# executes it too (`python -m pytest tests/ -q`). Both spellings count.
_CONTRACT_DIRS = {str(Path(_CONTRACT_FILE).parent), str(Path(_CONTRACT_FILE).parent) + "/"}

_FALSEY_CONDITIONS = {"false", "${{ false }}", "0"}


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


def _steps(workflow: dict):
    for job_name, job in (workflow.get("jobs") or {}).items():
        for step in (job or {}).get("steps") or []:
            yield job_name, job, step


def _run_lines(step: dict) -> list[list[str]]:
    """Each effective shell command in a step's `run`, tokenised.

    Comment lines and inline `#` comments are dropped, so a path that appears only in
    prose is not a command. A step with no `run` (e.g. a `uses:` action) yields nothing.
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
    merely appears as an argument is not an invocation. The index is into
    `_command_tokens(tokens)`.
    """
    cmd = _command_tokens(tokens)
    for i, tok in enumerate(cmd):
        if tok == "pytest" or tok.endswith("/pytest"):
            if i == 0 or cmd[i - 1] == "-m":
                return i
    return None


def _pytest_invokes(tokens: list[str]) -> bool:
    """Whether this command actually executes pytest against the contract.

    The contract must appear as an argument to the pytest command word — the contract
    file itself, a node-id selector on it (`file::test`), or the directory containing
    it (`pytest tests/ -q` collects and runs it).
    """
    idx = _pytest_command_index(tokens)
    if idx is None:
        return False
    arguments = _command_tokens(tokens)[idx + 1:]
    for arg in arguments:
        # Accept the file, a node-id selector on it (`file::test`), or the directory
        # containing it (`pytest tests/ -q` collects and runs it).
        if arg == _CONTRACT_FILE or arg.startswith(_CONTRACT_FILE + "::"):
            return True
        if arg in _CONTRACT_DIRS:
            return True
    return False


def _invocations(workflow: dict):
    """Steps that execute the contract with pytest: (job_name, job, step) triples."""
    found = []
    for job_name, job, step in _steps(workflow):
        if any(_pytest_invokes(cmd) for cmd in _run_lines(step)):
            found.append((job_name, job, step))
    return found


def _mentions_contract(workflow: dict) -> bool:
    """Anywhere the contract path appears as a command token or a trigger path."""
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
        return [_CONTRACT_FILE, _COMPOSITION_SURFACE]
    covered = set().union(*filters)
    return [s for s in (_CONTRACT_FILE, _COMPOSITION_SURFACE) if s not in covered]


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


def _candidates() -> list[tuple[Path, dict]]:
    """Workflows that reference the contract and are therefore judged by this guard."""
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
    """Defects that make a candidate workflow unable to satisfy the invariant.

    Empty is a pass. A workflow that does not mention the contract is not a candidate
    and is not judged (returns empty).
    """
    if not _mentions_contract(workflow):
        return []
    trigger = _trigger_block(workflow)
    defects: list[str] = []
    if not _effective_invocations(workflow):
        defects.append(_EXEMPTION_DEFECT)
    if not _is_dispatchable(trigger):
        defects.append("no workflow_dispatch: contract not executable on demand")
    defects.extend(
        f"paths filter omits {sel}" for sel in _missing_filter_coverage(trigger)
    )
    return defects


def test_some_workflow_executes_the_composed_route_contract():
    executed = [
        path for path, workflow in _candidates() if _effective_invocations(workflow)
    ]
    assert executed, (
        f"no workflow executes {_CONTRACT_FILE} with pytest: the composed-route "
        "contract is a guard that no gate executes"
    )


@pytest.mark.parametrize(
    "path,workflow", _candidates(), ids=lambda v: getattr(v, "name", None)
)
def test_every_candidate_workflow_is_executable_and_can_fail(path: Path, workflow: dict):
    defects = _audit(workflow)
    assert not defects, f"{path.name}: " + "; ".join(defects)


# --- detector controls: prove the guard bites on the forms it names -----------------


def _minimal_workflow(run: str, **trigger) -> dict:
    return {
        True: trigger,
        "jobs": {"router-composition": {"steps": [{"run": run}]}},
    }


_WIRED_TRIGGER = dict(
    pull_request={"paths": [_COMPOSITION_SURFACE, _CONTRACT_FILE]},
    push={"branches": ["main"], "paths": [_COMPOSITION_SURFACE, _CONTRACT_FILE]},
    workflow_dispatch=None,
)


def test_positive_control_is_silent_on_the_wired_shape():
    wired = _minimal_workflow(f"python -m pytest {_CONTRACT_FILE} -q", **_WIRED_TRIGGER)
    assert _audit(wired) == []


def test_positive_control_accepts_a_directory_invocation():
    """`pytest tests/ -q` executes the contract too; it must not be flagged."""
    wired = _minimal_workflow("python -m pytest tests/ -q", **_WIRED_TRIGGER)
    assert _audit(wired) == []


def test_negative_control_mention_without_executing_is_flagged():
    """An `echo` of the path is a mention, not an execution."""
    printing = _minimal_workflow(f"echo {_CONTRACT_FILE}", **_WIRED_TRIGGER)
    assert _audit(printing) == [_EXEMPTION_DEFECT]


def test_negative_control_comment_only_mention_is_flagged():
    commented = _minimal_workflow(f"# run {_CONTRACT_FILE}", **_WIRED_TRIGGER)
    assert _audit(commented) == [_EXEMPTION_DEFECT]


def test_negative_control_a_non_pytest_command_is_flagged():
    """A step that names the path but does not invoke pytest is not an execution."""
    other = _minimal_workflow(f"cat {_CONTRACT_FILE}", **_WIRED_TRIGGER)
    assert _audit(other) == [_EXEMPTION_DEFECT]


@pytest.mark.parametrize(
    "run",
    [
        f"echo pytest {_CONTRACT_FILE}",
        f"printf %s pytest {_CONTRACT_FILE}",
        f"echo 'python -m pytest {_CONTRACT_FILE}'",
    ],
)
def test_negative_control_pytest_as_an_argument_is_flagged(run: str):
    """`pytest` appearing as an *argument* to another command is not an invocation."""
    mentioned = _minimal_workflow(run, **_WIRED_TRIGGER)
    assert _audit(mentioned) == [_EXEMPTION_DEFECT]


@pytest.mark.parametrize(
    "run",
    [
        f"pytest {_CONTRACT_FILE} -q",
        f"python -m pytest {_CONTRACT_FILE} -q",
        f"python3 -m pytest {_CONTRACT_FILE}",
        f"PYTHONPATH=. python -m pytest {_CONTRACT_FILE} -q",
        f"env python -m pytest {_CONTRACT_FILE}",
        f"python -m pytest {_CONTRACT_FILE}::test_one -q",
    ],
)
def test_positive_control_real_pytest_invocations_are_accepted(run: str):
    wired = _minimal_workflow(run, **_WIRED_TRIGGER)
    assert _audit(wired) == []


def test_negative_control_pytest_elsewhere_is_not_the_contract_execution():
    """Running pytest on another file is not running the contract."""
    other = _minimal_workflow("python -m pytest tests/test_other.py -q", **_WIRED_TRIGGER)
    assert _audit(other) == [_EXEMPTION_DEFECT]


def test_negative_control_flags_the_pre_fix_shape():
    """The measured pre-fix workflow (path-filtered, no dispatch) must be flagged."""
    pre_fix = _minimal_workflow(
        f"python -m pytest {_CONTRACT_FILE} -q",
        pull_request={"paths": [_COMPOSITION_SURFACE, _CONTRACT_FILE]},
        push={"branches": ["main"], "paths": [_COMPOSITION_SURFACE, _CONTRACT_FILE]},
    )
    assert _audit(pre_fix) == ["no workflow_dispatch: contract not executable on demand"]


def test_negative_control_flags_incomplete_filter():
    incomplete = _minimal_workflow(
        f"python -m pytest {_CONTRACT_FILE} -q",
        pull_request={"paths": [_CONTRACT_FILE]},
        workflow_dispatch=None,
    )
    assert _audit(incomplete) == [f"paths filter omits {_COMPOSITION_SURFACE}"]


@pytest.mark.parametrize("placement", ["step", "job"])
def test_negative_control_flags_continue_on_error(placement: str):
    workflow = _minimal_workflow(
        f"python -m pytest {_CONTRACT_FILE} -q", **_WIRED_TRIGGER
    )
    if placement == "step":
        workflow["jobs"]["router-composition"]["steps"][0]["continue-on-error"] = True
    else:
        workflow["jobs"]["router-composition"]["continue-on-error"] = True
    assert _audit(workflow) == [_EXEMPTION_DEFECT]


@pytest.mark.parametrize("placement", ["step", "job"])
def test_negative_control_flags_if_false(placement: str):
    workflow = _minimal_workflow(
        f"python -m pytest {_CONTRACT_FILE} -q", **_WIRED_TRIGGER
    )
    if placement == "step":
        workflow["jobs"]["router-composition"]["steps"][0]["if"] = "false"
    else:
        workflow["jobs"]["router-composition"]["if"] = "${{ false }}"
    assert _audit(workflow) == [_EXEMPTION_DEFECT]


def test_detector_ignores_workflows_that_do_not_mention_the_contract():
    unrelated = _minimal_workflow(
        "python -m pytest tests/test_other.py -q", workflow_dispatch=None
    )
    assert _audit(unrelated) == []
