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

Files reached only through a directory argument (``pytest tests/`` or
``pytest tests/architecture``) are deliberately **excluded**: their domain is a
directory, and requiring the filter to enumerate its members would restate the corpus
and drift. Those are judged by ``test_ci_gate_trigger_coverage.py`` and by the
per-surface wiring guards, which derive their own domain at test time.

Controls
--------
``test_detector_flags_the_omitted_named_guard`` and
``test_detector_ignores_directory_reached_guards`` prove the detector reads the real
workflow file and is not trivially true or trivially false; the directory case is the
positive control that keeps the rule from over-reaching.
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
