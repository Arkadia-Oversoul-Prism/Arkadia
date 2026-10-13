"""Lane 3 — Knowledge OS graph provenance reader (feature-local recovery slice).

Binds the recovered provenance *reader* to the projection the backend actually
attaches, so the visible vocabulary cannot drift from the contract.

Contract under test (declared, not invented):
  * ``GET /api/knowledge/graph`` -> ``knowledge.graph.full_graph_export``
    -> ``_attach_provenance(nodes)`` -> ``capture.provenance_for_note(note_id)``
  * the projection is either the canonical GATE-01 dict or the literal
    ``{"state": "UNKNOWN"}`` for a note with no capture record.

The console-side vocabulary lives in
``web/arkadia_console/src/pages/knowledge/knowledgeContracts.ts``
(``classifyProvenance`` / ``summarizeProvenance`` / ``provenanceReading`` /
``provenanceNotice``) and is exercised through ``KnowledgeGraphPanel``. These
tests read that source and assert the three states it must never collapse:
``captured`` / ``undeclared`` / ``unknown``. Every claim has a negative control
so a reader that returned one value for *everything* could not pass.

The handler side is exercised over the live ASGI app against a sandboxed
database (``conftest.py`` redirects the store), so the reader is bound to a real
projection rather than a hand-written fixture.
"""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import api.auth as auth
from api.knowledge_routes import router as knowledge_router
from knowledge.capture import capture_and_ingest
from knowledge.db import get_connection
from knowledge.vault import create_note

pytestmark = pytest.mark.skipif(
    not auth._dev_mode,
    reason="identity tokens require the auth layer's dev-mode (no Firebase service account)",
)

REPO_ROOT = Path(__file__).resolve().parent.parent
CONSOLE_SRC = "web/arkadia_console"
CONTRACTS_TS = REPO_ROOT / CONSOLE_SRC / "src" / "pages" / "knowledge" / "knowledgeContracts.ts"
PANEL_TSX = REPO_ROOT / CONSOLE_SRC / "src" / "pages" / "knowledge" / "KnowledgeGraphPanel.tsx"

USER_A = "l3-provenance-user-a"
CANARY = "ARKADIA_PRIVATE_CANARY_L3_PROVENANCE"


def _token(uid: str) -> str:
    payload = base64.urlsafe_b64encode(json.dumps({"user_id": uid}).encode()).rstrip(b"=").decode()
    return f"header.{payload}.signature"


def _auth(uid: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(uid)}"}


@pytest.fixture(autouse=True)
def _fresh_store():
    conn = get_connection()
    for table in (
        "capture_records",
        "capture_sources",
        "graph_edges",
        "timeline",
        "chunks",
        "embeddings",
        "note_tags",
        "notes",
        "threads",
        "projects",
    ):
        try:
            conn.execute(f"DELETE FROM {table}")
        except Exception:
            pass
    conn.commit()
    yield


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(knowledge_router)
    return TestClient(app)


# ── handler side: the projection the reader consumes ─────────────────────────

def test_graph_attaches_provenance_to_every_node(client):
    """The projection the reader depends on is actually attached by the handler."""
    create_note("plain note", "no capture record for this one", user_id=None)
    graph = client.get("/api/knowledge/graph").json()
    assert graph["nodes"], "positive control: the public corpus is readable"
    for node in graph["nodes"]:
        assert "provenance" in node, "the handler must attach provenance to every node"


def test_note_without_a_capture_record_reports_unknown(client):
    create_note("plain note", "no capture record for this one", user_id=None)
    graph = client.get("/api/knowledge/graph").json()
    states = {node["provenance"]["state"] for node in graph["nodes"]}
    assert states == {"UNKNOWN"}


