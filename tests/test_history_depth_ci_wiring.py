"""Boundary guard: a workflow that executes a history-dependent guard needs full history.

`actions/checkout@v4` defaults to `fetch-depth: 1`. Six workflows in this repository
declare `fetch-depth: 0` and each does so because a guard they execute resolves a
*pinned revision* out of git history. `provider-routing.yml` runs the whole suite
(`pytest tests/ -q -rEf --continue-on-collection-errors`) on the default shallow
checkout, so every history-dependent guard it executes is decided by a truncated
repository rather than by the tree.

Measured at `main` `6109c72a` — the run `38224653480` dispatched at that exact SHA
reports **21 failed / 2859 passed / 1 error**, and the CI failure set differs from a
dependency-complete local run of the same revision by exactly four nodes, all in
`tests/test_agents_md_encoding_adjudication.py`. Reproduced in a `--depth 1` clone of
that revision: `git cat-file -t 6c43218a48a4` -> `fatal: Not a valid object name`,
`4 failed, 13 passed, 6 skipped`. The same four nodes pass with full history
(`18 passed, 5 skipped`).

The failure direction is what makes this a boundary defect rather than cosmetic noise:
`scripts/agents_md_encoding_audit.py::exit_code` returns **2** ("undecided") when the
oracle revision is unreachable, and `test_live_file_verdict_matches_its_state` requires
exit **1** for a clean file. A shallow clone therefore reports a *failure* on a file
that is provably clean. The upstream log already demonstrates the confusion —
`provider-routing.yml` carries the comment "the known CE-01 `weaver.autonomy`
module-vs-package collision aborts the whole session on a bare `pytest tests/`", which
is a different, real defect; a reader of that log has no way to tell the four
clone-depth failures from the repository's genuine debt.

These tests state the invariant once, generically over every workflow that executes a
history-dependent guard, so a new such workflow is judged by the same rule:

1. Every workflow whose steps execute a history-dependent guard must check out full
   history (`fetch-depth: 0`), so the guard's verdict is a function of the tree.
2. Such a workflow must select itself and the guard file in its `paths` filter, or the
   pull request that rewrites the boundary is judged by no gate — and it must not
   exempt the step that runs the guard.
3. The detector is proven against the shapes it must catch, and proven *not* to fire on
   a workflow that executes no history-dependent guard — a detector that flags
   everything is not a detector.

The domain is **derived**, not restated. A guard is history-dependent when it names a
revision pinned in the tree *and* resolves it through git (`show` / `cat-file` /
`rev-parse`), and that revision is still an object in this repository. The pinned
revisions themselves come from the modules that declare them
(`scripts/agents_md_encoding_audit.py`), not from a copy here: a revision the tree
rewrites away is a broken guard, not a history-dependent one. A hand-maintained list
would drift, and a drifted list makes the boundary assertion vacuous — the defect class
this repository has already recorded for `FINGERPRINT_DOCS` and for the console-contract
domain.

Consequence, recorded so it is not mistaken for a per-PR defect: a workflow whose
selection is derived from the repository cannot be validated by the branch that adds a
member to the domain. `provider-routing.yml` ran the whole suite while this guard did
not exist, so no pull request could have observed the defect — only the composition can.
"""

from __future__ import annotations

import re
import shlex
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
TESTS = ROOT / "tests"
_GUARD_FILE = "tests/test_history_depth_ci_wiring.py"

# `ORACLE_REV = "6c43218a48a4"` — a revision pinned in a module the tree imports.
_PIN = re.compile(
    r"^\s*([A-Z][A-Z0-9_]*)\s*=\s*[\"']([0-9a-f]{7,40})[\"']\s*$", re.MULTILINE
)
# A revision is *resolved* only where git reads an object out of history. `show`,
# `cat-file` and `rev-parse` all do; a revision pasted into a comment or compared as a
# display string does not, and must not place its test in the domain.
_GIT_READ = re.compile(r"[\"']git[\"'].*?[\"'](show|cat-file|rev-parse)[\"']", re.DOTALL)


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _run_scripts(workflow: dict) -> list[str]:
    scripts: list[str] = []
    for job in (workflow.get("jobs") or {}).values():
        for step in job.get("steps") or []:
            run = step.get("run")
            if isinstance(run, str):
                scripts.append(run)
    return scripts


def _checkout_steps(workflow: dict) -> list[dict]:
    steps: list[dict] = []
    for job in (workflow.get("jobs") or {}).values():
        for step in job.get("steps") or []:
            uses = step.get("uses")
            if isinstance(uses, str) and uses.startswith("actions/checkout@"):
                steps.append(step)
    return steps


