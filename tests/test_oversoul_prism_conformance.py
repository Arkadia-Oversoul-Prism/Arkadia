"""Boundary guard: the Oversoul Prism 144 conformance claims must be executed.

``research/oversoul_prism_144/README.md`` states what the harness checks, including
that "authority-shaped fields are rejected at the transformation boundary". The
harness that states it is ``test_substrate.py``, and until this cycle neither it nor
``scripts/validate_oversoul_prism_12x12_registry.py`` (which validates all 144
registry cells) was executed by any workflow:

    grep -rn "oversoul_prism_144\\|validate_oversoul_prism" .github/workflows/
    (no match)

So a documented conformance claim, and the registry it rests on, held only when a
human ran them by hand -- and the one test asserting the authority boundary raised
``NameError`` instead of running (repaired in this cycle; the class is guarded by
``tests/test_python_global_reference_integrity.py``).

This module keeps both executed and keeps the gate honest:

1. Some workflow must *execute* (not merely mention) the conformance test and the
   registry validator.
2. That workflow's ``paths`` filter must select **every input its commands name**,
   derived from those commands rather than restated -- a filter that omits an input
   lets a change to it land without the gate running.
3. The step and its job must be able to fail.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

CONFORMANCE_TEST = "research/oversoul_prism_144/test_substrate.py"
REGISTRY_VALIDATOR = "scripts/validate_oversoul_prism_12x12_registry.py"


# ------------------------------------------------------------------- workflow parsing


def _workflow_paths() -> list[Path]:
    return sorted(WORKFLOWS.glob("*.yml"))


def _load(path: Path | str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def _trigger_block(workflow: dict) -> dict:
    """The ``on:`` mapping (PyYAML parses the bare key ``on`` as boolean True)."""
    block = workflow.get(True, workflow.get("on"))
    return block if isinstance(block, dict) else {}


def _path_filter(workflow: dict, event: str) -> set[str] | None:
    event_block = _trigger_block(workflow).get(event)
    if not isinstance(event_block, dict):
        return None
    paths = event_block.get("paths")
    return None if paths is None else set(paths)


def _jobs(workflow: dict) -> list[tuple[str, dict]]:
    return list((workflow.get("jobs") or {}).items())


def _steps(workflow: dict) -> list[dict]:
    seen: list[dict] = []
    for _, job in _jobs(workflow):
        seen.extend(job.get("steps") or [])
    return seen


def _commands(workflow: dict) -> list[list[str]]:
    """Every ``run:`` block, tokenised with comments dropped."""
    commands: list[list[str]] = []
    for step in _steps(workflow):
        script = step.get("run")
        if not isinstance(script, str):
            continue
        for line in script.splitlines():
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            try:
                tokens = shlex.split(line)
            except ValueError:
                continue
            if tokens:
                commands.append(tokens)
    return commands


def _invokes_pytest_with(tokens: list[str], target: str) -> bool:
    """Whether ``tokens`` *invokes* pytest on ``target``.

    ``echo pytest <target>`` and a comment naming it must not count: the pytest
    word has to be the invoked command, and the target an argument to it.
    """
    if not tokens:
        return False
    if tokens[0] == "pytest":
        args = tokens[1:]
    elif tokens[0] in {"python", "python3"} and tokens[1:3] == ["-m", "pytest"]:
        args = tokens[3:]
    else:
        return False
    return any(arg == target or arg.startswith(target + "::") for arg in args)


def _invokes_python_script(tokens: list[str], script: str) -> bool:
    """Whether ``tokens`` run ``script`` through an interpreter."""
    for index, token in enumerate(tokens):
        if token == script and index >= 1 and tokens[index - 1] in {"python", "python3"}:
            return True
    return False


def _executing_workflows() -> list[str]:
    return [
        path.name
        for path in _workflow_paths()
        if any(_invokes_pytest_with(c, CONFORMANCE_TEST) for c in _commands(_load(path)))
        and any(_invokes_python_script(c, REGISTRY_VALIDATOR) for c in _commands(_load(path)))
    ]


# ------------------------------------------------------------------- glob selection


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    placeholders = {"\x00": "**/", "\x01": "**", "\x02": "*", "\x03": "?"}
    tokens = {"\x00": "(?:.*/)?", "\x01": ".*", "\x02": "[^/]*", "\x03": "[^/]"}
    body = pattern
    for ph, token in placeholders.items():
        body = body.replace(token, ph)
    body = body.replace(".", r"\.")
    for ph, rx in tokens.items():
        body = body.replace(ph, rx)
    return re.compile("^" + body + "$")


def _selects(path_filter: set[str], path: str) -> bool:
    return any(_glob_to_regex(pattern).match(path) for pattern in path_filter)


def _named_inputs(workflow: dict) -> set[str]:
    """Repo paths the workflow's own commands name — its inputs, not a remembered list."""
    inputs: set[str] = set()
    for tokens in _commands(workflow):
        for token in tokens:
            if token.startswith("-"):
                continue
            candidate = token.split("::", 1)[0]
            if "/" not in candidate:
                continue
            if (ROOT / candidate).exists():
                inputs.add(candidate)
    return inputs


