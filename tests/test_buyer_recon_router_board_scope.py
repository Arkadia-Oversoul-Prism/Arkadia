"""Buyer Recon router — board-scope isolation between the workspace and project write routes.

`SHARED-CONTRACTS.md` §1/§7.1 grants Workstream 2 scoped ownership of
`solspire/buyer_recon_router.py` for the measured board-scope defect class.

Defect 3 (measured after defect 2's repair): once one subject can hold both a
workspace board and a project board, `PATCH /solspire/buyer-recon/entries/{id}`
scoped the write by *subject alone*, so an owner's workspace request could read
and mutate an entry on one of their project boards. The project route already
guarded this; the workspace route did not.

The guard is the board id carried into the transaction. A post-write comparison
would be unsound — the manager commits before returning — so the property is
asserted on *persisted state*, not on the response alone. Negative controls
accompany each direction: the same-board write must still succeed.
"""
from __future__ import annotations

import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import solspire.buyer_recon as buyer_recon
import solspire.project_manager as project_manager
import solspire.workspace_manager as workspace_manager
from api.auth import require_auth
from solspire.console_router import router as console_router

OWNER = {"uid": "scope-owner", "access_level": 1}
OTHER = {"uid": "scope-other", "access_level": 1}

WORKSPACE_ENTRIES = "/solspire/buyer-recon/entries"
WORKSPACE_ENTRY = "/solspire/buyer-recon/entries/{entry_id}"


@pytest.fixture()
def app(tmp_path, monkeypatch):
    db = tmp_path / "solspire_projects.db"
    monkeypatch.setattr(buyer_recon, "_DB_PATH", str(db))
    monkeypatch.setattr(project_manager, "_DB_PATH", str(db))
    monkeypatch.setattr(workspace_manager, "_DB_PATH", str(db))
    application = FastAPI()
    application.include_router(console_router)
    yield application
    application.dependency_overrides.clear()


def _client(app: FastAPI, user: dict | None) -> TestClient:
    app.dependency_overrides.pop(require_auth, None)
    if user is not None:
        app.dependency_overrides[require_auth] = lambda: user
    return TestClient(app, raise_server_exceptions=False)


def _persisted_notes(entry_id: str) -> str:
    """Read the row straight from the store — the write is what matters, not the reply."""
    with buyer_recon._db() as conn:
        row = conn.execute(
            "SELECT notes FROM buyer_recon_entries WHERE id=?", (entry_id,)
        ).fetchone()
    return row["notes"]


def _project_entry(app: FastAPI, owner: dict) -> tuple[str, str]:
    project_id = project_manager.get_project_manager().create(name="Scope", owner_uid=owner["uid"]).id
    created = _client(app, owner).post(
        f"/solspire/buyer-recon/projects/{project_id}/entries", json={"prospect": "Buyer A"}
    )
    assert created.status_code == 201, created.text
    return project_id, created.json()["entry"]["id"]


def _workspace_entry(app: FastAPI, owner: dict) -> str:
    created = _client(app, owner).post(WORKSPACE_ENTRIES, json={"prospect": "Buyer W"})
    assert created.status_code == 201, created.text
    return created.json()["entry"]["id"]


# ---------------------------------------------------------------------------
# The workspace route must not reach a project-board entry
# ---------------------------------------------------------------------------


def test_workspace_patch_cannot_mutate_a_project_board_entry(app):
    """REPAIRED DEFECT 3 — the workspace route is scoped to the workspace board."""
    _project_id, entry_id = _project_entry(app, OWNER)
    response = _client(app, OWNER).patch(
        WORKSPACE_ENTRY.format(entry_id=entry_id), json={"notes": "MUTATED-FROM-WORKSPACE"}
    )
    assert response.status_code == 404, response.text
    # The response alone is not enough: assert the store was not written.
    assert _persisted_notes(entry_id) == "", "a cross-board write reached the row despite the refusal"
    assert _persisted_notes(entry_id) != "MUTATED-FROM-WORKSPACE"


