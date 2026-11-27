"""Boundary guard: the stellar-contract guards must be executed in CI, over their
whole derived domain.

`kernel/stellar.py` is a second implementation of the Ark Date and states that it
"mirrors `api.main._ark_date` exactly". Measured on `main` @ `cb284195`, no workflow
selected the engine at all (`grep -rn "kernel" .github/workflows/` matched only
`kernel/jobs.py` and `kernel/worker.py`), so the engine, its tests and the stated
parity invariant could be rewritten with no gate observing the change. This module
keeps the domain executed.

**Both sides derive from one source of truth.** `scripts/stellar_contract_domain.py`
is the single derivation. The gate runs
``python -m pytest -q $(python scripts/stellar_contract_domain.py)`` so its executed
inventory is *derived* rather than restated, and this module imports
:func:`derive_domain` from that same file. A fixed list on either side drifts the
moment a guard is added — the failure already recorded for the console contract and
the economic-seam engine.

The invariant is stated generically over the workflows that execute stellar guards:

1. At least one workflow must execute the **whole derived domain**. A step that
   merely prints or comments a path is a mention, not an execution, and a gate that
   runs a *fixed* subset leaves every guard added later unjudged.
2. Such a gate must be selected by the surfaces it judges (`kernel/stellar.py`,
   `api/main.py`, the derivation script), by every guard it runs, and by its own
   file, so a change to any of them is judged by the gate it changes.
3. Such a gate must be dispatchable, so the contract can be executed against an exact
   revision without a source change under the engine.
4. A complete gate's steps must be able to fail the run: no step- or job-level
   `continue-on-error`, no step- or job-level `if: false`.

Every detector is proven against the form it is meant to catch, including
mention-without-executing, a fixed inventory, a dropped input, and each exemption
form.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import pytest
import yaml

from scripts.stellar_contract_domain import SURFACES, derive_domain

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

_WORKFLOW_FILE = ".github/workflows/stellar-cartography-contract.yml"
_DOMAIN_SCRIPT = "scripts/stellar_contract_domain.py"

_FALSEY_CONDITIONS = {"false", "${{ false }}", "0"}

# A command substitution running the domain script, in either spelling.
_DERIVATION = re.compile(
    r"\$\(\s*(?:python[0-9.]*\s+)?scripts/stellar_contract_domain\.py\s*\)"
    r"|`\s*(?:python[0-9.]*\s+)?scripts/stellar_contract_domain\.py\s*`"
)


def _workflow_paths() -> list[Path]:
    return sorted(WORKFLOWS.glob("*.yml"))


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _trigger_block(workflow: dict) -> dict:
    # `on:` is parsed as the boolean True by YAML 1.1 loaders.
    return workflow.get("on") or workflow.get(True) or {}


def _path_filter(trigger_block: dict, event: str) -> set[str] | None:
    event_block = trigger_block.get(event)
    if not isinstance(event_block, dict):
        return None
    paths = event_block.get("paths")
    return set(paths) if isinstance(paths, list) else None


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    out = ["^"]
    i = 0
    while i < len(pattern):
        char = pattern[i]
        if char == "*":
            if pattern[i : i + 2] == "**":
                if pattern[i + 2 : i + 3] == "/":
                    out.append("(?:.*/)?")
                    i += 3
                    continue
                out.append(".*")
                i += 2
                continue
            out.append("[^/]*")
            i += 1
            continue
        out.append(re.escape(char))
        i += 1
    out.append("$")
    return re.compile("".join(out))


def _selects_path(path_filter: set[str], path: str) -> bool:
    return any(_glob_to_regex(pattern).match(path) for pattern in path_filter)


def _steps(workflow: dict):
    for job_name, job in (workflow.get("jobs") or {}).items():
        for step in (job or {}).get("steps") or []:
            yield job_name, job or {}, step or {}


def _run_text(step: dict) -> str:
    return step.get("run") or ""


def _command_lines(run_text: str) -> list[str]:
    """The run block's commands, with `\\` continuations joined and comments dropped."""
    joined = re.sub(r"\\\n", " ", run_text)
    lines = []
    for raw in joined.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(stripped)
    return lines


