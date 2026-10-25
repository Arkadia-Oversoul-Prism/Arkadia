"""Keep the lane-currency guard's authoritative oracle continuously executed.

A guard that exists but no workflow runs is decoration. That was the state of
the first wiring (the offline `--check`), and it would have been the state of
the second: the GitHub PR-state oracle is what actually detects a lane doc
pointing at a closed PR, and it is a separate command (`--verify-live`) that a
workflow can drop without any other test noticing.

Properties asserted here, each with a negative control:

1. The workflow that runs the currency contract executes the **whole derived
   domain**, not a remembered subset. The domain is derived by
   `scripts/lane_guard_domain.py` (single source of truth) and imported here, so
   the executed inventory and the verified inventory cannot disagree.
2. The workflow also runs the live oracle, with a token in scope -- otherwise the
   oracle is skipped or fails closed forever, and the gate is green while proving
   nothing.
3. The workflow's trigger filters name every input the contract reads. A filter
   that omits the guard script, the refresh script or the snapshot means a
   change to what the guard asserts does not execute the guard.

The detectors parse the workflow with a real command tokeniser (`shlex`), not a
substring search: `echo pytest ...` and a commented-out line must both fail to
count as execution, and `echo pytest tests/...` must not satisfy a check that
only looks for the word `pytest` anywhere in the line.

Measured at `76f6d87a`: the derived domain is 4 guards, the gate executed 3 and
filtered 3. `#567` added `tests/test_lane_guard_scope_boundary.py` -- the
acceptance test for the scope repair -- and no filter or step ever named it, so
it was executed by nothing. That is the same class PR #435 removed for the
console contract by deriving the inventory.
"""

from __future__ import annotations

import importlib.util
import re
import shlex
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
WORKFLOW = REPO / ".github/workflows/lane-doc-currency.yml"

# The single source of truth for the guard domain. The gate must invoke it (via a
# command substitution) so its executed inventory is derived, and this judge
# imports `derive_domain` from it -- the two cannot disagree.
_DOMAIN_SCRIPT = "scripts/lane_guard_domain.py"

# Every path the currency contract reads. A change to any of them can change
# what the contract asserts, so each must select the workflow that runs it.
REQUIRED_FILTERS = (
    "docs/control-plane/parallel-ui/**",
    "scripts/lane_state.py",
    "scripts/lane_state_refresh.py",
    "scripts/lane_scope_probe.py",
    _DOMAIN_SCRIPT,
    "tests/**",
)

_CONTRACT = "tests/test_lane_instruction_doc_currency.py"