def _full_history(workflow: dict) -> bool:
    """Whether every checkout in the workflow fetches the whole repository.

    Any shallow checkout is enough to truncate the history a guard resolves against,
    so the check is `all`, not `any`.
    """
    checkouts = _checkout_steps(workflow)
    return bool(checkouts) and all(
        (step.get("with") or {}).get("fetch-depth") == 0 for step in checkouts
    )


def _selects_path(path_filter: set[str], path: str) -> bool:
    """Whether a `paths` filter selects a literal path, mirroring GitHub's globs."""
    parts = [p for p in path.split("/") if p]
    for pattern in path_filter:
        segments = pattern.split("/")
        if segments[-1] == "**" and len(segments) - 1 <= len(parts):
            if all(
                ps == "*" or ps == pp
                for ps, pp in zip(segments[:-1], parts[: len(segments) - 1])
            ):
                return True
            continue
        if len(segments) != len(parts):
            continue
        if all(ps == "**" or ps == "*" or ps == pp for ps, pp in zip(segments, parts)):
            return True
    return False


def _pytest_command_index(tokens: list[str]) -> int | None:
    """Index of the `pytest` word **only when it is the invoked command**.

    `pytest x` and `python -m pytest x` count; `echo pytest x` does not. Leading `env`
    and `NAME=value` assignments are skipped so `PYTHONPATH=. pytest x` resolves.
    """
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if "=" in tok and not tok.startswith("-"):
            i += 1
            continue
        if tok == "env":
            i += 1
            continue
        if tok == "pytest" or tok.endswith("/pytest"):
            return i
        if tok in ("python", "python3") and i + 2 < len(tokens) and tokens[i + 1] == "-m":
            if tokens[i + 2] == "pytest":
                return i + 2
        return None
    return None


def _executes(tokens: list[str], relpath: str) -> bool:
    """Whether this command runs pytest against `relpath` (a repo-relative test path).

    Three shapes count: the exact path, the bare filename (`cd tests && pytest foo.py`),
    and a **directory that contains it** — `pytest tests/` collects and runs every test
    under `tests/`, so it executes the guard too. The directory form is the one that
    matters here: `provider-routing.yml` runs the whole suite, not a file list.
    """
    idx = _pytest_command_index(tokens)
    if idx is None:
        return False
    name = Path(relpath).name
    for arg in tokens[idx + 1 :]:
        if arg.startswith("-"):
            continue
        arg = arg.split("::", 1)[0].rstrip("/")
        if not arg:
            continue
        if arg in (relpath, name):
            return True
        if relpath.startswith(arg + "/"):
            return True
    return False


def _tokenize(line: str) -> list[str]:
    """Shell-tokenise one `run:` line, dropping comments. Never raises."""
    try:
        return shlex.split(line.strip(), comments=True)
    except ValueError:
        return []


def _workflow_executes(workflow: dict, relpath: str) -> bool:
    for script in _run_scripts(workflow):
        for line in script.splitlines():
            if _executes(_tokenize(line), relpath):
                return True
    return False


def _pinned_revisions() -> dict[str, str]:
    """`{symbol name: revision}` for every revision pinned in the tree.

    Read from the pin itself, not from a list here: `scripts/agents_md_encoding_audit.py`
    is the single source of the oracle revisions, and a test that imports the symbol
    depends on whatever that module pins.
    """
    revisions: dict[str, str] = {}
    for module in sorted(TESTS.glob("*.py")) + sorted((ROOT / "scripts").glob("*.py")):
        for name, rev in _PIN.findall(module.read_text(encoding="utf-8")):
            revisions[name] = rev
    return revisions


def _readable(rev: str) -> bool:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "cat-file", "-t", f"{rev}^{{commit}}"],
        capture_output=True,
    )
    return proc.returncode == 0


def _history_dependent_guards() -> dict[str, str]:
    """`{repo-relative test path: the pinned revision it resolves}`.

    Derived: the test must name a pinned symbol **and** resolve it through git, and the
    revision must be an object in this repository. A guard whose revision has been
    rewritten away is not history-dependent — it is broken, and reported by its own
    suite rather than by this boundary.

    The key is the repo-relative path, not the bare filename, so that a workflow running
    the containing directory (`pytest tests/`) is recognised as executing the guard.
    """
    guards: dict[str, str] = {}
    revisions = _pinned_revisions()
    for module in sorted(TESTS.glob("test_*.py")):
        if module.name == Path(__file__).name:
            continue
        text = module.read_text(encoding="utf-8")
        if not _GIT_READ.search(text):
            continue
        for name, rev in revisions.items():
            if re.search(rf"\b{re.escape(name)}\b", text) and _readable(rev):
                guards[module.relative_to(ROOT).as_posix()] = rev
                break
    return guards


