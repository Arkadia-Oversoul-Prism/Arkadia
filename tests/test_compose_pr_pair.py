"""Guard for `scripts/compose_pr_pair.py`.

Gate-cluster merge decisions in this repository rest on a composition claim: two
open PRs were shown to combine into one tree without a semantic collision. The
records (PRs #376 / #377 / #391) were produced by hand, so nothing re-derives
them. This guard pins the harness that now derives them.

The harness performs a *real* `git merge` in an isolated worktree. These tests
drive it against a throwaway repository built here, so they need no network and
no PR refs. Every assertion that matters carries a control: a detector that
returned `clean=True` unconditionally, or `overlap=[]` unconditionally, would be
self-satisfying, so the negative controls feed it the colliding shape and assert
it is caught.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


from scripts import compose_pr_pair as cpp


def _run(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", *args],
        cwd=str(repo), check=True, capture_output=True, text=True,
    )


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(repo, "init", "-q", "-b", "main")
    (repo / "shared.txt").write_text("line1\nline2\nline3\n")
    (repo / "only_a.txt").write_text("a\n")
    (repo / "only_b.txt").write_text("b\n")
    _run(repo, "add", "-A")
    _run(repo, "commit", "-q", "-m", "base")
    return repo


def test_clean_pair_composes_order_independently(tmp_path):
    repo = _init_repo(tmp_path)
    _run(repo, "checkout", "-q", "-b", "a")
    (repo / "only_a.txt").write_text("a changed\n")
    _run(repo, "commit", "-q", "-am", "a")
    _run(repo, "checkout", "-q", "-b", "b", "main")
    (repo / "only_b.txt").write_text("b changed\n")
    _run(repo, "commit", "-q", "-am", "b")

    result = cpp.compose(repo, "a", "b")
    assert result["clean"] is True
    assert result["order_independent"] is True
    assert result["overlapping_paths"] == []


def test_overlapping_edit_is_reported_even_when_auto_merged(tmp_path):
    """Overlap is reported on a shared file even when the merge is clean.

    The harness must not collapse "both touched X" into "conflict on X": an
    auto-merged shared path is still a semantic-compatibility question a reviewer
    needs to see.
    """
    repo = _init_repo(tmp_path)
    _run(repo, "checkout", "-q", "-b", "a")
    (repo / "shared.txt").write_text("line1\nA-A\nline3\n")
    _run(repo, "commit", "-q", "-am", "a")
    _run(repo, "checkout", "-q", "-b", "b", "main")
    (repo / "shared.txt").write_text("line1\nB-B\nline3\n")
    _run(repo, "commit", "-q", "-am", "b")

    result = cpp.compose(repo, "a", "b")
    assert result["overlapping_paths"] == ["shared.txt"]
    assert result["clean"] is False
    assert "shared.txt" in result["forward"]["conflicts"]


def test_conflicting_pair_is_never_reported_clean(tmp_path):
    """Negative control for a detector that would always answer `clean`."""
    repo = _init_repo(tmp_path)
    _run(repo, "checkout", "-q", "-b", "a")
    (repo / "shared.txt").write_text("line1\nfrom-a\nline3\n")
    _run(repo, "commit", "-q", "-am", "a")
    _run(repo, "checkout", "-q", "-b", "b", "main")
    (repo / "shared.txt").write_text("line1\nfrom-b\nline3\n")
    _run(repo, "commit", "-q", "-am", "b")

    result = cpp.compose(repo, "a", "b")
    assert result["clean"] is False, "an always-clean detector would pass here"
    assert result["forward"]["conflicts"], "a clean run must report the colliding path"


def test_overlap_detector_is_not_empty_blind(tmp_path):
    """Negative control for a detector that would always answer `no overlap`."""
    repo = _init_repo(tmp_path)
    _run(repo, "checkout", "-q", "-b", "a")
    (repo / "shared.txt").write_text("x\n")
    _run(repo, "commit", "-q", "-am", "a")
    _run(repo, "checkout", "-q", "-b", "b", "main")
    (repo / "shared.txt").write_text("y\n")
    _run(repo, "commit", "-q", "-am", "b")

    overlap = cpp.overlapping_paths(repo, "a", "b")
    assert overlap == ["shared.txt"], "an always-empty overlap detector would pass here"


def test_cli_exit_code_is_nonzero_on_conflict(tmp_path, capsys):
    repo = _init_repo(tmp_path)
    _run(repo, "checkout", "-q", "-b", "a")
    (repo / "shared.txt").write_text("a\n")
    _run(repo, "commit", "-q", "-am", "a")
    _run(repo, "checkout", "-q", "-b", "b", "main")
    (repo / "shared.txt").write_text("b\n")
    _run(repo, "commit", "-q", "-am", "b")

    rc = cpp._main(["a", "b", "--repo", str(repo)])
    assert rc == 1, "a conflicting composition must exit non-zero so it can gate a decision"


def test_cli_exit_code_is_zero_on_clean(tmp_path):
    repo = _init_repo(tmp_path)
    _run(repo, "checkout", "-q", "-b", "a")
    (repo / "only_a.txt").write_text("a changed\n")
    _run(repo, "commit", "-q", "-am", "a")
    _run(repo, "checkout", "-q", "-b", "b", "main")
    (repo / "only_b.txt").write_text("b changed\n")
    _run(repo, "commit", "-q", "-am", "b")

    assert cpp._main(["a", "b", "--repo", str(repo)]) == 0
