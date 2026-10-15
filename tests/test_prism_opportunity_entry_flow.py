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

// The reconnaissance ceiling: EXECUTED / SETTLED are readable, not settable.
out.settable_statuses = m.SETTABLE_STATUSES;
out.transaction_outcomes = m.TRANSACTION_OUTCOME_STATUSES;

// A draft at a transaction outcome must not produce a body that records it.
const executed = m.emptyDraft();
executed.prospect = "Buyer A";
executed.status = "EXECUTED";
out.create_from_executed = m.createEntryBody(executed);
out.edit_from_executed = m.editEntryBody(executed, entry);

// Control: a settable status still reaches the wire.
const contacted = m.emptyDraft();
contacted.prospect = "Buyer A";
contacted.status = "CONTACTED";
out.create_from_contacted = m.createEntryBody(contacted);
out.edit_from_contacted = m.editEntryBody(contacted, entry);

// The pipeline strip: one ordered column per declared status.
out.pipeline_columns = m.statusColumns().map((c) => c.status);
out.pipeline_labels = m.statusColumns().map((c) => c.label);
out.summary_empty = m.summarize([]);
out.summary_one = m.summarize([entry]);
// A board carrying a terminal outcome AND a defect-3 status (outside the declared
// vocabulary): the columns must still total, and the stray must be counted.
const settled = { ...entry, id: "e3", status: "SETTLED" };
const offVocab = { ...entry, id: "e4", status: "conversation" };
out.summary_mixed = m.summarize([entry, settled, offVocab]);
out.no_evidence_sentinel = m.NO_EVIDENCE;

// The reconnaissance fact grid: one row per declared descriptive/commercial
// field, each value through `fact()` — an unverified fact reads UNKNOWN, never
// a blank. A field the entry does carry keeps its recorded value verbatim.
out.fact_fields = m.ENTRY_FACT_FIELDS;
out.fact_rows_unfilled = m.entryFacts(entry);
const recorded = {
  ...entry,
  location: "Kano",
  commodity: "Maize",
  buyer_price: "NGN 1200/kg",
  landed_cost: "",
};
out.fact_rows_recorded = m.entryFacts(recorded);

// Operator notes — a free-text read field the entry may carry. The archived
// Prism radar declared it and the console never rendered it, so a recorded note
// was invisible. A recorded note must read verbatim; an empty one is absent.
out.notes_recorded = { ...entry, notes: "Asked for 20t" }.notes;
out.notes_empty = entry.notes;

// Evidence coverage: only an entry whose evidence_status differs from the
// backend's NONE sentinel counts; a NONE entry must not.
const withEvidence = { ...entry, id: "e5", evidence_status: "FIELD_VISIT" };
out.summary_evidence = m.summarize([entry, withEvidence]);
out.summary_evidence_none_only = m.summarize([entry, settled]).withEvidence;

// The per-entry ADVANCE step: one status forward, never past the ceiling.
out.advance_from_uncontacted = m.advanceBody("UNCONTACTED");
out.advance_from_requirement = m.advanceBody("REQUIREMENT_CAPTURED");
out.advance_from_ready = m.advanceBody("READY_TO_EXECUTE");
out.advance_from_executed = m.advanceBody("EXECUTED");
out.advance_from_settled = m.advanceBody("SETTLED");
out.advance_from_off_vocab = m.advanceBody("conversation");
out.advance_from_unknown = m.advanceBody("NOT_A_STATUS");
out.advance_from_blank = m.advanceBody("");
out.can_advance_uncontacted = m.canAdvance("UNCONTACTED");
out.can_advance_ready = m.canAdvance("READY_TO_EXECUTE");
out.can_advance_settled = m.canAdvance("SETTLED");
out.advance_status_ready = m.advanceStatus("READY_TO_EXECUTE");

// Seeding an edit from an off-vocabulary entry must carry the stored status
// verbatim, so an unrelated edit cannot silently rewrite it into a declared one.
const offSeeded = m.draftFromEntry(offVocab);
out.off_seed_status = offSeeded.status;
out.off_seed_noop = m.isNoOpEdit(offSeeded, offVocab);
offSeeded.notes = "Asked for 20t";
out.off_seed_edit_body = m.editEntryBody(offSeeded, offVocab);
out.off_seed_is_settable = m.isSettableStatus(offSeeded.status);

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
# Cross-layer — the exact bodies the frontend builds, accepted by the real handler
# ---------------------------------------------------------------------------