def test_note_through_the_capture_boundary_carries_a_declared_source(client):
    capture_and_ingest(
        source_kind="document",
        source_ref="l3://doc",
        source_title="L3 Doc",
        raw_content="captured body",
        content_kind="document",
        title="captured note",
    )
    graph = client.get("/api/knowledge/graph").json()
    assert len(graph["nodes"]) == 1
    provenance = graph["nodes"][0]["provenance"]
    assert provenance["state"] != "UNKNOWN"
    assert provenance["source"]["source_kind"] == "document"


def test_capture_without_a_declared_author_reports_declared_false(client):
    """An absent attribution is reported as undeclared, never as a name."""
    capture_and_ingest(
        source_kind="manual",
        source_ref="l3://anon",
        source_title="L3 Anon",
        raw_content="body with no author",
        content_kind="manual",
        title="undeclared note",
    )
    graph = client.get("/api/knowledge/graph").json()
    authorship = graph["nodes"][0]["provenance"]["authorship"]
    assert authorship is not None
    assert authorship["declared"] is False
    assert not authorship.get("authored_by")


def test_private_note_provenance_is_not_exposed_to_anonymous(client):
    """The projection the reader consumes is ownership-scoped, so a recovered
    reader cannot expose an origin the caller was never given."""
    capture_and_ingest(
        source_kind="manual",
        source_ref="l3://private",
        source_title="L3 Private",
        raw_content=CANARY,
        content_kind="manual",
        title=CANARY,
        user_id=USER_A,
    )
    anonymous = client.get("/api/knowledge/graph").json()
    assert all(node["title"] != CANARY for node in anonymous["nodes"])
    owner = client.get("/api/knowledge/graph", headers=_auth(USER_A)).json()
    assert any(node["title"] == CANARY for node in owner["nodes"]), (
        "positive control: the owner must still see their own captured note"
    )


# ── console side: the recovered reader, read from source ─────────────────────

def _contracts_source() -> str:
    return CONTRACTS_TS.read_text(encoding="utf-8")


def test_reader_declares_the_three_provenance_states():
    source = _contracts_source()
    assert 'export type ProvenanceState = "captured" | "undeclared" | "unknown";' in source


def test_reader_treats_unknown_as_a_value_not_a_missing_field():
    source = _contracts_source()
    classify = source.split("export function classifyProvenance", 1)[1].split("\n}", 1)[0]
    assert "UNKNOWN" in classify, "the reader must key on the contract's own UNKNOWN value"
    assert "unknown" in classify, "and map it to the unknown state"


def test_reader_never_synthesises_an_attribution():
    """The reading for an undeclared origin names the absence, not a person."""
    source = _contracts_source()
    reading = source.split("export function provenanceReading", 1)[1].split("\n}", 1)[0]
    assert "origin not declared" in reading
    assert "no capture record" in reading


def test_panel_renders_the_provenance_reading():
    source = PANEL_TSX.read_text(encoding="utf-8")
    assert "summarizeProvenance" in source
    assert "provenanceReading" in source
    assert 'data-testid="knowledge-graph-provenance"' in source
    assert 'data-testid="knowledge-graph-provenance-rows"' in source


def test_notice_counts_reconcile_with_the_node_total():
    """``provenanceNotice`` must state the unknown share against the *whole*
    readable set, not against the captured subset alone."""
    source = _contracts_source()
    notice = source.split("export function provenanceNotice", 1)[1]
    assert "summary.captured + summary.undeclared + summary.unknown" in notice


def test_negative_control_a_single_state_reader_is_not_the_contract():
    """The three states are not interchangeable: the vocabulary must contain all
    three distinct literals. A reader that collapsed them would lose at least one
    and this assertion would fail."""
    source = _contracts_source()
    for state in ("captured", "undeclared", "unknown"):
        assert f'"{state}"' in source, f"missing provenance state {state!r}"


def test_negative_control_panel_does_not_hardcode_an_origin():
    """No literal attribution may appear in the panel — provenance is data from
    the contract, never a value the surface invents."""
    source = PANEL_TSX.read_text(encoding="utf-8")
    assert not re.search(r"captured_by\s*=\s*\"", source)
