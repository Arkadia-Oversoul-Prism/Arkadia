"""Boundary guard: the posture-currency guard must actually be executed in CI.

``tests/test_console_posture_currency.py`` binds the operator console's claims to
the substrate. As introduced it was executed by **no** workflow
(``grep -rn test_console_posture_currency .github/workflows/`` returned 0), so the
checks held only when a human ran them by hand. This repository already names that
class: a guard no gate executes is decoration.

The invariant is stated over **every** workflow that runs the guard, not against
one file, so a second wiring is judged by the same rule and deleting this one
cannot make the assertions vacuous:

1. Some workflow must actually **execute** the guard. Tokenising the command and
   requiring ``pytest`` to be the invoked word (directly, or via ``python -m``)
   with the guard as an argument to it — a path mentioned in a comment, echoed, or
   present as a stray token is a mention, not an execution. Measured defect this
   catches: ``echo pytest tests/test_console_posture_currency.py``.
2. That workflow must be selected by **every input the guard reads**. The inputs
   are derived from the guard's own source by AST, not restated here: a second
   hand-maintained copy drifts, and a drifted copy makes the coverage assertion
   vacuous. Adding an input to the guard requires adding the same path to the
   filter in the same change.
3. It must be dispatchable, so the guard can be executed against an exact revision
   without a source change under the console.
4. Its executing steps must be able to fail the run: no step- or job-level
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
GUARD = "tests/test_console_posture_currency.py"
GUARD_PATH = ROOT / GUARD
WIRING_GUARD = "tests/test_console_posture_currency_ci_wiring.py"

# The module the guard imports to read the served route table. It is an input
# because a route added or removed changes what the guard asserts.
_ROUTE_TABLE_MODULE = "api.main"


def _trigger(workflow: dict) -> dict:
    # PyYAML reads the bare `on:` key as the boolean True.
    return workflow.get("on", workflow.get(True)) or {}


def _path_filter(workflow: dict, event: str) -> set[str] | None:
    trigger = _trigger(workflow)
    block = trigger.get(event)
    if not isinstance(block, dict):
        return None
    paths = block.get("paths")
    if paths is None:
        return None
    return set(paths)


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
    ``python -m pytest x``. A detector that accepts the token ``pytest`` anywhere
    in the command passes ``echo pytest x`` — the mention-vs-execution hole this
    repository has already been bitten by.
    """
    try:
        tokens = shlex.split(command, comments=True)
    except ValueError:
        return False
    if not tokens:
        return False
    for i, tok in enumerate(tokens):
        base = Path(tok).name
        if base not in ("pytest", "py.test"):
            continue
        # `python -m pytest` puts `-m` immediately before it.
        if i > 0 and tokens[i - 1] != "-m":
            continue
        args = tokens[i + 1 :]
        for arg in args:
            if arg.startswith("-"):
                continue
            normalised = arg.replace("::", " ").split()[0] if "::" in arg else arg
            if normalised.rstrip("/") == target.rstrip("/"):
                return True
            # `pytest tests/` executes the guard too.
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


def _job_blocks_steps(job: dict, step: dict) -> bool:
    """A step or its job is exempted from failing the run."""
    if job.get("continue-on-error") is True or job.get("if") is False:
        return True
    if step.get("continue-on-error") is True or step.get("if") is False:
        return True
    return False


