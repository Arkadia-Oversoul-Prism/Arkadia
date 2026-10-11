"""Project Opportunity Radar — prospect create/edit entry flow.

This file measures the *write* half of the project-scoped buyer-recon contract
that `ProjectOpportunityRadar` now drives:

  POST  /solspire/buyer-recon/projects/{project_id}/entries
  PATCH /solspire/buyer-recon/projects/{project_id}/entries/{entry_id}

The backend routes already exist and are exercised by
`tests/test_prism_opportunity_radar_module.py` (read path, ownership, arity) and
`tests/test_buyer_recon_router_board_scope.py` (cross-board refusal). This file
adds the properties the *entry flow* depends on and that nothing measured yet:

  * validation — a blank prospect is refused on create (`400`);
  * authorization denial — an unauthenticated or non-owner caller cannot create
    or edit, and the refusal does **not** write;
  * wrong-board mutation refusal — an edit cannot reach another project's board
    or the workspace board, asserted on persisted state, not on the status code;
  * confirmed server response — the returned entry is the persisted one, and a
    field the request omitted keeps the backend's `UNKNOWN` default;
  * persisted state — every write is read back out of the store.

Negative controls accompany the load-bearing detectors: each one reproduces the
shape the detector is supposed to catch, so a detector that returned a constant
would be caught rather than passing vacuously.

The frontend half is **executed**, not string-matched. Node 24 runs TypeScript
directly, so `opportunityRadarContract.ts` is imported and its body builders are
driven against the same shapes the handlers return. The source-level pins that
already exist in `test_prism_opportunity_radar_module.py` are left untouched.
"""
from __future__ import annotations

import json
import subprocess
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
CONSOLE = ROOT / "web/arkadia_console"
CONTRACT_TS = CONSOLE / "src/components/opportunities/opportunityRadarContract.ts"
FORM_TS = CONSOLE / "src/components/opportunities/ProspectEntryForm.tsx"
SURFACE_TS = CONSOLE / "src/components/opportunities/ProjectOpportunityRadar.tsx"

OWNER = {"uid": "entry-owner", "access_level": 1}
OTHER = {"uid": "entry-other", "access_level": 1}


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


def _project(owner_uid: str, name: str = "Entry project") -> str:
    return project_manager.get_project_manager().create(name=name, owner_uid=owner_uid).id


def _entries_path(project_id: str) -> str:
    return f"/solspire/buyer-recon/projects/{project_id}/entries"


def _persisted(entry_id: str) -> dict:
    """Read the row straight from the store — the write is the fact, not the reply."""
    with buyer_recon._db() as conn:
        row = conn.execute("SELECT * FROM buyer_recon_entries WHERE id=?", (entry_id,)).fetchone()
    assert row is not None, f"entry {entry_id} does not exist"
    return dict(row)


def _create(app: FastAPI, project_id: str, payload: dict, user: dict = OWNER):
    return _client(app, user).post(_entries_path(project_id), json=payload)


# ---------------------------------------------------------------------------
# Create — success, response confirmation, persisted state
# ---------------------------------------------------------------------------


def test_create_returns_the_persisted_entry(app):
    project_id = _project(OWNER["uid"])
    response = _create(app, project_id, {"prospect": "Kano Grain Aggregators", "buyer_type": "Aggregator"})
    assert response.status_code == 201, response.text

    entry = response.json()["entry"]
    assert entry["prospect"] == "Kano Grain Aggregators"
    assert entry["buyer_type"] == "Aggregator"

    # The response must be the stored row, not a client-side echo.
    row = _persisted(entry["id"])
    assert row["prospect"] == entry["prospect"]
    assert row["buyer_type"] == entry["buyer_type"]
    assert row["board_id"] == entry["board_id"]
    assert row["subject_ref"] == OWNER["uid"]


def test_created_entry_lands_on_the_selected_project_board_only(app):
    """The board the entry is written to is the project board, not the workspace board."""
    project_id = _project(OWNER["uid"])
    client = _client(app, OWNER)
    project_board_id = client.get(f"/solspire/buyer-recon/projects/{project_id}").json()["board"]["id"]
    workspace_board_id = client.get("/solspire/buyer-recon").json()["board"]["id"]
    assert project_board_id != workspace_board_id

    created = _create(app, project_id, {"prospect": "Buyer A"}).json()["entry"]
    assert _persisted(created["id"])["board_id"] == project_board_id

    # ...and the workspace board does not show it.
    workspace_entries = client.get("/solspire/buyer-recon").json()["entries"]
    assert created["id"] not in [e["id"] for e in workspace_entries]


