"""Regression guard for the open-PR integration oracle (gate-hygiene recon).

The queue carried no way to answer "has this PR's work already landed?", so an
"open" PR read as unfinished work. The oracle answers it from *content*, not from
commit identity: a squash merge rewrites commits, so ``git cherry`` reports every
squashed PR as unlanded, while the blob sha of each changed path survives.

The property that matters is the negative direction — a PR whose content is *not*
at base must never be reported as integrated, because that is the direction that
would justify a wrongful closure. ``test_negative_control_*`` pins it against the
pre-oracle shape (compare nothing, call it landed).

Every blob comparison runs against a real temporary git repository, so the fixture
is the same ``git ls-tree`` the CLI uses. No network, no mocks.
"""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "pr_integration_oracle", REPO_ROOT / "scripts" / "pr_integration_oracle.py"
)
assert _SPEC and _SPEC.loader
oracle = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(oracle)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """A real repository with one commit: ``a.txt`` = "one", ``b.txt`` = "bee"."""
    path = tmp_path / "repo"
    path.mkdir()
    _git(path, "init", "-q", "-b", "main")
    _git(path, "config", "user.email", "guard@example.invalid")
    _git(path, "config", "user.name", "guard")
    (path / "a.txt").write_text("one\n", encoding="utf-8")
    (path / "b.txt").write_text("bee\n", encoding="utf-8")
    _git(path, "add", "-A")
    _git(path, "commit", "-q", "-m", "base")
    return path


def _head(repo: Path) -> str:
    return _git(repo, "rev-parse", "HEAD")


def _blob(repo: Path, path: str) -> str:
    return _git(repo, "hash-object", path)


def _entry(path: str, status: str, sha: str | None, previous: str | None = None) -> dict:
    entry = {"filename": path, "status": status, "sha": sha}
    if previous is not None:
        entry["previous_filename"] = previous
    return entry


# --------------------------------------------------------------------------- blob_map


def test_blob_map_reads_the_committed_tree(repo: Path) -> None:
    blobs = oracle.blob_map(str(repo), _head(repo))
    assert blobs is not None
    assert blobs["a.txt"] == _blob(repo, "a.txt")
    assert blobs["b.txt"] == _blob(repo, "b.txt")


def test_blob_map_is_none_for_an_unknown_revision(repo: Path) -> None:
    assert oracle.blob_map(str(repo), "0" * 40) is None


# --------------------------------------------------------------------------- classify


