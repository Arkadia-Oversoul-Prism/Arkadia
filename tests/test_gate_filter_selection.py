"""Boundary guard: a workflow that *executes* a test file must *select* it.

`tests/test_ci_gate_trigger_coverage.py` states two narrower invariants — a pytest
workflow must trigger on its own file, and its ``push``/``pull_request`` filters must
be identical. Neither covers the case measured on `main` @ `850216fc`: a workflow whose
filter is **already asymmetric**, or whose filters agree, while a file the step
*explicitly names* is selected by neither.

The instance: `sg-02-fe-2-v.yml` step ``SolSpire isolated runtime and integration
contract tests`` runs nine named guards in a blocking step (no ``continue-on-error``),
and its ``pull_request``/``push`` filters omit all nine. A change to one of those guards
is therefore never judged by the gate that runs it — the exact "a guard no gate executes
is decoration" class, in its filter-selection form.

Two facts make this measurable rather than inferred, and both were checked before the
filter was widened:

1. The narrowest PR touching *only* an omitted guard fires **no** gate at all — not
   `sg-02-fe-2-v.yml`, not the full-suite `provider-routing.yml` (path-filtered to
   ``weaver/**``/``providers/**`` and a handful of named files).
2. The 14 omitted guards named by the repaired filters all **pass** on `main`
   (86 passed, 1 skipped), so widening the filters cannot redden an unrelated PR.

The invariant is stated generically over the live corpus:

    for every workflow W, every event E with a ``paths`` filter, and every tracked
    test file T that a step of W names as a pytest argument:
        E's filter must select T.

Directory arguments (``pytest tests/`` or ``pytest tests/architecture``) are a *site*
the detector must see, not a case it may ignore: a file reached only through one of them
has no named selector, so the invariant above says nothing about it. Two rules cover
them, and a third is deliberately **not** asserted.

1. A directory argument is detected as an execution site
   (``test_detector_detects_directory_execution_sites``).
2. A **judging** directory site — one that can fail the job, i.e. neither the step nor
   its job sets ``continue-on-error`` — must select at least one member of the directory
   it runs (``test_a_judging_directory_site_selects_a_member``). A judging step that runs
   a directory its filter selects nothing from is the "gate that cannot be reached"
   shape: the step can fail, and no change to the tree it runs would ever trigger it.

The stronger reading — *every* member of a directory a judging step runs must be
selected — is **not** asserted, and the reason is measured rather than stylistic. On
`main` @ `36f53be2` it breaches 3 times (``provider-routing.yml`` omits 294 of 299
members; ``sg-02-fe-2-v.yml`` omits 279 on each of ``pull_request`` and ``push``), and
satisfying it would mean adding ``tests/**`` to the whole-suite gate's filter — every
test edit triggering a full-suite run — and editing a workflow outside this change.
"Enumerate the directory's membership" restates the corpus, which is the drift this file
exists to avoid.

The measured size of the unasserted gap is **207 of 299** tracked ``test_*.py`` files
that are executed only through a directory argument by a workflow whose filter selects no
file under it. That is recorded debt, not a property this change can make true; it needs
roughly 200 filter edits and is out of scope here.

The defect this change repairs is narrower and is pinned directly: an ``api/main.py``
edit fired six workflows and **none of them ran ``pytest tests/``**, so neither the
approval-perimeter guard nor the ``api/main.py`` line-count budget test had a selected
execution site. ``test_the_whole_suite_gate_selects_the_surfaces_it_judges`` states that
contract over the surfaces this change wires.

Controls
--------
``test_detector_flags_the_omitted_named_guard`` and
``test_detector_ignores_directory_reached_guards`` prove the detector reads the real
workflow file and is not trivially true or trivially false. Each new rule carries a
negative control that fails when the rule is removed, so the assertions cannot be
disarmed by editing the workflow without reddening this file.
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

_TRIGGER_EVENTS = ("pull_request", "push")
_COMMENT = re.compile(r"(?:^|\s)#.*$", re.MULTILINE)


def _tracked_test_paths() -> set[str]:
    """Every tracked file under ``tests/``, repo-relative — the guard's domain."""
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", "tests/"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {p for p in result.stdout.split("\0") if p}


def _workflow_paths() -> list[Path]:
    return sorted(WORKFLOWS.glob("*.yml"))


