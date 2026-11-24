"""Boundary guard: the HTTP error contract must be executed, and selected, by CI.

``tests/test_http_error_contract.py`` judges a property of every 5xx handler under
``api/``. Measured on ``main`` ``bb19aabd``: ``grep -rln test_http_error_contract
.github/workflows/`` returned **0** — no workflow executed it, so the invariant
held only when a human ran the suite by hand. ``economic-seam-engine.yml`` and
``prism-console-contract.yml`` are selected by ``tests/**`` but execute only their
own derived domains, and ``knowledge-connection-lifecycle-guard.yml`` is
deliberately stdlib+pytest only while this guard imports the application.

``.github/workflows/http-error-contract.yml`` is the executable surface. This
module states the invariant over that workflow:

1. **Selected by the surface it judges.** ``api/**`` is in the ``pull_request``
   filter, so a leaking handler added to any API module reaches the guard.
2. **Self-selected.** The guard file, the judge, and the workflow itself are all in
   the filter, so a rewrite of either the gate or its assertion is judged.
3. **Actually executed.** A step invokes ``pytest`` with the guard as an argument.
   A path that is merely *mentioned* — echoed, commented, or named in a step that
   runs something else — is not an execution.
4. **Able to fail.** No step- or job-level ``continue-on-error`` and no
   ``if: false`` anywhere in the job, so a red guard reddens the run.
5. **Dispatchable.** ``workflow_dispatch`` is present, so the contract can be
   executed against an exact revision without a source change under ``api/``.

Each detector is proven against the defect it exists to catch (negative controls)
and against the wired shape it must stay silent on, so the boundary cannot be
disarmed by editing the workflow.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "http-error-contract.yml"

GUARD = "tests/test_http_error_contract.py"
JUDGE = "tests/test_http_error_contract_ci_wiring.py"
WORKFLOW_RELATIVE = ".github/workflows/http-error-contract.yml"
JUDGED_SURFACE = "api/**"

_FALSEY = {"false", "${{ false }}", "0"}


# ---------------------------------------------------------------------------
# Detectors — module level, so the controls exercise the code the assertions use.
# ---------------------------------------------------------------------------


def _glob_to_regex(pattern: str) -> str:
    """Translate a GitHub path filter to a regex.

    ``**`` spans path separators (``api/**`` must match ``api/a/b.py``); ``*`` and
    ``?`` do not. A naive segment-count matcher misses the nested case.
    """
    out = []
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if pattern.startswith("**/", index):
            out.append("(?:.*/)?")
            index += 3
        elif pattern.startswith("**", index):
            out.append(".*")
            index += 2
        elif char == "*":
            out.append("[^/]*")
            index += 1
        elif char == "?":
            out.append("[^/]")
            index += 1
        else:
            out.append(re.escape(char))
            index += 1
    return "^" + "".join(out) + "$"


def selected_paths(workflow: dict, event: str) -> list[str]:
    """The path filters of one event. A bare ``on:`` trigger selects everything."""
    trigger = workflow.get("on", workflow.get(True, {}))
    if isinstance(trigger, list):
        return [] if event in trigger else ["<not triggered>"]
    if isinstance(trigger, str):
        return [] if trigger == event else ["<not triggered>"]
    block = trigger.get(event)
    if block is None:
        return ["<not triggered>"]
    if block is None or block == {}:
        return []
    return list(block.get("paths", []))


def selects(patterns: list[str], path: str) -> bool:
    return any(re.match(_glob_to_regex(pattern), path) for pattern in patterns)


def invoked_pytest_arguments(step: dict) -> list[list[str]]:
    """Tokenised arguments of every real ``pytest`` invocation in a step.

    Comments are dropped and the command word must be ``pytest`` itself (or
    ``python -m pytest``). A detector that accepts the word "pytest" anywhere in
    the string passes ``echo pytest <file>``, which executes nothing.
    """
    script = step.get("run")
    if not isinstance(script, str):
        return []
    invocations = []
    for raw in script.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        try:
            tokens = shlex.split(line)
        except ValueError:
            continue
        for index, token in enumerate(tokens):
            if token == "pytest" and (index == 0 or tokens[index - 1] == "-m"):
                invocations.append(tokens[index + 1 :])
                break
    return invocations


def executes(workflow: dict, path: str) -> bool:
    """Whether some step runs pytest with *path* as an argument."""
    for job in (workflow.get("jobs") or {}).values():
        for step in job.get("steps") or []:
            for arguments in invoked_pytest_arguments(step):
                if any(
                    argument == path
                    or argument.startswith(path + "::")
                    or argument.rstrip("/") == str(Path(path).parent)
                    for argument in arguments
                ):
                    return True
    return False


def unfailable(workflow: dict) -> list[str]:
    """Exemptions that let a red guard pass: ``continue-on-error`` or ``if: false``."""
    findings = []
    for name, job in (workflow.get("jobs") or {}).items():
        if job.get("continue-on-error") or str(job.get("if", "")).strip() in _FALSEY:
            findings.append(f"job {name} cannot fail the run")
        for index, step in enumerate(job.get("steps") or []):
            label = step.get("name") or f"step {index}"
            if step.get("continue-on-error") or str(step.get("if", "")).strip() in _FALSEY:
                findings.append(f"{label} cannot fail the run")
    return findings


# ---------------------------------------------------------------------------
# Negative controls
# ---------------------------------------------------------------------------


def test_the_selector_understands_nested_globs():
    assert selects(["api/**"], "api/knowledge_routes.py")
    assert selects(["api/**"], "api/routes/deep/module.py")
    assert not selects(["api/**"], "tests/test_http_error_contract.py")
    assert not selects(["tests/**"], "api/knowledge_routes.py")


def test_mention_without_execution_is_not_execution():
    """The pre-fix shape: a path named in a step that runs something else."""
    workflow = {
        "jobs": {
            "j": {
                "steps": [
                    {"run": f"echo {GUARD}"},
                    {"run": f"# pytest {GUARD}"},
                    {"run": f"pytest {JUDGE}"},
                ]
            }
        }
    }
    assert executes(workflow, GUARD) is False


def test_execution_is_recognised_in_both_invocation_forms():
    for command in (f"pytest {GUARD} -q", f"python -m pytest -q {GUARD}"):
        workflow = {"jobs": {"j": {"steps": [{"run": command}]}}}
        assert executes(workflow, GUARD) is True, command


def test_a_directory_argument_counts_as_execution():
    workflow = {"jobs": {"j": {"steps": [{"run": "python -m pytest tests/ -q"}]}}}
    assert executes(workflow, GUARD) is True


def test_an_exemption_is_reported_at_step_and_job_level():
    step_level = {"jobs": {"j": {"steps": [{"run": "pytest x", "continue-on-error": True}]}}}
    job_level = {"jobs": {"j": {"continue-on-error": True, "steps": [{"run": "pytest x"}]}}}
    frozen = {"jobs": {"j": {"steps": [{"run": "pytest x", "if": "false"}]}}}
    assert unfailable(step_level)
    assert unfailable(job_level)
    assert unfailable(frozen)
    assert unfailable({"jobs": {"j": {"steps": [{"run": "pytest x"}]}}}) == []


# ---------------------------------------------------------------------------
# The live workflow
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def workflow() -> dict:
    return yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))


def test_the_gate_selects_the_surface_it_judges(workflow):
    for event in ("pull_request", "push"):
        patterns = selected_paths(workflow, event)
        assert selects(patterns, JUDGED_SURFACE.replace("**", "knowledge_routes.py")), event


def test_the_gate_selects_itself_its_guard_and_its_judge(workflow):
    for event in ("pull_request", "push"):
        patterns = selected_paths(workflow, event)
        for path in (GUARD, JUDGE, WORKFLOW_RELATIVE):
            assert selects(patterns, path), f"{event} does not select {path}"


def test_push_and_pull_request_filters_are_identical(workflow):
    assert selected_paths(workflow, "pull_request") == selected_paths(workflow, "push")


def test_the_gate_executes_the_guard_and_its_judge(workflow):
    assert executes(workflow, GUARD)
    assert executes(workflow, JUDGE)


def test_the_gate_can_fail(workflow):
    assert unfailable(workflow) == []


def test_the_gate_is_dispatchable(workflow):
    trigger = workflow.get("on", workflow.get(True, {}))
    assert "workflow_dispatch" in trigger