def _history_dependent_workflows() -> list[str]:
    guards = _history_dependent_guards()
    return [
        p.name
        for p in sorted(WORKFLOWS.glob("*.yml"))
        if any(_workflow_executes(_load(p), name) for name in guards)
    ]


def _exempt_steps(workflow: dict) -> set[int]:
    """`id()`s of steps whose failure cannot redden the job.

    A step is exempt when the step *or* its whole job carries
    `continue-on-error: true` or `if: false`. A `continue-on-error` surface is a
    legitimate non-judging report — `sg-02-fe-2-v.yml` runs the whole suite that way —
    so the boundary must distinguish *executing* the guard from *judging* on it.
    """
    exempt: set[int] = set()
    for job in (workflow.get("jobs") or {}).values():
        job_exempt = job.get("continue-on-error") is True or job.get("if") is False
        for step in job.get("steps") or []:
            if job_exempt or step.get("continue-on-error") is True or step.get("if") is False:
                exempt.add(id(step))
    return exempt


def _judging_run_scripts(workflow: dict) -> list[str]:
    """`run:` bodies whose failure *can* redden the job they belong to."""
    exempt = _exempt_steps(workflow)
    scripts: list[str] = []
    for job in (workflow.get("jobs") or {}).values():
        for step in job.get("steps") or []:
            run = step.get("run")
            if isinstance(run, str) and id(step) not in exempt:
                scripts.append(run)
    return scripts


def _judging_workflows() -> list[str]:
    """Workflows that execute a history-dependent guard and can fail on it."""
    guards = _history_dependent_guards()
    judging: list[str] = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        for script in _judging_run_scripts(_load(path)):
            if any(_executes(_tokenize(line), g) for line in script.splitlines() for g in guards):
                judging.append(path.name)
                break
    return judging


# ---------------------------------------------------------------------------
# Detector negative controls
# ---------------------------------------------------------------------------


def _minimal_workflow(run: str, fetch_depth: int | None = None) -> dict:
    checkout: dict = {"uses": "actions/checkout@v4"}
    if fetch_depth is not None:
        checkout["with"] = {"fetch-depth": fetch_depth}
    return {
        "on": {"pull_request": {"paths": ["tests/**"]}},
        "jobs": {"g": {"runs-on": "ubuntu-latest", "steps": [checkout, {"run": run}]}},
    }


def test_detector_accepts_the_forms_this_repository_uses():
    """The spellings of a whole-suite or file-targeted invocation must all resolve."""
    guard = "tests/test_agents_md_encoding_adjudication.py"
    assert _workflow_executes(_minimal_workflow("python -m pytest tests/ -q"), guard)
    assert _workflow_executes(_minimal_workflow(f"pytest {guard} -q"), guard)
    assert _workflow_executes(
        _minimal_workflow("PYTHONPATH=. python -m pytest tests/ -q"), guard
    )


@pytest.mark.parametrize(
    "run",
    [
        "echo pytest tests/",
        "printf %s pytest tests/",
        "echo 'python -m pytest tests/ -q'",
        "# python -m pytest tests/ -q",
    ],
)
def test_negative_control_a_mention_is_not_an_execution(run: str):
    """A path named but not executed must not count as a workflow that runs the guard."""
    guard = "tests/test_agents_md_encoding_adjudication.py"
    assert not _workflow_executes(_minimal_workflow(run), guard)


def test_negative_control_a_shallow_checkout_is_not_full_history():
    """`fetch-depth: 1` and an absent `with:` block are both shallow."""
    run = "python -m pytest tests/ -q"
    assert not _full_history(_minimal_workflow(run))
    assert not _full_history(_minimal_workflow(run, fetch_depth=1))
    assert _full_history(_minimal_workflow(run, fetch_depth=0))


def test_negative_control_an_unrelated_workflow_is_not_in_the_domain():
    """A workflow that runs no history-dependent guard must not be flagged."""
    workflow = _minimal_workflow("python -m pytest tests/test_key_pool.py -q")
    guards = _history_dependent_guards()
    assert guards, "the domain is empty — the detector would be vacuously true"
    assert not any(_workflow_executes(workflow, name) for name in guards), (
        "a key-pool-only workflow must not be treated as history-dependent"
    )


def test_positive_control_the_shallow_form_is_flagged():
    """The defect shape: a history-dependent guard on a default shallow checkout.

    The detector must both *place* the workflow in the domain and report it as
    shallow; either half alone would let the boundary assertion pass vacuously.
    """
    workflow = _minimal_workflow("python -m pytest tests/ -q")
    guards = _history_dependent_guards()
    assert any(_workflow_executes(workflow, name) for name in guards), (
        "a whole-suite step must place the workflow in the history-dependent domain"
    )
    assert not _full_history(workflow), "the default checkout is shallow and must be flagged"