def _load_domain_module():
    spec = importlib.util.spec_from_file_location("lane_guard_domain", REPO / _DOMAIN_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["lane_guard_domain"] = module
    spec.loader.exec_module(module)
    return module


def _lane_domain() -> list[str]:
    """The lane guards, derived from the shared source of truth.

    Restating the list here would let it drift from the corpus it claims to cover:
    a new lane guard would be omitted from the gate while this file stayed green.
    """
    return _load_domain_module().derive_domain(REPO)


def _real_domain() -> list[str]:
    """The corpus as it is on disk, bypassing any monkeypatch of ``_lane_domain``.

    The fixed-inventory negative control has to build a run over the guards that
    existed when the gate was written. Reading the patched accessor would hand it
    the *grown* list and make the control assert the opposite of its intent.
    """
    return _load_domain_module().derive_domain(REPO)


# A shell command substitution running the domain script. Both `$(...)` and the
# legacy backtick form are accepted; the script path is matched literally
# (escaped) so `$(python scripts/lane_guard_domain.py)` is recognised but a
# mention of the *name* elsewhere is not.
_DERIVED_INVENTORY = re.compile(
    r"\$\(\s*\S*(?:python[0-9.]*|-m\s+python)\s+"
    r"(?:\./)?"
    + re.escape(_DOMAIN_SCRIPT)
    + r"\s*\)|`\s*\S*python[0-9.]*\s+(?:\./)?"
    + re.escape(_DOMAIN_SCRIPT)
    + r"\s*`"
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


def _command_word(tokens: list[str]) -> list[str]:
    """The tokens from the invoked executable onward (leading ``env``/``NAME=value``)."""
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
    """Index of the ``pytest`` word **only when it is the invoked command**.

    ``pytest x`` and ``python -m pytest x`` count; ``echo pytest x`` does not --
    a word that merely appears as an argument is not an invocation.

    The interpreter must be the **first** token, not merely present. Accepting
    ``-m`` before ``pytest`` anywhere in the line also accepts
    ``echo python -m pytest x``, and that hole is measured: it let the executing
    step be replaced by an ``echo`` while this guard stayed green. A detector that
    only checks adjacency cannot tell execution from mention.
    """
    cmd = _command_word(tokens)
    if not cmd:
        return None
    if cmd[0] == "pytest" or cmd[0].endswith("/pytest"):
        return 0
    if (
        re.fullmatch(r"python[0-9.]*", cmd[0])
        and len(cmd) > 2
        and cmd[1] == "-m"
        and (cmd[2] == "pytest" or cmd[2].endswith("/pytest"))
    ):
        return 2
    return None


def _derives_inventory(tokens: list[str]) -> bool:
    """Whether this command executes the domain script as a command substitution.

    ``python -m pytest -q $(python scripts/lane_guard_domain.py)`` runs the whole
    derived domain at run time, including a guard added after the workflow was
    written. That is the *derived* inventory the single-source-of-truth contract
    requires, and it cannot be evaluated from a static argument list -- the guards
    are whatever the script prints.
    """
    return bool(_DERIVED_INVENTORY.search(" ".join(tokens)))


def _executed_guards(tokens: list[str]) -> set[str]:
    """Which guards this command executes with pytest.

    A guard counts when it is an argument to the pytest command word, or when the
    containing directory is (``pytest tests/ -q`` collects and runs it). A command
    that runs the domain script as a command substitution executes the whole
    derived domain by construction.
    """
    idx = _pytest_command_index(tokens)
    if idx is None:
        return set()
    if _derives_inventory(tokens):
        return set(_lane_domain())
    arguments = _command_word(tokens)[idx + 1:]
    executed: set[str] = set()
    for guard in _lane_domain():
        if any(
            arg == guard
            or arg.startswith(guard + "::")
            or arg.rstrip("/") == str(Path(guard).parent)
            for arg in arguments
        ):
            executed.add(guard)
    return executed


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
    return target in _executed_guards(tokens)


@pytest.mark.parametrize("target", _lane_domain())
def test_workflow_executes_every_guard_in_the_derived_domain(target):
    """Selection without execution is not coverage.

    A path filter decides *when* the workflow runs; only the step decides *what*
    it runs. The two can drift apart: the fixed-scope guard was added to both
    filters but not to any step, and every other assertion in this file stayed
    green -- the gate would have selected itself on that file's changes and then
    executed nothing that reads it. Measured on the real workflow by deleting the
    step and observing this node redden, while the filter assertions held.

    Parametrized over the *derived* domain rather than a hand-written list, so a
    future guard added to the corpus is covered by the same rule without an edit
    here -- and so the omission of a newly added guard cannot go unnoticed.
    """
    commands = _commands(_workflow_text())
    assert any(_invokes(c, target) for c in commands), (
        f"the workflow does not execute {target}, which is part of the derived "
        f"lane-guard domain"
    )


def test_domain_is_derived_and_not_empty():
    """A derivation that returns nothing would make every assertion vacuous."""
    domain = _lane_domain()
    assert domain, (
        "no tracked test names the lane substrate; the lane boundary moved and "
        "this guard's derivation must be updated"
    )
    assert _CONTRACT in domain, (
        "the currency contract is not derived; the needle set no longer matches "
        "how guards name the lane substrate"
    )


def test_real_gate_inventory_is_derived_not_fixed():
    """The shipped gate must derive, or the drift regression is not actually held."""
    commands = _commands(_workflow_text())
    assert any(_derives_inventory(c) for c in commands), (
        f"{WORKFLOW.name} does not derive its executed inventory from "
        f"{_DOMAIN_SCRIPT}; a fixed list drifts the moment a guard is added"
    )


@pytest.mark.parametrize("path", REQUIRED_FILTERS)
def test_trigger_filters_name_every_input_the_contract_reads(path):
    """A filter that omits an input lets a change to it skip the guard."""
    text = _workflow_text()
    pull_request, _, push = text.partition("  push:")
    assert path in pull_request, f"pull_request filter omits {path}"
    assert path in push, f"push filter omits {path}"


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


# --- the drift regression: a newly added guard must be executed, not omitted --------

_NEW_GUARD = "tests/test_newly_added_lane_guard.py"


@pytest.fixture
def _grown_domain(monkeypatch):
    """Simulate a guard added to the corpus after the gate was written.

    The gate's executed inventory must follow the corpus -- if it does not, the new
    guard is unexecuted and this fixture is how that becomes observable without
    committing a dummy guard.
    """
    grown = [*_lane_domain(), _NEW_GUARD]
    monkeypatch.setattr(sys.modules[__name__], "_lane_domain", lambda: list(grown))
    return grown


_DERIVED_RUN = f"python -m pytest -q $(python {_DOMAIN_SCRIPT})"


def test_derived_inventory_is_recognised_as_executing_the_run():
    """The command substitution is an execution of the whole derived domain."""
    assert _derives_inventory(shlex.split(_DERIVED_RUN))


@pytest.mark.parametrize(
    "run",
    [
        f"echo $(python {_DOMAIN_SCRIPT})",
        f"# $(python {_DOMAIN_SCRIPT})",
        f"echo 'python -m pytest $(python {_DOMAIN_SCRIPT})'",
        f"python {_DOMAIN_SCRIPT}",
    ],
)
def test_derived_inventory_detector_rejects_non_executions(run: str):
    """A mention of the script that does not run pytest is not an execution."""
    assert _executed_guards(shlex.split(run)) == set()


def test_derived_inventory_executes_a_guard_added_after_the_gate(_grown_domain):
    """A *derived* inventory follows the corpus, so a new guard is executed.

    This is the invariant the single-source-of-truth contract exists to hold: the
    gate does not carry a fixed list, so a guard added later cannot leave it behind.
    """
    assert set(_grown_domain) <= _executed_guards(shlex.split(_DERIVED_RUN))


def test_fixed_inventory_omits_a_guard_added_after_the_gate(_grown_domain):
    """Negative control: the measured pre-repair shape.

    A gate carrying a fixed list -- the guards that existed when it was written --
    silently stops executing the domain the moment a new guard arrives. Without this
    control the drift regression above could not distinguish derived from fixed.
    """
    fixed_run = "python -m pytest -q " + " ".join(_real_domain())
    executed = _executed_guards(shlex.split(fixed_run))
    assert _NEW_GUARD not in executed
    assert not executed >= set(_grown_domain), "a fixed inventory is not a complete gate"


# ------------------------------------------------------------------ controls


def test_detector_rejects_a_mention_in_an_echo():
    """Negative control: mentioning pytest is not executing it.

    ``echo pytest tests/...`` tokenises with ``pytest`` present as an argument,
    so a detector that accepts the word anywhere would pass it.
    """
    assert not _invokes(shlex.split("echo pytest " + _CONTRACT), _CONTRACT)


def test_detector_rejects_echo_prefixed_interpreter_invocation():
    """Negative control: the measured hole.

    ``echo python -m pytest ...`` satisfies an adjacency-only check -- ``-m`` does
    precede ``pytest`` -- so a detector that never requires the interpreter to be
    the *first* token accepts a command that executes nothing. This form is the
    realistic mutation of the executing step (a debug echo left in place), and it
    passed an earlier revision of this guard.
    """
    assert not _invokes(shlex.split("echo python -m pytest -q " + _CONTRACT), _CONTRACT)
    assert not _invokes(
        shlex.split("echo python -m pytest -q $(python scripts/lane_guard_domain.py)"),
        _CONTRACT,
    )


def test_detector_accepts_the_two_real_invocations():
    """Positive control: both accepted forms must be recognised."""
    assert _invokes(shlex.split(f"pytest -q {_CONTRACT}"), _CONTRACT)
    assert _invokes(shlex.split(f"python -m pytest -q {_CONTRACT}"), _CONTRACT)


def test_detector_rejects_a_comment():
    """Negative control: a commented-out command executes nothing."""
    assert _commands("# run: pytest " + _CONTRACT) == []
