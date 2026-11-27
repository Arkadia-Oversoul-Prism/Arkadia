"""Boundary guard: the gate that executes the GOV-04 conformance guard must select it.

`tests/test_gov04_bounded_merge_delegation.py` asserts the wording of the GOV-04
authorization record and the fail-closed shape of the runtime adapter. It is
executed by exactly one whole-suite surface, `provider-routing.yml`
(`pytest tests/ -q -rEf --continue-on-collection-errors`). Its inputs were never
enumerated in that workflow's `paths` filter, so a revision touching only the
authorization record -- or only the conformance test -- ran no gate that executes
it. Measured at `main` `fd0a4fdc`: `grep -rn test_gov04_bounded_merge_delegation
.github/` matched **nothing**, and the only workflows selecting `tests/**`
(`economic-seam-engine`, `operator-console-posture`, `prism-console-contract`) run
named guards, not the whole suite.

`provider-routing.yml` already repairs this exact class for a different guard: its
`AGENTS.md` entry exists because `tests/test_agents_md_encoding_adjudication.py`
reads that file. This guard completes the same enumeration for the GOV-04
conformance guard.

Two conditions, both required, neither implied by the other:

1. **Executes** -- some workflow step actually invokes pytest on the conformance
   guard (directly, or via a directory argument that contains it). A workflow that
   merely *mentions* the path (`echo pytest tests/...`) does not execute it.
2. **Selects** -- that workflow's `paths` filter names the guard file, every input
   the guard reads, and the workflow itself. A guard the pull request cannot
   trigger is decoration.

The input list is **derived** from the conformance guard's own source, not restated
here. A hand-maintained copy drifts, and a drifted copy makes the assertion
vacuous -- the defect class this repository has already recorded for
`FINGERPRINT_DOCS` and for the console-contract domain. Accepted consequence:
adding a `Path` input to the conformance guard requires adding the same path to the
workflow filter in the same change.
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
GUARD = "tests/test_gov04_bounded_merge_delegation.py"
SELF = "tests/test_gov04_conformance_ci_wiring.py"


def _inputs(guard: str = GUARD) -> list[str]:
    """Every repository path the conformance guard reads, derived by AST.

    The guard declares its inputs as module-level ``NAME = ROOT / "a" / "b"``
    constants. Only that shape is collected: a restated list would drift, and a
    comment mentioning a path is not an input.
    """
    tree = ast.parse((ROOT / guard).read_text(encoding="utf-8"))
    found: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.BinOp) or not isinstance(node.value.op, ast.Div):
            continue
        parts: list[str] = []
        cur = node.value
        while isinstance(cur, ast.BinOp) and isinstance(cur.op, ast.Div):
            if not isinstance(cur.right, ast.Constant) or not isinstance(cur.right.value, str):
                parts = []
                break
            parts.append(cur.right.value)
            cur = cur.left
        if parts and isinstance(cur, ast.Name) and cur.id == "ROOT":
            found.append("/".join(reversed(parts)))
    return sorted(found)


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Translate a workflow `paths` glob. `**/` matches zero or more segments."""
    out: list[str] = []
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def _selects(paths: list[str], target: str) -> bool:
    return any(_glob_to_regex(p).match(target) for p in paths)


def _pull_request_paths(workflow: Path) -> list[str]:
    data = yaml.safe_load(workflow.read_text(encoding="utf-8")) or {}
    on = data.get(True) or data.get("on") or {}
    if not isinstance(on, dict):
        return []
    pr = on.get("pull_request")
    if not isinstance(pr, dict):
        return []
    return [p for p in pr.get("paths", []) if isinstance(p, str)]


def _commands(workflow: Path) -> list[list[str]]:
    """Every command line in every step's `run` block, tokenised, comments dropped."""
    data = yaml.safe_load(workflow.read_text(encoding="utf-8")) or {}
    commands: list[list[str]] = []
    for job in (data.get("jobs") or {}).values():
        for step in job.get("steps") or []:
            script = step.get("run")
            if not isinstance(script, str):
                continue
            for line in script.splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                try:
                    commands.append(shlex.split(stripped, comments=True))
                except ValueError:
                    continue
    return commands


_SHELL_SPLIT = {"&&", "||", ";", "|", "&"}


def _simple_commands(argv: list[str]) -> list[list[str]]:
    """Split a tokenised line on shell operators so each head is a real command."""
    segments: list[list[str]] = [[]]
    for token in argv:
        if token in _SHELL_SPLIT:
            segments.append([])
        else:
            segments[-1].append(token)
    return [s for s in segments if s]