# ---------------------------------------------------------------------------
# The boundary
# ---------------------------------------------------------------------------


def test_the_domain_is_not_empty():
    """A guard over an empty domain asserts nothing."""
    assert _history_dependent_guards(), (
        "no history-dependent guard was found: either the pinned revisions are "
        "unreachable in this clone or the detector stopped resolving them"
    )
    assert _history_dependent_workflows(), (
        "no workflow executes a history-dependent guard; the detector is not resolving "
        "whole-suite invocations"
    )


@pytest.mark.parametrize("name", _history_dependent_workflows())
def test_a_workflow_running_a_history_dependent_guard_fetches_full_history(name: str):
    """The guard's verdict must be a function of the tree, not of the clone depth.

    Parametrized over the *executing* domain, not the judging one: a reporting surface
    that misreports because its clone was truncated is the same defect family as a gate
    that judges wrongly. `sg-02-fe-2-v.yml` runs the whole suite under
    `continue-on-error`, so it cannot redden a job — but it must still report on a tree
    it actually checked out.
    """
    workflow = _load(WORKFLOWS / name)
    guards = [g for g in _history_dependent_guards() if _workflow_executes(workflow, g)]
    assert guards, f"{name} is in the domain but executes no history-dependent guard"
    assert _full_history(workflow), (
        f"{name} executes {', '.join(sorted(guards))} on a shallow checkout. Those "
        f"guards resolve pinned revisions out of git history, so a shallow clone "
        f"changes their verdict — measured at main 6109c72a, four "
        f"test_agents_md_encoding_adjudication.py nodes fail on a --depth 1 clone and "
        f"pass with full history. Declare `fetch-depth: 0` on every checkout."
    )


@pytest.mark.parametrize("name", _judging_workflows())
def test_a_workflow_selects_itself_and_the_guard(name: str):
    """A boundary a pull request cannot trigger is judged by no gate."""
    workflow = _load(WORKFLOWS / name)
    events = workflow.get("on") or workflow.get(True) or {}
    pull_request = events.get("pull_request") if isinstance(events, dict) else None
    assert isinstance(pull_request, dict) and pull_request.get("paths"), (
        f"{name} executes a history-dependent guard but declares no pull_request paths "
        f"filter, so it cannot be triggered by the change it judges"
    )
    paths = set(pull_request["paths"])
    for surface in (f".github/workflows/{name}", _GUARD_FILE):
        assert _selects_path(paths, surface), (
            f"{name} does not select {surface} in its pull_request paths filter. A "
            f"workflow that judges the boundary must be selected by a change to that "
            f"boundary, or the gate is decoration."
        )


def test_negative_control_a_non_judging_surface_is_not_in_the_judging_domain():
    """`sg-02-fe-2-v.yml` reports the suite with `continue-on-error`, so it does not judge.

    Executing a guard and *judging* on it are different properties. A non-judging
    whole-suite step cannot redden a job, so it is out of the judging domain — but it
    must still be in the *executing* domain, or the exemption would hide it entirely.
    """
    run = "python -m pytest tests/ -q"
    lenient = _minimal_workflow(run)
    lenient["jobs"]["g"]["steps"][1]["continue-on-error"] = True
    guards = _history_dependent_guards()
    assert _workflow_executes(lenient, next(iter(guards)))
    assert _exempt_steps(lenient), "continue-on-error must exempt the step"
    strict = _minimal_workflow(run)
    assert not _exempt_steps(strict), "a plain step must not be exempt"


def test_negative_control_a_guard_mention_is_not_a_guard_execution():
    """A workflow that only names the guard in prose must not enter the domain."""
    workflow = _minimal_workflow(f"echo 'see {_GUARD_FILE} for the rationale'")
    assert not _workflow_executes(workflow, _GUARD_FILE)


def test_positive_control_a_reporting_surface_is_executing_but_not_judging():
    """The executing and judging domains are different properties, and both must be real.

    `sg-02-fe-2-v.yml` is the live instance: it runs the whole suite (so it executes the
    history-dependent guard) under `continue-on-error` (so it cannot redden a job). If the
    two domains ever collapse into one, the exemption detector stopped working and the
    fetch-depth invariant silently narrowed to the judging surface.
    """
    executing = set(_history_dependent_workflows())
    judging = set(_judging_workflows())
    assert judging <= executing, "a judging surface must also be an executing one"
    reporting_only = executing - judging
    assert reporting_only, (
        "no reporting-only surface is in the executing domain; either the exemption "
        "detector stopped recognising `continue-on-error`, or the whole-suite reporting "
        "surface no longer runs a history-dependent guard"
    )
