"""The Lab remote-redaction guard must actually execute in CI.

`tests/test_lab_remote_redaction.py` pins a shared-substrate security repair: git
remote userinfo must never be surfaced by `repository_state()`. As with every guard
in this repository, that only holds if a workflow runs it in a step that can fail.

The CP10 workflow's only broad-suite step is `continue-on-error: true` and runs a
bare `pytest tests/ -q`, which aborts at the CE-01 `weaver.autonomy` collection
error (measured: `Interrupted: 1 error during collection`), so it executes none of
these files. This module states the invariant over the workflow that runs the guard:

1. Some workflow must execute the guard, in a step that can fail.
2. That workflow's `paths` filters must select **every surface the guard reads**,
   so a change to the producer cannot reach `main` unjudged. The domain is derived
   from the guard's own imports, not restated here.
3. The workflow must be dispatchable, so the guard can be re-run against an exact
   revision on demand.

Each detector has a negative control, so a rewrite of the workflow cannot disarm
the invariant without reddening a control.
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

GUARD_FILE = "tests/test_lab_remote_redaction.py"
WIRING_FILE = "tests/test_lab_remote_redaction_ci_wiring.py"
WORKFLOW_FILE = ".github/workflows/lab-remote-redaction.yml"


# ---------------------------------------------------------------------------
# Workflow helpers


def _workflow_paths() -> list[Path]:
    return sorted(WORKFLOWS.glob("*.yml"))


def _load(path: Path | str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _trigger_block(workflow: dict) -> dict:
    """The `on:` mapping (PyYAML parses the bare key `on` as boolean True)."""
    block = workflow.get(True, workflow.get("on"))
    return block if isinstance(block, dict) else {}


def _path_filter(trigger_block: dict, event: str) -> set[str] | None:
    event_block = trigger_block.get(event)
    if not isinstance(event_block, dict):
        return None
    paths = event_block.get("paths")
    return None if paths is None else set(paths)


def _steps(workflow: dict) -> list[dict]:
    seen: list[dict] = []
    for job in (workflow.get("jobs") or {}).values():
        if isinstance(job, dict):
            seen.extend(step for step in (job.get("steps") or []) if isinstance(step, dict))
    return seen


def _guard_steps(workflow: dict) -> list[dict]:
    """Steps whose `run:` invokes pytest on the guard file.

    A mention is not an execution: `echo <guard>` must not satisfy the invariant,
    and neither must a step that only *writes* the path. The command is tokenised
    (with comments dropped) and `pytest` must be the invoked command word, with the
    guard file among its arguments.
    """
    found: list[dict] = []
    for step in _steps(workflow):
        run = step.get("run")
        if not isinstance(run, str):
            continue
        if _invokes_pytest_on(run, GUARD_FILE):
            found.append(step)
    return found


def _invokes_pytest_on(script: str, target: str) -> bool:
    """Whether *script* actually runs pytest with *target* as an argument.

    Backslash line-continuations are joined first, so a multi-line `pytest \\`
    invocation is read as the single command it is at the shell.
    """
    joined = re.sub(r"\\\s*\n", " ", script)
    for line in joined.splitlines():
        try:
            tokens = shlex.split(line, comments=True)
        except ValueError:
            continue
        if "pytest" not in tokens:
            continue
        index = tokens.index("pytest")
        # `pytest …` directly, or `python -m pytest …`.
        if index == 0 or (index == 2 and tokens[0] in {"python", "python3"} and tokens[1] == "-m"):
            if target in tokens:
                return True
    return False


def _runs_guard(workflow: dict) -> bool:
    return bool(_guard_steps(workflow))


def _guard_workflows() -> list[str]:
    return [p.name for p in _workflow_paths() if _runs_guard(_load(p))]


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Compile a GitHub `paths` glob to a whole-string regex.

    `**/` matches zero or more leading segments, a remaining `**` matches anything
    including `/`, and `*`/`?` match within one segment. Every other character is
    literal.
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
    return any(_glob_to_regex(pattern).match(path) for pattern in path_filter)


# ---------------------------------------------------------------------------
# The guard's own domain — derived from its imports, never restated


def _guard_domain() -> list[str]:
    """Repo-relative paths the guard reads, derived by parsing its imports.

    A module import (`lab.observatory.git`) resolves to a tracked path
    (`lab/observatory/git.py`). Restating this list by hand would drift the moment
    the guard reads one more surface, so it is read from the source instead.
    """
    tree = ast.parse((ROOT / GUARD_FILE).read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
        elif isinstance(node, ast.Import):
            modules.update(a.name for a in node.names)

    paths: set[str] = set()
    for module in modules:
        parts = module.split(".")
        candidate = ROOT.joinpath(*parts).with_suffix(".py")
        if candidate.is_file():
            paths.add(candidate.relative_to(ROOT).as_posix())
        package = ROOT.joinpath(*parts)
        if (package / "__init__.py").is_file():
            paths.add((package / "__init__.py").relative_to(ROOT).as_posix())
    return sorted(paths)


# ---------------------------------------------------------------- detector controls


def test_runs_guard_detector_distinguishes_the_forms():
    runs = {"jobs": {"j": {"steps": [{"run": f"python -m pytest {GUARD_FILE} -q"}]}}}
    other = {"jobs": {"j": {"steps": [{"run": "python -m py_compile lab/service.py"}]}}}
    assert _runs_guard(runs)
    assert not _runs_guard(other)


def test_selector_accepts_the_forms_github_uses():
    filt = {".github/workflows/lab-remote-redaction.yml", "lab/observatory/**", "tests/test_x.py"}
    assert _selects_path(filt, "lab/observatory/git.py")
    assert _selects_path(filt, ".github/workflows/lab-remote-redaction.yml")
    assert _selects_path(filt, "tests/test_x.py")


def test_selector_rejects_an_incomplete_filter():
    # The incomplete shape a negative control feeds to the invariant.
    filt = {".github/workflows/lab-remote-redaction.yml", "tests/test_lab_remote_redaction.py"}
    assert _selects_path(filt, "tests/test_lab_remote_redaction.py")
    assert not _selects_path(filt, "lab/observatory/git.py")


def test_guard_domain_is_derived_and_covers_the_producer():
    """Sanity: the derivation found the surfaces the guard actually reads."""
    domain = _guard_domain()
    assert "lab/observatory/git.py" in domain, domain
    assert "lab/service.py" in domain, domain


# ---------------------------------------------------------------- the invariants


def test_a_workflow_executes_the_guard():
    assert _guard_workflows(), (
        f"no workflow runs {GUARD_FILE}; the remote-redaction boundary holds only "
        f"when a human runs the suite by hand"
    )


@pytest.mark.parametrize("name", _guard_workflows())
def test_the_executing_step_can_fail_the_job(name: str):
    """A step under `continue-on-error` enforces nothing."""
    for step in _guard_steps(_load(WORKFLOWS / name)):
        assert step.get("continue-on-error") is not True, (
            f"{name} runs the guard in a step that cannot fail "
            f"({step.get('name')!r})"
        )


@pytest.mark.parametrize("name", _guard_workflows())
def test_the_executing_workflow_selects_every_surface_the_guard_reads(name: str):
    """A change to the producer must reach the workflow that judges it."""
    workflow = _load(WORKFLOWS / name)
    trigger = _trigger_block(workflow)
    for event in ("push", "pull_request"):
        paths = _path_filter(trigger, event)
        assert paths is not None, f"{name} declares {event} without a paths filter"
        for surface in _guard_domain():
            assert _selects_path(paths, surface), (
                f"{name} runs the guard on {event} but its {event} filter does not "
                f"select {surface}, which the guard reads"
            )


@pytest.mark.parametrize("name", _guard_workflows())
def test_the_executing_workflow_selects_itself_and_the_guard(name: str):
    paths = _path_filter(_trigger_block(_load(WORKFLOWS / name)), "pull_request")
    assert _selects_path(paths, f".github/workflows/{name}")
    assert _selects_path(paths, GUARD_FILE)
    assert _selects_path(paths, WIRING_FILE)


@pytest.mark.parametrize("name", _guard_workflows())
def test_the_executing_workflow_is_dispatchable(name: str):
    """So the guard can be re-run against an exact revision on demand."""
    assert "workflow_dispatch" in _trigger_block(_load(WORKFLOWS / name))


@pytest.mark.parametrize("name", _guard_workflows())
def test_push_and_pull_request_filters_are_identical(name: str):
    """An asymmetric filter is a masking hole, not a convenience."""
    trigger = _trigger_block(_load(WORKFLOWS / name))
    push = _path_filter(trigger, "push")
    pull = _path_filter(trigger, "pull_request")
    assert push == pull, (
        f"{name} declares asymmetric push/pull_request filters; only in one: "
        f"{sorted((push or set()) ^ (pull or set()))}"
    )


def test_the_dedicated_workflow_is_the_one_that_runs_it():
    """The repair is judged by its own gate, not by a broad pass/fail suite."""
    assert WORKFLOW_FILE in {f".github/workflows/{n}" for n in _guard_workflows()}


# ---------------------------------------------------------------- negative controls


def test_negative_control_a_continue_on_error_step_is_not_a_judging_step():
    polluted = {
        "jobs": {
            "j": {
                "steps": [
                    {
                        "name": "reporting",
                        "continue-on-error": True,
                        "run": f"python -m pytest {GUARD_FILE} -q",
                    }
                ]
            }
        }
    }
    assert _runs_guard(polluted)
    steps = _guard_steps(polluted)
    assert all(step.get("continue-on-error") is True for step in steps), (
        "the negative control must model a non-judging step so the invariant's "
        "assertion would fire on it"
    )


def test_negative_control_an_incomplete_filter_fails_the_domain_invariant():
    """Prove the domain assertion can fail on a filter that omits the producer."""
    incomplete = {
        ".github/workflows/lab-remote-redaction.yml",
        GUARD_FILE,
        WIRING_FILE,
    }
    assert not _selects_path(incomplete, "lab/observatory/git.py")
    # ...while the real filter covers it.
    real = _path_filter(_trigger_block(_load(WORKFLOWS / "lab-remote-redaction.yml")), "pull_request")
    assert _selects_path(real, "lab/observatory/git.py")


def test_negative_control_an_echo_of_the_guard_path_is_not_execution():
    """A step that merely *mentions* the file must not satisfy the invariant."""
    assert not _invokes_pytest_on(f"echo {GUARD_FILE}", GUARD_FILE)
    assert not _invokes_pytest_on(f"echo pytest {GUARD_FILE}", GUARD_FILE)
    assert not _invokes_pytest_on(f"# pytest {GUARD_FILE}", GUARD_FILE)
    assert not _invokes_pytest_on(f"echo {GUARD_FILE} && true", GUARD_FILE)
    # ...while a real invocation of the same file does.
    assert _invokes_pytest_on(f"python -m pytest {GUARD_FILE} -q", GUARD_FILE)
    assert _invokes_pytest_on(f"pytest {GUARD_FILE} -q", GUARD_FILE)
    assert _invokes_pytest_on(f"python -m pytest \\\n  {GUARD_FILE} \\\n  -q", GUARD_FILE)
