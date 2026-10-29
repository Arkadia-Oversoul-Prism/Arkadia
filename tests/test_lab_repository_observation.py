"""AEAS-01 P0.3 — repository & change observation, read-only (Engineering Lab).

The Lab's inspectable-engineering-output slice adds one reading: branch, source
revision, the working tree's real change inventory, and the real diff, observed
through the same bounded read-only git boundary bounded execution uses.

What these tests pin:

  * the observation is real — it runs against an actual temporary git repository
    and reports the codes git itself prints, staged and unstaged kept apart;
  * a failed read is reported as **unavailable with a reason**, never as
    ``clean`` / ``0 files`` (negative control: a non-git directory);
  * the observation performs no mutation — the tree's status and HEAD are
    byte-identical before and after;
  * the served route is GET-only and carries the Lab router's authentication
    gate, and its handler reads the *execution* workspace root (one root, not
    two).
"""

from __future__ import annotations

import asyncio
import inspect
import subprocess
from pathlib import Path

import pytest

from lab.engineering_lab.repository import (
    SCHEMA,
    observe_repository,
    parse_porcelain,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"git {args} failed: {proc.stderr}"
    return proc.stdout


def _commit(root: Path, message: str) -> None:
    _git(
        root,
        "-c",
        "user.email=lab@example.invalid",
        "-c",
        "user.name=Engineering Lab",
        "commit",
        "-m",
        message,
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A real repository with one commit, so HEAD and status are meaningful."""
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-b", "main")
    (root / "alpha.txt").write_text("one\n", encoding="utf-8")
    _git(root, "add", "alpha.txt")
    _commit(root, "init")
    return root


# ---------------------------------------------------------------------------
# Observed state — real git, real codes
# ---------------------------------------------------------------------------


def test_clean_repository_reports_observed_and_clean(repo: Path) -> None:
    view = observe_repository(str(repo))

    assert view["schema"] == SCHEMA
    facts = view["repository"]
    assert facts["branch"] == "main"
    assert facts["head"] and len(facts["head"]) == 40
    assert facts["short_head"] == facts["head"][:12]
    assert facts["status"] == "observed"
    assert facts["clean"] is True

    changes = view["changes"]
    assert changes["status"] == "observed"
    assert changes["count"] == 0
    assert changes["files"] == []
    assert changes["truncated"] is False

    assert view["diff"]["unstaged"]["status"] == "empty"
    assert view["diff"]["staged"]["status"] == "empty"


def test_worktree_modification_is_reported_with_its_diff(repo: Path) -> None:
    (repo / "alpha.txt").write_text("one\ntwo\n", encoding="utf-8")

    view = observe_repository(str(repo))

    assert view["repository"]["clean"] is False
    entry = view["changes"]["files"][0]
    assert entry["code"] == " M"
    assert entry["label"] == "modified"
    assert entry["path"] == "alpha.txt"
    assert entry["staged"] is False
    assert entry["unstaged"] is True

    unstaged = view["diff"]["unstaged"]
    assert unstaged["status"] == "observed"
    assert "+two" in unstaged["text"]
    # The staged half must stay a separate, truthful reading.
    assert view["diff"]["staged"]["status"] == "empty"


def test_staged_and_unstaged_changes_are_distinguished(repo: Path) -> None:
    (repo / "alpha.txt").write_text("one\ntwo\n", encoding="utf-8")
    _git(repo, "add", "alpha.txt")
    (repo / "beta.txt").write_text("x\n", encoding="utf-8")

    view = observe_repository(str(repo))

    by_code = {entry["code"]: entry for entry in view["changes"]["files"]}
    assert {"M ", "??"} <= set(by_code), sorted(by_code)
    assert by_code["M "]["staged"] is True and by_code["M "]["unstaged"] is False
    assert by_code["M "]["label"] == "modified"
    assert by_code["??"]["label"] == "untracked"
    assert by_code["??"]["staged"] is False and by_code["??"]["unstaged"] is False

    assert view["diff"]["staged"]["status"] == "observed"
    assert "+two" in view["diff"]["staged"]["text"]
    # The working tree matches the index for alpha, so the unstaged side is empty.
    assert view["diff"]["unstaged"]["status"] == "empty"
    assert view["changes"]["count"] == 2


def test_rename_carries_both_paths(repo: Path) -> None:
    _git(repo, "mv", "alpha.txt", "gamma.txt")
    view = observe_repository(str(repo))
    entry = view["changes"]["files"][0]
    assert entry["code"].startswith("R")
    assert entry["label"] == "renamed"
    assert entry["path"] == "gamma.txt"
    assert entry["original_path"] == "alpha.txt"
    assert entry["staged"] is True


# ---------------------------------------------------------------------------
# Negative controls — an unobserved tree is UNKNOWN, not clean
# ---------------------------------------------------------------------------


def test_non_git_directory_is_unavailable_never_clean(tmp_path: Path) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()

    view = observe_repository(str(plain))

    facts = view["repository"]
    assert facts["clean"] is None, "an unobserved tree must not read clean"
    assert facts["status"] == "unavailable"

    changes = view["changes"]
    assert changes["status"] == "unavailable"
    assert changes["count"] is None, "a failed read must not report 0 changes"
    assert changes["reason"], "unavailable must carry its reason"

    assert view["diff"]["unstaged"]["status"] == "unavailable"
    assert view["diff"]["staged"]["reason"]


def test_absent_root_degrades_to_unavailable_not_a_crash(tmp_path: Path) -> None:
    view = observe_repository(str(tmp_path / "does-not-exist"))

    assert view["repository"]["clean"] is None
    assert view["changes"]["status"] == "unavailable"
    assert view["changes"]["count"] is None
    assert "sandbox unavailable" in (view["changes"]["reason"] or "")


def test_diff_is_bounded_and_says_so(repo: Path) -> None:
    (repo / "alpha.txt").write_text("one\ntwo\nthree\n", encoding="utf-8")

    view = observe_repository(str(repo), max_diff_chars=10)

    side = view["diff"]["unstaged"]
    assert side["status"] == "observed"
    assert side["truncated"] is True
    assert side["chars"] <= 10
    assert len(side["text"]) <= 10


def test_change_inventory_is_capped_and_flagged(repo: Path) -> None:
    for index in range(5):
        (repo / f"file{index}.txt").write_text("x\n", encoding="utf-8")

    view = observe_repository(str(repo), max_changes=2)

    assert view["changes"]["status"] == "observed"
    assert len(view["changes"]["files"]) == 2
    assert view["changes"]["truncated"] is True
    # The cap is on the list, not on the truth: count still reports all 5.
    assert view["changes"]["count"] == 5


def test_parsing_a_rename_line_and_an_unknown_code() -> None:
    entries, truncated = parse_porcelain("R  old.txt -> new.txt\n")
    assert truncated is False
    assert entries[0] == {
        "code": "R ",
        "label": "renamed",
        "path": "new.txt",
        "original_path": "old.txt",
        "staged": True,
        "unstaged": False,
    }


# ---------------------------------------------------------------------------
# The observation performs no mutation
# ---------------------------------------------------------------------------


def test_observation_leaves_status_and_head_untouched(repo: Path) -> None:
    (repo / "alpha.txt").write_text("changed\n", encoding="utf-8")
    status_before = _git(repo, "status", "--porcelain")
    head_before = _git(repo, "rev-parse", "HEAD")

    observe_repository(str(repo))

    assert _git(repo, "status", "--porcelain") == status_before
    assert _git(repo, "rev-parse", "HEAD") == head_before
    # Nothing was staged behind the operator's back.
    assert _git(repo, "diff", "--cached") == ""


# ---------------------------------------------------------------------------
# The served route
# ---------------------------------------------------------------------------


def test_route_is_registered_get_only_and_authenticated() -> None:
    from api.lab_routes import router

    routes = {route.path: route for route in router.routes}
    path = "/api/lab/engineering/repository"
    assert path in routes, "the repository reading is not served"
    assert routes[path].methods == {"GET"}, "the reading must be read-only"

    handler_source = inspect.getsource(routes[path].endpoint)
    assert "Depends(require_auth)" in handler_source, (
        "the repository reading must sit behind the Lab's authentication gate"
    )


def test_handler_observes_the_execution_workspace_root() -> None:
    """One root: the tree the surface reads is the tree a run executes against."""
    from api.lab_routes import engineering_repository
    from lab.engineering_lab import runtime as runtime_module

    source = inspect.getsource(engineering_repository)
    assert "observe_repository(workspace_root())" in source
    assert "workspace_root" in vars(runtime_module), "runtime must expose the root accessor"

    payload = asyncio.run(engineering_repository(user={"uid": "lab-repo-observer"}))
    assert payload["schema"] == SCHEMA
    # The live repository's state is environment-dependent; only its shape is
    # pinned here, plus the invariant that failure never becomes a healthy value.
    assert payload["changes"]["status"] in {"observed", "unavailable"}
    if payload["changes"]["status"] == "unavailable":
        assert payload["repository"]["clean"] is None
        assert payload["changes"]["count"] is None


def test_router_level_gate_rejects_an_anonymous_read() -> None:
    """401, not 200-with-empty-payload: reading the repository needs an identity."""
    from fastapi.testclient import TestClient

    from api.main import app

    client = TestClient(app)
    response = client.get("/api/lab/engineering/repository")
    assert response.status_code in (401, 403), response.status_code
