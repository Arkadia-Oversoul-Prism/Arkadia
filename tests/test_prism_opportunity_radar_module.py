"""Project Opportunity Radar — capability matrix for the reconnaissance contract.

This file **measures** the backend contract the project-scoped Opportunity
Radar depends on. It does not assert a design, and it does not repair the
backend.

Source of truth (read, not assumed):

  * `solspire/buyer_recon_router.py` — the project-scoped routes.
  * `solspire/buyer_recon.py` — the `STATUSES` vocabulary, the `UNKNOWN`
    default for an unverified commercial fact, and the persistence table.
  * `solspire/console_router.py:51` — the `/solspire` router carries
    `dependencies=[Depends(require_auth)]`, so every nested route is
    authenticated.
  * `api/auth.py:446` — `require_auth` raises `401` when no identity resolves.

Recorded capability matrix (status per row):

  | capability                                     | status                     |
  |------------------------------------------------|----------------------------|
  | project board read (GET), first board          | WORKS                      |
  | project ownership enforcement                  | WORKS (404 for non-owner)  |
  | reconnaissance-only authority block            | PRESENT                    |
  | unverified facts default to `UNKNOWN`          | PRESENT                    |
  | project + workspace board coexist              | **BROKEN — defect 2**      |
  | project/workspace entry **create** (POST)      | **BROKEN — defect 1**      |

**Defect 1 — entry create arity.** `BuyerReconManager.create_entry` supplies 34
values to a 33-column `buyer_recon_entries` table, so *every* create raises
`sqlite3.OperationalError: table buyer_recon_entries has 33 columns but 34
values were supplied`.

**Defect 2 — one board per subject.** `buyer_recon_boards` declares
`subject_ref TEXT NOT NULL UNIQUE`, while `_project_board` keys the board by
`f"{workspace.id}:project:{project_id}"`. The UNIQUE is on the *subject*, not on
the composite, so a subject can hold exactly one board: whichever scope is read
second raises `sqlite3.IntegrityError: UNIQUE constraint failed:
buyer_recon_boards.subject_ref` → HTTP 500. Since `/solspire/buyer-recon` (the
workspace board) is the natural first read, the **project-scoped radar is
unreachable for any subject who has opened the workspace board** — which is the
blocker for this workstream's project-level slice.

Both were introduced at `5de6d476` (PR #199, 2026-10-02) and are reachable on the
live deployment. They are pinned below as the *current* measured state; repairing
either edits `solspire/buyer_recon.py`, which is outside this workstream's owned
paths, so they are recorded as a proposed workstream rather than fixed. When they
are repaired, these pins must be re-pointed to the working contract.

Negative controls are included so a detector that returns a constant would be
caught: the auth pin is proven to fire without an identity and to pass with
one, and the ownership pin is proven to fire for a non-owner.
"""
from __future__ import annotations

import re
import time
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import solspire.buyer_recon as buyer_recon
import solspire.project_manager as project_manager
import solspire.workspace_manager as workspace_manager
from api.auth import require_auth
from solspire.console_router import router as console_router

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_TS = ROOT / "web/arkadia_console/src/components/opportunities/opportunityRadarContract.ts"
SURFACE_TS = ROOT / "web/arkadia_console/src/components/opportunities/ProjectOpportunityRadar.tsx"

OWNER = {"uid": "subject-owner", "access_level": 1}
OTHER = {"uid": "subject-other", "access_level": 1}

PROJECT_ROUTES = [
    ("GET", "/solspire/buyer-recon/projects/{project_id}"),
    ("POST", "/solspire/buyer-recon/projects/{project_id}/entries"),
    ("PATCH", "/solspire/buyer-recon/projects/{project_id}/entries/{entry_id}"),
]


@pytest.fixture()
def app(tmp_path, monkeypatch):
    """A composed console-router app with every store redirected into tmp_path."""
    db = tmp_path / "solspire_projects.db"
    monkeypatch.setattr(buyer_recon, "_DB_PATH", str(db))
    monkeypatch.setattr(project_manager, "_DB_PATH", str(db))
    monkeypatch.setattr(workspace_manager, "_DB_PATH", str(db))
    application = FastAPI()
    application.include_router(console_router)
    yield application
    application.dependency_overrides.clear()