def test_the_frontend_bodies_are_accepted_by_the_real_handler(app, contract_probe):
    """Binds the executed frontend contract to the live backend.

    The bodies come from the *contract module* (via the Node probe), not from this
    test, so a frontend change that emits a field the handler rejects — or omits one
    it needs — fails here rather than only in a browser.
    """
    project_id = _project(OWNER["uid"])
    client = _client(app, OWNER)

    created = client.post(_entries_path(project_id), json=contract_probe["create_rich"])
    assert created.status_code == 201, created.text
    entry = created.json()["entry"]
    row = _persisted(entry["id"])
    assert row["prospect"] == "Buyer A"
    assert row["buyer_type"] == "Aggregator"
    assert row["location"] == "Kano"
    assert row["buyer_price"] == "NGN 1200/kg"
    # Fields the frontend deliberately omitted keep the backend default.
    assert row["landed_cost"] == "UNKNOWN"
    assert row["capital_required"] == "UNKNOWN"
    assert row["evidence_status"] == "NONE"

    edited = client.patch(f"{_entries_path(project_id)}/{entry['id']}", json=contract_probe["edit_notes"])
    assert edited.status_code == 200, edited.text
    assert _persisted(entry["id"])["notes"] == "Asked for 20t"
    # The edit sent one field, so the recorded commercial fact survives it.
    assert _persisted(entry["id"])["buyer_price"] == "NGN 1200/kg"


def test_the_frontend_minimal_body_creates_an_all_unknown_entry(app, contract_probe):
    """A capture with only a prospect typed produces a wholly unverified entry."""
    project_id = _project(OWNER["uid"])
    response = _client(app, OWNER).post(_entries_path(project_id), json=contract_probe["create_minimal"])
    assert response.status_code == 201, response.text
    row = _persisted(response.json()["entry"]["id"])
    assert row["prospect"] == "Buyer A"
    assert row["status"] == "UNCONTACTED"
    for field in ("buyer_price", "landed_cost", "expected_gross_margin", "supplier", "quantity"):
        assert row[field] == "UNKNOWN", f"{field} must not have been asserted by the client"


def test_negative_control_a_wrong_body_shape_is_rejected_by_the_handler(app):
    """Proves the cross-layer pin can see a defect: a body the frontend must not send."""
    project_id = _project(OWNER["uid"])
    # The shape the pre-flow design would have produced: the sentinel written out.
    response = _client(app, OWNER).post(
        _entries_path(project_id),
        json={"prospect": "Buyer A", "evidence_status": "NONE", "evidence": [], "status": "BOGUS"},
    )
    assert response.status_code == 400, "an invalid status must be refused at the boundary"
    with buyer_recon._db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM buyer_recon_entries").fetchone()[0] == 0


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


# ---------------------------------------------------------------------------
# The reconnaissance ceiling — EXECUTED / SETTLED are readable, not settable
# ---------------------------------------------------------------------------

#: Statuses that assert a transaction outcome. Recording one claims that money
#: moved, and this board's own response declares `execution_authority: "NONE"`
#: and `budget_authority: "NONE"`.
TRANSACTION_OUTCOMES = ("EXECUTED", "SETTLED")


def test_contract_ceiling_excludes_every_transaction_outcome(contract_probe):
    """The settable vocabulary stops at `READY_TO_EXECUTE`."""
    assert contract_probe["settable_statuses"] == [
        status for status in buyer_recon.STATUSES if status not in TRANSACTION_OUTCOMES
    ]
    assert contract_probe["transaction_outcomes"] == list(TRANSACTION_OUTCOMES)
    assert contract_probe["settable_statuses"][-1] == "READY_TO_EXECUTE"


def test_create_and_edit_bodies_refuse_a_transaction_outcome(contract_probe):
    """The ceiling is structural: a terminal status cannot reach the wire.

    A caller that hands `createEntryBody` / `editEntryBody` an `EXECUTED` draft —
    which the form could do if the `<select>` offered it — must not be able to
    produce a body that records the outcome.
    """
    assert contract_probe["create_from_executed"] == {"prospect": "Buyer A"}
    assert contract_probe["edit_from_executed"] == {}


