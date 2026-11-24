"""Boundary guard: the deployment-host currency guard must actually be executed.

``tests/test_root_doc_deployment_host_currency.py`` judges the operational documents
against `architecture/runtime_manifest.yaml`. A guard no workflow executes holds only
when a human runs it by hand — the class this repository has already closed for
`test_boot_syntax_boundary.py`, `test_baseline_fingerprint.py` and
`test_console_posture_currency.py`.

The invariant is stated over **every** workflow that runs the guard, not against one
file, so a second wiring is judged by the same rule and deleting this one cannot make
the assertions vacuous:

1. Some workflow must actually **execute** the guard. Tokenising the command and
   requiring ``pytest`` to be the invoked word (directly, or via ``python -m``) with
   the guard as an argument — a path mentioned in a comment, echoed, or present as a
   stray token is a mention, not an execution.
2. That workflow must be **selected** by every input the guard reads. The inputs are
   derived from the guard's own source by AST, not restated here: the manifest it
   parses and the ``*.md`` corpus it enumerates. A hand-maintained second copy drifts,
   and a drifted copy makes the coverage assertion vacuous.
3. It must be **dispatchable**, so the guard can be executed against an exact revision
   without a source change under the documents.
4. Its executing steps must be able to **fail** the run: no step- or job-level
   ``continue-on-error``, no step- or job-level ``if: false``.

Each defect form has a negative control that feeds the detector the shape it must
reject, so the detector cannot be disarmed by rewriting the workflow.
"""

from __future__ import annotations

import ast
import re
import shlex
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
GUARD = "tests/test_root_doc_deployment_host_currency.py"
GUARD_PATH = ROOT / GUARD
WIRING_GUARD = "tests/test_root_doc_deployment_host_ci_wiring.py"


def _trigger(workflow: dict) -> dict:
    # PyYAML reads the bare `on:` key as the boolean True.
    return workflow.get("on", workflow.get(True)) or {}


def _path_filter(workflow: dict, event: str) -> set[str] | None:
    block = _trigger(workflow).get(event)
    if not isinstance(block, dict):
        return None
    paths = block.get("paths")
    return None if paths is None else set(paths)


def _iter_steps(workflow: dict):
    for job in (workflow.get("jobs") or {}).values():
        if not isinstance(job, dict):
            continue
        yield job, None
        for step in job.get("steps") or []:
            if isinstance(step, dict):
                yield job, step


def _invokes_pytest_with(command: str, target: str) -> bool:
    """True when ``command`` executes pytest with ``target`` as an argument.

    ``pytest`` must be the *invoked* word: either ``pytest x`` or
    ``python -m pytest x``. A detector that accepts the token ``pytest`` anywhere in
    the command passes ``echo pytest x`` — the mention-vs-execution hole this
    repository has already been bitten by.
    """
    try:
        tokens = shlex.split(command, comments=True)
    except ValueError:
        return False
    if not tokens:
        return False
    for index, token in enumerate(tokens):
        if Path(token).name not in ("pytest", "py.test"):
            continue
        if index > 0 and tokens[index - 1] != "-m":
            continue
        for argument in tokens[index + 1 :]:
            if argument.startswith("-"):
                continue
            normalised = argument.replace("::", " ").split()[0] if "::" in argument else argument
            if normalised.rstrip("/") == target.rstrip("/"):
                return True
            if target.startswith(normalised.rstrip("/") + "/"):
                return True
    return False


def _executing_workflows(target: str = GUARD) -> list[str]:
    found = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        workflow = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for _job, step in _iter_steps(workflow):
            if step and isinstance(step.get("run"), str):
                if _invokes_pytest_with(step["run"], target):
                    found.append(path.name)
                    break
    return found


def _selects(workflow: dict, needle: str) -> bool:
    """True when the workflow's own `paths:` filter names ``needle``."""
    for event in ("pull_request", "push"):
        paths = _path_filter(workflow, event)
        if paths and _filter_selects(paths, needle):
            return True
    return False


def _glob_to_regex(entry: str) -> str:
    """Translate a `paths:` glob the way GitHub's filter reads it.

    ``**/`` matches **zero** or more directories — so ``**/*.md`` selects a root
    document as well as a nested one. A translator that requires the slash reports a
    correct filter as incomplete, which is the false-negative this models away.
    """
    out = []
    index = 0
    while index < len(entry):
        if entry.startswith("**/", index):
            out.append("(?:.*/)?")
            index += 3
        elif entry.startswith("**", index):
            out.append(".*")
            index += 2
        elif entry[index] == "*":
            out.append("[^/]*")
            index += 1
        elif entry[index] == "?":
            out.append("[^/]")
            index += 1
        else:
            out.append(re.escape(entry[index]))
            index += 1
    return "".join(out)


def _filter_selects(paths: set[str], needle: str) -> bool:
    """Does a `paths:` entry select ``needle``? Handles `**` and a trailing `/**`."""
    for entry in paths:
        if entry == needle:
            return True
        if entry.endswith("/**"):
            prefix = entry[: -len("/**")]
            if needle == prefix or needle.startswith(prefix + "/"):
                return True
        if re.fullmatch(_glob_to_regex(entry), needle):
            return True
    return False


