"""AEAS-01 P0.3 — the repository reading's console surface (Engineering Lab).

Two things are guarded here, in the repository's established style:

  * **the projection is executed** — Node imports `labRepository.ts` and runs it,
    so what is judged is behaviour (an absent `clean` renders UNKNOWN, an
    unavailable diff carries its reason), not a source substring;
  * **the projection is bound to the serving handler** — every field it reads is
    asserted in `api/lab_routes.py::engineering_repository`, so a handler rename
    reddens this guard instead of letting the panel render a healthy-looking
    `unknown`.

Plus the boundary: the panel performs **reads only** (no mutating method), and
the path it requests is the registry entry, never a page-local literal.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CONSOLE = REPO_ROOT / "web" / "arkadia_console"
SRC = CONSOLE / "src"
LAB_TREE = SRC / "components" / "lab"
PROJECTION = LAB_TREE / "labRepository.ts"
SURFACE = LAB_TREE / "LabRepositoryContext.tsx"
LAB_PAGE = SRC / "pages" / "EngineeringLabPage.tsx"
ENDPOINTS = SRC / "lib" / "endpoints.ts"
HANDLER = REPO_ROOT / "api" / "lab_routes.py"

REPOSITORY_PATH = "/api/lab/engineering/repository"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _node() -> str:
    found = shutil.which("node")
    if not found:
        pytest.skip("node is unavailable, so the projection cannot be executed here")
    return found


def run_projection(function: str, payload: object) -> object:
    """Execute a real export of ``labRepository.ts`` over *payload*."""
    node = _node()
    program = (
        f"const m = await import({json.dumps(PROJECTION.as_uri())});\n"
        "const [fn, arg] = JSON.parse(process.argv[1]);\n"
        f"const fnRef = m[fn];\n"
        "if (typeof fnRef !== 'function') { throw new Error('missing export: ' + fn); }\n"
        "process.stdout.write(JSON.stringify(fnRef(arg)));\n"
    )
    completed = subprocess.run(
        [node, "--input-type=module", "-e", program, json.dumps([function, payload])],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if completed.returncode != 0:
        pytest.fail(f"projection execution failed: {completed.stderr.strip()[:800]}")
    return json.loads(completed.stdout)


# ---------------------------------------------------------------------------
# Registry + served route
# ---------------------------------------------------------------------------


def test_registry_declares_the_repository_reading_and_it_is_served() -> None:
    """One registry, and the entry must resolve to a real handler (§3.3)."""
    declared = dict(
        re.findall(
            r'(\w+):\s*"([^"]+)"',
            re.search(
                r"export const endpoints\s*=\s*\{(.*?)\}\s*as const;",
                _read(ENDPOINTS),
                re.DOTALL,
            ).group(1),
        )
    )
    assert declared.get("labRepository") == REPOSITORY_PATH

    from api.main import app

    served = set(app.openapi()["paths"].keys())
    assert REPOSITORY_PATH in served, "the registry entry must be a served route"


def test_surface_reads_the_registry_entry_not_a_literal() -> None:
    source = _read(SURFACE)
    assert "endpoints.labRepository" in source
    assert REPOSITORY_PATH not in source, "a page-local path is a second registry"


def test_surface_performs_reads_only() -> None:
    """No mutating method may appear: reading the repository is not changing it."""
    source = _read(SURFACE)
    for method in ("POST", "PUT", "PATCH", "DELETE"):
        assert f'method: "{method}"' not in source, f"the panel declares a {method} call"


def _matching_details_close(page: str, open_index: int) -> int:
    """Index of the ``</details>`` that closes the ``<details`` at *open_index*.

    A structural scan, not a substring search: nested ``<details>`` elements are
    counted, so the returned close is the one that actually closes the
    container rather than the first one that happens to appear after it.
    """
    depth = 0
    i = open_index
    while i < len(page):
        nxt_open = page.find("<details", i)
        nxt_close = page.find("</details>", i)
        if nxt_close == -1:
            raise AssertionError("unbalanced <details>: no closing tag")
        if nxt_open != -1 and nxt_open < nxt_close:
            depth += 1
            i = nxt_open + len("<details")
        else:
            depth -= 1
            if depth == 0:
                return nxt_close
            i = nxt_close + len("</details>")
    raise AssertionError("unbalanced <details>: reached end of file")


def _engineering_details_span(page: str) -> tuple[int, int]:
    """The ``(open, close)`` character span of the diagnostics container."""
    marker = page.find('data-testid="lab-engineering-details"')
    assert marker != -1, "the lab-engineering-details container is gone"
    open_index = page.rfind("<details", 0, marker)
    assert open_index != -1, "the diagnostics container is not a <details> element"
    return open_index, _matching_details_close(page, open_index)


def test_repository_context_is_contained_in_the_engineering_details_container() -> None:
    """The repository reading lives INSIDE the diagnostics disclosure.

    Structural, not a substring check: the container's own closing tag is
    located by counting nested ``<details>`` elements, so moving
    ``<LabRepositoryContext />`` back outside the container reddens this guard
    even though the string is still present in the file.
    """
    page = _read(LAB_PAGE)
    open_index, close_index = _engineering_details_span(page)

    mount = page.find("<LabRepositoryContext />")
    assert mount != -1, "the repository context is not mounted"
    assert open_index < mount < close_index, (
        "LabRepositoryContext must be mounted inside the lab-engineering-details "
        "container, not beside it"
    )


def test_mission_workspace_is_the_first_child_of_the_page() -> None:
    """Mission Control leads the surface; the diagnostics container follows it.

    Ordering is asserted structurally: the first element after the ``<Page>``
    opening tag must be ``<MissionWorkspace />``, and it must precede the
    diagnostics container.
    """
    page = _read(LAB_PAGE)

    mission = page.find("<MissionWorkspace />")
    assert mission != -1, "MissionWorkspace is not mounted"

    open_index, _ = _engineering_details_span(page)
    assert mission < open_index, (
        "MissionWorkspace must precede the lab-engineering-details container"
    )

    page_open = page.find("<Page")
    assert page_open != -1, "the page element is gone"
    tag_end = page.find(">", page_open)
    assert tag_end != -1, "the <Page> opening tag is unterminated"
    first_child = page[tag_end + 1 :].lstrip()
    assert first_child.startswith("<MissionWorkspace />"), (
        "MissionWorkspace must be the first child of <Page>; found "
        f"{first_child[:40]!r} instead"
    )


# ---------------------------------------------------------------------------
# Handler binding — the fields the projection reads must exist upstream
# ---------------------------------------------------------------------------


def test_handler_declares_every_field_the_projection_reads() -> None:
    source = _read(HANDLER)
    assert '@router.get("/engineering/repository")' in source
    assert "observe_repository(workspace_root())" in source
    # The reading itself lives in the substrate module; assert against it too.
    module = _read(REPO_ROOT / "lab" / "engineering_lab" / "repository.py")
    for field in (
        '"branch"',
        '"head"',
        '"short_head"',
        '"remote"',
        '"clean"',
        '"status"',
        '"reason"',
        '"files"',
        '"count"',
        '"truncated"',
        '"text"',
        '"chars"',
        '"staged"',
        '"unstaged"',
        '"observed_at"',
        '"schema"',
    ):
        assert field in module, f"repository observation no longer declares {field}"


# ---------------------------------------------------------------------------
# Behaviour — the projection is executed, not read
# ---------------------------------------------------------------------------


def _handler_shaped_payload() -> dict:
    return {
        "schema": "arkadia.lab.repository/1",
        "observed_at": "2026-10-29T00:00:00Z",
        "repository": {
            "branch": "main",
            "head": "a" * 40,
            "short_head": "a" * 12,
            "remote": "https://example.invalid/org/repo.git",
            "remote_redacted": True,
            "status": "observed",
            "reason": None,
            "clean": False,
        },
        "changes": {
            "status": "observed",
            "reason": None,
            "files": [
                {
                    "code": " M",
                    "label": "modified",
                    "path": "alpha.txt",
                    "original_path": None,
                    "staged": False,
                    "unstaged": True,
                }
            ],
            "count": 1,
            "truncated": False,
        },
        "diff": {
            "unstaged": {"status": "observed", "reason": None, "text": "+two\n", "chars": 5, "truncated": False},
            "staged": {"status": "unavailable", "reason": "not a git repository", "text": "", "chars": 0, "truncated": False},
        },
        "boundary": "read-only git observation",
    }


def test_projection_projects_a_real_reading() -> None:
    payload = _handler_shaped_payload()
    facts = run_projection("buildRepositoryFacts", payload)
    values = {row["label"]: row["value"] for row in facts}
    assert values["branch"] == "main"
    assert values["source revision"] == "a" * 12
    assert values["working tree"] == "changes present"
    assert values["changes"] == "1 file"
    assert "redacted" in values["origin"]
    assert run_projection("describeDiff", payload["diff"]["unstaged"]).startswith("observed")


def test_absent_clean_never_renders_as_clean() -> None:
    """Negative control: an unobserved tree is UNKNOWN, not clean."""
    assert run_projection("describeClean", None) == "UNKNOWN"
    assert run_projection("describeClean", True) == "clean"
    assert run_projection("describeClean", False) == "changes present"


def test_absent_count_never_renders_as_zero() -> None:
    assert "UNKNOWN" in str(run_projection("describeChangeCount", None))
    assert run_projection("describeChangeCount", 0) == "0 files"
    assert run_projection("describeChangeCount", 2) == "2 files"


def test_unavailable_diff_carries_its_reason() -> None:
    reading = str(run_projection("describeDiff", {"status": "unavailable", "reason": "not a git repository", "text": "", "chars": 0, "truncated": False}))
    assert "unavailable" in reading
    assert "not a git repository" in reading
    # An empty read is a fact, distinct from an unread one.
    empty = str(run_projection("describeDiff", {"status": "empty", "reason": None, "text": "", "chars": 0, "truncated": False}))
    assert "empty" in empty and "succeeded" in empty
    assert "UNKNOWN" in str(run_projection("describeDiff", None))


def test_coverage_states_the_cap_and_the_failure() -> None:
    observed = str(run_projection("describeCoverage", {"status": "observed", "reason": None, "files": [1, 2], "count": 5, "truncated": True}))
    assert "2 of 5" in observed and "capped" in observed
    failed = str(run_projection("describeCoverage", {"status": "unavailable", "reason": "denied", "files": [], "count": None, "truncated": False}))
    assert "not observed" in failed and "denied" in failed


def test_facts_without_a_reading_are_unknown_not_blank() -> None:
    facts = run_projection("buildRepositoryFacts", None)
    assert len(facts) == 1
    assert "UNKNOWN" in facts[0]["value"]


# ---------------------------------------------------------------------------
# The surface states its unavailable case in source
# ---------------------------------------------------------------------------


def test_surface_renders_the_unobserved_and_unknown_states() -> None:
    source = _read(SURFACE)
    assert "lab-repository-unobserved" in source
    assert "not a clean-tree claim" in source
    assert "UNKNOWN" in str(run_projection("describeRevision", {"branch": "main", "head": None, "short_head": None, "status": "unavailable", "reason": "git failed"}))
    for testid in (
        "lab-repository-panel",
        "lab-repository-refresh",
        "lab-repository-changes",
        "lab-repository-diff-staged",
        "lab-repository-diff-unstaged",
    ):
        assert testid in source, f"missing {testid}"
    # The diff sides receive their id as a prop, so the mapping itself must be
    # asserted: a literal ``data-testid="…"`` never appears in the source.
    assert "data-testid={testid}" in source