def _tokens(line: str) -> list[str]:
    try:
        return shlex.split(line, comments=True)
    except ValueError:
        return line.split()


def _invokes_pytest(tokens: list[str]) -> bool:
    """True when `pytest` is the command word, not an argument to another command.

    `echo pytest tests/…` and `echo python -m pytest …` both *contain* the token, so a
    detector that searches the whole line accepts a step that executes nothing. The
    command word is the first token after any leading `VAR=value` assignments.
    """
    index = 0
    while index < len(tokens) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", tokens[index]):
        index += 1
    if index >= len(tokens):
        return False
    command = tokens[index]
    if command == "pytest" or command.endswith("/pytest"):
        return True
    is_python = command in {"python", "python3"} or re.fullmatch(r"python[0-9.]+", command)
    if is_python:
        return tokens[index + 1 : index + 3] == ["-m", "pytest"]
    return False


def _executes_domain(step: dict) -> bool:
    """True when the step actually invokes pytest over the derived domain."""
    for line in _command_lines(_run_text(step)):
        if not _DERIVATION.search(line):
            continue
        if _invokes_pytest(_tokens(line)):
            return True
    return False


def _mentions_domain(workflow: dict) -> bool:
    return any(_DERIVATION.search(_run_text(step)) for _, _, step in _steps(workflow))


def _is_dispatchable(trigger_block: dict) -> bool:
    return "workflow_dispatch" in trigger_block


def _is_falsey_condition(value: object) -> bool:
    return str(value).strip().lower() in _FALSEY_CONDITIONS


def _exemption(job: dict, step: dict) -> str | None:
    if job.get("continue-on-error"):
        return "job-level continue-on-error"
    if step.get("continue-on-error"):
        return "step-level continue-on-error"
    if _is_falsey_condition(job.get("if")):
        return "job-level if: false"
    if _is_falsey_condition(step.get("if")):
        return "step-level if: false"
    return None


def _complete_gates() -> list[tuple[Path, dict]]:
    return [
        (path, workflow)
        for path in _workflow_paths()
        for workflow in [_load(path)]
        if any(_executes_domain(step) for _, _, step in _steps(workflow))
    ]


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _gate_defects(path: Path, workflow: dict) -> list[str]:
    own_file = _relative(path)
    defects = []
    trigger_block = _trigger_block(workflow)
    for event in ("pull_request", "push"):
        path_filter = _path_filter(trigger_block, event)
        if path_filter is None:
            defects.append(f"{event} has no paths filter")
            continue
        for surface in (*SURFACES, *derive_domain(), own_file):
            if not _selects_path(path_filter, surface):
                defects.append(f"{event} filter omits {surface}")
    if not _is_dispatchable(trigger_block):
        defects.append("not dispatchable (no workflow_dispatch)")
    for job_name, job, step in _steps(workflow):
        if not _executes_domain(step):
            continue
        reason = _exemption(job, step)
        if reason:
            defects.append(f"{job_name}: executing step cannot fail ({reason})")
    return defects


@pytest.fixture(scope="module")
def complete_gates() -> list[tuple[Path, dict]]:
    gates = _complete_gates()
    assert gates, (
        "no workflow executes the whole derived stellar-contract domain; a guard no "
        "workflow runs is decoration"
    )
    return gates


def test_domain_is_derived_and_names_the_parity_guard():
    domain = derive_domain()
    assert domain, "the stellar-contract domain is empty"
    assert "tests/test_stellar_ark_date_parity.py" in domain


def test_every_derived_guard_actually_names_the_engine():
    """Membership must be by naming the engine, not by a stray quoted word.

    This judge names `kernel.stellar` itself, so it is a member of the domain it
    derives — and is therefore executed by the gate it judges. A gate that judges its
    own rewrite is the strongest signal available.
    """
    for guard in derive_domain():
        text = (ROOT / guard).read_text(encoding="utf-8", errors="ignore")
        assert "kernel.stellar" in text or "kernel import stellar" in text, (
            f"{guard} is in the domain but never names the engine module"
        )
    assert "tests/test_stellar_contract_ci_wiring.py" in derive_domain()


