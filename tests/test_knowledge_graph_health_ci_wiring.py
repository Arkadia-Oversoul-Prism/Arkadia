"""Lane 3 — the graph-health guard must be *executed*, not merely present.

``tests/test_knowledge_graph_health_read_boundary.py`` holds the ``_count()``
defect. Measured on the branch that added it (``8442ace4``), it was executed by
**no** workflow: the head produced 7 workflow runs and a scan of every run log
for the guard's filename returned 0 mentions. ``knowledge-connection-lifecycle-guard.yml``
is the executable surface for this class -- it exists for exactly this reason,
because the two workflows whose ``tests/**`` filter *selects* a new knowledge test
(``economic-seam-engine.yml``, ``prism-console-contract.yml``) run only their own
derived domains and never reach it.

A guard no gate executes is decoration, so this file states the invariant over the
real workflow file rather than asserting the wiring in prose:

1. some workflow *executes* the guard (a real ``pytest`` invocation, not a mention);
2. that workflow is dispatchable, so the guard can be re-run at an exact revision;
3. every declared ``paths`` filter selects every input the guard reads;
4. the executing step can fail the job (no ``continue-on-error`` / falsey ``if``).

Each property carries a negative control that feeds the detector the defective
shape, so the detector cannot be disarmed by rewriting the workflow. The control
that matters most is the **live** one: ``test_negative_control_the_real_workflow_is_rejudged``
mutates the real file and asserts the detector notices.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]

_GUARD_FILE = "tests/test_knowledge_graph_health_ci_wiring.py"
_CONTRACT_FILE = "tests/test_knowledge_graph_health_read_boundary.py"
_WORKFLOW_FILE = ".github/workflows/knowledge-connection-lifecycle-guard.yml"

# Every path the contract reads. `knowledge/**` is the bounded scan domain
# `test_no_other_module_reads_a_row_positionally` sweeps, so the filter must
# select the whole package rather than the one module that held the defect.
_REQUIRED_INPUTS = (
    _CONTRACT_FILE,
    _GUARD_FILE,
    "knowledge/graph_health.py",
    "knowledge/db.py",
)


def _load(path: Path | str) -> dict:
    return yaml.safe_load((REPO_ROOT / path).read_text(encoding="utf-8"))


def _trigger_block(workflow: dict) -> dict:
    # PyYAML reads the bare key `on` as the boolean True.
    return workflow.get("on") or workflow.get(True) or {}


def _path_filter(trigger_block: dict, event: str) -> set[str] | None:
    block = trigger_block.get(event)
    if not isinstance(block, dict):
        return None
    paths = block.get("paths")
    return None if paths is None else set(paths)


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Compile a GitHub `paths` glob to a whole-string regex.

    `**/` matches zero or more path segments (so it also matches a root file),
    `**` matches across separators, and `*`/`?` stay within one segment.
    """
    out: list[str] = []
    i = 0
    while i < len(pattern):
        char = pattern[i]
        if char == "*":
            if pattern.startswith("**/", i):
                out.append("(?:.*/)?")
                i += 3
                continue
            if pattern.startswith("**", i):
                out.append(".*")
                i += 2
                continue
            out.append("[^/]*")
        elif char == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(char))
        i += 1
    return re.compile("^" + "".join(out) + "$")


def _selects_path(path_filter: set[str], path: str) -> bool:
    return any(_glob_to_regex(p).match(path) for p in path_filter)


def _steps(workflow: dict):
    for job in (workflow.get("jobs") or {}).values():
        for step in job.get("steps") or []:
            yield job, step


def _pytest_invokes(tokens: list[str]) -> bool:
    """Whether a token list *invokes* pytest rather than mentioning it.

    `echo pytest x` tokenises to `["echo", "pytest", "x"]` and must not count, so
    `pytest` has to be the invoked command word -- either directly or as
    `python -m pytest`.
    """
    for i, token in enumerate(tokens):
        base = Path(token).name
        if base == "pytest":
            if i == 0:
                return True
            if i >= 2 and tokens[i - 1] == "-m" and Path(tokens[i - 2]).name.startswith("python"):
                return True
    return False


def _invocations(workflow: dict):
    """Every step whose `run` actually invokes pytest, with its job and tokens."""
    for job, step in _steps(workflow):
        run = step.get("run")
        if not isinstance(run, str):
            continue
        for line in run.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            tokens = line.split()
            if _pytest_invokes(tokens):
                yield job, step, tokens


def _is_dispatchable(trigger_block: dict) -> bool:
    return "workflow_dispatch" in trigger_block


def _is_falsey_condition(value: object) -> bool:
    if isinstance(value, bool):
        return value is False
    if isinstance(value, str):
        return value.strip().lower() in {"false", "${{ false }}"}
    return value is None


def _exemption(job: dict, step: dict) -> str | None:
    """A step or job that cannot fail the build, or is skipped outright.

    The `if` key must be *present* to count: an absent `if` is the normal case,
    and treating it as falsey would report every ordinary step as exempt.
    """
    for label, holder in (("step", step), ("job", job)):
        if holder.get("continue-on-error") is True:
            return f"{label} continue-on-error: true"
        if "if" in holder and _is_falsey_condition(holder.get("if")):
            return f"{label} if: false"
    return None


def _mentions_contract(workflow: dict) -> bool:
    """Whether the workflow names the contract file in a step or a `paths` filter."""
    for _job, step, tokens in _invocations(workflow):
        if any(_CONTRACT_FILE in t for t in tokens):
            return True
    for event in ("pull_request", "push"):
        path_filter = _path_filter(_trigger_block(workflow), event)
        if path_filter and _CONTRACT_FILE in path_filter:
            return True
    return False