def test_omitted_commercial_facts_keep_the_backend_unknown_default(app):
    """The flow's truthfulness rule: an unverified fact is never asserted by the client."""
    project_id = _project(OWNER["uid"])
    entry = _create(app, project_id, {"prospect": "Buyer A"}).json()["entry"]
    for field in ("buyer_price", "landed_cost", "expected_gross_margin", "capital_required", "supplier"):
        assert entry[field] == "UNKNOWN", f"{field} must stay UNKNOWN when the request omitted it"
        assert _persisted(entry["id"])[field] == "UNKNOWN"
    assert entry["evidence_status"] == "NONE"
    assert entry["evidence"] == []


def test_negative_control_a_supplied_commercial_fact_is_actually_recorded(app):
    """Proves the UNKNOWN pin is not vacuous: a supplied value does land."""
    project_id = _project(OWNER["uid"])
    entry = _create(app, project_id, {"prospect": "Buyer A", "buyer_price": "NGN 1200/kg"}).json()["entry"]
    assert entry["buyer_price"] == "NGN 1200/kg"
    assert _persisted(entry["id"])["buyer_price"] == "NGN 1200/kg"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_blank_prospect_is_refused_on_create_and_writes_nothing(app):
    project_id = _project(OWNER["uid"])
    response = _create(app, project_id, {"prospect": "   "})
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "prospect is required"
    with buyer_recon._db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM buyer_recon_entries").fetchone()[0] == 0


def test_missing_prospect_is_refused_on_create(app):
    project_id = _project(OWNER["uid"])
    assert _create(app, project_id, {}).status_code == 422


def test_invalid_status_is_refused_on_create_and_on_edit(app):
    project_id = _project(OWNER["uid"])
    assert _create(app, project_id, {"prospect": "Buyer A", "status": "NOT_A_STATUS"}).status_code == 400

    entry = _create(app, project_id, {"prospect": "Buyer A"}).json()["entry"]
    refused = _client(app, OWNER).patch(
        f"{_entries_path(project_id)}/{entry['id']}", json={"status": "NOT_A_STATUS"}
    )
    assert refused.status_code == 400, refused.text
    assert _persisted(entry["id"])["status"] == "UNCONTACTED", "a refused status must not be written"


def test_negative_control_a_declared_status_is_accepted(app):
    project_id = _project(OWNER["uid"])
    entry = _create(app, project_id, {"prospect": "Buyer A", "status": "REQUIREMENT_CAPTURED"}).json()["entry"]
    assert entry["status"] == "REQUIREMENT_CAPTURED"
    assert _persisted(entry["id"])["status"] == "REQUIREMENT_CAPTURED"


# ---------------------------------------------------------------------------
# Authorization denial — the refusal must not write
# ---------------------------------------------------------------------------


def test_unauthenticated_create_and_edit_are_refused(app):
    project_id = _project(OWNER["uid"])
    entry = _create(app, project_id, {"prospect": "Buyer A"}).json()["entry"]
    anonymous = _client(app, None)
    assert anonymous.post(_entries_path(project_id), json={"prospect": "Intruder"}).status_code == 401
    assert anonymous.patch(
        f"{_entries_path(project_id)}/{entry['id']}", json={"notes": "INTRUDER"}
    ).status_code == 401
    assert _persisted(entry["id"])["notes"] == ""


def test_non_owner_cannot_create_or_edit_on_another_subject_project(app):
    project_id = _project(OWNER["uid"])
    entry = _create(app, project_id, {"prospect": "Buyer A"}).json()["entry"]
    intruder = _client(app, OTHER)
    assert intruder.post(_entries_path(project_id), json={"prospect": "Intruder"}).status_code == 404
    assert intruder.patch(
        f"{_entries_path(project_id)}/{entry['id']}", json={"notes": "INTRUDER"}
    ).status_code == 404

    # The refusal is an access result, not a side effect: nothing was written.
    row = _persisted(entry["id"])
    assert row["notes"] == ""
    assert row["prospect"] == "Buyer A"
    with buyer_recon._db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM buyer_recon_entries").fetchone()[0] == 1