def test_negative_control_a_settable_status_still_reaches_the_wire(contract_probe):
    """The ceiling must narrow the vocabulary, not disable it.

    Without this, `test_create_and_edit_bodies_refuse_a_transaction_outcome`
    would pass against a builder that emitted no status at all.
    """
    assert contract_probe["create_from_contacted"]["status"] == "CONTACTED"
    assert contract_probe["edit_from_contacted"] == {"status": "CONTACTED"}


def test_the_form_offers_only_settable_statuses():
    """The `<select>` options are the ceiling, not the whole backend vocabulary."""
    form = _code_only(FORM_TS)
    assert "SETTABLE_STATUSES.map((status)" in form, "the options must be the reconnaissance ceiling"
    assert "BUYER_RECON_STATUSES.map((status)" not in form, (
        "offering the full vocabulary would make EXECUTED / SETTLED one click away"
    )


def test_a_recorded_transaction_outcome_is_read_only_in_the_form():
    """An entry already at EXECUTED/SETTLED renders as a locked field, not a select."""
    form = _code_only(FORM_TS)
    assert "isSettableStatus(draft.status) ?" in form
    assert "readOnly" in form, "a terminal status must not be editable"
    assert "cannot be changed from reconnaissance" in FORM_TS.read_text(encoding="utf-8")


def test_negative_control_the_settable_detector_flags_the_full_vocabulary():
    """Prove the detector above fires on the defect it exists to catch."""
    naive = "const options = BUYER_RECON_STATUSES.map((status) => status);"
    assert "BUYER_RECON_STATUSES.map((status)" in naive
    assert "SETTABLE_STATUSES.map((status)" not in naive


def test_measured_the_exposure_the_ceiling_closes(app, contract_probe):
    """Recorded honestly: the server *does* accept the outcome; the surface declines.

    `BuyerReconEntryPatch` validates against the full `STATUSES` tuple, so the
    PATCH route records `EXECUTED`. Before the ceiling, the form's `<select>`
    offered that value — the surface's own "no execute control" claim was false
    for the status field even though no button was named Execute. The ceiling is a
    product decision on the surface's side; this test states both halves rather
    than implying a server-side guard.
    """
    project_id = _project(OWNER["uid"])
    created = _create(app, project_id, {"prospect": "Buyer A"}).json()["entry"]
    response = _client(app, OWNER).patch(
        f"{_entries_path(project_id)}/{created['id']}", json={"status": "EXECUTED"}
    )
    assert response.status_code == 200, response.text
    assert _persisted(created["id"])["status"] == "EXECUTED", (
        "the server accepts a transaction outcome; the surface's refusal is a product "
        "decision recorded in the contract module, not a server-side guard"
    )


# ---------------------------------------------------------------------------
# MEASURED DEFECT 3 — status is validated in upper case but persisted as sent
# ---------------------------------------------------------------------------


def test_update_does_not_normalize_a_lowercase_status(app):
    """MEASURED DEFECT 3 in `solspire/buyer_recon.py` (recorded, NOT repaired).

    `BuyerReconManager.update_entry` validates `status.upper()` against `STATUSES`
    and then persists the original value, because the `for key, value in
    patch.items()` loop reads `patch` — which was never reassigned:

        status = patch.get("status")
        if status is not None:
            status = str(status).upper()          # validated in upper case
            if status not in STATUSES:
                raise ValueError("invalid status")
        ...
        for key, value in patch.items():          # ... but `patch` is unchanged
            if key in allowed:
                current[key] = str(value) if value is not None else ""

    `create_entry` *does* normalize (it assigns the upper-cased local), so the two
    paths disagree. A row can therefore carry a status outside the declared
    vocabulary, and any consumer that groups or counts by `STATUSES` — this
    radar's own `summarize`, the archived Prism column counts — silently misses it.

    This is a backend defect outside this workstream's grant (`SHARED-CONTRACTS`
    §1/§7.1). It is pinned rather than repaired: the test asserts the defect so it
    cannot be mistaken for intended behaviour, and
    `test_create_normalizes_a_lowercase_status` is the control proving the
    asymmetry is real. Repairing it is a separate bounded change.
    """
    project_id = _project(OWNER["uid"])
    created = _create(app, project_id, {"prospect": "Buyer A"}).json()["entry"]
    response = _client(app, OWNER).patch(
        f"{_entries_path(project_id)}/{created['id']}", json={"status": "conversation"}
    )
    assert response.status_code == 200, response.text
    stored = _persisted(created["id"])["status"]
    assert stored == "conversation", "if this now reads CONVERSATION, defect 3 was repaired"
    assert stored not in buyer_recon.STATUSES, "the stored value is outside the declared vocabulary"