def test_workspace_patch_leaves_a_project_entry_readable_after_refusal(app):
    """A refused cross-board write is not a side-effect read either."""
    project_id, entry_id = _project_entry(app, OWNER)
    client = _client(app, OWNER)
    assert client.patch(
        WORKSPACE_ENTRY.format(entry_id=entry_id), json={"notes": "x"}
    ).status_code == 404
    entries = client.get(f"/solspire/buyer-recon/projects/{project_id}").json()["entries"]
    assert [e["id"] for e in entries] == [entry_id]
    assert entries[0]["notes"] == ""


# ---------------------------------------------------------------------------
# Negative controls — the same-board write must still work, both directions
# ---------------------------------------------------------------------------


def test_control_workspace_patch_still_writes_its_own_board(app):
    """The narrowing must not break the working path it guards."""
    entry_id = _workspace_entry(app, OWNER)
    response = _client(app, OWNER).patch(
        WORKSPACE_ENTRY.format(entry_id=entry_id), json={"notes": "ws-ok"}
    )
    assert response.status_code == 200, response.text
    assert _persisted_notes(entry_id) == "ws-ok"


def test_control_project_patch_still_writes_its_own_board(app):
    project_id, entry_id = _project_entry(app, OWNER)
    response = _client(app, OWNER).patch(
        f"/solspire/buyer-recon/projects/{project_id}/entries/{entry_id}",
        json={"notes": "proj-ok"},
    )
    assert response.status_code == 200, response.text
    assert _persisted_notes(entry_id) == "proj-ok"


def test_control_project_route_cannot_reach_a_workspace_board_entry(app):
    """The mirror direction: the project route is scoped to its project board."""
    project_id = project_manager.get_project_manager().create(name="Scope", owner_uid=OWNER["uid"]).id
    entry_id = _workspace_entry(app, OWNER)
    response = _client(app, OWNER).patch(
        f"/solspire/buyer-recon/projects/{project_id}/entries/{entry_id}", json={"notes": "cross"}
    )
    assert response.status_code == 404, response.text
    assert _persisted_notes(entry_id) == ""


# ---------------------------------------------------------------------------
# The guard is a real detector — the pre-repair form must fail these tests
# ---------------------------------------------------------------------------


def test_negative_control_a_subject_wide_write_reaches_the_wrong_board(app):
    """Proves the detector can see the defect it claims to.

    Called against the *manager* with no board id (the pre-repair call shape the
    workspace route used), the same subject-wide write reaches the project entry.
    If this ever stops reproducing, the tests above are measuring nothing.
    """
    _project_id, entry_id = _project_entry(app, OWNER)
    buyer_recon.get_buyer_recon_manager().update_entry(
        entry_id, OWNER["uid"], {"notes": "SUBJECT-WIDE"}
    )
    assert _persisted_notes(entry_id) == "SUBJECT-WIDE"

    # ... and the workspace route, which now passes its board id, does not.
    other_id = None
    created = _client(app, OWNER).post(WORKSPACE_ENTRIES, json={"prospect": "Buyer W"})
    assert created.status_code == 201, created.text
    other_id = created.json()["entry"]["id"]
    refused = _client(app, OWNER).patch(
        WORKSPACE_ENTRY.format(entry_id=entry_id), json={"notes": "MUTATED-FROM-WORKSPACE"}
    )
    assert refused.status_code == 404
    assert _persisted_notes(entry_id) == "SUBJECT-WIDE", "the route must not have written"
    assert other_id != entry_id


def test_routes_pass_a_board_id_into_the_manager(app):
    """The isolation is the board id at the call sites, not a post-hoc comparison."""
    import inspect

    import solspire.buyer_recon_router as router_module

    source = inspect.getsource(router_module.update_buyer_recon_entry)
    project_source = inspect.getsource(router_module.update_project_buyer_recon_entry)
    for text in (source, project_source):
        assert "board.id" in text, "the route must narrow the write to its own board"
        assert "update_entry(" in text

    # The manager honours the parameter inside the transaction.
    manager_source = inspect.getsource(buyer_recon.BuyerReconManager.update_entry)
    assert "board_id=?" in manager_source, "the scope must be part of the SQL, not a later comparison"
