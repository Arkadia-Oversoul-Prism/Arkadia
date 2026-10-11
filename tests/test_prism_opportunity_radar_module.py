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
  | project + workspace board coexist              | **REPAIRED — was defect 2** |
  | project/workspace entry **create** (POST)      | **REPAIRED — was defect 1** |

**Defect 1 — entry create arity (REPAIRED).** `BuyerReconManager.create_entry`
was supplying 34 values to a 33-column `buyer_recon_entries` table. `create_entry`
now names its columns explicitly (`_ENTRY_COLUMNS`) so the arity cannot drift.
The pin below asserts the repair holds on a live create, on both scopes.

**Defect 2 — one board per subject (REPAIRED).** `buyer_recon_boards` declared
`subject_ref TEXT NOT NULL UNIQUE`, while `_project_board` keys the board by
`f"{workspace.id}:project:{project_id}"`. The unique constraint is now the
composite `(workspace_ref, subject_ref)`, so one subject may hold one workspace
board **and** one board per project. Existing databases are migrated in place by
`_migrate_boards`; the migration rebuilds the table transactionally, copying
every row, and is idempotent on an already-migrated database.

Both repairs are owned by this workstream under `SHARED-CONTRACTS.md` §1/§7.1.
The four former defect pins are re-pointed below to the repaired contract, and
the migration is measured explicitly (fresh vs. legacy schema) in
`tests/test_buyer_recon_board_contract.py`.