def _load(path: Path | str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


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

    ``**/`` matches zero or more leading path segments (so ``**/*.py`` selects
    ``weaver.py`` as well as ``api/main.py``), a remaining ``**`` matches anything
    including ``/``, and ``*``/``?`` match within a single path segment. Every other
    character is literal. Placeholders keep the single-``*`` rewrite from clobbering
    the ``**`` expansion.
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


def _command_words(run: str) -> list[list[str]]:
    """Tokenise each command in a ``run:`` block, dropping comments and continuations.

    A detector that accepts the word ``pytest`` *anywhere* is disarmed by
    ``echo pytest tests/x.py``; requiring ``pytest`` to be the invoked command word
    (directly, or after ``python -m``) is what makes the reading a statement about
    execution rather than about mention.
    """
    commands: list[list[str]] = []
    for line in _COMMENT.sub("", run).replace("\\\n", " ").splitlines():
        line = line.strip()
        if not line:
            continue
        for part in re.split(r"&&|\|\||;|\|", line):
            part = part.strip()
            if not part:
                continue
            try:
                words = shlex.split(part)
            except ValueError:
                words = part.split()
            if words:
                commands.append(words)
    return commands


def _named_test_arguments(run: str, tracked: set[str]) -> set[str]:
    """Tracked test files a ``run:`` block passes as arguments to a real pytest call."""
    found: set[str] = set()
    for words in _command_words(run):
        for index, word in enumerate(words):
            if word == "pytest" and (index == 0 or words[index - 1] == "-m"):
                invokes_pytest = True
            elif word == "pytest" and index > 0 and words[index - 1] != "-m":
                invokes_pytest = False
            else:
                continue
            if not invokes_pytest:
                continue
            for argument in words[index + 1 :]:
                if argument.startswith("-"):
                    continue
                candidate = argument.split("::")[0].rstrip("/")
                if candidate in tracked:
                    found.add(candidate)
    return found


def _executed_named_tests(workflow: dict, tracked: set[str]) -> set[str]:
    """Every tracked test file named as a pytest argument by any step of the workflow."""
    executed: set[str] = set()
    for job in (workflow.get("jobs") or {}).values():
        for step in job.get("steps") or []:
            run = step.get("run")
            if isinstance(run, str):
                executed |= _named_test_arguments(run, tracked)
    return executed


def _directory_arguments(run: str, tracked: set[str]) -> set[str]:
    """Tracked directories passed as arguments to a real pytest invocation.

    A directory argument is an execution *site*: it runs every test file beneath it.
    It is deliberately not resolved to its members here — that membership is the corpus,
    and enumerating it is what the class-level docstring explains must not happen.
    """
    found: set[str] = set()
    for words in _command_words(run):
        for index, word in enumerate(words):
            if word != "pytest" or not (index == 0 or words[index - 1] == "-m"):
                continue
            for argument in words[index + 1 :]:
                if argument.startswith("-"):
                    continue
                candidate = argument.split("::")[0].rstrip("/")
                if candidate in tracked:
                    continue
                if any(path.startswith(candidate + "/") for path in tracked):
                    found.add(candidate)
            break
    return found


def _judging_directory_sites() -> list[tuple[str, str, str]]:
    """``(workflow, event, directory)`` for every directory site that can fail the job.

    A step that carries ``continue-on-error`` — or whose job does — reports without
    judging, so it cannot be the execution site of an enforcement boundary. Reading the
    step *and* the job is the whole exemption path; reading the step alone would let a
    job-level ``continue-on-error: true`` hide an always-passing gate.
    """
    tracked = _tracked_test_paths()
    sites: list[tuple[str, str, str]] = []
    for path in _workflow_paths():
        workflow = _load(path)
        trigger = _trigger_block(workflow)
        for job in (workflow.get("jobs") or {}).values():
            if job.get("continue-on-error"):
                continue
            for step in job.get("steps") or []:
                run = step.get("run")
                if not isinstance(run, str) or step.get("continue-on-error"):
                    continue
                for directory in sorted(_directory_arguments(run, tracked)):
                    for event in _TRIGGER_EVENTS:
                        if _path_filter(trigger, event) is None:
                            continue
                        sites.append((path.name, event, directory))
    return sites


# Surfaces this change wires into the whole-suite gate. Each is a file whose change must
# select a workflow that runs the full suite, because the guard or budget it is judged by
# has no other execution site.
WHOLE_SUITE_JUDGED_SURFACES = (
    "api/main.py",
    "api/approval_routes.py",
    "api/ceo_chat_routes.py",
    "tests/test_tool_execution_perimeter.py",
)

# Paths that must NOT be dragged into the whole-suite gate by that wiring: widening a
# filter until it selects everything is not a repair, it is a different defect.
UNRELATED_CONTROL_PATHS = (
    "web/arkadia_console/src/App.tsx",
    "docs/control-plane/overnight/PRISM-UI-RECONCILIATION.md",
    "android/sonata-android/app/build.gradle.kts",
)


def _whole_suite_judging_workflows() -> list[tuple[str, dict]]:
    """Workflows with a directory site running the whole suite in a judging step."""
    tracked = _tracked_test_paths()
    found: list[tuple[str, dict]] = []
    for path in _workflow_paths():
        workflow = _load(path)
        for job in (workflow.get("jobs") or {}).values():
            if job.get("continue-on-error"):
                continue
            for step in job.get("steps") or []:
                run = step.get("run")
                if not isinstance(run, str) or step.get("continue-on-error"):
                    continue
                if "tests" in _directory_arguments(run, tracked):
                    found.append((path.name, workflow))
                    break
    return found


def _selects_any_member(path_filter: set[str], directory: str, tracked: set[str]) -> bool:
    """Whether a filter selects at least one tracked file beneath ``directory``."""
    return any(
        path.startswith(directory + "/") and _selects_path(path_filter, path)
        for path in tracked
    )


def _omissions() -> list[tuple[str, str, str]]:
    """``(workflow, event, test_file)`` triples that breach the invariant."""
    tracked = _tracked_test_paths()
    breaches: list[tuple[str, str, str]] = []
    for path in _workflow_paths():
        workflow = _load(path)
        executed = _executed_named_tests(workflow, tracked)
        if not executed:
            continue
        for event in _TRIGGER_EVENTS:
            paths = _path_filter(_trigger_block(workflow), event)
            if paths is None:
                continue
            for guard in sorted(executed):
                if not _selects_path(paths, guard):
                    breaches.append((path.name, event, guard))
    return breaches


# ---------------------------------------------------------------- detector controls


def test_detector_flags_the_omitted_named_guard():
    """Negative control: the real pre-repair filter must be reported.

    Feeds the detector the shape measured on `main` — a named, blocking guard that
    the ``pull_request`` filter does not select — so the repair cannot be undone
    without reddening this file.
    """
    tracked = _tracked_test_paths()
    workflow = _load(WORKFLOWS / "sg-02-fe-2-v.yml")
    executed = _executed_named_tests(workflow, tracked)
    assert "tests/test_solspire_project_execution_service.py" in executed, (
        "sg-02-fe-2-v.yml no longer names the SolSpire runtime contract tests; the "
        "negative control below would be vacuous"
    )
    assert _selects_path(
        {".github/workflows/sg-02-fe-2-v.yml"}, "tests/test_solspire_project_execution_service.py"
    ) is False
    assert not [
        guard
        for name, event, guard in _omissions()
        if name == "sg-02-fe-2-v.yml" and event == "pull_request"
    ], "sg-02-fe-2-v.yml still omits a guard it executes"


def test_detector_ignores_directory_reached_guards():
    """Positive control: a directory argument is not a named selector.

    ``pytest tests/`` and ``pytest tests/architecture`` execute every file beneath
    them; requiring the filter to enumerate that membership would restate the corpus.
    """
    tracked = _tracked_test_paths()
    assert _named_test_arguments("python -m pytest tests/ -q", tracked) == set()
    assert _named_test_arguments("python -m pytest tests/architecture -q", tracked) == set()
    assert _named_test_arguments(
        "python -m pytest tests/test_key_pool.py -q", tracked
    ) == {"tests/test_key_pool.py"}


def test_detector_requires_an_invoked_pytest_word():
    """A mention of ``pytest`` is not an execution of it."""
    tracked = _tracked_test_paths()
    assert _named_test_arguments("echo pytest tests/test_key_pool.py", tracked) == set()
    assert _named_test_arguments("# pytest tests/test_key_pool.py", tracked) == set()
    assert _named_test_arguments(
        "python -m pytest tests/test_key_pool.py::test_x -q", tracked
    ) == {"tests/test_key_pool.py"}


def test_selector_accepts_the_forms_github_uses():
    assert _selects_path({"tests/**"}, "tests/test_key_pool.py")
    assert _selects_path({"tests/test_key_pool.py"}, "tests/test_key_pool.py")
    assert _selects_path({"**"}, "tests/anything.py")


def test_selector_rejects_unrelated_paths():
    assert not _selects_path({"weaver/**", "providers/**"}, "tests/test_key_pool.py")
    assert not _selects_path({"tests/*.py"}, "tests/architecture/test_layers.py")


# ------------------------------------------------- directory sites: detection and judging


def test_detector_detects_directory_execution_sites():
    """A directory argument is a site, and it is read from a real pytest invocation."""
    tracked = _tracked_test_paths()
    assert _directory_arguments(
        "python -m pytest tests/ -q -rEf --continue-on-collection-errors", tracked
    ) == {"tests"}
    assert _directory_arguments("python -m pytest tests/architecture -q", tracked) == {
        "tests/architecture"
    }
    assert _directory_arguments("python -m pytest tests/architecture/ -q", tracked) == {
        "tests/architecture"
    }
    # A mention is still not an execution, and a named file is not a directory.
    assert _directory_arguments("echo pytest tests/", tracked) == set()
    assert _directory_arguments("python -m pytest tests/test_key_pool.py -q", tracked) == set()


def test_detector_ignores_directory_reached_guards():
    """Positive control: a directory argument is not a *named* selector.

    ``pytest tests/`` and ``pytest tests/architecture`` execute every file beneath
    them; requiring the named-selector rule to enumerate that membership would restate
    the corpus. The directory rules are separate and stated below.
    """
    tracked = _tracked_test_paths()
    assert _named_test_arguments("python -m pytest tests/ -q", tracked) == set()
    assert _named_test_arguments("python -m pytest tests/architecture -q", tracked) == set()
    assert _named_test_arguments(
        "python -m pytest tests/test_key_pool.py -q", tracked
    ) == {"tests/test_key_pool.py"}


def test_a_judging_directory_site_selects_a_member():
    """A judging directory site must be reachable: its filter selects some member.

    A step that can fail the job while running a directory its filter selects nothing
    from is a gate no change to that tree can trigger — the defect measured on `main`
    @ `36f53be2`, where an ``api/main.py`` edit fired six workflows and none of them ran
    the full suite.
    """
    tracked = _tracked_test_paths()
    breaches: list[str] = []
    for name, event, directory in _judging_directory_sites():
        path_filter = _path_filter(_trigger_block(_load(WORKFLOWS / name)), event)
        if path_filter is None:
            continue
        if not _selects_any_member(path_filter, directory, tracked):
            breaches.append(f"{name} [{event}] runs `pytest {directory}/` but selects no member")
    assert not breaches, (
        "a judging step runs a test directory its paths filter cannot reach, so the "
        "gate can fail but no change to the tree it runs will ever trigger it:\n  "
        + "\n  ".join(breaches)
    )


def test_judging_directory_sites_are_non_empty():
    """The rule above must have a domain, or it is vacuously true."""
    sites = _judging_directory_sites()
    assert sites, (
        "no judging directory site was found; the invariant above would be vacuous. "
        "Either the detector stopped reading directory arguments or every whole-suite "
        "step became `continue-on-error`."
    )
    assert any(name == "provider-routing.yml" for name, _, _ in sites), (
        "provider-routing.yml no longer registers a judging directory site; the "
        "whole-suite gate has been demoted to a reporting surface"
    )


def test_negative_control_a_judging_site_without_a_reachable_member_is_reported():
    """The rule bites: strip every member-selecting entry and it must report.

    Mutates the real workflow's filter in memory — the file on disk is untouched — so a
    reader cannot disarm the rule by editing the workflow without reddening this file.
    """
    tracked = _tracked_test_paths()
    name, event, directory = next(
        (n, e, d)
        for n, e, d in _judging_directory_sites()
        if n == "provider-routing.yml" and d == "tests"
    )
    workflow = _load(WORKFLOWS / name)
    path_filter = _path_filter(_trigger_block(workflow), event)
    assert path_filter is not None
    assert _selects_any_member(path_filter, directory, tracked), (
        "precondition failed: provider-routing.yml must currently reach its directory"
    )
    stripped = {
        pattern
        for pattern in path_filter
        if not any(
            _glob_to_regex(pattern).match(path)
            for path in tracked
            if path.startswith(directory + "/")
        )
    }
    assert stripped != path_filter, "mutation applied nothing; the control would be vacuous"
    assert not _selects_any_member(stripped, directory, tracked), (
        "removing every member-selecting entry still reports a reachable member, so the "
        "detector is not reading the filter"
    )


# --------------------------------------------- the surfaces this change wires in


@pytest.mark.parametrize("surface", WHOLE_SUITE_JUDGED_SURFACES)
def test_the_whole_suite_gate_selects_the_surfaces_it_judges(surface: str):
    """A change to ``surface`` must select a workflow that runs the whole suite.

    This is the contract the wiring repair establishes, and the reason it is stated over
    a named surface list rather than inferred: ``tests/test_tool_execution_perimeter.py``
    and ``tests/architecture/test_layer_boundaries.py`` (the ``api/main.py`` line-count
    budget) are executed only through the whole-suite step, so a filter that omits these
    files leaves both guards with no execution site at all.
    """
    gates = _whole_suite_judging_workflows()
    assert gates, "no workflow runs the whole suite in a judging step"
    selected = [
        name
        for name, workflow in gates
        if any(
            (path_filter := _path_filter(_trigger_block(workflow), event)) is not None
            and _selects_path(path_filter, surface)
            for event in _TRIGGER_EVENTS
        )
    ]
    assert selected, (
        f"no whole-suite judging workflow selects {surface}; a change to it is judged by "
        f"no gate that runs the suite. Candidate gates: {sorted(n for n, _ in gates)}"
    )


def test_the_wiring_does_not_drag_unrelated_paths_into_the_gate():
    """The converse control: the widened filter must not select everything.

    A filter widened until it matches unrelated surfaces is not a repair — it makes the
    whole suite run on every change. These paths are unrelated to the approval perimeter
    and must stay out.
    """
    gates = dict(_whole_suite_judging_workflows())
    assert "provider-routing.yml" in gates, "the whole-suite gate is missing"
    trigger = _trigger_block(gates["provider-routing.yml"])
    for surface in UNRELATED_CONTROL_PATHS:
        selected = any(
            (path_filter := _path_filter(trigger, event)) is not None
            and _selects_path(path_filter, surface)
            for event in _TRIGGER_EVENTS
        )
        assert not selected, (
            f"provider-routing.yml now selects {surface}, an unrelated path; the filter "
            f"has been broadened past the surfaces it judges"
        )


def test_negative_control_a_removed_surface_is_reported():
    """Removing one wired surface from the filter must breach the contract."""
    workflow = _load(WORKFLOWS / "provider-routing.yml")
    trigger = _trigger_block(workflow)
    for event in _TRIGGER_EVENTS:
        block = trigger.get(event)
        if not isinstance(block, dict) or not isinstance(block.get("paths"), list):
            continue
        block["paths"] = [
            p
            for p in block["paths"]
            if not _glob_to_regex(p).match("tests/test_tool_execution_perimeter.py")
        ]
    selected = [
        event
        for event in _TRIGGER_EVENTS
        if (path_filter := _path_filter(trigger, event)) is not None
        and _selects_path(path_filter, "tests/test_tool_execution_perimeter.py")
    ]
    assert not selected, (
        "the mutated filter still selects the perimeter guard, so the mutation applied "
        "nothing and this control is vacuous"
    )


# ---------------------------------------------------------------- the invariant


def test_no_workflow_omits_a_test_file_it_executes():
    """The invariant over the live corpus: execution implies selection."""
    breaches = _omissions()
    by_workflow: dict[str, list[str]] = {}
    for name, event, guard in breaches:
        by_workflow.setdefault(f"{name} [{event}]", []).append(guard)
    detail = "\n".join(
        f"  {key}: {len(guards)} omitted\n" + "\n".join(f"      {g}" for g in guards)
        for key, guards in sorted(by_workflow.items())
    )
    assert not breaches, (
        "a workflow executes a test file that its paths filter does not select, so a "
        "change to that file is never judged by the gate that runs it:\n" + detail
    )


@pytest.mark.parametrize("name", [p.name for p in _workflow_paths()])
def test_executed_files_are_selected_or_the_workflow_is_unfiltered(name: str):
    """Per-workflow view, so a regression names the offending gate."""
    tracked = _tracked_test_paths()
    workflow = _load(WORKFLOWS / name)
    executed = _executed_named_tests(workflow, tracked)
    if not executed:
        return
    for event in _TRIGGER_EVENTS:
        paths = _path_filter(_trigger_block(workflow), event)
        if paths is None:
            continue
        omitted = sorted(g for g in executed if not _selects_path(paths, g))
        assert not omitted, (
            f"{name} runs {len(omitted)} test file(s) on {event} that its paths filter "
            f"does not select, e.g. {omitted[:5]}"
        )