# ---------------------------------------------------------------- detector controls


def test_detector_distinguishes_execution_from_mention():
    executing = [["python", "-m", "pytest", CONFORMANCE_TEST, "-q"]]
    mentioned = [["echo", "pytest", CONFORMANCE_TEST]]
    commented = [["true"]]
    assert any(_invokes_pytest_with(c, CONFORMANCE_TEST) for c in executing)
    assert not any(_invokes_pytest_with(c, CONFORMANCE_TEST) for c in mentioned)
    assert not any(_invokes_pytest_with(c, CONFORMANCE_TEST) for c in commented)
    assert _invokes_python_script(["python", REGISTRY_VALIDATOR], REGISTRY_VALIDATOR)
    assert not _invokes_python_script(["echo", REGISTRY_VALIDATOR], REGISTRY_VALIDATOR)


def test_selector_rejects_an_incomplete_filter():
    assert _selects({"research/**"}, CONFORMANCE_TEST)
    assert not _selects({"tests/**"}, CONFORMANCE_TEST)


# ------------------------------------------------------------------- the invariants


def test_a_workflow_executes_the_conformance_harness_and_the_registry_validator():
    assert _executing_workflows(), (
        f"no workflow executes both {CONFORMANCE_TEST} and {REGISTRY_VALIDATOR}; the "
        "package README's conformance claims then rest on tests nobody runs"
    )


@pytest.mark.parametrize("name", _executing_workflows())
def test_gate_selects_every_input_its_commands_name(name: str):
    """The filter must name the inputs the gate reads, derived from its own commands."""
    workflow = _load(WORKFLOWS / name)
    paths = _path_filter(workflow, "pull_request")
    assert paths is not None, f"{name} executes the harness but is not path-filtered"
    inputs = _named_inputs(workflow)
    assert CONFORMANCE_TEST in inputs and REGISTRY_VALIDATOR in inputs
    omitted = sorted(i for i in inputs if not _selects(paths, i))
    assert not omitted, (
        f"{name} executes {len(inputs)} named input(s) but its pull_request paths "
        f"filter omits {omitted}; a change to one of them would not run this gate"
    )


@pytest.mark.parametrize("name", _executing_workflows())
def test_gate_can_fail_the_job(name: str):
    workflow = _load(WORKFLOWS / name)
    for job_name, job in _jobs(workflow):
        for step in job.get("steps") or []:
            script = step.get("run")
            if not isinstance(script, str):
                continue
            if CONFORMANCE_TEST in script or REGISTRY_VALIDATOR in script:
                assert not step.get("continue-on-error", False), (
                    f"{name}/{job_name}: the conformance step is continue-on-error"
                )
                assert not job.get("continue-on-error", False), (
                    f"{name}/{job_name}: the job is continue-on-error"
                )