def _candidates() -> list[tuple[Path, dict]]:
    return [
        (path, _load(path))
        for path in sorted((REPO_ROOT / ".github/workflows").glob("*.yml"))
        if _mentions_contract(_load(path))
    ]


def _audit(workflow: dict) -> list[str]:
    defects: list[str] = []
    trigger = _trigger_block(workflow)
    if not _is_dispatchable(trigger):
        defects.append("not dispatchable (no workflow_dispatch)")
    for event in ("pull_request", "push"):
        path_filter = _path_filter(trigger, event)
        if path_filter is None:
            continue  # event not declared, or all paths selected
        omitted = sorted(p for p in _REQUIRED_INPUTS if not _selects_path(path_filter, p))
        if omitted:
            defects.append(f"{event} paths filter omits {', '.join(omitted)}")
    executed = False
    for job, step, tokens in _invocations(workflow):
        if not any(_CONTRACT_FILE in t for t in tokens):
            continue
        exemption = _exemption(job, step)
        if exemption:
            defects.append(f"executing step is exempted by {exemption}")
            continue
        executed = True
    if not executed:
        defects.append("no step executes the contract")
    return defects


def test_the_derived_inputs_resolve_to_real_paths():
    missing = [p for p in _REQUIRED_INPUTS if not (REPO_ROOT / p).exists()]
    assert missing == [], f"declared inputs do not exist: {missing}"


def test_some_workflow_executes_the_guard():
    candidates = _candidates()
    assert candidates, f"no workflow names {_CONTRACT_FILE}"
    executed = [(p, w) for p, w in candidates if not _audit(w)]
    assert executed, {str(p.relative_to(REPO_ROOT)): _audit(w) for p, w in candidates}


@pytest.mark.parametrize("path", [p for p, _ in _candidates()], ids=lambda p: p.name)
def test_every_candidate_workflow_is_executable_and_can_fail(path: Path):
    assert _audit(_load(path)) == []


def test_negative_control_an_omitted_input_is_reported():
    trigger = {"pull_request": {"paths": sorted(set(_REQUIRED_INPUTS) - {"knowledge/db.py"})}}
    defects = _audit({"on": trigger, "jobs": {"j": {"steps": [{"run": f"python -m pytest {_CONTRACT_FILE} -q"}]}}})
    assert any("knowledge/db.py" in d for d in defects), defects


def test_negative_control_a_mention_without_execution_is_reported():
    workflow = {
        "on": {"workflow_dispatch": {}, "pull_request": {"paths": sorted(_REQUIRED_INPUTS)}},
        "jobs": {"j": {"steps": [{"run": f"echo pytest {_CONTRACT_FILE}"}]}},
    }
    assert "no step executes the contract" in _audit(workflow)


def test_negative_control_a_directory_argument_is_not_an_execution():
    """`pytest tests/` does not name the contract, so it cannot be its execution site."""
    workflow = {
        "on": {"workflow_dispatch": {}, "pull_request": {"paths": sorted(_REQUIRED_INPUTS)}},
        "jobs": {"j": {"steps": [{"run": "python -m pytest tests/ -q"}]}},
    }
    assert "no step executes the contract" in _audit(workflow)


@pytest.mark.parametrize(
    "exempt",
    [
        {"continue-on-error": True},
        {"if": False},
        {"if": "false"},
    ],
)
def test_negative_control_each_exemption_form_is_reported(exempt):
    workflow = {
        "on": {"workflow_dispatch": {}, "pull_request": {"paths": sorted(_REQUIRED_INPUTS)}},
        "jobs": {"j": {"steps": [{"run": f"python -m pytest {_CONTRACT_FILE} -q", **exempt}]}},
    }
    defects = _audit(workflow)
    assert any("exempted by" in d for d in defects), defects


def test_negative_control_a_job_level_exemption_is_reported():
    workflow = {
        "on": {"workflow_dispatch": {}, "pull_request": {"paths": sorted(_REQUIRED_INPUTS)}},
        "jobs": {
            "j": {
                "continue-on-error": True,
                "steps": [{"run": f"python -m pytest {_CONTRACT_FILE} -q"}],
            }
        },
    }
    defects = _audit(workflow)
    assert any("job continue-on-error" in d for d in defects), defects


def test_negative_control_a_missing_dispatch_is_reported():
    workflow = {
        "on": {"pull_request": {"paths": sorted(_REQUIRED_INPUTS)}},
        "jobs": {"j": {"steps": [{"run": f"python -m pytest {_CONTRACT_FILE} -q"}]}},
    }
    assert "not dispatchable (no workflow_dispatch)" in _audit(workflow)


def test_negative_control_the_real_workflow_is_rejudged(tmp_path):
    """The decisive control: mutate the *real* file, not a synthetic fixture.

    A detector that only agrees with a fixture it was handed proves nothing about
    the workflow that actually gates the guard.
    """
    real = (REPO_ROOT / _WORKFLOW_FILE).read_text(encoding="utf-8")
    assert _audit(_load(_WORKFLOW_FILE)) == [], "precondition: the real file is clean"

    disabled = real.replace(
        f"python -m pytest tests/test_knowledge_shared_connection_lifecycle.py",
        f"echo pytest tests/test_knowledge_shared_connection_lifecycle.py",
    )
    probe = tmp_path / "probe.yml"
    probe.write_text(disabled, encoding="utf-8")
    assert "no step executes the contract" in _audit(_load(probe)), (
        "the detector did not notice the real step was replaced by a mention"
    )

    dropped = real.replace("      - \"knowledge/**\"\n", "", 1)
    probe2 = tmp_path / "probe2.yml"
    probe2.write_text(dropped, encoding="utf-8")
    assert any("omits" in d for d in _audit(_load(probe2))), (
        "the detector did not notice a dropped input from the real filter"
    )
