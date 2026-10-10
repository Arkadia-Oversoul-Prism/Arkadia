"""Boundary guard: the baseline reproducibility preflight must be executed in CI.

`tests/test_baseline_preflight.py` proves `scripts/baseline_preflight.py` detects the two
environment properties that silently change a full-suite failing/error node set — a
shallow clone and a missing declared dependency. As introduced, no workflow named it
(`grep -rn baseline_preflight .github/workflows/` returned 0), so the guard held only
when a human invoked it by hand. That is the defect class the repository already names:
a guard no workflow executes is decoration.

The invariant is stated generically over every workflow that runs the guard:

1. Some workflow must run the preflight guard, selected on `pull_request` by the guard
   file, the script, and every input the script reads.
2. Such a workflow must check out full history — one of the properties the preflight
   exists to detect is a shallow clone.
3. Such a workflow must let the guard step fail the job (`continue-on-error` off).

The script's inputs are read from the script's own source by AST rather than duplicated
here: a second hand-maintained copy drifts, and a drifted copy makes the coverage
assertion vacuous. Adding an import or a repo-root path literal to the script therefore
requires adding the same path to the workflow filter in the same change.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

_GUARD_FILE = "tests/test_baseline_preflight.py"
_SCRIPT_FILE = "scripts/baseline_preflight.py"
_WIRING_FILE = "tests/test_baseline_preflight_ci_wiring.py"
_WORKFLOW_FILE = ".github/workflows/baseline-preflight.yml"


def _workflow_paths() -> list[Path]:
    return sorted(WORKFLOWS.glob("*.yml"))


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _trigger_block(workflow: dict) -> dict:
    """The `on:` mapping (PyYAML parses the bare key `on` as boolean True)."""
    block = workflow.get(True, workflow.get("on"))
    return block if isinstance(block, dict) else {}


def _path_filter(trigger_block: dict, event: str) -> set[str] | None:
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


def _script_inputs(source: str) -> set[str]:
    """Repo-relative inputs `scripts/baseline_preflight.py` reads, from its own AST.

    Two shapes are recognised, both of which make an edit change what the guard asserts:

    * `from scripts.<module> import ...` — the module is a repository file. The script
      imports its oracle revision (`ORACLE_REV`) this way, so the audit module is an
      input even though the guard suite never names it.
    * `<CONST> = REPO_ROOT / "<name>"` — a repo-root-relative path literal, e.g. the
      dependency contract `requirements.txt`.
    """
    tree = ast.parse(source)
    inputs: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("scripts."):
            inputs.add(node.module.replace(".", "/") + ".py")
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.BinOp)
            and isinstance(node.value.op, ast.Div)
            and isinstance(node.value.left, ast.Name)
            and node.value.left.id == "REPO_ROOT"
            and isinstance(node.value.right, ast.Constant)
            and isinstance(node.value.right.value, str)
        ):
            inputs.add(node.value.right.value)
    return inputs


def _guard_inputs() -> set[str]:
    """Every surface whose edit changes the guard's verdict."""
    return (
        {
            _GUARD_FILE,
            _SCRIPT_FILE,
            _WIRING_FILE,
            _WORKFLOW_FILE,
        }
        | _script_inputs((ROOT / _SCRIPT_FILE).read_text(encoding="utf-8"))
    )


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
    assert _runs_guard(
        {"jobs": {"j": {"steps": [{"run": f"python -m pytest {_GUARD_FILE} -q"}]}}}
    )
    assert not _runs_guard(
        {"jobs": {"j": {"steps": [{"run": "python -m pytest tests/test_key_pool.py -q"}]}}}
    )