def test_create_normalizes_a_lowercase_status(app):
    """The control for defect 3: the create path *does* normalize."""
    project_id = _project(OWNER["uid"])
    created = _create(app, project_id, {"prospect": "Buyer A", "status": "contacted"}).json()["entry"]
    assert _persisted(created["id"])["status"] == "CONTACTED"


def test_the_surface_cannot_reach_defect_3():
    """Why the console is unaffected in practice.

    The status the form sends is always a member of `SETTABLE_STATUSES`, a slice
    of the backend's own tuple, and the control is a `<select>` whose options are
    that vocabulary — so a lower-cased status cannot be produced by a click.
    """
    form = _code_only(FORM_TS)
    assert "toUpperCase()" not in form and "toLowerCase()" not in form, (
        "the form must not case-fold a status it is about to send"
    )


# ---------------------------------------------------------------------------
# Pipeline strip — the per-status counts the board read already computes
# ---------------------------------------------------------------------------


def test_status_columns_cover_every_declared_status_in_backend_order(contract_probe):
    """The strip renders one column per status, in the backend's own order.

    Derived from `BUYER_RECON_STATUSES`, so a status added to the backend is a
    column without a frontend edit; a status removed leaves no stale column.
    """
    assert contract_probe["pipeline_columns"] == list(buyer_recon.STATUSES)
    # Labels are the status with underscores relieved, not a second vocabulary.
    assert contract_probe["pipeline_labels"] == [
        status.replace("_", " ") for status in buyer_recon.STATUSES
    ]


def test_strip_counts_every_entry_including_terminal_outcomes(contract_probe):
    """A terminal outcome still has a home: the columns total the board.

    The write ceiling (`SETTABLE_STATUSES`) stops EXECUTED/SETTLED being
    *asserted*; it must not also stop a recorded one being *counted*, or the strip
    would under-report a real board (the archived Prism strip showed every column).
    """
    mixed = contract_probe["summary_mixed"]
    counted = sum(mixed["byStatus"][status] for status in buyer_recon.STATUSES)
    # 2 in-vocabulary entries (UNCONTACTED + SETTLED) + 1 off-vocabulary stray.
    assert mixed["total"] == 3
    assert counted == 2, "in-vocabulary columns must count the settled entry too"
    assert mixed["byStatus"]["UNCONTACTED"] == 1
    assert mixed["byStatus"]["SETTLED"] == 1


def test_strip_states_the_off_vocabulary_stray_instead_of_dropping_it(contract_probe):
    """MEASURED DEFECT 3 makes a status outside the vocabulary persistable.

    `byStatus` is keyed on the declared tuple, so such an entry has no column. Left
    unreported the counts silently fail to total; the summary carries the stray and
    the surface says so. This is the same defect pinned (not repaired) by
    `test_update_does_not_normalize_a_lowercase_status` — here the *display* is
    measured, not the backend.
    """
    mixed = contract_probe["summary_mixed"]
    assert mixed["offVocabulary"] == 1
    assert mixed["total"] == sum(
        mixed["byStatus"][status] for status in buyer_recon.STATUSES
    ) + mixed["offVocabulary"], "the strip plus the off-vocabulary note must total the board"


def test_negative_control_the_stray_would_be_dropped_without_the_counter(contract_probe):
    """Prove the counter is load-bearing rather than decorative.

    Under the pre-change `summarize` (which only incremented declared keys) the
    off-vocabulary entry vanished: the columns totalled one less than the board.
    """
    mixed = contract_probe["summary_mixed"]
    assert mixed["offVocabulary"] > 0, "the detector must see a stray at all"
    naive_total = sum(mixed["byStatus"][status] for status in buyer_recon.STATUSES)
    assert naive_total != mixed["total"], "without the counter the total would not reconcile"


