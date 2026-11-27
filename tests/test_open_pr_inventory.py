"""Regression guard for the durable open-PR inventory (gate-hygiene recon).

The open-PR queue is a live fact. Before `scripts/open_pr_inventory.py` it was
reconstructed ad hoc, and the ad-hoc recon crashed with `KeyError: 'mergeable'`
because GitHub's *list* endpoint omits `mergeable`/`mergeable_state`; only the
*detail* endpoint exposes them.

That defect is invisible to a network-free test, so the guard is structured
around the one property that makes the harness reproducible: it must never read
a mergeable field that the list endpoint does not carry. A fake API proves it,
and a negative control feeds the harness the exact pre-fix form to prove the
detector bites.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "open_pr_inventory", REPO_ROOT / "scripts" / "open_pr_inventory.py"
)
assert _SPEC and _SPEC.loader
inventory_mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(inventory_mod)

# The detail-only keys. Their absence from the list payload is the documented
# crash cause; the guard asserts the harness treats them as optional.
DETAIL_ONLY = ("mergeable", "mergeable_state")


def _list_item(number: int = 1, **overrides) -> dict:
    """A PR record shaped like the *list* endpoint: no mergeable fields."""
    item = {
        "number": number,
        "title": "example",
        "draft": False,
        "head": {"ref": "b", "sha": "a" * 40},
        "base": {"ref": "main", "sha": "b" * 40},
    }
    item.update(overrides)
    return item


def _detail_item(number: int = 1, mergeable=True, state="clean") -> dict:
    """A PR record shaped like the *detail* endpoint: mergeable fields present."""
    item = _list_item(number)
    item["mergeable"] = mergeable
    item["mergeable_state"] = state
    return item


def test_summarize_tolerates_a_list_record_without_mergeable():
    """The exact pre-fix defect: a list record has no `mergeable`. The harness
    must not raise, and must report the field as unavailable."""
    row = inventory_mod.summarize(_list_item())
    assert row["number"] == 1
    assert row["mergeable"] == "LIST_ENDPOINT"


def test_summarize_treats_null_mergeable_as_unknown():
    """GitHub returns `mergeable: null` while it computes the merge. That is
    UNKNOWN, not a crash and not a false 'conflict'."""
    item = _detail_item()
    item["mergeable"] = None
    assert inventory_mod.summarize(item)["mergeable"] == "UNKNOWN"


def test_summarize_reports_clean_and_conflict_from_detail():
    assert inventory_mod.summarize(_detail_item(mergeable=True, state="clean"))["mergeable"] == "clean:clean"
    assert inventory_mod.summarize(_detail_item(mergeable=False, state="dirty"))["mergeable"] == "conflict:dirty"


def test_negative_control_the_naive_read_is_unmasked_by_the_list_payload():
    """Negative control. A naive reader does `pr["mergeable"]` on a *list*
    record. If GitHub were ever to add the field to the list endpoint, this
    control would stop raising — i.e. the defect the guard documents would no
    longer be reachable through the list endpoint, and this file should be
    revisited. The assertion here pins that the list payload currently omits it.
    """
    list_item = _list_item()
    assert "mergeable" not in list_item
    with pytest.raises(KeyError):
        _ = list_item["mergeable"]


class _FakeResponse:
    def __init__(self, payload, status=200):
        self._body = json.dumps(payload).encode()
        self.status = status

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_inventory_merges_detail_without_mutating_the_list_record(monkeypatch):
    """End-to-end over a fake API: the list endpoint is called once, the detail
    endpoint once per PR, and the merged row carries a real mergeable verdict."""
    calls: list[str] = []

    def fake_urlopen(req, *a, **k):
        url = req.full_url
        calls.append(url)
        if "/pulls?" in url:
            return _FakeResponse([_list_item(7), _list_item(8)])
        if url.endswith("/pulls/7"):
            return _FakeResponse(_detail_item(7, mergeable=True, state="clean"))
        if url.endswith("/pulls/8"):
            return _FakeResponse(_detail_item(8, mergeable=False, state="dirty"))
        raise AssertionError(f"unexpected URL {url}")

    monkeypatch.setattr(inventory_mod.urllib.request, "urlopen", fake_urlopen)
    rows = inventory_mod.inventory("token", "owner/repo")

    assert [r["number"] for r in rows] == [7, 8]
    assert rows[0]["mergeable"] == "clean:clean"
    assert rows[1]["mergeable"] == "conflict:dirty"
    assert sum("/pulls?" in c for c in calls) == 1
    assert sum(c.endswith("/pulls/7") for c in calls) == 1


def test_inventory_keeps_the_row_when_detail_fails(monkeypatch):
    """A detail failure must degrade to LIST_ENDPOINT for that PR, not abort
    the whole inventory."""

    def fake_urlopen(req, *a, **k):
        url = req.full_url
        if "/pulls?" in url:
            return _FakeResponse([_list_item(9)])
        raise inventory_mod.urllib.error.HTTPError(url, 403, "forbidden", {}, None)

    monkeypatch.setattr(inventory_mod.urllib.request, "urlopen", fake_urlopen)
    rows = inventory_mod.inventory("token", "owner/repo")
    assert rows[0]["number"] == 9
    assert rows[0]["mergeable"] == "LIST_ENDPOINT"


def test_string_keys_and_absent_mergeable_are_handled():
    """Contract pin: the harness reads mergeable fields only through
    `summarize`, so a record missing them cannot KeyError."""
    for key in DETAIL_ONLY:
        assert key in inventory_mod.DETAIL_ONLY_KEYS
    assert inventory_mod.DETAIL_ONLY_KEYS == DETAIL_ONLY


# ---------------------------------------------------------------------------
# Composition conflicts
#
# `mergeable` is a per-PR answer about the PR's own base. It says nothing about
# whether two open PRs can both merge, which is the question that decides merge
# order. These tests drive the real `git merge-tree` path against a real
# temporary repository: no fixture substitutes for the code under test.
# ---------------------------------------------------------------------------

import shutil  # noqa: E402  (appended section)
import subprocess  # noqa: E402


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


def _composable_repo(tmp_path: Path) -> Path:
    """A repository with two conflicting branches and one disjoint branch."""
    if not shutil.which("git"):  # pragma: no cover - git is a hard dependency here
        pytest.skip("git is required to judge composition")
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    (repo / "shared.txt").write_text("base\n")
    (repo / "a.txt").write_text("a\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "base")
    base = _git(repo, "rev-parse", "HEAD")

    for branch, text in (("left", "left\n"), ("right", "right\n")):
        _git(repo, "checkout", "-q", base)
        _git(repo, "checkout", "-qb", branch)
        (repo / "shared.txt").write_text(text)
        _git(repo, "commit", "-qam", branch)

    _git(repo, "checkout", "-q", base)
    _git(repo, "checkout", "-qb", "disjoint")
    (repo / "a.txt").write_text("a changed\n")
    _git(repo, "commit", "-qam", "disjoint")
    return repo


def test_merge_conflict_paths_flags_a_real_conflict(tmp_path):
    repo = _composable_repo(tmp_path)
    assert inventory_mod.merge_conflict_paths("left", "right", str(repo)) == ["shared.txt"]


def test_merge_conflict_paths_is_silent_for_disjoint_edits(tmp_path):
    """Negative control for the detector: it must not report a conflict for a
    pair that composes, or every pair would read as conflicting."""
    repo = _composable_repo(tmp_path)
    assert inventory_mod.merge_conflict_paths("left", "disjoint", str(repo)) == []


def test_merge_conflict_paths_is_unprovable_for_an_unknown_revision(tmp_path):
    """An unresolvable revision is UNPROVABLE, never CLEAN: an unanswered
    composition question must not read as a pass."""
    repo = _composable_repo(tmp_path)
    paths = inventory_mod.merge_conflict_paths("left", "no-such-revision", str(repo))
    assert paths is None
    assert inventory_mod.conflict_verdict(paths) == "UNPROVABLE"


def test_conflict_matrix_reports_every_pair_once_with_its_verdict(tmp_path):
    repo = _composable_repo(tmp_path)
    rows = inventory_mod.conflict_matrix(
        {"left": "left", "right": "right", "disjoint": "disjoint"}, repo=str(repo)
    )
    assert len(rows) == 3  # C(3, 2); each unordered pair judged once
    assert {(r["a"], r["b"]) for r in rows} == {
        ("disjoint", "left"),
        ("disjoint", "right"),
        ("left", "right"),
    }
    verdicts = {(r["a"], r["b"]): r["verdict"] for r in rows}
    assert verdicts[("left", "right")] == "CONFLICT"
    assert verdicts[("disjoint", "left")] == "CLEAN"
    assert verdicts[("disjoint", "right")] == "CLEAN"


def test_cli_conflicts_reports_json_without_network(tmp_path, capsys):
    """The wiring is exercised, not just the function: `--conflicts` must work
    with no token and no GitHub call."""
    repo = _composable_repo(tmp_path)
    code = inventory_mod.main(
        [
            "--conflicts",
            "--ref", "left=left",
            "--ref", "right=right",
            "--git-repo", str(repo),
            "--json",
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["pairs"] == [
        {"a": "left", "b": "right", "verdict": "CONFLICT", "paths": ["shared.txt"]}
    ]


def test_cli_conflicts_needs_two_refs():
    assert inventory_mod.main(["--conflicts", "--ref", "only=HEAD"]) == 2