def test_selector_rejects_unrelated_paths():
    # Negative control: a selector that matched everything would make the coverage
    # assertions vacuously green.
    assert not _selects_path({"weaver/**"}, _SCRIPT_FILE)
    assert not _selects_path({"api/*.py"}, "api/sub/module.py")
    # The selector models whole-segment globs (`*`, `**`), the forms GitHub's `paths`
    # filters here actually use; a partial-segment glob is not a supported form.
    assert _selects_path({"scripts/**"}, _SCRIPT_FILE)
    assert _selects_path({"**"}, _SCRIPT_FILE)
    # `*` does not cross a directory boundary.
    assert not _selects_path({"*"}, _SCRIPT_FILE)


def test_script_inputs_are_derived_not_restated():
    """The input set must come from the script's AST, not a copy kept here."""
    inputs = _script_inputs((ROOT / _SCRIPT_FILE).read_text(encoding="utf-8"))
    # The oracle module is imported, so it is an input the guard suite never names.
    assert "scripts/agents_md_encoding_audit.py" in inputs
    # The dependency contract is a repo-root path literal.
    assert "requirements.txt" in inputs
    assert _SCRIPT_FILE not in inputs, "the script is an input by identity, not by import"


def test_negative_control_flags_a_new_script_input():
    """A newly added input must be reported, or the derivation is vacuous."""
    synthetic = (
        "from scripts.agents_md_encoding_audit import ORACLE_REV\n"
        "REPO_ROOT = 1\n"
        "REQUIREMENTS = REPO_ROOT / 'requirements.txt'\n"
        "EXTRA = REPO_ROOT / 'docs/ledger.md'\n"
        "from scripts.some_new_module import helper\n"
    )
    inputs = _script_inputs(synthetic)
    assert "docs/ledger.md" in inputs
    assert "scripts/some_new_module.py" in inputs


def test_negative_control_flags_a_filter_omitting_an_input():
    """A filter naming the guard but not the script's oracle module must be rejected."""
    inputs = _guard_inputs()
    oracle = "scripts/agents_md_encoding_audit.py"
    assert oracle in inputs
    incomplete = inputs - {oracle}
    assert not _selects_path(incomplete, oracle), (
        "a filter omitting the script's oracle module must not count as covering "
        "the guard's inputs"
    )


# ---------------------------------------------------------------------------
# The invariants, over every workflow that runs the preflight guard
# ---------------------------------------------------------------------------


def test_a_workflow_executes_the_preflight_guard():
    assert _guard_workflows(), (
        f"no workflow runs {_GUARD_FILE}; the preflight is decoration and holds only "
        f"when a human runs it by hand"
    )


@pytest.mark.parametrize("name", _guard_workflows())
def test_guard_workflow_is_selected_by_every_input(name: str):
    workflow = _load(WORKFLOWS / name)
    paths = _path_filter(_trigger_block(workflow), "pull_request")
    if paths is None:
        return  # undeclared or unfiltered: every path is already selected
    for surface in sorted(_guard_inputs()):
        assert _selects_path(paths, surface), (
            f"{name} runs {_GUARD_FILE} on pull_request but is not selected by "
            f"{surface!r}; a change to what the guard asserts would not execute it"
        )


@pytest.mark.parametrize("name", _guard_workflows())
def test_guard_workflow_checks_out_full_history(name: str):
    workflow = _load(WORKFLOWS / name)
    checkouts = _checkout_steps(workflow)
    assert checkouts, f"{name} runs the preflight without an actions/checkout step"
    assert any((step.get("with") or {}).get("fetch-depth") == 0 for step in checkouts), (
        f"{name} runs {_GUARD_FILE} on a shallow checkout; the preflight exists to "
        f"detect a shallow clone, so its own environment must not be shallow"
    )


@pytest.mark.parametrize("name", _guard_workflows())
def test_guard_workflow_judges_its_guard_step(name: str):
    workflow = _load(WORKFLOWS / name)
    for job in (workflow.get("jobs") or {}).values():
        for step in job.get("steps") or []:
            run = step.get("run")
            if isinstance(run, str) and _GUARD_FILE in run:
                assert step.get("continue-on-error") is not True, (
                    f"{name} runs {_GUARD_FILE} with continue-on-error, so the guard "
                    f"can fail without the job turning red"
                )