def _executes_guard(workflow: Path, guard: str = GUARD) -> bool:
    """True when a step invokes pytest in a way that actually runs `guard`.

    `pytest` must be the *invoked command word* of a simple command: `pytest x` or
    `python -m pytest x` (leading `env`/`VAR=value` assignments are skipped). A
    token appearing later (`echo pytest x`) is a mention, not an execution, and
    must not satisfy this.

    A directory argument (`pytest tests/`) only counts when the invocation carries
    `--continue-on-collection-errors`. Without it the session aborts on the known
    CE-01 `weaver.autonomy` collection error and runs **zero** tests, so the step
    cannot execute the guard it appears to select. Measured at `main` `fd0a4fdc`:
    `sg-02-fe-2-v.yml`'s CP10-B step runs `python -m pytest tests/ -q` and its log
    reads `Interrupted: 1 error during collection`.
    """
    directory = str(Path(guard).parent)
    for argv in _commands(workflow):
        for command in _simple_commands(argv):
            head = list(command)
            while head and (head[0] == "env" or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", head[0])):
                head.pop(0)
            if not head:
                continue
            if head[0] == "pytest":
                args = head[1:]
            elif (
                len(head) >= 3
                and head[0].startswith("python")
                and head[1] == "-m"
                and head[2] == "pytest"
            ):
                args = head[3:]
            else:
                continue
            if any(a == guard or a.startswith(guard + "::") for a in args):
                return True
            if any(a.rstrip("/") == directory for a in args) and (
                "--continue-on-collection-errors" in args
            ):
                return True
    return False


def _executing_workflows() -> list[Path]:
    return [w for w in sorted(WORKFLOWS.glob("*.yml")) if _executes_guard(w)]


def _selecting_workflows() -> list[Path]:
    """Workflows that both execute the guard and can be triggered by a change to it.

    The invariant is existential, not universal. `sg-02-fe-2-v.yml` runs the whole
    suite, so it *executes* every guard, but its filter is scoped to console /
    spiral_grove / lab work and must not be widened to governance documents. What
    matters is that a change to the guard or one of its inputs triggers at least one
    workflow that executes it.
    """
    return [w for w in _executing_workflows() if _selects(_pull_request_paths(w), GUARD)]


def test_the_conformance_guard_has_derived_inputs():
    """The domain is non-empty and includes the authorization record."""
    inputs = _inputs()
    assert GUARD not in inputs  # the guard reads its inputs; it is not one of them
    assert "docs/control-plane/evidence/gov-04-bounded-merge-delegation/AUTHORIZATION.md" in inputs


def test_at_least_one_gate_both_executes_and_selects_the_guard():
    selecting = _selecting_workflows()
    assert selecting, (
        f"no workflow both executes {GUARD} and selects it in its pull_request "
        f"filter, so a change to the guard runs no gate that executes it"
    )


@pytest.mark.parametrize("workflow", _selecting_workflows(), ids=lambda p: p.name)
def test_a_workflow_selects_every_input_its_guard_reads(workflow: Path):
    paths = _pull_request_paths(workflow)
    assert paths, f"{workflow.name} executes the guard but declares no pull_request paths"
    missing = [p for p in _inputs() if not _selects(paths, p)]
    assert not missing, (
        f"{workflow.name} executes {GUARD} but its pull_request filter omits these "
        f"inputs, so a change to them runs no gate that executes the guard: {missing}"
    )


@pytest.mark.parametrize("workflow", _selecting_workflows(), ids=lambda p: p.name)
def test_a_workflow_selects_itself_and_the_guard(workflow: Path):
    paths = _pull_request_paths(workflow)
    relative = str(workflow.relative_to(ROOT))
    for required in (relative, GUARD, SELF):
        assert _selects(paths, required), (
            f"{workflow.name} does not select {required}; a change to it would run "
            f"no gate that judges this wiring"
        )


def test_detector_rejects_mention_without_execution():
    """Negative control: `echo pytest <guard>` is a mention, not an execution."""
    mention = WORKFLOWS / "_synthetic_mention.yml"
    mention.write_text(
        "name: synthetic\non:\n  pull_request:\n    paths:\n      - 'tests/**'\n"
        "jobs:\n  j:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - run: echo pytest tests/test_gov04_bounded_merge_delegation.py\n",
        encoding="utf-8",
    )
    try:
        assert not _executes_guard(mention)
    finally:
        mention.unlink()


def test_detector_rejects_an_incomplete_filter():
    """Negative control: a filter missing one derived input is not a selection."""
    paths = _pull_request_paths(WORKFLOWS / "provider-routing.yml")
    dropped = "docs/control-plane/evidence/gov-04-bounded-merge-delegation/AUTHORIZATION.md"
    reduced = [p for p in paths if p != dropped]
    assert _selects(paths, dropped)
    assert not _selects(reduced, dropped)