def _blocks_the_run(job: dict, step: dict) -> bool:
    """A step or its job is exempted from failing the run."""
    if job.get("continue-on-error") is True or job.get("if") is False:
        return True
    return step.get("continue-on-error") is True or step.get("if") is False


def _path_parts(node: ast.AST) -> list[str]:
    """Flatten a ``ROOT / "a" / "b"`` chain into its literal segments, in order."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return _path_parts(node.left) + _path_parts(node.right)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    return []


def guard_inputs() -> set[str]:
    """The paths the currency guard reads, derived from its own source by AST.

    Two derivations, both from how the guard *uses* a value rather than from what a
    constant is called:

    * a ``ROOT / ... / "name.yaml"`` chain — the manifest it parses;
    * the ``*.md`` glob it hands to ``git ls-files`` — the corpus it enumerates.
    """
    tree = ast.parse(GUARD_PATH.read_text(encoding="utf-8"))
    inputs: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            parts = _path_parts(node)
            if len(parts) >= 2 and parts[-1].endswith((".yaml", ".yml")):
                inputs.add("/".join(parts))
        if isinstance(node, ast.Constant) and node.value == "*.md":
            inputs.add("**/*.md")
            inputs.add("*.md")
    return inputs


def _gates() -> list[str]:
    """Workflows that both select and execute the guard — the gates that judge it."""
    gates = []
    for name in _executing_workflows():
        workflow = yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8")) or {}
        if _selects(workflow, GUARD):
            gates.append(name)
    return gates


# ─────────────────────────────────────────────────────────────────────────────
# The invariants
# ─────────────────────────────────────────────────────────────────────────────


def test_a_workflow_executes_the_guard():
    assert _executing_workflows(), (
        f"no workflow executes {GUARD}; the guard holds only when run by hand"
    )


def test_a_workflow_selects_and_executes_the_guard():
    assert _gates(), (
        f"no workflow both selects and executes {GUARD}, so a change to it or to the "
        "documents it judges can land without the guard running"
    )


def test_every_gate_selects_every_input_the_guard_reads():
    inputs = guard_inputs()
    assert "architecture/runtime_manifest.yaml" in inputs, (
        "the input derivation no longer finds the manifest the guard parses"
    )
    assert "**/*.md" in inputs, (
        "the input derivation no longer finds the markdown corpus the guard enumerates"
    )
    missing = {}
    for name in _gates():
        workflow = yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8")) or {}
        gaps = [
            item
            for item in sorted(inputs | {GUARD, WIRING_GUARD, f".github/workflows/{name}"})
            if not _selects(workflow, item)
        ]
        if gaps:
            missing[name] = gaps
    assert not missing, f"gate(s) omit inputs the guard reads: {missing}"


def test_every_gate_is_dispatchable():
    for name in _gates():
        workflow = yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8")) or {}
        assert "workflow_dispatch" in _trigger(workflow), (
            f"{name} cannot be dispatched against an exact revision"
        )


def test_every_executing_step_can_fail_the_run():
    offenders = []
    for name in _gates():
        workflow = yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8")) or {}
        for job, step in _iter_steps(workflow):
            if step and isinstance(step.get("run"), str):
                if _invokes_pytest_with(step["run"], GUARD) and _blocks_the_run(job, step):
                    offenders.append(name)
    assert not offenders, f"a gate's executing step cannot fail the run: {offenders}"


# ─────────────────────────────────────────────────────────────────────────────
# Negative controls — the detectors must reject the shapes they exist to catch
# ─────────────────────────────────────────────────────────────────────────────


def test_control_a_mention_is_not_an_execution():
    assert not _invokes_pytest_with(f"echo pytest {GUARD}", GUARD)
    assert not _invokes_pytest_with(f"# pytest {GUARD}", GUARD)


def test_control_a_real_invocation_is_an_execution():
    assert _invokes_pytest_with(f"python -m pytest {GUARD} -q", GUARD)
    assert _invokes_pytest_with(f"pytest {GUARD} -q", GUARD)


def test_control_a_filter_omitting_the_manifest_is_reported():
    paths = {GUARD, WIRING_GUARD, "**/*.md", "*.md", ".github/workflows/root-doc-deployment-host.yml"}
    assert not _filter_selects(paths, "architecture/runtime_manifest.yaml")
    assert _filter_selects(paths | {"architecture/runtime_manifest.yaml"}, "architecture/runtime_manifest.yaml")


def test_control_a_filter_omitting_the_document_corpus_is_reported():
    paths = {GUARD, WIRING_GUARD, "architecture/runtime_manifest.yaml"}
    assert not _filter_selects(paths, "**/*.md")
    assert not _filter_selects(paths, "MISSION.md")
    assert _filter_selects(paths | {"**/*.md"}, "MISSION.md")
    assert _filter_selects(paths | {"**/*.md"}, "docs/anything.md")


def test_control_a_glob_translation_matches_root_and_nested_paths():
    assert _filter_selects({"**/*.md"}, "MISSION.md")
    assert _filter_selects({"**/*.md"}, "a/b/c.md")
    assert _filter_selects({"*.md"}, "MISSION.md")
    assert not _filter_selects({"*.md"}, "a/MISSION.md")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