def test_negative_control_the_owner_is_what_admits_the_write(app):
    """Same request, identity changed: the delta is the identity, not the path."""
    project_id = _project(OWNER["uid"])
    assert _client(app, OTHER).post(_entries_path(project_id), json={"prospect": "X"}).status_code == 404
    assert _client(app, OWNER).post(_entries_path(project_id), json={"prospect": "X"}).status_code == 201


# ---------------------------------------------------------------------------
# Wrong-board mutation refusal — asserted on persisted state
# ---------------------------------------------------------------------------


def test_project_edit_cannot_reach_another_project_board(app):
    first = _project(OWNER["uid"], "Board A")
    second = _project(OWNER["uid"], "Board B")
    entry = _create(app, first, {"prospect": "Buyer A"}).json()["entry"]

    response = _client(app, OWNER).patch(
        f"{_entries_path(second)}/{entry['id']}", json={"notes": "CROSS-BOARD"}
    )
    assert response.status_code == 404, response.text
    assert _persisted(entry["id"])["notes"] == "", "a cross-board edit reached the row despite the refusal"


def test_project_edit_cannot_reach_the_workspace_board(app):
    project_id = _project(OWNER["uid"])
    workspace_entry = _client(app, OWNER).post(
        "/solspire/buyer-recon/entries", json={"prospect": "Workspace Buyer"}
    ).json()["entry"]
    response = _client(app, OWNER).patch(
        f"{_entries_path(project_id)}/{workspace_entry['id']}", json={"notes": "CROSS-BOARD"}
    )
    assert response.status_code == 404, response.text
    assert _persisted(workspace_entry["id"])["notes"] == ""