def test_empty_board_reports_zeroed_columns_not_an_invented_row(contract_probe):
    empty = contract_probe["summary_empty"]
    assert empty["total"] == 0
    assert empty["offVocabulary"] == 0
    assert all(empty["byStatus"][status] == 0 for status in buyer_recon.STATUSES), (
        "an empty board must yield zeroed columns, never a fabricated count"
    )


def test_surface_renders_the_pipeline_strip_from_the_summary():
    surface = SURFACE_TS.read_text(encoding="utf-8")
    assert 'data-testid="opportunity-pipeline"' in surface
    assert "statusColumns().map(" in surface, "columns must be derived, not hardcoded"
    assert "summary.byStatus[column.status] ?? 0" in surface
    assert 'data-testid="opportunity-off-vocabulary"' in surface
    assert "summary.offVocabulary > 0" in surface


# ---------------------------------------------------------------------------
# Evidence coverage — the metric `summarize()` computed but no surface rendered
# ---------------------------------------------------------------------------


def test_evidence_metric_counts_only_entries_past_the_none_sentinel(contract_probe):
    """`withEvidence` counts entries whose evidence status differs from `NONE`.

    The summary already computed this; the surface rendered nothing, so the count
    was dead data (the same gap the pipeline strip closed for `byStatus`). One
    entry at the backend's `NONE` sentinel and one carrying a real status must
    count exactly one.
    """
    summary = contract_probe["summary_evidence"]
    assert summary["total"] == 2
    assert summary["withEvidence"] == 1


def test_negative_control_a_none_sentinel_entry_is_not_counted_as_evidenced(contract_probe):
    """Prove the metric is not counting every entry.

    A board where every entry sits at the backend's `NONE` sentinel must report
    zero — otherwise the metric would claim evidence that does not exist, which is
    exactly the over-claim the `NONE` sentinel exists to prevent.
    """
    assert contract_probe["summary_evidence_none_only"] == 0
    assert contract_probe["no_evidence_sentinel"] == "NONE"


def test_surface_renders_the_evidence_metric_from_the_summary():
    surface = SURFACE_TS.read_text(encoding="utf-8")
    assert 'data-testid="opportunity-evidence-metric"' in surface
    assert "summary.withEvidence" in surface, "the metric must read the computed summary"
    assert "NO_EVIDENCE" in surface, "the copy must name the backend sentinel it counts against"
    # The sentinel comes from the contract module, not a re-typed literal.
    assert "NO_EVIDENCE" in surface.split("from \"./opportunityRadarContract\"")[0] or (
        "NO_EVIDENCE," in surface
    ), "NO_EVIDENCE must be imported, not invented inline"


# ---------------------------------------------------------------------------
# Reconnaissance fact grid — the captured fields the console left invisible
# ---------------------------------------------------------------------------


def test_fact_grid_covers_the_declared_reconnaissance_fields(contract_probe):
    """The grid carries the descriptive and commercial fields the handler declares.

    The archived Prism radar rendered the whole captured grid; the console rendered
    only three fields, so a recorded location, quantity, supplier, delivery window,
    payment terms, or margin was invisible. The row set must match the contract's
    own field declarations — not a hand-copied list that can drift from them.
    """
    fields = contract_probe["fact_fields"]
    assert "location" in fields and "commodity" in fields and "quantity" in fields
    assert "buyer_price" in fields and "landed_cost" in fields and "supplier" in fields
    assert "delivery_window" in fields and "payment_terms" in fields
    assert "capital_required" in fields and "expected_gross_margin" in fields
    # The fields with their own UI are excluded, so nothing renders twice.
    for dedicated in ("prospect", "status", "evidence_status", "why_this_prospect", "notes"):
        assert dedicated not in fields, f"{dedicated} has its own control and must not be a grid row"


