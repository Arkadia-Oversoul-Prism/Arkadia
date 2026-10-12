"""Boundary guard: the console-contract guards must be executed in CI, over their
whole derived domain.

The active console (``web/arkadia_console``) and the serving path that fronts it
(``api/frontend_routes.py``) are judged by a set of contract guards. Measured on
``main`` @ ``f390526``, no workflow executed **the whole set**: the only console-aware
workflow (``n-atlas-developer-lab.yml``) runs ``tests/test_canonical_frontend_routing.py``
alone, among tests from other workstreams, so a rewrite of any other console guard, of
the console source, or of the serving path produced no contract check-run. A guard no
workflow executes is decoration; this module keeps the domain executed.

**Both sides derive from one source of truth.** ``scripts/console_contract_domain.py``
is the single derivation. The gate runs
``python -m pytest -q $(python scripts/console_contract_domain.py)`` so its executed
inventory is *derived* rather than restated, and this module imports :func:`derive_domain`
from that same file. A fixed list on either side drifts the moment a guard is added:
measured on ``main`` @ ``17988afd``, PR #435 merged after three new console guards
arrived (``tests/test_knowledge_projects_boundary.py``,
``tests/test_knowledge_timeline_boundary.py``,
``tests/test_prism_opportunity_entry_flow.py``); the gate ran the twelve it was written
with, this judge derived 16, and ``_complete_gates()`` returned ``[]`` -- the whole
console contract had no complete gate again, silently.

The invariant is stated generically over the workflows that execute console guards:

1. At least one workflow must execute the **whole derived domain** -- a step that
   merely *prints* or *comments* a path is a mention, not an execution, and a gate
   that runs part of the domain leaves the rest unjudged. A *derived* inventory
   (``$(python scripts/console_contract_domain.py)``) executes the whole domain by
   construction, including a guard that did not exist when the gate was written.
2. Such a gate must be selected by the surfaces it judges (``web/arkadia_console/**``,
   ``api/frontend_routes.py``), by every guard it runs, and by its own file, so a
   change to any of them is judged by the gate it changes.
3. Such a gate must be dispatchable (``workflow_dispatch``), so the contract can be
   executed against an exact revision without a source change under the console.
4. A complete gate's executing steps must be able to fail the run: no step- or
   job-level ``continue-on-error``, no step- or job-level ``if: false``. The rule is
   scoped to the complete gate(s) deliberately: ``sg-02-fe-2-v.yml`` runs the whole
   suite on a ``continue-on-error: true`` step as recorded pre-existing debt from
   another workstream, and re-litigating that here would be scope expansion.

The domain is derived at test time, never restated, so a guard that leaves the
repository (or is renamed) reddens the invariant until the gate is updated in the same
change. The detector is proven against the forms it is meant to catch, including
mention-without-executing, partial coverage, a fixed inventory left behind by a newly
added guard, and each exemption form.
"""

from __future__ import annotations

import re
import shlex
import sys
from pathlib import Path

import pytest
import yaml

from scripts.console_contract_domain import (
    DOMAIN_NEEDLES,
    SURFACES,
    derive_domain,
)

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

_WORKFLOW_FILE = ".github/workflows/prism-console-contract.yml"

# The single source of truth for the guard domain. The gate must invoke it (via a
# command substitution) so its executed inventory is derived, and this judge imports
# `derive_domain` from it -- the two cannot disagree.
_DOMAIN_SCRIPT = "scripts/console_contract_domain.py"

_SURFACES = SURFACES

_FALSEY_CONDITIONS = {"false", "${{ false }}", "0"}

# A shell command substitution running the domain script. Both `$(...)` and the
# legacy backtick form are accepted; the script path is matched literally (escaped)
# so `$(python scripts/console_contract_domain.py)` is recognised but a mention of
# the *name* elsewhere is not.
_DERIVED_INVENTORY = re.compile(
    r"\$\(\s*\S*(?:python[0-9.]*|-m\s+python)\s+"
    r"(?:\./)?"
    + re.escape(_DOMAIN_SCRIPT)
    + r"\s*\)|`\s*\S*python[0-9.]*\s+(?:\./)?"
    + re.escape(_DOMAIN_SCRIPT)
    + r"\s*`"
)


