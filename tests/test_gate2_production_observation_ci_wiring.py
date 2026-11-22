"""Boundary guard: the Gate-2 observation fitness tests must be *executed*.

`tests/test_gate2_production_observation.py` pins the harness's classifiers and
the app-identity resolution that binds a marker observation to the application it
measures. Measured on `main` @ `034d8879`, `grep -rn
test_gate2_production_observation .github/` returned **0**: the suite ran only when
a human invoked pytest by hand, so the oracle could regress silently -- the same
"a guard no workflow executes is decoration" class already closed for the
baseline-fingerprint and boot-syntax guards.

The invariant is stated generically over every workflow that executes the suite:

1. Some workflow must **execute** it -- a step whose command is a pytest
   invocation whose arguments name the file (or the directory containing it). A
   step that merely *prints* the path does not satisfy this.
2. Such a workflow must be dispatchable (`workflow_dispatch`), so the oracle can be
   executed against an exact revision without a source change under its paths.
3. Its `paths` filter must name every input the suite reads: the harness script,
   the test file, the wiring guard, and the two `index.html` shells whose `<title>`
   is the app identity the tests exercise. A shell-only commit must run the guard.
4. An executing step must be able to fail the run: no step- or job-level
   `continue-on-error`, and no step- or job-level `if: false`.

Negative controls prove the detector catches the forms it exists to catch,
including mention-without-execution and each exemption form, so disarming the
wiring cannot pass silently.
"""

from __future__ import annotations

import shlex
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

_TARGET = "tests/test_gate2_production_observation.py"
_TARGET_DIRS = {"tests", "tests/"}
# Every input the suite reads. The shells are read by `served_identity`, so a change
# to either changes what the guard asserts -- it is an input, not incidental markup.
_REQUIRED_SELECTORS = (
    "scripts/gate2_production_observation.py",
    _TARGET,
    "tests/test_gate2_production_observation_ci_wiring.py",
    "web/arkadia_console/index.html",
    "archive/frontend/arkadia-prism/web/public_prism/index.html",
)

_FALSEY = {"false", "${{ false }}", "0"}


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _trigger(workflow: dict) -> dict:
    """The `on:` mapping. PyYAML parses a bare `on` key as boolean True."""
    block = workflow.get(True, workflow.get("on"))
    return block if isinstance(block, dict) else {}


def _steps(workflow: dict):
    for job_name, job in (workflow.get("jobs") or {}).items():
        for step in (job or {}).get("steps") or []:
            yield job_name, job, step


def _commands(step: dict) -> list[list[str]]:
    """Each effective shell command in a step's `run`, tokenised.

    Comment lines are dropped, so a path that appears only in prose is not a
    command. A `uses:` action yields nothing.
    """
    run = step.get("run")
    if not isinstance(run, str):
        return []
    out: list[list[str]] = []
    for line in run.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            tokens = shlex.split(stripped, comments=True)
        except ValueError:
            tokens = stripped.split()
        if tokens:
            out.append(tokens)
    return out


def _command_tokens(tokens: list[str]) -> list[str]:
    """Tokens from the invoked executable onward (leading `env`/`NAME=value` dropped)."""
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


def _pytest_invokes_target(tokens: list[str]) -> bool:
    """Whether this command *executes* pytest against the target.

    `pytest` must be the invoked command word (`pytest x` or `python -m pytest x`),
    and the target must be one of its arguments. `echo pytest <target>` is a
    mention, not an execution, and is rejected.
    """
    cmd = _command_tokens(tokens)
    idx = None
    for i, tok in enumerate(cmd):
        if tok == "pytest" or tok.endswith("/pytest"):
            if i == 0 or cmd[i - 1] == "-m":
                idx = i
                break
    if idx is None:
        return False
    for arg in cmd[idx + 1:]:
        if arg == _TARGET or arg.startswith(_TARGET + "::") or arg in _TARGET_DIRS:
            return True
    return False


def _executing_steps(workflow: dict):
    """(job_name, job, step) triples that execute the suite with pytest."""
    return [
        (name, job, step)
        for name, job, step in _steps(workflow)
        if any(_pytest_invokes_target(c) for c in _commands(step))
    ]


def _mentions(workflow: dict) -> bool:
    if any(_TARGET in str(step.get("run", "")) for _, _, step in _steps(workflow)):
        return True
    trigger = _trigger(workflow)
    for event in ("pull_request", "push"):
        block = trigger.get(event)
        paths = block.get("paths") if isinstance(block, dict) else None
        if paths and _TARGET in set(paths):
            return True
    return False


def _is_falsey(value: object) -> bool:
    return str(value).strip().lower() in _FALSEY


def _exemption(job: dict, step: dict) -> str | None:
    if job.get("continue-on-error", False):
        return "job continue-on-error"
    if _is_falsey(job.get("if", "")):
        return "job if: false"
    if _is_falsey(step.get("if", "")):
        return "step if: false"
    if step.get("continue-on-error", False):
        return "step continue-on-error"
    return None


def _effective(workflow: dict):
    return [
        (name, job, step)
        for name, job, step in _executing_steps(workflow)
        if _exemption(job, step) is None
    ]