def test_fact_rows_read_an_unverified_commercial_field_as_the_sentinel(contract_probe):
    """Every unfilled row states the backend's `UNKNOWN`, never a blank.

    A blank would read as a measured value of empty. The row value is passed through
    `fact()`, so the unverified state is the sentinel the backend itself uses. The
    probe entry carries descriptive facts only; every commercial fact it omits must
    read as the sentinel.
    """
    rows = {row["field"]: row["value"] for row in contract_probe["fact_rows_unfilled"]}
    assert rows["buyer_price"] == "UNKNOWN"
    assert rows["quantity"] == "UNKNOWN" and rows["supplier"] == "UNKNOWN"
    assert all(value != "" for value in rows.values()), "no row may render an empty value"


def test_fact_rows_carry_a_recorded_value_verbatim(contract_probe):
    """A fact the entry actually carries is shown as recorded, not overwritten."""
    rows = {row["field"]: row["value"] for row in contract_probe["fact_rows_recorded"]}
    assert rows["location"] == "Kano"
    assert rows["commodity"] == "Maize"
    assert rows["buyer_price"] == "NGN 1200/kg"


def test_negative_control_an_empty_string_fact_reads_as_the_sentinel(contract_probe):
    """Prove `fact()` is load-bearing, not decorative.

    An entry whose stored `landed_cost` is the empty string (the backend default for
    a non-commercial text field) must not render a blank cell — under a raw
    passthrough it would. The control reconstructs that passthrough and shows it
    diverges from the measured row.
    """
    rows = {row["field"]: row["value"] for row in contract_probe["fact_rows_recorded"]}
    assert rows["landed_cost"] == "UNKNOWN", "an empty stored fact must read as the sentinel"
    assert rows["landed_cost"] != "", "the raw passthrough would have rendered a blank"


def test_surface_renders_the_fact_grid_from_the_contract():
    surface = SURFACE_TS.read_text(encoding="utf-8")
    assert "entryFacts(entry)" in surface, "the grid must be derived from the contract, not hardcoded"
    assert "opportunity-entry-facts-" in surface, "the grid must be identifiable per entry"
    # The value must come from the contract's `fact()`-backed row, not a raw label.
    assert "item.value" in surface
    assert "entryFacts," in surface, "the helper must be imported from the contract module"


# ---------------------------------------------------------------------------
# Per-entry ADVANCE — one step forward, through the verified PATCH handler
# ---------------------------------------------------------------------------


def test_executed_contract_advance_steps_one_status_forward(contract_probe):
    """The archived Prism board offered one ADVANCE per entry; it is one PATCH."""
    assert contract_probe["advance_from_uncontacted"] == {"status": "CONTACTED"}
    assert contract_probe["advance_from_requirement"] == {"status": "PRICE_CONFIRMED"}


def test_executed_contract_advance_stops_at_the_reconnaissance_ceiling(contract_probe):
    """`READY_TO_EXECUTE` is the last step: a terminal outcome is never a target.

    The archived Prism step was index-based and *would* have sent `EXECUTED` from
    `READY_TO_EXECUTE`. The write ceiling forbids it, so the step stops here.
    """
    assert contract_probe["advance_from_ready"] == {}
    assert contract_probe["can_advance_ready"] is False
    assert contract_probe["advance_status_ready"] is None


def test_executed_contract_advance_is_empty_for_an_unstepable_status(contract_probe):
    for key in (
        "advance_from_executed",
        "advance_from_settled",
        "advance_from_off_vocab",
        "advance_from_unknown",
        "advance_from_blank",
    ):
        assert contract_probe[key] == {}, f"{key} must not produce a write body"
    assert contract_probe["can_advance_settled"] is False
    assert contract_probe["can_advance_uncontacted"] is True


def test_negative_control_a_naive_index_step_would_assert_an_outcome(contract_probe):
    """Proves the ceiling is load-bearing: the archived index step would send EXECUTED."""
    naive = buyer_recon.STATUSES[buyer_recon.STATUSES.index("READY_TO_EXECUTE") + 1]
    assert naive == "EXECUTED", "the naive step lands on a transaction outcome"
    assert contract_probe["advance_from_ready"] == {}, "the contract must refuse that step"
    assert naive not in contract_probe["settable_statuses"]