def test_a_pr_whose_paths_are_already_at_base_is_integrated(repo: Path) -> None:
    (repo / "a.txt").write_text("two\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "change")
    blobs = oracle.blob_map(str(repo), _head(repo))
    assert blobs is not None
    verdict, rows = oracle.classify([_entry("a.txt", "modified", blobs["a.txt"])], blobs)
    assert verdict == oracle.INTEGRATED
    assert rows[0]["landed"] is True


def test_negative_control_a_differing_path_is_not_integrated(repo: Path) -> None:
    """The pre-oracle shape compares nothing and calls everything landed."""
    base = oracle.blob_map(str(repo), _head(repo))
    assert base is not None
    (repo / "a.txt").write_text("two\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "change")
    head_blob = _blob(repo, "a.txt")
    assert head_blob != base["a.txt"]  # the control has something to differ on

    verdict, rows = oracle.classify([_entry("a.txt", "modified", head_blob)], base)
    assert verdict == oracle.CONTRIBUTES
    assert rows[0]["landed"] is False


def test_partial_when_some_paths_landed_and_some_did_not(repo: Path) -> None:
    (repo / "a.txt").write_text("two\n", encoding="utf-8")
    _git(repo, "commit", "-qam", "land a.txt")
    base = oracle.blob_map(str(repo), _head(repo))
    assert base is not None

    (repo / "c.txt").write_text("sea\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "add c.txt")
    blobs = oracle.blob_map(str(repo), _head(repo))
    assert blobs is not None

    # a.txt already carries the PR's content at base; c.txt does not exist at base
    verdict, _ = oracle.classify(
        [
            _entry("a.txt", "modified", blobs["a.txt"]),
            _entry("c.txt", "added", blobs["c.txt"]),
        ],
        base,
    )
    assert verdict == oracle.PARTIAL


def test_a_removed_path_is_landed_only_when_it_is_absent_from_base(repo: Path) -> None:
    base = oracle.blob_map(str(repo), _head(repo))
    assert base is not None
    assert oracle.classify([_entry("a.txt", "removed", None)], base)[0] == oracle.CONTRIBUTES

    _git(repo, "rm", "-q", "a.txt")
    _git(repo, "commit", "-q", "-m", "remove")
    after = oracle.blob_map(str(repo), _head(repo))
    assert after is not None
    assert oracle.classify([_entry("a.txt", "removed", None)], after)[0] == oracle.INTEGRATED


def test_a_rename_needs_both_halves(repo: Path) -> None:
    base = oracle.blob_map(str(repo), _head(repo))
    assert base is not None
    _git(repo, "mv", "a.txt", "renamed.txt")
    _git(repo, "commit", "-q", "-m", "rename")
    after = oracle.blob_map(str(repo), _head(repo))
    assert after is not None
    entry = _entry("renamed.txt", "renamed", after["renamed.txt"], previous="a.txt")

    assert oracle.classify([entry], after)[0] == oracle.INTEGRATED
    # same head content, but the old path is still present at base -> not landed
    assert oracle.classify([entry], base)[0] == oracle.CONTRIBUTES


def test_an_undecidable_path_makes_the_whole_pr_unknown(repo: Path) -> None:
    base = oracle.blob_map(str(repo), _head(repo))
    assert base is not None
    verdict, _ = oracle.classify(
        [_entry("a.txt", "modified", base["a.txt"]), _entry("z.txt", "teleported", None)], base
    )
    assert verdict == oracle.UNKNOWN


def test_a_truncated_file_list_is_undecidable_not_integrated(repo: Path) -> None:
    """Negative control: a lenient reader would call the visible paths landed."""
    base = oracle.blob_map(str(repo), _head(repo))
    assert base is not None
    truncated = [_entry("a.txt", "modified", base["a.txt"])] * oracle.FILE_LIST_CEILING
    assert oracle.classify(truncated, base)[0] == oracle.UNKNOWN


def test_an_empty_diff_is_undecidable_not_integrated(repo: Path) -> None:
    """Superseded pin: this test asserted ``INTEGRATED`` for an empty file list.

    A zero-path list carries no content to compare, so it cannot establish that
    anything landed -- and ``pr_files`` returns ``None`` (not ``[]``) when the
    endpoint is unreadable, so the lenient reading also turned a failed fetch into
    a landing claim. Both read ``UNKNOWN`` now.
    """
    base = oracle.blob_map(str(repo), _head(repo))
    assert base is not None
    assert oracle.classify([], base)[0] == oracle.UNKNOWN


def test_an_unreadable_file_list_is_unknown_not_integrated(repo: Path) -> None:
    """Negative control: a closed port stands in for a rate limit or a 403.

    The pre-repair shape returned ``[]`` on any failed page and classified it
    ``INTEGRATED``; the same call now yields ``None`` and an ``UNKNOWN`` row.
    """
    unreachable = "http://127.0.0.1:9"
    assert oracle.pr_files("token", "owner/repo", 1, api=unreachable) is None

    base = oracle.blob_map(str(repo), _head(repo))
    assert base is not None
    rows = oracle.evaluate(
        [{"number": 1, "title": "unreadable", "head": {"sha": "0" * 40}}],
        "token",
        "owner/repo",
        base,
        _head(repo),
        api=unreachable,
    )
    assert rows[0]["verdict"] == oracle.UNKNOWN
    assert rows[0]["reason"] == "file_list_unavailable"
    assert rows[0]["changed_paths"] is None


# --------------------------------------------------------------------------- read-only


def test_the_oracle_issues_no_mutating_request() -> None:
    """A closure input must not be able to change PR state."""
    source = (REPO_ROOT / "scripts" / "pr_integration_oracle.py").read_text(encoding="utf-8")
    for verb in ('"POST"', '"PUT"', '"PATCH"', '"DELETE"'):
        assert verb not in source
    # the only HTTP call site the module carries, and it sets no method (urllib
    # defaults to GET), so no request can mutate PR state
    assert source.count("urlopen(") == 1
    assert "method=" not in source