def _path_parts(node: ast.AST) -> list[str]:
    """Flatten a ``ROOT / "a" / "b"`` chain into its literal segments, in order."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return _path_parts(node.left) + _path_parts(node.right)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    return []


def guard_inputs() -> set[str]:
    """The paths the currency guard reads, derived from its own source.

    Derived by AST rather than restated: a second copy drifts, and a drifted copy
    makes the coverage assertion vacuous.

    Two derivations, both from how the guard *uses* a path rather than from what a
    constant is called:
      * ``<NAME>.glob(...)`` / ``<NAME>.rglob(...)`` — the console tree it judges.
      * ``git ls-files -- tests/`` — the corpus its citations must resolve against.
      * ``from api.main import app`` — the route table its surfaces must resolve against.
    """
    tree = ast.parse(GUARD_PATH.read_text(encoding="utf-8"))

    # name -> literal path segments, for resolving a receiver in a glob call.
    assigned: dict[str, list[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.BinOp):
            parts = _path_parts(node.value)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned[target.id] = parts

    inputs: set[str] = set()

    for node in ast.walk(tree):
        # The tree the guard globs over.
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in ("glob", "rglob", "iterdir"):
                parts = assigned.get(getattr(node.func.value, "id", ""), [])
                if len(parts) >= 2:
                    inputs.add("/".join(parts[:2]) + "/**")
        # The corpus the citations resolve against.
        if isinstance(node, ast.Constant) and node.value == "tests/":
            inputs.add("tests/**")
        # The route table the declared surfaces resolve against.
        if isinstance(node, ast.ImportFrom) and node.module == _ROUTE_TABLE_MODULE:
            inputs.add("api/**")

    return inputs


def _filter_selects(paths: set[str], needle: str) -> bool:
    """Does a `paths:` entry select `needle`? Handles `**` and a trailing `/**`."""
    for entry in paths:
        if entry == needle:
            return True
        if entry.endswith("/**"):
            prefix = entry[: -len("/**")]
            if needle == prefix or needle.startswith(prefix + "/"):
                return True
        if entry.startswith("**/") and needle.endswith(entry[3:]):
            return True
        if "*" in entry:
            regex = re.escape(entry).replace(r"\*\*", ".*").replace(r"\*", "[^/]*")
            if re.fullmatch(regex, needle):
                return True
    return False


def _selects_guard(workflow: dict) -> bool:
    """True when the workflow's own `paths:` filter names the guard file.

    This separates a **gate** from an incidental executor. `sg-02-fe-2-v.yml` and
    `provider-routing.yml` run the whole `tests/` directory, so they execute this
    guard in passing — but they are not gates for it, and requiring a broad-suite
    workflow to name every input of every test it happens to run would be absurd.
    A gate is a workflow that deliberately selects the guard.
    """
    for event in ("pull_request", "push"):
        paths = _path_filter(workflow, event)
        if paths and _filter_selects(paths, GUARD):
            return True
    return False


def _gates() -> list[str]:
    """Workflows that both select and execute the guard — the gates that judge it."""
    out = []
    for name in _executing_workflows():
        workflow = yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8")) or {}
        if _selects_guard(workflow):
            out.append(name)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# The invariants
# ─────────────────────────────────────────────────────────────────────────────

def test_the_guard_derives_at_least_one_input():
    """An empty input set would make the coverage assertions vacuous."""
    inputs = guard_inputs()
    assert inputs, "no inputs derived from the guard's source"
    assert "web/console/**" in inputs, f"console tree not derived: {sorted(inputs)}"


def test_some_workflow_executes_the_guard():
    """The guard must be executed somewhere, or it is decoration."""
    assert _executing_workflows(), (
        f"no workflow executes {GUARD} — a guard no gate runs is decoration"
    )


def test_a_dedicated_gate_exists_for_the_guard():
    """An incidental broad-suite executor is not a gate: it names no input.

    `sg-02-fe-2-v.yml` and `provider-routing.yml` run the whole `tests/` tree and so
    execute this guard in passing. Neither names it, so neither is selected by a
    change to it — a rewrite of the guard would not necessarily run the workflow
    that is supposed to judge it.
    """
    gates = _gates()
    assert gates, (
        f"no workflow both selects and executes {GUARD}; the guard has no gate"
    )


@pytest.mark.parametrize("workflow_name", _gates() or ["<none>"])
def test_a_workflow_selects_every_input_its_guard_reads(workflow_name: str):
    """The gate must be selected by each input, or an input edit runs nothing."""
    if workflow_name == "<none>":
        pytest.skip("no executing workflow to judge")
    workflow = yaml.safe_load((WORKFLOWS / workflow_name).read_text(encoding="utf-8"))
    for event in ("pull_request", "push"):
        paths = _path_filter(workflow, event)
        if paths is None:
            continue
        for needle in sorted(guard_inputs()):
            assert _filter_selects(paths, needle), (
                f"{workflow_name} {event} filter does not select {needle}, "
                "which the guard reads"
            )


@pytest.mark.parametrize("workflow_name", _gates() or ["<none>"])
def test_a_workflow_selects_itself_and_the_guard(workflow_name: str):
    """A gate that does not select itself can be rewritten unjudged."""
    if workflow_name == "<none>":
        pytest.skip("no executing workflow to judge")
    workflow = yaml.safe_load((WORKFLOWS / workflow_name).read_text(encoding="utf-8"))
    for event in ("pull_request", "push"):
        paths = _path_filter(workflow, event)
        if paths is None:
            continue
        for needle in (f".github/workflows/{workflow_name}", GUARD, WIRING_GUARD):
            assert _filter_selects(paths, needle), (
                f"{workflow_name} {event} filter does not select {needle}"
            )


@pytest.mark.parametrize("workflow_name", _gates() or ["<none>"])
def test_the_executing_step_can_fail_the_run(workflow_name: str):
    """An executing step that cannot fail is not a gate."""
    if workflow_name == "<none>":
        pytest.skip("no executing workflow to judge")
    workflow = yaml.safe_load((WORKFLOWS / workflow_name).read_text(encoding="utf-8"))
    for job, step in _iter_steps(workflow):
        if step is None or not isinstance(step.get("run"), str):
            continue
        if not _invokes_pytest_with(step["run"], GUARD):
            continue
        assert not _job_blocks_steps(job, step), (
            f"{workflow_name} exempts its executing step from failing the run "
            f"(step={step.get('name')!r})"
        )


@pytest.mark.parametrize("workflow_name", _gates() or ["<none>"])
def test_a_workflow_is_dispatchable(workflow_name: str):
    """A path-filtered gate leaves a revision that touches nothing unjudged."""
    if workflow_name == "<none>":
        pytest.skip("no executing workflow to judge")
    workflow = yaml.safe_load((WORKFLOWS / workflow_name).read_text(encoding="utf-8"))
    assert "workflow_dispatch" in _trigger(workflow), (
        f"{workflow_name} runs the guard but is not dispatchable"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Negative controls — prove each detector rejects the shape it must
# ─────────────────────────────────────────────────────────────────────────────

def test_negative_control_mention_is_not_an_execution():
    """`echo pytest <guard>` tokenises with `pytest` present but not invoked."""
    assert not _invokes_pytest_with(f"echo pytest {GUARD}", GUARD)
    assert not _invokes_pytest_with(f"# pytest {GUARD}", GUARD)


def test_negative_control_a_real_invocation_is_recognised():
    """Positive control: the forms that DO execute must be accepted."""
    assert _invokes_pytest_with(f"pytest {GUARD} -q", GUARD)
    assert _invokes_pytest_with(f"python -m pytest {GUARD}", GUARD)
    assert _invokes_pytest_with("python -m pytest tests/ -q", GUARD)


def test_negative_control_a_narrowed_filter_is_caught():
    """Dropping an input from the filter must redden the coverage rule."""
    narrowed = {"web/console/**", ".github/workflows/operator-console-posture.yml"}
    inputs = guard_inputs()
    assert not all(_filter_selects(narrowed, n) for n in inputs), (
        "the narrowed filter unexpectedly covers every input"
    )
    assert _filter_selects(narrowed, "web/console/**")
    assert not _filter_selects(narrowed, "tests/**")


def test_negative_control_a_blocked_step_is_caught():
    """`continue-on-error` at step or job level must be rejected."""
    assert _job_blocks_steps({}, {"continue-on-error": True})
    assert _job_blocks_steps({"continue-on-error": True}, {})
    assert _job_blocks_steps({}, {"if": False})
    assert not _job_blocks_steps({}, {})


def test_negative_control_a_directory_argument_is_recognised():
    """`pytest tests/` executes the guard and must count as execution."""
    assert _invokes_pytest_with("python -m pytest tests/ -q -rEf", GUARD)
    assert not _invokes_pytest_with("python -m pytest tests/test_other.py", GUARD)


# ─────────────────────────────────────────────────────────────────────────────
# Clone depth — the guard reads history, so the checkout must provide it
# ─────────────────────────────────────────────────────────────────────────────

def _checkout_steps(workflow: dict):
    """Every `actions/checkout` step in the workflow, with its `with:` block."""
    for _job, step in _iter_steps(workflow):
        if step is None:
            continue
        uses = str(step.get("uses") or "")
        if uses.startswith("actions/checkout@"):
            yield step


def _checkout_provides_history(workflow: dict) -> bool:
    """True when some checkout step fetches full history (``fetch-depth: 0``).

    A workflow with no checkout step at all is treated as not providing history:
    the guard cannot resolve a commit that was never fetched.
    """
    for step in _checkout_steps(workflow):
        depth = (step.get("with") or {}).get("fetch-depth")
        # YAML may parse `0` as int or `"0"` as str depending on quoting.
        if depth is not None and str(depth).strip() == "0":
            return True
    return False


@pytest.mark.parametrize("workflow_name", _gates() or ["<none>"])
def test_a_workflow_provides_the_history_its_guard_reads(workflow_name: str):
    """A gate must fetch full history, because the guard resolves a real commit.

    `test_the_map_derivation_point_is_a_real_commit` runs `git cat-file -e` on
    `MAP_DERIVED_FROM`, so that object must exist in the checkout. The default
    `fetch-depth: 1` omits it and the guard fails with
    "MAP_DERIVED_FROM=ae847dd is not a commit in this repository" — a wiring
    defect that reads as a posture defect.

    Measured on a depth-1 clone of this branch: `1 failed, 19 passed`. On a full
    clone: `20 passed`. This test is what makes the difference visible in CI
    rather than in a red gate nobody can explain.
    """
    workflow = yaml.safe_load((WORKFLOWS / workflow_name).read_text(encoding="utf-8")) or {}
    assert _checkout_provides_history(workflow), (
        f"{workflow_name} executes {GUARD}, which reads repository history, but its "
        f"checkout does not set `fetch-depth: 0`; the guard will fail on a shallow clone"
    )


def test_the_history_invariant_is_not_vacuous():
    """The derived gate set must be non-empty, or the parametrisation asserts nothing."""
    assert _gates(), "no gates derived; the history invariant would be vacuous"


def test_negative_control_a_shallow_checkout_is_caught():
    """The detector must flag the exact pre-repair shape and accept the repair."""
    shallow = {
        "jobs": {"j": {"steps": [{"uses": "actions/checkout@v4"}]}},
    }
    explicit_shallow = {
        "jobs": {"j": {"steps": [{"uses": "actions/checkout@v4", "with": {"fetch-depth": 1}}]}},
    }
    repaired = {
        "jobs": {"j": {"steps": [{"uses": "actions/checkout@v4", "with": {"fetch-depth": 0}}]}},
    }
    quoted = {
        "jobs": {"j": {"steps": [{"uses": "actions/checkout@v4", "with": {"fetch-depth": "0"}}]}},
    }
    no_checkout = {"jobs": {"j": {"steps": [{"run": "pytest tests/"}]}}}

    assert not _checkout_provides_history(shallow), "default depth must be flagged"
    assert not _checkout_provides_history(explicit_shallow), "depth 1 must be flagged"
    assert not _checkout_provides_history(no_checkout), "no checkout cannot provide history"
    assert _checkout_provides_history(repaired), "fetch-depth: 0 (int) must pass"
    assert _checkout_provides_history(quoted), "fetch-depth: '0' (str) must pass"