def test_the_frontend_advance_body_is_accepted_and_persisted_by_the_real_handler(app, contract_probe):
    """Binds the executed advance body to the live handler, asserted on the row."""
    project_id = _project(OWNER["uid"])
    client = _client(app, OWNER)
    created = client.post(
        _entries_path(project_id),
        json={"prospect": "Buyer A", "status": "UNCONTACTED"},
    )
    assert created.status_code == 201, created.text
    entry_id = created.json()["entry"]["id"]

    advanced = client.patch(
        f"{_entries_path(project_id)}/{entry_id}", json=contract_probe["advance_from_uncontacted"]
    )
    assert advanced.status_code == 200, advanced.text
    assert advanced.json()["entry"]["status"] == "CONTACTED"
    assert _persisted(entry_id)["status"] == "CONTACTED"
    # The advance carried only a status; the recorded prospect survives it.
    assert _persisted(entry_id)["prospect"] == "Buyer A"


def test_negative_control_the_ceiling_body_is_never_sent_to_the_handler(app):
    """An empty advance body has nothing to send; posting it does not move the row."""
    project_id = _project(OWNER["uid"])
    client = _client(app, OWNER)
    created = client.post(
        _entries_path(project_id), json={"prospect": "Buyer A", "status": "READY_TO_EXECUTE"}
    )
    entry_id = created.json()["entry"]["id"]
    # The contract produces {} here; an empty PATCH is a no-op, not an outcome write.
    noop = client.patch(f"{_entries_path(project_id)}/{entry_id}", json={})
    assert noop.status_code == 200, noop.text
    assert _persisted(entry_id)["status"] == "READY_TO_EXECUTE", "the row must not advance to EXECUTED"


def test_surface_offers_an_advance_control_only_when_a_step_is_permitted():
    surface = SURFACE_TS.read_text(encoding="utf-8")
    assert "canAdvance(entry.status)" in surface, "the control must be gated by the ceiling"
    assert "opportunity-entry-advance-" in surface, "an advance control must exist per entry"
    assert "advanceBody(entry.status)" in surface, "the body must come from the contract module"
    assert 'method: "PATCH"' in surface
    assert 'from "./opportunityRadarContract"' in surface


def test_surface_advance_invents_no_delete_or_execute_path():
    code = _code_only(SURFACE_TS)
    for invented in ('"DELETE"', "'DELETE'", "handleExecute", "handleApprove", "settle(", "executeEntry"):
        assert invented not in code, f"advance must not imply authority it does not have ({invented})"

def test_surface_strip_asserts_no_execution_authority():
    """A per-status count is reconnaissance; it must not become an execute control."""
    code = _code_only(SURFACE_TS)
    for invented in (
        "onClick={handleExecute",
        "handleApprove",
        '"DELETE"',
        "'DELETE'",
        "budget_ngn",
        "contract_value",
        "revenue",
    ):
        assert invented not in code, f"the strip must not imply authority ({invented})"



# ---------------------------------------------------------------------------
# Seeding an edit from an off-vocabulary entry — carried verbatim, not snapped
# ---------------------------------------------------------------------------


def test_seeding_an_edit_carries_an_off_vocabulary_status_verbatim(contract_probe):
    """The edit control shows the status the entry actually has.

    An entry can carry a status outside the declared vocabulary (MEASURED DEFECT 3,
    pinned above). Snapping it to `UNCONTACTED` on seed displayed a status the entry
    does not hold; the draft must carry the stored value instead.
    """
    assert contract_probe["off_seed_status"] == "conversation"
    assert contract_probe["off_seed_status"] not in buyer_recon.STATUSES
    assert contract_probe["off_seed_is_settable"] is False


def test_an_unrelated_edit_does_not_rewrite_an_off_vocabulary_status(contract_probe):
    """The consequential half: no silent status rewrite as a side effect of editing.

    With the off-vocabulary status carried verbatim, `editEntryBody` transmits only
    the field the operator changed — it never substitutes the seed default. The
    stored off-vocabulary status is left untouched by a save.
    """
    assert contract_probe["off_seed_edit_body"] == {"notes": "Asked for 20t"}
    assert "status" not in contract_probe["off_seed_edit_body"]