def _path_filters(workflow: dict) -> set[str]:
    trigger = _trigger(workflow)
    covered: set[str] = set()
    for event in ("pull_request", "push"):
        block = trigger.get(event)
        paths = block.get("paths") if isinstance(block, dict) else None
        if paths:
            covered |= set(paths)
    return covered


def _audit(workflow: dict) -> list[str]:
    """Defects that make a workflow unable to satisfy the invariant (empty = pass).

    A workflow that does not mention the suite is not a candidate and is not judged.
    """
    if not _mentions(workflow):
        return []
    defects: list[str] = []
    if not _effective(workflow):
        defects.append(
            "no effective step executes the suite (a mention is not an execution, "
            "or the step is exempted by continue-on-error / if: false)"
        )
    if "workflow_dispatch" not in _trigger(workflow):
        defects.append("no workflow_dispatch: not executable on demand")
    missing = [s for s in _REQUIRED_SELECTORS if s not in _path_filters(workflow)]
    defects.extend(f"paths filter omits {s}" for s in missing)
    return defects


def _candidates() -> list[tuple[Path, dict]]:
    out = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        workflow = _load(path)
        if _mentions(workflow):
            out.append((path, workflow))
    return out


def test_some_workflow_executes_the_gate2_observation_suite():
    executed = [path.name for path, wf in _candidates() if _effective(wf)]
    assert executed, (
        f"no workflow executes {_TARGET} with pytest: the harness's fitness tests "
        "run nowhere, so the observation oracle can regress silently"
    )


def test_every_executing_workflow_satisfies_the_invariant():
    """Parametrized over the workflows that run the suite, not against one file.

    A second wiring is judged by the same rule, so deleting the only one cannot
    make these assertions vacuous.
    """
    candidates = [path for path, wf in _candidates() if _effective(wf)]
    assert candidates
    for path in candidates:
        defects = _audit(_load(path))
        assert not defects, f"{path.name}: {defects}"


def test_the_shells_are_named_by_the_trigger():
    """The identity inputs must select the gate that asserts on them."""
    for path, wf in _candidates():
        if not _effective(wf):
            continue
        covered = _path_filters(wf)
        for shell in (
            "web/arkadia_console/index.html",
            "archive/frontend/arkadia-prism/web/public_prism/index.html",
        ):
            assert shell in covered, f"{path.name} does not select {shell}"


# ---------------------------------------------------------------------------
# Negative controls: the detector must catch what it exists to catch.
# ---------------------------------------------------------------------------


def _workflow_with(step_run: str, *, paths=None, dispatch: bool = True) -> dict:
    trigger = {
        "pull_request": {"paths": paths if paths is not None else list(_REQUIRED_SELECTORS)},
        "push": {"paths": paths if paths is not None else list(_REQUIRED_SELECTORS)},
    }
    if dispatch:
        trigger["workflow_dispatch"] = None
    return {"on": trigger, "jobs": {"g": {"steps": [{"run": step_run}]}}}


def test_negative_control_a_mention_is_not_an_execution():
    """`echo pytest <target>` tokenises to a pytest word but invokes `echo`."""
    wf = _workflow_with(f"echo pytest {_TARGET}")
    assert _mentions(wf)
    assert _executing_steps(wf) == []
    assert _audit(wf)


def test_positive_control_a_real_invocation_passes_the_detector():
    for form in (
        f"pytest -q {_TARGET}",
        f"python -m pytest -q {_TARGET}",
        "python -m pytest -q tests/",
    ):
        wf = _workflow_with(form)
        assert _effective(wf), form
        assert _audit(wf) == [], form


def test_negative_control_each_exemption_form_is_reported():
    base = {"on": {"workflow_dispatch": None}, "jobs": {}}
    step = {"run": f"pytest -q {_TARGET}"}
    for job_extra, step_extra, expected in (
        ({"continue-on-error": True}, {}, "job continue-on-error"),
        ({"if": "false"}, {}, "job if: false"),
        ({}, {"if": "false"}, "step if: false"),
        ({}, {"continue-on-error": True}, "step continue-on-error"),
    ):
        wf = {**base, "jobs": {"g": {**job_extra, "steps": [{**step, **step_extra}]}}}
        wf["on"] = {
            "workflow_dispatch": None,
            "pull_request": {"paths": list(_REQUIRED_SELECTORS)},
            "push": {"paths": list(_REQUIRED_SELECTORS)},
        }
        assert _exemption(wf["jobs"]["g"], wf["jobs"]["g"]["steps"][0]) == expected
        assert _effective(wf) == []


def test_negative_control_a_missing_input_selector_is_reported():
    paths = [p for p in _REQUIRED_SELECTORS if p != "web/arkadia_console/index.html"]
    wf = _workflow_with(f"pytest -q {_TARGET}", paths=paths)
    assert any("web/arkadia_console/index.html" in d for d in _audit(wf))


def test_negative_control_a_missing_dispatch_is_reported():
    wf = _workflow_with(f"pytest -q {_TARGET}", dispatch=False)
    assert any("workflow_dispatch" in d for d in _audit(wf))