def test_a_workflow_executes_the_whole_stellar_contract(complete_gates):
    assert complete_gates


def test_complete_gate_is_selected_by_everything_it_judges(complete_gates):
    defects = [d for path, workflow in complete_gates for d in _gate_defects(path, workflow)]
    assert defects == []


def test_wiring_workflow_is_a_complete_gate_that_selects_itself():
    path = ROOT / _WORKFLOW_FILE
    assert path.exists(), f"{_WORKFLOW_FILE} is missing"
    workflow = _load(path)
    assert any(_executes_domain(step) for _, _, step in _steps(workflow))
    assert _gate_defects(Path(_WORKFLOW_FILE), workflow) == []


# ── Detector controls ────────────────────────────────────────────────────────
# The controls drive the detectors with workflow *shapes* rather than editing the
# real workflow file, because a shape is what the detectors read. The real file is
# exercised by the assertions above.


def _workflow(run: str, paths: list[str] | None = None) -> dict:
    paths = paths if paths is not None else [
        *SURFACES,
        *derive_domain(),
        _WORKFLOW_FILE,
    ]
    return {
        "on": {
            "pull_request": {"paths": paths},
            "push": {"branches": ["main"], "paths": paths},
            "workflow_dispatch": None,
        },
        "jobs": {"gate": {"steps": [{"run": run}]}},
    }


_DERIVED_RUN = f"python -m pytest -q $({_DOMAIN_SCRIPT})"


def test_positive_control_accepts_the_derived_shape():
    assert any(_executes_domain(step) for _, _, step in _steps(_workflow(_DERIVED_RUN)))
    assert _gate_defects(Path(_WORKFLOW_FILE), _workflow(_DERIVED_RUN)) == []


def test_negative_control_mention_without_executing_is_flagged():
    run = f"echo python -m pytest -q $({_DOMAIN_SCRIPT})"
    assert not any(_executes_domain(step) for _, _, step in _steps(_workflow(run)))
    assert _mentions_domain(_workflow(run)), "the mention detector must still see it"


def test_negative_control_a_fixed_inventory_is_not_the_domain():
    run = "python -m pytest -q tests/test_stellar_cartography.py"
    assert not any(_executes_domain(step) for _, _, step in _steps(_workflow(run)))


def test_negative_control_pytest_as_an_argument_is_not_an_execution():
    run = f"echo pytest $({_DOMAIN_SCRIPT})"
    assert not any(_executes_domain(step) for _, _, step in _steps(_workflow(run)))


def test_negative_control_a_dropped_input_is_flagged():
    paths = [p for p in (*SURFACES, *derive_domain(), _WORKFLOW_FILE) if p != "api/main.py"]
    defects = _gate_defects(Path(_WORKFLOW_FILE), _workflow(_DERIVED_RUN, paths))
    assert any("api/main.py" in defect for defect in defects)


@pytest.mark.parametrize("placement", ["step", "job"])
def test_negative_control_continue_on_error_is_flagged(placement):
    workflow = _workflow(_DERIVED_RUN)
    if placement == "step":
        workflow["jobs"]["gate"]["steps"][0]["continue-on-error"] = True
    else:
        workflow["jobs"]["gate"]["continue-on-error"] = True
    defects = _gate_defects(Path(_WORKFLOW_FILE), workflow)
    assert any("cannot fail" in defect for defect in defects)


@pytest.mark.parametrize("placement", ["step", "job"])
def test_negative_control_a_disabled_step_is_flagged(placement):
    workflow = _workflow(_DERIVED_RUN)
    if placement == "step":
        workflow["jobs"]["gate"]["steps"][0]["if"] = "false"
    else:
        workflow["jobs"]["gate"]["if"] = "${{ false }}"
    defects = _gate_defects(Path(_WORKFLOW_FILE), workflow)
    assert any("cannot fail" in defect for defect in defects)


def test_negative_control_a_missing_dispatch_is_flagged():
    workflow = _workflow(_DERIVED_RUN)
    del workflow["on"]["workflow_dispatch"]
    defects = _gate_defects(Path(_WORKFLOW_FILE), workflow)
    assert any("dispatchable" in defect for defect in defects)