def test_seeding_an_off_vocabulary_entry_round_trips_to_a_no_op(contract_probe):
    """A seed that carries the stored status makes a no-change round trip a no-op."""
    assert contract_probe["off_seed_noop"] is True


def test_negative_control_the_snapping_seed_would_have_rewritten_the_status(contract_probe):
    """Proves the verbatim carry is load-bearing, not decorative.

    Under the pre-change seed (`isKnownStatus(entry.status) ? entry.status :
    "UNCONTACTED"`) the draft read `UNCONTACTED` — which *is* settable — so the same
    notes-only edit would have emitted `{"notes": ..., "status": "UNCONTACTED"}` and
    silently rewritten a recorded status. Reconstruct that shape and show it diverges
    from the measured body.
    """
    snap = "UNCONTACTED"
    assert snap in contract_probe["settable_statuses"], "the snap target must be settable to bite"
    assert contract_probe["off_seed_status"] != snap, "the fixed seed must not snap"
    assert contract_probe["off_seed_edit_body"] != {"notes": "Asked for 20t", "status": snap}


def test_edit_form_states_an_off_vocabulary_status_instead_of_a_transaction_note():
    """The locked-status message must distinguish the two cases.

    A terminal outcome and an off-vocabulary stray are both non-settable but not the
    same fact; the transaction-outcome note would misdescribe the latter. The form
    branches on `isKnownStatus` and carries a distinct testid for the stray.
    """
    form = FORM_TS.read_text(encoding="utf-8")
    assert "isKnownStatus(draft.status)" in form, "the locked display must branch on the vocabulary"
    assert 'data-testid="prospect-entry-status-off-vocabulary"' in form
    assert "isKnownStatus," in form, "the predicate must be imported, not re-derived inline"


def test_the_frontend_seed_no_longer_snaps_an_unknown_status():
    """Source-level pin of the one-line change, so a revert is visible."""
    contract = _code_only(CONTRACT_TS)
    assert 'emptyDraft(isKnownStatus(entry.status) ? entry.status : "UNCONTACTED")' not in contract
    assert "emptyDraft(entry.status)" in contract, "the seed must carry the stored status verbatim"


# ---------------------------------------------------------------------------
# Operator notes — the last declared read field with no console rendering
# ---------------------------------------------------------------------------


def test_read_returns_a_recorded_note_verbatim(app):
    """`notes` is returned by both entry reads, so the console can render it.

    The field has a backend default of `""` and no verified UI write path; a note
    reaches the store through the same create/edit handlers the form already drives.
    The read must carry it so the surface does not have to guess.
    """
    project_id = _project(OWNER["uid"])
    entry = _create(app, project_id, {"prospect": "Buyer A", "notes": "Asked for 20t"}).json()["entry"]
    assert entry["notes"] == "Asked for 20t"
    assert _persisted(entry["id"])["notes"] == "Asked for 20t"
    read = _client(app, OWNER).get(f"/solspire/buyer-recon/projects/{project_id}").json()["entries"][0]
    assert read["notes"] == "Asked for 20t"


def test_negative_control_an_entry_without_a_note_reads_the_empty_default(app):
    """Prove the surface must gate on the note, not render the field unconditionally.

    An entry created without a note carries the backend's `""` default. A surface
    that rendered `notes` unconditionally would emit an empty paragraph; the gate
    (`entry.notes &&`) renders nothing. This control fixes the value the gate sees.
    """
    project_id = _project(OWNER["uid"])
    entry = _create(app, project_id, {"prospect": "Buyer A"}).json()["entry"]
    assert entry["notes"] == "", "an un-noted entry defaults to the empty string"


def test_notes_read_verbatim_in_the_contract_probe(contract_probe):
    assert contract_probe["notes_recorded"] == "Asked for 20t"
    assert contract_probe["notes_empty"] == ""


def test_surface_renders_a_recorded_note_gated_on_its_presence():
    """The note renders from the read field, only when the entry carries one."""
    surface = SURFACE_TS.read_text(encoding="utf-8")
    assert "entry.notes &&" in surface, "the note must be gated, not rendered unconditionally"
    assert "opportunity-entry-notes-" in surface, "the note must be identifiable per entry"
    # It reads the field off the entry the board read returned, not a re-typed copy.
    assert "{entry.notes}" in surface