Negative controls are included so a detector that returns a constant would be
caught: the auth pin is proven to fire without an identity and to pass with
one, and the ownership pin is proven to fire for a non-owner.
"""
from __future__ import annotations

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
SECTION_TS = ROOT / "web/arkadia_console/src/components/opportunities/OpportunityRadarSection.tsx"
SOLSPIRE_PAGE_TS = ROOT / "web/arkadia_console/src/pages/SolSpirePage.tsx"

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
    """Insert a row through the store's own table to measure the read path.

    The read contract is exercised here with a row written directly and with the
    route-created row (`test_create_entry_persists_with_declared_arity`). Only
    NOT-NULL-without-default columns are supplied; the table defaults the rest,
    including `UNKNOWN`.
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

    Read in isolation, the project board is a distinct scope. Its *coexistence*
    with the workspace board for one subject is asserted separately.
    """
    project_id = _make_project("Radar project", OWNER["uid"])
    client = _client(app, OWNER)
    project_board = client.get(f"/solspire/buyer-recon/projects/{project_id}").json()["board"]
    assert project_board["workspace_ref"].endswith(f":project:{project_id}")
    assert project_board["board_type"] == "eden_buyer_recon"
    assert project_board["lifecycle"] == "active"


def test_workspace_and_project_board_coexist_for_one_subject(app):
    """REPAIRED DEFECT 2 — re-pointed from the prior defect pin.

    `buyer_recon_boards` no longer constrains `subject_ref` alone; the scope is
    the composite `(workspace_ref, subject_ref)`. One subject therefore holds its
    workspace board **and** a distinct board per project, in any read order.
    """
    project_id = _make_project("Radar project", OWNER["uid"])
    client = _client(app, OWNER)

    workspace_read = client.get("/solspire/buyer-recon")
    assert workspace_read.status_code == 200, "the workspace board read is the working path"

    project_read = client.get(f"/solspire/buyer-recon/projects/{project_id}")
    assert project_read.status_code == 200, "the project board must resolve alongside the workspace board"
    assert project_read.json()["board"]["id"] != workspace_read.json()["board"]["id"]

    with buyer_recon._db() as conn:
        boards = conn.execute(
            "SELECT COUNT(*) FROM buyer_recon_boards WHERE subject_ref=?", (OWNER["uid"],)
        ).fetchone()[0]
    assert boards == 2, "a subject holds one workspace board and one project board"


def test_workspace_board_first_then_project_board_also_coexists(app):
    """The repaired contract is order-independent: either read order succeeds."""
    project_id = _make_project("Radar project", OWNER["uid"])
    client = _client(app, OWNER)
    assert client.get(f"/solspire/buyer-recon/projects/{project_id}").status_code == 200
    assert client.get("/solspire/buyer-recon").status_code == 200


def test_two_project_boards_for_one_subject_are_distinct(app):
    """The composite scope is per-project, so a second project board is its own."""
    first = _make_project("Radar A", OWNER["uid"])
    second = _make_project("Radar B", OWNER["uid"])
    client = _client(app, OWNER)
    board_a = client.get(f"/solspire/buyer-recon/projects/{first}").json()["board"]
    board_b = client.get(f"/solspire/buyer-recon/projects/{second}").json()["board"]
    assert board_a["id"] != board_b["id"]
    assert board_a["workspace_ref"] != board_b["workspace_ref"]


# ---------------------------------------------------------------------------
# Repaired pin — the create path
# ---------------------------------------------------------------------------


def test_create_entry_persists_with_declared_arity(app):
    """REPAIRED DEFECT 1 — re-pointed from the prior defect pin.

    `create_entry` names its columns explicitly, so the value tuple and the table
    columns cannot drift. A create now returns `201` and the row reads back.
    """
    source = (ROOT / "solspire/buyer_recon.py").read_text(encoding="utf-8")
    # The insert names its columns; a bare `VALUES (?,?,…)` cannot be re-derived
    # from the source any more, which is exactly what the repair changed.
    assert "INSERT INTO buyer_recon_entries ({columns})" in source, "the insert must name its columns"
    assert "_ENTRY_COLUMNS" in source, "the column tuple must be derived from the dataclass"

    project_id = _make_project("Radar project", OWNER["uid"])
    response = _client(app, OWNER).post(
        f"/solspire/buyer-recon/projects/{project_id}/entries", json={"prospect": "Test Buyer"}
    )
    assert response.status_code == 201, response.text

    with buyer_recon._db() as conn:
        rows = conn.execute("SELECT COUNT(*) FROM buyer_recon_entries").fetchone()[0]
    assert rows == 1, "the created entry must persist"


def test_create_entry_works_on_the_workspace_scope_too(app):
    """The arity repair is shared by both scopes — it is one manager method."""
    response = _client(app, OWNER).post("/solspire/buyer-recon/entries", json={"prospect": "Test Buyer"})
    assert response.status_code == 201, response.text
    assert response.json()["entry"]["prospect"] == "Test Buyer"


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


# ---------------------------------------------------------------------------
# Projects-surface mount — source-level, matching this repo's console style
# ---------------------------------------------------------------------------


def test_mount_section_selects_a_project_and_delegates_the_read():
    """The section owns selection; the landed surface owns the read states."""
    section = SECTION_TS.read_text(encoding="utf-8")
    assert "<ProjectOpportunityRadar readPath={projectBoardPath(selected)} />" in section, (
        "the section must delegate the read to the landed surface with a derived path"
    )
    assert 'import { projectBoardPath } from "./opportunityRadarContract";' in section
    assert "projects.map((project) => (" in section, "options must come from the returned projects, never a fixed id"


def test_mount_section_invents_no_project_or_commercial_fact():
    section = SECTION_TS.read_text(encoding="utf-8")
    # No transport of its own; the path comes from the contract module's helper.
    for forbidden in ("fetch(", "http://", "https://", "VITE_API_URL", "API_BASE"):
        assert forbidden not in section, f"the section must not resolve transport ({forbidden})"
    assert "readPath={" in section, "the section must hand the landed surface a derived path"
    # No execute/spend control and no invented commercial claim.
    for invented in ("budget_ngn", "contract_value", "revenue", "onClick={handleExecute"):
        assert invented not in section, f"the section must not imply transaction authority ({invented})"


def test_mount_section_states_an_empty_project_list_honestly():
    section = SECTION_TS.read_text(encoding="utf-8")
    assert "No projects exist in this workspace yet" in section
    assert "This is not an empty" in section, "an empty project list must not read as an empty opportunity board"


def test_projects_surface_mounts_the_opportunity_radar_section():
    """The Projects surface (SolSpire, inventory Slice D) renders the section.

    The section only renders once the project list is `ready`, so a failed list
    read cannot be presented as an empty opportunity board.
    """
    page = SOLSPIRE_PAGE_TS.read_text(encoding="utf-8")
    assert "import { OpportunityRadarSection }" in page
    assert "<OpportunityRadarSection projects={projects.data.projects} />" in page
    assert 'projects.state === "ready" && projects.data' in page


def test_negative_control_the_mount_pins_are_not_vacuous():
    """Prove the mount detectors fail on the pre-mount page text."""
    pre_mount = 'import { Page } from "../components/ui";\nexport function SolSpirePage() { return null; }\n'
    assert "OpportunityRadarSection" not in pre_mount
    assert "readPath={projectBoardPath(selected)}" not in pre_mount
    assert "No projects exist in this workspace yet" not in pre_mount