def _console_domain() -> list[str]:
    """The console-contract guards, derived from the shared source of truth.

    Restating the list here would let it drift from the corpus it claims to cover:
    a new console guard would be omitted from the gate while this file stayed green.
    """
    return derive_domain(ROOT)


def _workflow_paths() -> list[Path]:
    return sorted(WORKFLOWS.glob("*.yml"))


def _load(path: Path | str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _trigger_block(workflow: dict) -> dict:
    """The ``on:`` mapping (PyYAML parses the bare key ``on`` as boolean True)."""
    block = workflow.get(True, workflow.get("on"))
    return block if isinstance(block, dict) else {}


def _path_filter(trigger_block: dict, event: str) -> set[str] | None:
    event_block = trigger_block.get(event)
    if not isinstance(event_block, dict):
        return None
    paths = event_block.get("paths")
    return None if paths is None else set(paths)


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Compile a GitHub ``paths`` glob to a whole-string regex.

    ``**/`` matches zero or more leading segments, a remaining ``**`` matches anything
    including ``/``, and ``*``/``?`` match within one segment. Placeholders keep the
    single-``*`` rewrite from clobbering the ``**`` expansion.
    """
    placeholders = {"\x00": "**/", "\x01": "**", "\x02": "*", "\x03": "?"}
    tokens = {"\x00": "(?:.*/)?", "\x01": ".*", "\x02": "[^/]*", "\x03": "[^/]"}
    body = pattern
    for ph, token in placeholders.items():
        body = body.replace(token, ph)
    body = body.replace(".", r"\.")
    for ph, rx in tokens.items():
        body = body.replace(ph, rx)
    return re.compile("^" + body + "$")


def _selects_path(path_filter: set[str], path: str) -> bool:
    """Whether a ``paths`` filter selects a literal path, mirroring GitHub's globs."""
    return any(_glob_to_regex(pattern).match(path) for pattern in path_filter)


def _steps(workflow: dict):
    for job_name, job in (workflow.get("jobs") or {}).items():
        for step in (job or {}).get("steps") or []:
            yield job_name, job, step


def _run_lines(step: dict) -> list[list[str]]:
    """Each effective shell command in a step's ``run``, tokenised.

    Comment lines are dropped, so a path that appears only in prose is not a command.
    A step with no ``run`` (e.g. a ``uses:`` action) yields nothing.
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

    ``pytest x`` and ``python -m pytest x`` count; ``echo pytest x`` does not — a word
    that merely appears as an argument is not an invocation.
    """
    cmd = _command_tokens(tokens)
    for i, tok in enumerate(cmd):
        if tok == "pytest" or tok.endswith("/pytest"):
            if i == 0 or cmd[i - 1] == "-m":
                return i
    return None


def _derives_inventory(tokens: list[str]) -> bool:
    """Whether this command executes the domain script as a command substitution.

    ``python -m pytest -q $(python scripts/console_contract_domain.py)`` runs the
    whole derived domain at run time, including a guard added after the workflow was
    written. That is the *derived* inventory the single-source-of-truth contract
    requires, and it cannot be evaluated from a static argument list -- the guards
    are whatever the script prints.
    """
    return bool(_DERIVED_INVENTORY.search(" ".join(tokens)))


def _executed_guards(tokens: list[str]) -> set[str]:
    """Which guards this command executes with pytest.

    A guard counts when it is an argument to the pytest command word, or when the
    containing directory is (``pytest tests/ -q`` collects and runs it). A command
    that runs the domain script as a command substitution executes the whole derived
    domain by construction.
    """
    idx = _pytest_command_index(tokens)
    if idx is None:
        return set()
    if _derives_inventory(tokens):
        return set(_console_domain())
    arguments = _command_tokens(tokens)[idx + 1:]
    executed: set[str] = set()
    for guard in _console_domain():
        if any(
            arg == guard
            or arg.startswith(guard + "::")
            or arg.rstrip("/") == str(Path(guard).parent)
            for arg in arguments
        ):
            executed.add(guard)
    return executed


def _invocations(workflow: dict):
    """Steps that execute at least one console guard: (job_name, job, step, guards)."""
    found = []
    for job_name, job, step in _steps(workflow):
        guards: set[str] = set()
        for command in _run_lines(step):
            guards |= _executed_guards(command)
        if guards:
            found.append((job_name, job, step, guards))
    return found


def _mentions_domain(workflow: dict) -> bool:
    """Anywhere a console guard or judged surface appears as a command or trigger path."""
    domain = set(_console_domain())
    for _, _, step in _steps(workflow):
        run = step.get("run")
        if isinstance(run, str) and any(guard in run for guard in domain):
            return True
    trigger = _trigger_block(workflow)
    for event in ("pull_request", "push"):
        paths = " ".join(_path_filter(trigger, event) or set())
        if "web/arkadia_console" in paths or "api/frontend_routes" in paths:
            return True
    return False


def _is_dispatchable(trigger_block: dict) -> bool:
    return "workflow_dispatch" in trigger_block


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


def _candidates() -> list[tuple[Path, dict]]:
    """Workflows that reference the domain and are therefore judged by this guard."""
    out = []
    for path in _workflow_paths():
        workflow = _load(path)
        if _mentions_domain(workflow):
            out.append((path, workflow))
    return out


def _effective_executed_by(workflow: dict) -> set[str]:
    """Every console guard this workflow executes on a step that can fail the run."""
    executed: set[str] = set()
    for _, job, step, guards in _invocations(workflow):
        if _exemption(job, step) is None:
            executed |= guards
    return executed


def _complete_gates() -> list[tuple[Path, dict]]:
    """Workflows that execute the whole derived domain, not a remembered subset."""
    domain = set(_console_domain())
    return [
        (path, workflow)
        for path, workflow in _candidates()
        if _effective_executed_by(workflow) >= domain
    ]


def _exemption_defects(workflow: dict) -> list[str]:
    """Executing steps that cannot fail the run — a gate that cannot bite."""
    defects: list[str] = []
    for _, job, step, _ in _invocations(workflow):
        reason = _exemption(job, step)
        if reason:
            defects.append(f"executing step is exempted by {reason}")
    return defects


def _gate_defects(workflow: dict) -> list[str]:
    """Why a complete gate cannot judge the changes it is meant to judge."""
    trigger = _trigger_block(workflow)
    defects: list[str] = []
    if not _is_dispatchable(trigger):
        defects.append("no workflow_dispatch: contract not executable on demand")
    for event in ("pull_request", "push"):
        paths = _path_filter(trigger, event)
        if paths is None:
            continue
        for selector in (*_SURFACES, *_console_domain()):
            if not _selects_path(paths, selector):
                defects.append(f"{event} paths filter omits {selector}")
    return defects


# ---------------------------------------------------------------- the invariants


def test_domain_is_derived_and_not_empty():
    """A derivation that returns nothing would make every assertion vacuous."""
    domain = _console_domain()
    assert domain, (
        "no tracked test names the console or its serving path; the console boundary "
        "moved and this guard's derivation must be updated"
    )
    assert "tests/test_canonical_frontend_routing.py" in domain, (
        "the routing guard is not derived; the needle set no longer matches how guards "
        "name the console"
    )


def test_a_workflow_executes_the_whole_console_contract():
    """A domain executed in part, or by no gate, is not a boundary."""
    complete = _complete_gates()
    assert complete, (
        "no workflow executes the whole console-contract domain: the guards that are "
        "not executed hold only when a human runs the suite by hand"
    )


@pytest.mark.parametrize(
    "path,workflow", _complete_gates(), ids=lambda v: getattr(v, "name", None)
)
def test_complete_gate_is_selected_by_everything_it_judges(path: Path, workflow: dict):
    defects = _gate_defects(workflow)
    assert not defects, f"{path.name}: " + "; ".join(defects)


@pytest.mark.parametrize(
    "path,workflow", _complete_gates(), ids=lambda v: getattr(v, "name", None)
)
def test_complete_gate_can_fail_the_run(path: Path, workflow: dict):
    defects = _exemption_defects(workflow)
    assert not defects, f"{path.name}: " + "; ".join(defects)


def test_wiring_workflow_is_a_complete_gate_that_selects_itself():
    """A gate that rejects the branch it watches is the omission class again."""
    complete = dict((p.name, w) for p, w in _complete_gates())
    assert Path(_WORKFLOW_FILE).name in complete, (
        f"{_WORKFLOW_FILE} does not execute the whole console-contract domain"
    )
    workflow = complete[Path(_WORKFLOW_FILE).name]
    paths = _path_filter(_trigger_block(workflow), "pull_request")
    assert paths is not None
    assert _selects_path(paths, _WORKFLOW_FILE)


# --- detector controls: prove the guard bites on the forms it names -----------------

_DOMAIN = _console_domain()
_ONE = "tests/test_canonical_frontend_routing.py"
_ALL = " ".join(_DOMAIN)


def _minimal_workflow(run: str, **trigger) -> dict:
    return {
        True: trigger,
        "jobs": {"console-contract": {"steps": [{"run": run}]}},
    }


_WIRED_TRIGGER = dict(
    pull_request={"paths": [*_SURFACES, *_DOMAIN, _WORKFLOW_FILE]},
    push={"branches": ["main"], "paths": [*_SURFACES, *_DOMAIN, _WORKFLOW_FILE]},
    workflow_dispatch=None,
)


def test_positive_control_is_silent_on_the_wired_shape():
    wired = _minimal_workflow(f"python -m pytest {_ALL} -q", **_WIRED_TRIGGER)
    assert _gate_defects(wired) == []
    assert _effective_executed_by(wired) >= set(_DOMAIN)


def test_positive_control_accepts_a_directory_invocation():
    """`pytest tests/ -q` executes the whole domain; it must not be flagged."""
    wired = _minimal_workflow("python -m pytest tests/ -q", **_WIRED_TRIGGER)
    assert _effective_executed_by(wired) >= set(_DOMAIN)


def test_negative_control_mention_without_executing_is_flagged():
    printing = _minimal_workflow(f"echo {_ALL}", **_WIRED_TRIGGER)
    assert _effective_executed_by(printing) == set()


def test_negative_control_comment_only_mention_is_flagged():
    commented = _minimal_workflow(f"# run {_ALL}", **_WIRED_TRIGGER)
    assert _effective_executed_by(commented) == set()


@pytest.mark.parametrize(
    "run",
    [
        f"echo pytest {_ALL}",
        f"printf %s pytest {_ALL}",
        f"echo 'python -m pytest {_ALL}'",
    ],
)
def test_negative_control_pytest_as_an_argument_is_flagged(run: str):
    """`pytest` appearing as an *argument* to another command is not an invocation."""
    assert _effective_executed_by(_minimal_workflow(run, **_WIRED_TRIGGER)) == set()


def test_negative_control_partial_domain_is_not_a_complete_gate():
    """The measured pre-fix shape: one console guard, the rest of the domain unrun."""
    partial = _minimal_workflow(f"python -m pytest {_ONE} -q", **_WIRED_TRIGGER)
    executed = _effective_executed_by(partial)
    assert executed == {_ONE}
    assert not executed >= set(_DOMAIN), "a partial executor is not a complete gate"


def test_negative_control_flags_the_pre_fix_shape():
    """A gate that runs the domain but is path-filtered and undispatched is flagged."""
    pre_fix = _minimal_workflow(
        f"python -m pytest {_ALL} -q",
        pull_request={"paths": [*_SURFACES, *_DOMAIN, _WORKFLOW_FILE]},
        push={"branches": ["main"], "paths": [*_SURFACES, *_DOMAIN, _WORKFLOW_FILE]},
    )
    assert _gate_defects(pre_fix) == ["no workflow_dispatch: contract not executable on demand"]


def test_negative_control_flags_incomplete_filter():
    incomplete = _minimal_workflow(
        f"python -m pytest {_ALL} -q",
        pull_request={"paths": [_ONE]},
        workflow_dispatch=None,
    )
    defects = _gate_defects(incomplete)
    assert defects, "a filter selecting one guard must not pass"
    assert all("paths filter omits" in d for d in defects)


@pytest.mark.parametrize("placement", ["step", "job"])
def test_negative_control_flags_continue_on_error(placement: str):
    workflow = _minimal_workflow(f"python -m pytest {_ALL} -q", **_WIRED_TRIGGER)
    if placement == "step":
        workflow["jobs"]["console-contract"]["steps"][0]["continue-on-error"] = True
    else:
        workflow["jobs"]["console-contract"]["continue-on-error"] = True
    assert _exemption_defects(workflow) == [
        f"executing step is exempted by {placement} continue-on-error"
    ]


@pytest.mark.parametrize("placement", ["step", "job"])
def test_negative_control_flags_if_false(placement: str):
    workflow = _minimal_workflow(f"python -m pytest {_ALL} -q", **_WIRED_TRIGGER)
    if placement == "step":
        workflow["jobs"]["console-contract"]["steps"][0]["if"] = "false"
    else:
        workflow["jobs"]["console-contract"]["if"] = "${{ false }}"
    assert _exemption_defects(workflow) == [
        f"executing step is exempted by {placement} if: false"
    ]


def test_selector_rejects_unrelated_paths():
    """A selector that matched everything would make the filter assertions vacuous."""
    assert not _selects_path({"solspire/**"}, "tests/test_canonical_frontend_routing.py")
    assert not _selects_path({"api/*.py"}, "api/sub/module.py")


def test_detector_ignores_workflows_that_do_not_mention_the_domain():
    unrelated = _minimal_workflow(
        "python -m pytest tests/test_other.py -q", workflow_dispatch=None
    )
    assert not _mentions_domain(unrelated)


# --- the drift regression: a newly added guard must be executed, not omitted --------

_NEW_GUARD = "tests/test_newly_added_console_guard.py"


@pytest.fixture
def _grown_domain(monkeypatch):
    """Simulate a guard added to the corpus after the gate was written.

    The gate's executed inventory must follow the corpus -- if it does not, the new
    guard is unexecuted and this fixture is how that becomes observable without
    committing a dummy guard.
    """
    grown = [*_DOMAIN, _NEW_GUARD]
    monkeypatch.setattr(sys.modules[__name__], "_console_domain", lambda: list(grown))
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
        f"python scripts/console_contract_domain.py",
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
    workflow = _minimal_workflow(_DERIVED_RUN, **_WIRED_TRIGGER)
    executed = _effective_executed_by(workflow)
    assert set(_grown_domain) <= executed, (
        "a derived inventory left a newly added guard unexecuted"
    )


def test_fixed_inventory_omits_a_guard_added_after_the_gate(_grown_domain):
    """Negative control: the measured post-#435 shape.

    A gate carrying a fixed list -- the guards that existed when it was written --
    silently stops executing the domain the moment a new guard arrives. Without this
    control the drift regression above could not distinguish derived from fixed.
    """
    fixed = _minimal_workflow(f"python -m pytest -q {_ALL}", **_WIRED_TRIGGER)
    executed = _effective_executed_by(fixed)
    assert _NEW_GUARD not in executed
    assert not executed >= set(_grown_domain), "a fixed inventory is not a complete gate"


def test_real_gate_inventory_is_derived_not_fixed():
    """The shipped gate must derive, or the drift regression is not actually held."""
    workflow = _load(WORKFLOWS / Path(_WORKFLOW_FILE).name)
    invocations = _invocations(workflow)
    assert invocations, "the gate executes no console guard"
    assert any(
        _derives_inventory(command)
        for _, _, step, _ in invocations
        for command in _run_lines(step)
    ), (
        f"{_WORKFLOW_FILE} does not derive its executed inventory from "
        f"{_DOMAIN_SCRIPT}; a fixed list drifts the moment a guard is added"
    )


def test_real_gate_selects_a_guard_added_after_the_gate(_grown_domain):
    """A new guard changes `tests/**`, which must select the gate that judges it.

    If the filter enumerated guards instead, adding one would leave the very judge
    that reports it unexecuted without a trigger.
    """
    workflow = _load(WORKFLOWS / Path(_WORKFLOW_FILE).name)
    for event in ("pull_request", "push"):
        paths = _path_filter(_trigger_block(workflow), event)
        assert paths is not None
        assert _selects_path(paths, _NEW_GUARD), (
            f"{event} paths filter would not select a newly added guard, so the "
            "judge that reports it unexecuted would not run"
        )