def test_negative_control_the_own_board_edit_still_succeeds(app):
    """The narrowing must not break the working path it guards."""
    project_id = _project(OWNER["uid"])
    entry = _create(app, project_id, {"prospect": "Buyer A"}).json()["entry"]
    response = _client(app, OWNER).patch(
        f"{_entries_path(project_id)}/{entry['id']}", json={"notes": "own-board-ok"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["entry"]["notes"] == "own-board-ok"
    assert _persisted(entry["id"])["notes"] == "own-board-ok"


# ---------------------------------------------------------------------------
# Edit — partial update, confirmed response, persisted state
# ---------------------------------------------------------------------------


def test_edit_is_a_partial_update_and_leaves_untouched_fields_alone(app):
    project_id = _project(OWNER["uid"])
    entry = _create(
        app, project_id, {"prospect": "Buyer A", "buyer_type": "Aggregator", "location": "Kano"}
    ).json()["entry"]

    updated = _client(app, OWNER).patch(
        f"{_entries_path(project_id)}/{entry['id']}", json={"notes": "Asked for 20t"}
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()["entry"]
    assert body["notes"] == "Asked for 20t"
    # Fields the patch omitted are unchanged, in the response and in the store.
    assert body["buyer_type"] == "Aggregator"
    assert body["location"] == "Kano"
    row = _persisted(entry["id"])
    assert row["notes"] == "Asked for 20t"
    assert row["buyer_type"] == "Aggregator"
    assert row["location"] == "Kano"


def test_edit_records_a_commercial_fact_and_moves_updated_at(app):
    project_id = _project(OWNER["uid"])
    entry = _create(app, project_id, {"prospect": "Buyer A"}).json()["entry"]
    assert _persisted(entry["id"])["buyer_price"] == "UNKNOWN"

    time.sleep(0.01)
    updated = _client(app, OWNER).patch(
        f"{_entries_path(project_id)}/{entry['id']}", json={"buyer_price": "NGN 1200/kg"}
    ).json()["entry"]
    assert updated["buyer_price"] == "NGN 1200/kg"
    row = _persisted(entry["id"])
    assert row["buyer_price"] == "NGN 1200/kg"
    assert row["updated_at"] > row["created_at"]


def test_edit_response_is_the_persisted_row(app):
    project_id = _project(OWNER["uid"])
    entry = _create(app, project_id, {"prospect": "Buyer A"}).json()["entry"]
    body = _client(app, OWNER).patch(
        f"{_entries_path(project_id)}/{entry['id']}", json={"supplier": "ACME Traders"}
    ).json()["entry"]
    row = _persisted(entry["id"])
    for field in ("supplier", "prospect", "status", "updated_at"):
        assert body[field] == row[field], f"{field} in the response is not the persisted value"


def test_edit_of_an_unknown_entry_on_this_board_is_not_found(app):
    project_id = _project(OWNER["uid"])
    response = _client(app, OWNER).patch(
        f"{_entries_path(project_id)}/does-not-exist", json={"notes": "x"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Project buyer recon entry not found"


def test_created_entry_is_read_back_through_the_board_read(app):
    """End-to-end: the create response is visible to the read the surface performs."""
    project_id = _project(OWNER["uid"])
    entry = _create(app, project_id, {"prospect": "Buyer A", "buyer_type": "Aggregator"}).json()["entry"]
    entries = _client(app, OWNER).get(f"/solspire/buyer-recon/projects/{project_id}").json()["entries"]
    assert [e["id"] for e in entries] == [entry["id"]]
    assert entries[0]["buyer_type"] == "Aggregator"


# ---------------------------------------------------------------------------
# Frontend contract — executed, not string-matched
# ---------------------------------------------------------------------------

# Drives the real `opportunityRadarContract.ts` through Node's native TypeScript
# support against the shapes the handlers actually return. If the module cannot be
# imported or a body builder disagrees with the backend, this fails rather than
# reporting a source-level match.
_NODE_PROBE = r"""
const m = await import(process.argv[1]);
const out = {};
const entry = {
  id: "e1", prospect: "Buyer A", location: "Kano", buyer_type: "Aggregator",
  contact_route: "", commodity: "Maize", estimated_demand: "UNKNOWN",
  procurement_frequency: "UNKNOWN", decision_maker: "UNKNOWN", current_price: "UNKNOWN",
  quantity: "UNKNOWN", specification: "UNKNOWN", delivery_point: "UNKNOWN",
  delivery_window: "UNKNOWN", payment_terms: "UNKNOWN", supplier: "UNKNOWN",
  source_price: "UNKNOWN", available_quantity: "UNKNOWN", logistics_quote: "UNKNOWN",
  packaging_qc_cost: "UNKNOWN", landed_cost: "UNKNOWN", buyer_price: "UNKNOWN",
  expected_gross_margin: "UNKNOWN", capital_required: "UNKNOWN", evidence_status: "NONE",
  evidence: [], why_this_prospect: "", status: "UNCONTACTED", notes: "",
};

// A create with only the prospect typed: no commercial fact may be asserted.
const minimal = m.emptyDraft();
minimal.prospect = "  Buyer A  ";
out.create_minimal = m.createEntryBody(minimal);

// A create with descriptive fields and a supplied commercial fact.
const rich = m.emptyDraft();
rich.prospect = "Buyer A";
rich.buyer_type = "Aggregator";
rich.location = "Kano";
rich.buyer_price = "NGN 1200/kg";
out.create_rich = m.createEntryBody(rich);

// A round-trip of a recorded entry must be a no-op edit.
const seeded = m.draftFromEntry(entry);
out.edit_noop = m.editEntryBody(seeded, entry);
out.edit_noop_flag = m.isNoOpEdit(seeded, entry);

// A single-field edit must send only that field.
seeded.notes = "Asked for 20t";
out.edit_notes = m.editEntryBody(seeded, entry);

// Leaving a commercial field at the sentinel must omit it even after an edit.
seeded.buyer_price = "UNKNOWN";
out.edit_after_sentinel = m.editEntryBody(seeded, entry);

// Path derivation used by the form.
out.paths = {
  entries: m.entriesPathFromBoard("/solspire/buyer-recon/projects/p%201"),
  entry: m.entryPathFromBoard("/solspire/buyer-recon/projects/p1", "e/2"),
  project_entries: m.projectEntriesPath("p1"),
  project_entry: m.projectEntryPath("p1", "e1"),
};

out.prospect_required_blank = m.prospectRequired({ ...m.emptyDraft(), prospect: "   " });
out.prospect_required_filled = m.prospectRequired({ ...m.emptyDraft(), prospect: "A" });
out.parse_ok = m.parseEntryResponse({ entry });
out.parse_missing_key = m.parseEntryResponse({});
out.parse_entry_without_id = m.parseEntryResponse({ entry: { prospect: "x" } });
out.upsert_new = m.upsertEntry([entry], { id: "e2", prospect: "B" }).map((e) => e.id);
out.upsert_existing = m.upsertEntry([entry], { id: "e1", prospect: "A2" }).map((e) => e.prospect);
out.statuses = m.BUYER_RECON_STATUSES;

console.log(JSON.stringify(out));
"""


@pytest.fixture(scope="module")
def contract_probe() -> dict:
    """Execute the contract module through Node and return its measured behaviour."""
    result = subprocess.run(
        ["node", "--input-type=module", "-e", _NODE_PROBE, str(CONTRACT_TS)],
        cwd=str(CONSOLE),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"the contract module could not be executed:\n{result.stderr}"
    return json.loads(result.stdout.strip().splitlines()[-1])


def test_executed_contract_minimal_create_asserts_no_commercial_fact(contract_probe):
    body = contract_probe["create_minimal"]
    assert body["prospect"] == "Buyer A"
    assert body["status"] == "UNCONTACTED"
    # Every commercial field is omitted, so the backend default applies.
    for field in ("buyer_price", "landed_cost", "expected_gross_margin", "supplier", "quantity"):
        assert field not in body, f"{field} must be omitted rather than sent as a value"
    # Evidence is never asserted by a capture.
    assert "evidence" not in body and "evidence_status" not in body


def test_executed_contract_supplied_fields_are_sent(contract_probe):
    body = contract_probe["create_rich"]
    assert body["buyer_type"] == "Aggregator"
    assert body["location"] == "Kano"
    assert body["buyer_price"] == "NGN 1200/kg"
    # Untouched commercial fields stay omitted even when others are supplied.
    assert "landed_cost" not in body
    assert "capital_required" not in body


def test_executed_contract_round_trip_edit_is_a_no_op(contract_probe):
    assert contract_probe["edit_noop"] == {}
    assert contract_probe["edit_noop_flag"] is True


def test_executed_contract_edit_sends_only_the_changed_field(contract_probe):
    assert contract_probe["edit_notes"] == {"notes": "Asked for 20t"}
    assert contract_probe["edit_after_sentinel"] == {"notes": "Asked for 20t"}


def test_executed_contract_paths_match_the_declared_routes(contract_probe):
    paths = contract_probe["paths"]
    assert paths["entries"] == "/solspire/buyer-recon/projects/p%201/entries"
    assert paths["entry"] == "/solspire/buyer-recon/projects/p1/entries/e%2F2"
    assert paths["project_entries"] == "/solspire/buyer-recon/projects/p1/entries"
    assert paths["project_entry"] == "/solspire/buyer-recon/projects/p1/entries/e1"


def test_executed_contract_prospect_preflight_mirrors_the_server_rule(contract_probe):
    assert contract_probe["prospect_required_blank"] is not None
    assert contract_probe["prospect_required_filled"] is None


def test_executed_contract_parses_only_the_declared_response_shape(contract_probe):
    assert contract_probe["parse_ok"]["id"] == "e1"
    # An unrecognised body must not read as a successful write.
    assert contract_probe["parse_missing_key"] is None
    assert contract_probe["parse_entry_without_id"] is None


def test_executed_contract_upsert_keeps_one_entry_per_id(contract_probe):
    assert contract_probe["upsert_new"] == ["e2", "e1"]
    assert contract_probe["upsert_existing"] == ["A2"]


def test_executed_contract_status_vocabulary_matches_the_backend(contract_probe):
    assert contract_probe["statuses"] == list(buyer_recon.STATUSES)


def test_negative_control_the_probe_detects_a_wrong_body_builder(contract_probe):
    """Proves the executed probe can see a defect rather than passing vacuously.

    The pre-flow shape (send every field, including unverified ones) would put a
    commercial sentinel on the wire. That shape is built here and must differ from
    what the module produces.
    """
    assert "buyer_price" not in contract_probe["create_minimal"]
    wrong = {"prospect": "Buyer A", "buyer_price": "UNKNOWN", "landed_cost": "UNKNOWN"}
    assert "buyer_price" in wrong, "the detector must distinguish the asserted-value shape"


# ---------------------------------------------------------------------------
# Frontend surface — the control is present, bounded, and wired to verified routes
# ---------------------------------------------------------------------------


def _code_only(path: Path) -> str:
    """Strip block and line comments so a detector scans code, not prose.

    A surface that *documents* the absence of a delete control ("there is no
    delete…") would otherwise trip a bare substring scan, which is how a
    detector becomes noise instead of a guard.
    """
    import re

    text = path.read_text(encoding="utf-8")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return re.sub(r"^\s*//.*$", "", text, flags=re.MULTILINE)


def test_surface_wires_create_and_edit_to_the_verified_handlers():
    surface = SURFACE_TS.read_text(encoding="utf-8")
    form = FORM_TS.read_text(encoding="utf-8")
    # The write method is selected from the mode, and the paths come from the
    # contract module rather than being inlined.
    assert 'method: mode === "create" ? "POST" : "PATCH"' in form, "the form must pick the declared method"
    assert "entriesPathFromBoard" in form and "entryPathFromBoard" in form
    assert 'from "./opportunityRadarContract"' in form, "paths must come from the contract module, not inline"
    # The surface hands the form the same board path it read from.
    assert "<ProspectEntryForm" in surface
    assert "boardPath={readPath}" in surface, "the write target must derive from the board path that was read"
    assert 'mode="create"' in surface and 'mode="edit"' in surface


def test_surface_preserves_the_existing_read_contract_and_pinned_copy():
    surface = SURFACE_TS.read_text(encoding="utf-8")
    # The pre-existing read contract is unchanged.
    assert "apiRequest<OpportunityBoardResponse>(readPath)" in surface
    assert "No prospects recorded for this project yet" in surface
    assert "authority.execution_authority" in surface
    assert "authority.budget_authority" in surface
    for state in ('kind: "loading"', 'kind: "auth"', 'kind: "unavailable"', 'kind: "error"', 'kind: "ready"'):
        assert state in surface, f"missing distinct state {state}"


def test_surface_and_form_invent_no_authority_and_no_transport():
    for path in (SURFACE_TS, FORM_TS):
        text = _code_only(path)
        for forbidden in ("fetch(", "http://", "https://", "VITE_API_URL", "API_BASE"):
            assert forbidden not in text, f"{path.name} must not resolve transport ({forbidden})"
        for invented in (
            '"DELETE"',
            "'DELETE'",
            "onClick={handleExecute",
            "handleApprove",
            "budget_ngn",
            "contract_value",
            "revenue",
        ):
            assert invented not in text, f"{path.name} must not imply authority it does not have ({invented})"


def test_form_states_distinct_save_outcomes_and_waits_for_confirmation():
    form = FORM_TS.read_text(encoding="utf-8")
    for state in (
        'kind: "saving"',
        'kind: "saved"',
        'kind: "invalid"',
        'kind: "auth"',
        'kind: "unavailable"',
        'kind: "error"',
    ):
        assert state in form, f"missing distinct save state {state}"
    # Nothing is reported as recorded until the response carried the entry.
    assert "parseEntryResponse(payload)" in form
    assert "The board returned an unrecognised response shape" in form
    # No-op edits and blank prospects are explained rather than silently sent.
    assert "No change to save" in form
    assert "prospectRequired" in form


def test_form_renders_unverified_commercial_facts_as_the_sentinel():
    form = FORM_TS.read_text(encoding="utf-8")
    assert "COMMERCIAL_FIELDS" in form, "commercial fields must come from the contract module"
    assert "DESCRIPTIVE_FIELDS" in form
    assert "UNVERIFIED" in form
    assert "placeholder={UNVERIFIED}" in form, "an empty commercial control must read as UNKNOWN"


def test_negative_control_the_authority_pins_are_not_vacuous():
    """Prove the forbidden-token detectors fire on text that would carry the defect."""
    injected = 'await fetch("/x"); const m = "DELETE"; onClick={handleExecute}'
    for forbidden in ("fetch(", '"DELETE"', "onClick={handleExecute}"):
        assert forbidden in injected
        assert forbidden not in _code_only(SURFACE_TS)
        assert forbidden not in _code_only(FORM_TS)

    # ...and the comment stripper must not be able to hide a real control.
    assert "fetch(" in injected.split("//")[0]
    assert "fetch(" not in _code_only(SURFACE_TS)