def _client(app: FastAPI, user: dict | None) -> TestClient:
    """A client that surfaces an unhandled handler error as `500`, not as a raise.

    The defect pins below measure exactly that: the handler raises and the
    client observes a server error, which is what a real caller sees.
    """
    app.dependency_overrides.pop(require_auth, None)
    if user is not None:
        app.dependency_overrides[require_auth] = lambda: user
    return TestClient(app, raise_server_exceptions=False)


def _make_project(name: str, owner_uid: str) -> str:
    return project_manager.get_project_manager().create(name=name, owner_uid=owner_uid).id


def _seed_entry(board_id: str, subject_ref: str, prospect: str) -> str:
    """Insert a row through the store's own table so the read path can be exercised.

    The create *route* is broken (see the module docstring), so a seeded row is
    the only way to measure the read contract. Only NOT-NULL-without-default
    columns are supplied; the table defaults the rest, including `UNKNOWN`.
    """
    entry_id = f"seed-{prospect.lower().replace(' ', '-')}"
    with buyer_recon._db() as conn:
        conn.execute(
            """INSERT INTO buyer_recon_entries
               (id, board_id, subject_ref, prospect, status, evidence_status, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (entry_id, board_id, subject_ref, prospect, "REQUIREMENT_CAPTURED", "NONE", time.time(), time.time()),
        )
    return entry_id


# ---------------------------------------------------------------------------
# Route + auth matrix
# ---------------------------------------------------------------------------


def test_project_opportunity_routes_are_declared(app):
    """The composed app is the route oracle — `router.routes` holds include markers."""
    declared = set(app.openapi()["paths"])
    for _method, path in PROJECT_ROUTES:
        assert path in declared, f"{path} is not declared by the composed console router"


def test_project_routes_are_authenticated(app):
    unauthenticated = _client(app, None)
    for method, path in PROJECT_ROUTES:
        url = path.replace("{project_id}", "p1").replace("{entry_id}", "e1")
        response = unauthenticated.request(method, url, json={})
        assert response.status_code == 401, f"{method} {url} reached a handler without identity"


def test_negative_control_unauthenticated_read_is_actually_rejected(app):
    """Proves the auth detector fires rather than passing vacuously."""
    project_id = _make_project("Radar project", OWNER["uid"])
    response = _client(app, None).get(f"/solspire/buyer-recon/projects/{project_id}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_negative_control_the_identity_is_what_admits_the_read(app):
    """Same request, identity present → 200. The delta is the identity, not the path."""
    project_id = _make_project("Radar project", OWNER["uid"])
    assert _client(app, None).get(f"/solspire/buyer-recon/projects/{project_id}").status_code == 401
    assert _client(app, OWNER).get(f"/solspire/buyer-recon/projects/{project_id}").status_code == 200


# ---------------------------------------------------------------------------
# Read contract
# ---------------------------------------------------------------------------


def test_owner_reads_an_empty_board_with_the_declared_vocabulary(app):
    project_id = _make_project("Radar project", OWNER["uid"])
    response = _client(app, OWNER).get(f"/solspire/buyer-recon/projects/{project_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == project_id
    assert body["entries"] == []
    assert body["statuses"] == list(buyer_recon.STATUSES)
    assert body["persistence"]["project_binding"] is True
    assert body["persistence"]["subject_binding"] == "authenticated_firebase_uid"


def test_authority_block_declares_reconnaissance_only(app):
    """The contract states its own ceiling; the surface repeats it, never exceeds it."""
    project_id = _make_project("Radar project", OWNER["uid"])
    body = _client(app, OWNER).get(f"/solspire/buyer-recon/projects/{project_id}").json()
    assert body["authority"] == {
        "reconnaissance_only": True,
        "execution_authority": "NONE",
        "budget_authority": "NONE",
    }


def test_seeded_entry_reads_back_with_unverified_facts(app):
    project_id = _make_project("Radar project", OWNER["uid"])
    client = _client(app, OWNER)
    board = client.get(f"/solspire/buyer-recon/projects/{project_id}").json()["board"]
    _seed_entry(board["id"], OWNER["uid"], "Test Buyer")

    entries = client.get(f"/solspire/buyer-recon/projects/{project_id}").json()["entries"]
    assert [e["prospect"] for e in entries] == ["Test Buyer"]
    # Absent commercial facts carry the backend default, never a guess.
    assert entries[0]["buyer_price"] == "UNKNOWN"
    assert entries[0]["landed_cost"] == "UNKNOWN"
    assert entries[0]["expected_gross_margin"] == "UNKNOWN"


# ---------------------------------------------------------------------------
# Ownership boundary
# ---------------------------------------------------------------------------


def test_non_owner_cannot_read_a_project_board(app):
    project_id = _make_project("Radar project", OWNER["uid"])
    assert _client(app, OTHER).get(f"/solspire/buyer-recon/projects/{project_id}").status_code == 404


def test_unknown_project_resolves_to_not_found(app):
    """A missing project is an access result, not an empty radar."""
    assert _client(app, OWNER).get("/solspire/buyer-recon/projects/does-not-exist").status_code == 404


def test_project_board_is_a_distinct_scope_from_the_workspace_board(app):
    """The project board is keyed `{workspace}:project:{id}`, so its id is its own.

    Read in isolation, the project board is a distinct scope. The *coexistence*
    of the two scopes is the defect pinned below.
    """
    project_id = _make_project("Radar project", OWNER["uid"])
    client = _client(app, OWNER)
    project_board = client.get(f"/solspire/buyer-recon/projects/{project_id}").json()["board"]
    assert project_board["workspace_ref"].endswith(f":project:{project_id}")
    assert project_board["board_type"] == "eden_buyer_recon"
    assert project_board["lifecycle"] == "active"


def test_recorded_defect_project_and_workspace_board_cannot_coexist(app):
    """MEASURED DEFECT 2, pinned as current state — re-point when repaired.

    `buyer_recon_boards.subject_ref` is UNIQUE while the project board is keyed
    on the composite workspace ref, so the second scope read for one subject
    raises `IntegrityError` → HTTP 500. The workspace board is the natural first
    read, which makes the project radar unreachable for that subject.
    """
    project_id = _make_project("Radar project", OWNER["uid"])
    client = _client(app, OWNER)

    workspace_read = client.get("/solspire/buyer-recon")
    assert workspace_read.status_code == 200, "the workspace board read is the working path"

    project_read = client.get(f"/solspire/buyer-recon/projects/{project_id}")
    assert project_read.status_code == 500, "the project board read no longer resolves once a board exists"

    with buyer_recon._db() as conn:
        boards = conn.execute(
            "SELECT COUNT(*) FROM buyer_recon_boards WHERE subject_ref=?", (OWNER["uid"],)
        ).fetchone()[0]
    assert boards == 1, "only one board may exist per subject — that is the defect"


def test_recorded_defect_project_board_first_then_workspace_also_fails(app):
    """The collision is order-independent: either second read fails."""
    project_id = _make_project("Radar project", OWNER["uid"])
    client = _client(app, OWNER)
    assert client.get(f"/solspire/buyer-recon/projects/{project_id}").status_code == 200
    assert client.get("/solspire/buyer-recon").status_code == 500


# ---------------------------------------------------------------------------
# Recorded defect pin — the create path
# ---------------------------------------------------------------------------


def test_recorded_defect_create_entry_arity_mismatch(app):
    """MEASURED DEFECT, pinned as current state — re-point when repaired.

    `create_entry` passes 34 values into a 33-column table, so no prospect can be
    captured on any scope. Introduced at `5de6d476` (PR #199). Repairing it edits
    `solspire/buyer_recon.py`, which this workstream does not own.
    """
    source = (ROOT / "solspire/buyer_recon.py").read_text(encoding="utf-8")
    insert = re.search(r"INSERT INTO buyer_recon_entries\s*\n\s*VALUES \((.*?)\)\"\"\"", source, re.S)
    assert insert, "create_entry INSERT not found — the pin needs re-deriving"
    placeholders = insert.group(1).count("?")

    # Count the real table's columns, not a regex over the DDL.
    with buyer_recon._db() as conn:
        columns = len(conn.execute("PRAGMA table_info(buyer_recon_entries)").fetchall())
    assert placeholders == 34 and columns == 33, "the arity mismatch changed; re-point this pin"

    project_id = _make_project("Radar project", OWNER["uid"])
    response = _client(app, OWNER).post(
        f"/solspire/buyer-recon/projects/{project_id}/entries", json={"prospect": "Test Buyer"}
    )
    assert response.status_code == 500

    with buyer_recon._db() as conn:
        rows = conn.execute("SELECT COUNT(*) FROM buyer_recon_entries").fetchone()[0]
    assert rows == 0, "no entry may persist through the broken create path"


def test_recorded_defect_also_breaks_the_workspace_scope(app):
    """The same arity defect is shared by both scopes — it is one manager method."""
    response = _client(app, OWNER).post("/solspire/buyer-recon/entries", json={"prospect": "Test Buyer"})
    assert response.status_code == 500


# ---------------------------------------------------------------------------
# Frontend contract — source-level, matching this repo's console test style
# ---------------------------------------------------------------------------


def test_contract_module_declares_the_backend_paths():
    text = CONTRACT_TS.read_text(encoding="utf-8")
    assert 'const BASE = "/solspire/buyer-recon"' in text
    assert "/projects/${encodeURIComponent(projectId)}" in text
    assert "${projectBoardPath(projectId)}/entries" in text


def test_contract_module_supplies_the_read_path_the_landed_surface_consumes():
    """The landed surface takes a `readPath` prop; this module builds exactly that path.

    `ProjectOpportunityRadar.tsx` was landed by a concurrent commit at this path
    (read-only, prop-driven). It is kept byte-identical; the contract module is
    the complementary piece that resolves the project-scoped path for it.
    """
    surface = SURFACE_TS.read_text(encoding="utf-8")
    assert "readPath" in surface, "the landed surface is expected to be prop-driven"
    assert "projectBoardPath" in CONTRACT_TS.read_text(encoding="utf-8")


def test_landed_surface_uses_the_canonical_client_and_no_hardcoded_origin():
    surface = SURFACE_TS.read_text(encoding="utf-8")
    assert 'from "../../lib/apiClient"' in surface
    assert "apiRequest" in surface
    for forbidden in ("fetch(", "http://", "https://", "VITE_API_URL", "API_BASE"):
        assert forbidden not in surface, f"the surface must not resolve transport concerns ({forbidden})"


def test_contract_module_declares_the_backend_status_vocabulary():
    text = CONTRACT_TS.read_text(encoding="utf-8")
    for status in buyer_recon.STATUSES:
        assert f'"{status}"' in text, f"backend status {status} is missing from the contract module"


def test_landed_surface_renders_distinct_states_and_invents_no_commercial_facts():
    surface = SURFACE_TS.read_text(encoding="utf-8")
    # Distinct read states, not one collapsed error string.
    for state in ('kind: "loading"', 'kind: "auth"', 'kind: "unavailable"', 'kind: "error"', 'kind: "ready"'):
        assert state in surface, f"missing distinct state {state}"
    # Empty is stated as empty, never as success with fabricated rows.
    assert "No prospects recorded for this project yet" in surface
    # Authority is read from the response, never asserted as a success state.
    assert "authority.execution_authority" in surface
    assert "authority.budget_authority" in surface
    # No execute/spend surface and no invented commercial claims.
    for invented in ("BUYER_COMMITMENT_SIGNED", "budget_ngn", "contract_value", "revenue", "onClick={handleExecute"):
        assert invented not in surface, f"the surface must not imply transaction authority ({invented})"
