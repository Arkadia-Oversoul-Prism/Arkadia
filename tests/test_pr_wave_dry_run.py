"""Composition dry-run: a shared file is not a conflict, a real merge decides.

Every test drives real git in a throwaway repository. Nothing here mocks the merge.
"""
from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import pr_wave_dry_run as wave  # noqa: E402

WORKFLOW = REPO_ROOT / ".github" / "workflows" / "pr-wave-dry-run.yml"
SCRIPT = REPO_ROOT / "scripts" / "pr_wave_dry_run.py"
THIS_TEST = Path(__file__).resolve()


def _git(repo: Path, *args: str) -> str:
    done = subprocess.run(("git", "-C", str(repo), *args), capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    return done.stdout


def _write(repo: Path, name: str, text: str) -> None:
    (repo / name).write_text(text, encoding="utf-8")


def _commit_all(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", message)
    return _git(repo, "rev-parse", "HEAD").strip()


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    path = tmp_path / "repo"
    path.mkdir()
    _git(path, "init", "-q", "-b", "main")
    _git(path, "config", "user.email", "test@example.com")
    _git(path, "config", "user.name", "test")
    _write(path, "shared.txt", "one\ntwo\nthree\nfour\nfive\n")
    _write(path, "other.txt", "base\n")
    _commit_all(path, "base")
    return path


def _branch(repo: Path, name: str, edits: dict[str, str]) -> str:
    _git(repo, "checkout", "-q", "-b", name, "main")
    for filename, text in edits.items():
        _write(repo, filename, text)
    sha = _commit_all(repo, name)
    _git(repo, "checkout", "-q", "main")
    return sha


def test_pull_requests_on_different_files_compose_cleanly(repo: Path) -> None:
    first = _branch(repo, "pr-10", {"other.txt": "base\nfirst\n"})
    second = _branch(repo, "pr-11", {"third.txt": "second\n"})
    packet = wave.dry_run(str(repo), "main", [
        {"number": 10, "head_sha": first},
        {"number": 11, "head_sha": second},
    ])
    assert packet["clean"] == [10, 11]
    assert packet["conflicts"] == []


def test_shared_file_is_not_a_conflict_when_the_regions_differ(repo: Path) -> None:
    """Negative control: a changed-path overlap map calls this a conflict; git does not.

    Both branches edit `shared.txt`, so milestone 1's overlap map clusters them. The
    edits are in different regions, so the composition is clean. A detector that
    reports this as a conflict is measuring the wrong thing.
    """
    first = _branch(repo, "pr-10", {"shared.txt": "ONE\ntwo\nthree\nfour\nfive\n"})
    second = _branch(repo, "pr-11", {"shared.txt": "one\ntwo\nthree\nfour\nFIVE\n"})
    assert set(wave.changed_paths(str(repo), "main", first)) == {"shared.txt"}
    assert set(wave.changed_paths(str(repo), "main", second)) == {"shared.txt"}
    packet = wave.dry_run(str(repo), "main", [
        {"number": 10, "head_sha": first},
        {"number": 11, "head_sha": second},
    ])
    assert packet["clean"] == [10, 11]
    assert packet["conflicts"] == []


def test_overlapping_regions_report_the_conflict_its_paths_and_its_edge(repo: Path) -> None:
    first = _branch(repo, "pr-10", {"shared.txt": "one\nTEN\nthree\nfour\nfive\n"})
    second = _branch(repo, "pr-11", {"shared.txt": "one\nELEVEN\nthree\nfour\nfive\n"})
    packet = wave.dry_run(str(repo), "main", [
        {"number": 10, "head_sha": first},
        {"number": 11, "head_sha": second},
    ])
    assert packet["clean"] == [10]
    assert [row["number"] for row in packet["conflicts"]] == [11]
    conflict = packet["conflicts"][0]
    assert conflict["conflicted_paths"] == ["shared.txt"]
    assert conflict["edges"] == [10]


def test_a_head_already_in_the_base_is_not_reported_as_clean(repo: Path) -> None:
    contained = _branch(repo, "pr-10", {"other.txt": "base\ncontained\n"})
    _git(repo, "merge", "-q", "--no-ff", "--no-edit", "pr-10")
    packet = wave.dry_run(str(repo), "main", [{"number": 10, "head_sha": contained}])
    assert packet["already_contained"] == [10]
    assert packet["clean"] == []
    assert packet["conflicts"] == []


def test_an_unresolvable_base_fails_closed_instead_of_reporting_a_clean_wave(repo: Path) -> None:
    with pytest.raises(wave.DryRunError):
        wave.dry_run(str(repo), "refs/heads/does-not-exist", [])


def test_a_missing_head_sha_fails_closed(repo: Path) -> None:
    with pytest.raises(wave.DryRunError):
        wave.dry_run(str(repo), "main", [{"number": 10, "head_sha": ""}])


def test_a_head_that_conflicts_with_the_base_is_not_reported_as_a_wave_conflict(repo: Path) -> None:
    """The base conflict and the wave conflict need opposite responses.

    `stale` is cut from the base, then the base rewrites the same line, so `stale`
    conflicts with the base and with nothing in the wave -- its edge list is empty,
    exactly as a wave conflict's would be. `first`/`second` compose with the base and
    conflict with each other. A packet that reports both as CONFLICT tells the reader
    to adjudicate a rebase and to rebase an adjudication.
    """
    stale = _branch(repo, "pr-9", {"shared.txt": "one\nNINE\nthree\nfour\nfive\n"})
    _write(repo, "shared.txt", "one\nBASE MOVED\nthree\nfour\nfive\n")
    _commit_all(repo, "the base moves on the same line")
    first = _branch(repo, "pr-10", {"other.txt": "base\nfirst\n"})
    second = _branch(repo, "pr-11", {"other.txt": "base\nsecond\n"})
    packet = wave.dry_run(str(repo), "main", [
        {"number": 9, "head_sha": stale},
        {"number": 10, "head_sha": first},
        {"number": 11, "head_sha": second},
    ])
    assert [row["number"] for row in packet["base_conflicts"]] == [9]
    base_conflict = packet["base_conflicts"][0]
    assert base_conflict["conflicted_paths"] == ["shared.txt"]
    assert base_conflict["conflicted_paths_at_base"] == ["shared.txt"]
    assert base_conflict["edges"] == []
    assert [row["number"] for row in packet["conflicts"]] == [11]
    assert packet["conflicts"][0]["edges"] == [10]
    assert packet["state_counts"] == {"CLEAN": 1, "CONFLICT": 1, "CONFLICT_BASE": 1}


def test_the_base_probe_names_only_the_head_that_fails_against_the_base(repo: Path) -> None:
    """Negative control: a probe that named every head, or none, would prove nothing."""
    stale = _branch(repo, "pr-9", {"shared.txt": "one\nNINE\nthree\nfour\nfive\n"})
    _write(repo, "shared.txt", "one\nBASE MOVED\nthree\nfour\nfive\n")
    _commit_all(repo, "the base moves on the same line")
    composes = _branch(repo, "pr-11", {"other.txt": "base\nsecond\n"})
    at_base = wave.conflicts_at_base(
        str(repo), _git(repo, "rev-parse", "main").strip(), [(9, stale), (11, composes)])
    assert sorted(at_base) == [9]
    assert at_base[9] == ["shared.txt"]


def test_an_unmeasurable_conflict_edge_fails_closed(repo: Path) -> None:
    """No merge base means the edge set cannot be measured, not that it is empty."""
    _git(repo, "checkout", "-q", "--orphan", "orphan")
    _write(repo, "orphan.txt", "unrelated\n")
    orphan = _commit_all(repo, "orphan")
    _git(repo, "checkout", "-q", "main")
    with pytest.raises(wave.DryRunError):
        wave.changed_paths(str(repo), _git(repo, "rev-parse", "main").strip(), orphan)


def test_every_pull_request_is_accounted_for_exactly_once(repo: Path) -> None:
    first = _branch(repo, "pr-10", {"shared.txt": "one\nTEN\nthree\nfour\nfive\n"})
    second = _branch(repo, "pr-11", {"shared.txt": "one\nELEVEN\nthree\nfour\nfive\n"})
    third = _branch(repo, "pr-12", {"other.txt": "base\nthird\n"})
    packet = wave.dry_run(str(repo), "main", [
        {"number": 10, "head_sha": first},
        {"number": 11, "head_sha": second},
        {"number": 12, "head_sha": third},
    ])
    reported = packet["clean"] + packet["already_contained"] + [
        row["number"] for row in packet["conflicts"]] + [
        row["number"] for row in packet["base_conflicts"]]
    assert sorted(reported) == [10, 11, 12]
    assert packet["accounted"] == 3
    assert sum(packet["state_counts"].values()) == 3


def test_the_scratch_worktree_is_removed_and_the_callers_tree_is_untouched(repo: Path) -> None:
    head_before = _git(repo, "rev-parse", "HEAD").strip()
    status_before = _git(repo, "status", "--porcelain")
    branch = _branch(repo, "pr-10", {"other.txt": "base\nfirst\n"})
    wave.dry_run(str(repo), "main", [{"number": 10, "head_sha": branch}])
    assert _git(repo, "rev-parse", "HEAD").strip() == head_before
    assert _git(repo, "status", "--porcelain") == status_before
    assert len([line for line in _git(repo, "worktree", "list").splitlines() if line]) == 1


def test_the_packet_claims_no_merge_authority() -> None:
    packet = wave.dry_run(str(REPO_ROOT), "HEAD", [])
    authority = packet["authority"]
    assert authority["read_only"] is True
    assert authority["pull_request_mutated"] is False
    assert authority["merge_or_push_performed"] is False
    assert authority["ready_for_merge_authorized"] is False


FORBIDDEN = ('"push"', "'push'", "/merge", "auto_merge", "merge-async")


def _breaches(source: str) -> list[str]:
    return [marker for marker in FORBIDDEN if marker in source]


def test_the_tool_cannot_mutate_github_state() -> None:
    assert _breaches(SCRIPT.read_text(encoding="utf-8")) == []


def test_the_mutation_detector_flags_the_forms_it_exists_to_catch() -> None:
    """Negative control: the detector must bite on a remote push or a merge call."""
    assert _breaches('subprocess.run(("git", "push", "origin", "main"))') == ['"push"']
    assert _breaches('POST /repos/x/y/pulls/1/merge') == ["/merge"]
    assert _breaches('{"auto_merge": True}') == ["auto_merge"]


def _invoked_pytest_arguments(run_text: str) -> list[list[str]]:
    """Arguments of every *executed* pytest call; a mention is not an execution.

    `echo pytest tests/x.py` tokenises to ["echo", "pytest", ...] and is not a call.
    """
    calls: list[list[str]] = []
    for raw in run_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            tokens = shlex.split(line)
        except ValueError:
            continue
        for index, token in enumerate(tokens):
            if token != "pytest":
                continue
            invoked = index == 0 or (
                index >= 2 and tokens[index - 1] == "-m" and tokens[index - 2].endswith("python"))
            if invoked:
                calls.append(tokens[index + 1:])
                break
    return calls


def _gate_steps() -> list[dict]:
    document = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    return [step for job in document["jobs"].values() for step in job.get("steps", [])]


SELECTED = ("scripts/pr_wave_dry_run.py", "tests/test_pr_wave_dry_run.py",
            ".github/workflows/pr-wave-dry-run.yml")


def _triggers(document: dict) -> dict:
    # PyYAML resolves the bare key `on:` to the boolean True.
    return document.get("on", document.get(True)) or {}


def _selected_paths(document: dict, event: str) -> list[str]:
    return list((_triggers(document).get(event) or {}).get("paths") or [])


def test_the_gate_executes_this_guard_and_selects_every_input_it_reads() -> None:
    document = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert "workflow_dispatch" in _triggers(document), \
        "a path-filtered gate must be dispatchable"
    for event in ("pull_request", "push"):
        selected = _selected_paths(document, event)
        for path in SELECTED:
            assert path in selected, f"{event} must select {path}"
    executed = [args for step in _gate_steps() if isinstance(step.get("run"), str)
                for args in _invoked_pytest_arguments(step["run"])]
    assert any("tests/test_pr_wave_dry_run.py" in args for args in executed), \
        "the gate must execute this guard, not merely mention it"
    for name, job in document["jobs"].items():
        assert not job.get("continue-on-error"), f"job {name} cannot hide a failure"
        assert job.get("if") not in (False, "false"), f"job {name} cannot be disabled"
        for step in job.get("steps", []):
            assert not step.get("continue-on-error"), f"step {step} cannot hide a failure"
            assert step.get("if") not in (False, "false"), f"step {step} cannot be disabled"


def test_the_selection_detector_reads_the_filter_not_a_mention_elsewhere() -> None:
    """Negative control: a path named only in a step does not select the gate."""
    synthetic = {True: {"pull_request": {"paths": ["scripts/pr_wave_dry_run.py"]},
                        "workflow_dispatch": None},
                 "jobs": {"g": {"steps": [{"run": "python -m pytest tests/test_pr_wave_dry_run.py"}]}}}
    assert "tests/test_pr_wave_dry_run.py" not in _selected_paths(synthetic, "pull_request")
    assert "workflow_dispatch" in _triggers(synthetic)


def test_the_execution_detector_rejects_a_mention_and_accepts_a_call() -> None:
    """Negative control: the mention form is the defect this detector exists to catch."""
    assert _invoked_pytest_arguments("echo pytest tests/test_pr_wave_dry_run.py") == []
    assert _invoked_pytest_arguments("# pytest tests/test_pr_wave_dry_run.py") == []
    assert _invoked_pytest_arguments(
        "python -m pytest tests/test_pr_wave_dry_run.py -q") == [["tests/test_pr_wave_dry_run.py", "-q"]]
    assert _invoked_pytest_arguments("pytest -q tests/test_pr_wave_dry_run.py") == [
        ["-q", "tests/test_pr_wave_dry_run.py"]]
