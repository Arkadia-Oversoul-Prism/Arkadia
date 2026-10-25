"""Keep the lane-currency guard's authoritative oracle continuously executed.

A guard that exists but no workflow runs is decoration. That was the state of
the *first* wiring (the offline `--check`), and it would have been the state of
the second: the GitHub PR-state oracle is what actually detects a lane doc
pointing at a closed PR, and it is a separate command (`--verify-live`) that a
workflow can drop without any other test noticing.

Two properties, each with a negative control:

1. The workflow that runs the currency contract also runs the live oracle, with
   a token in scope -- otherwise the oracle is skipped or fails closed forever,
   and the gate is green while proving nothing.
2. The workflow's trigger filters name every input the contract reads. A filter
   that omits the guard script, the refresh script or the snapshot means a
   change to what the guard asserts does not execute the guard.

The detectors parse the workflow with a real command tokeniser (`shlex`), not a
substring search: `echo pytest ...` and a commented-out line must both fail to
count as execution.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
WORKFLOW = REPO / ".github/workflows/lane-doc-currency.yml"
CONTRACT = "tests/test_lane_instruction_doc_currency.py"
WIRING = "tests/test_lane_currency_ci_wiring.py"

# Every path the currency contract reads. A change to any of them can change
# what the contract asserts, so each must select the workflow that runs it.
# The wiring guard is included so a rewrite of this workflow is judged by the
# workflow it rewrites.
REQUIRED_FILTERS = (
    "docs/control-plane/parallel-ui/**",
    "scripts/lane_state.py",
    "scripts/lane_state_refresh.py",
    CONTRACT,
    WIRING,
)


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _commands(text: str) -> list[list[str]]:
    """Tokenise every ``run:`` command in the workflow.

    Comments are dropped and shell operators split, so a detector cannot be
    satisfied by a mention inside a comment or a quoted string.
    """
    commands: list[list[str]] = []
    for raw in re.findall(r"^\s*(?:-\s*)?run:\s*(.+)$", text, flags=re.MULTILINE):
        line = raw.split("#", 1)[0]
        try:
            tokens = shlex.split(line)
        except ValueError:
            continue
        if tokens:
            commands.append(tokens)
    return commands


def _invokes(tokens: list[str], target: str) -> bool:
    """True when ``tokens`` *executes* ``target`` as an argument to pytest.

    The command word must be ``pytest`` itself, or ``python -m pytest``. Requiring
    the command word -- rather than accepting the word ``pytest`` anywhere in the
    line -- is what distinguishes execution from mention. Measured on the real
    workflow: an earlier version of this detector accepted
    ``echo python -m pytest tests/...``, because it only checked that ``-m``
    preceded ``pytest`` and never that the command started there. A detector with
    that hole would have let the executing step be replaced by an ``echo`` while
    the wiring guard stayed green.
    """
    if not tokens:
        return False
    head = Path(tokens[0]).name
    if head == "pytest":
        rest = tokens[1:]
    elif head.startswith("python") and tokens[1:3] == ["-m", "pytest"]:
        rest = tokens[3:]
    else:
        return False
    return target in rest


def test_workflow_exists_and_runs_the_contract():
    text = _workflow_text()
    commands = _commands(text)
    assert any(_invokes(c, CONTRACT) for c in commands), (
        "the workflow must execute the currency contract"
    )


def test_workflow_runs_its_own_wiring_guard():
    """The gate must judge itself.

    Without this, the workflow could be rewritten to stop running the wiring
    guard, and nothing would notice -- the guard would be green on a gate that
    no longer executes it.
    """
    commands = _commands(_workflow_text())
    assert any(_invokes(c, WIRING) for c in commands), (
        "the workflow must execute the wiring guard, so a rewrite of this "
        "workflow is judged by the workflow it rewrites"
    )


def test_workflow_runs_the_authoritative_oracle():
    """The oracle is the check that finds a doc pointing at a closed PR.

    Asserted separately from running the contract because they are separate
    commands: a workflow can run every test in the file and never ask GitHub,
    which is exactly the decoration this test exists to prevent.
    """
    commands = _commands(_workflow_text())
    assert any("--verify-live" in c for c in commands), (
        "the workflow must execute the live oracle (--verify-live); without it "
        "the snapshot's agreement with GitHub is never checked"
    )


def test_oracle_step_has_a_token_in_scope():
    """A live check with no token fails closed forever, or is silently skipped.

    Fail-closed is the right behaviour for the guard, but it makes the step
    useless as a signal if the token is never provided: it would be permanently
    red (and disabled by an operator) or the oracle would be dropped. The
    token is required to be wired, so the check can actually decide.
    """
    text = _workflow_text()
    oracle_steps = [
        block
        for block in re.split(r"\n(?=\s*- name:)", text)
        if "--verify-live" in block
    ]
    assert oracle_steps, "no step runs the live oracle"
    assert any("GH_TOKEN" in block for block in oracle_steps), (
        "the oracle step must pass GH_TOKEN; without it the check can only fail "
        "closed and will be switched off"
    )


@pytest.mark.parametrize("path", REQUIRED_FILTERS)
def test_trigger_filters_name_every_input_the_contract_reads(path):
    """A filter that omits an input lets a change to it skip the guard."""
    text = _workflow_text()
    pull_request, _, push = text.partition("  push:")
    assert path in pull_request, f"pull_request filter omits {path}"
    assert path in push, f"push filter omits {path}"


# ------------------------------------------------------------------ controls


def test_detector_rejects_a_mention_in_an_echo():
    """Negative control: mentioning pytest is not executing it.

    ``echo pytest tests/...`` tokenises with ``pytest`` present as an argument,
    so a detector that accepts the word anywhere would pass it.
    """
    tokens = shlex.split("echo pytest " + CONTRACT)
    assert not _invokes(tokens, CONTRACT)


def test_detector_accepts_the_two_real_invocations():
    """Positive control: both accepted forms must be recognised."""
    assert _invokes(shlex.split(f"pytest -q {CONTRACT}"), CONTRACT)
    assert _invokes(shlex.split(f"python -m pytest -q {CONTRACT}"), CONTRACT)


def test_detector_rejects_a_comment():
    """Negative control: a commented-out command executes nothing."""
    assert _commands("# run: pytest " + CONTRACT) == []
