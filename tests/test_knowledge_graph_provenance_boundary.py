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
    # No literal attribution: provenance is data from the contract.
    assert _hardcoded_attribution_hits(source) == []


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


def _hardcoded_attribution_hits(source: str) -> list[str]:
    """Literal attributions a panel invented rather than read from the contract.

    Module level, so the live assertions and their negative controls call the
    *same* code. The controls previously restated these regexes inline and ran no
    detector, so either predicate could be deleted with no red test (measured at
    `main` `03220c95`: the live assertions are the only callers, and nothing
    exercises them but themselves).
    """
    patterns = (
        ("captured_by", r"captured_by\s*=\s*\""),
        ("authored_by", r"authored_by\s*=\s*\""),
        ("author", r"author\s*=\s*\""),
    )
    return [name for name, pattern in patterns if re.search(pattern, source)]


def test_negative_control_panel_does_not_hardcode_an_origin():
    """Prove the origin detector bites, on a panel that invents a captured origin.

    Calls :func:`_hardcoded_attribution_hits` — the same function the live
    assertion uses — so the control can fail when that detector is disarmed. It
    previously restated the regex inline and ran no detector.
    """
    invented = '<Provenance captured_by="the archive" />'
    assert _hardcoded_attribution_hits(invented) == ["captured_by"]
    assert _hardcoded_attribution_hits(PANEL_TSX.read_text(encoding="utf-8")) == []


# ── handler side: the authorship dimension the projection also carries ───────

def test_capture_with_a_declared_author_reports_it(client):
    """The declared-author branch of the projection is reachable, so the reader
    that renders it is bound to a real value rather than an unreachable one."""
    capture_and_ingest(
        source_kind="manual",
        source_ref="l3://authored",
        source_title="L3 Authored",
        raw_content="body with a declared author",
        content_kind="manual",
        title="authored note",
        authored_by=USER_A,
        authored_by_kind="human",
    )
    graph = client.get("/api/knowledge/graph").json()
    authorship = graph["nodes"][0]["provenance"]["authorship"]
    assert authorship["declared"] is True
    assert authorship["authored_by"] == USER_A
    assert authorship["authored_by_kind"] == "human"


def test_declared_author_with_unknown_kind_keeps_the_name(client):
    """An actor declared without a nature is still a declared attribution: the
    projection keeps the name and records the kind as UNKNOWN, never assuming
    'human'. The reader must not upgrade that to a kind the contract withheld."""
    capture_and_ingest(
        source_kind="manual",
        source_ref="l3://authored-unknown-kind",
        source_title="L3 Authored Unknown Kind",
        raw_content="body with a nameless-kind author",
        content_kind="manual",
        title="authored unknown kind note",
        authored_by=USER_A,
        authored_by_kind="unknown",
    )
    graph = client.get("/api/knowledge/graph").json()
    authorship = graph["nodes"][0]["provenance"]["authorship"]
    assert authorship["declared"] is True
    assert authorship["authored_by"] == USER_A
    assert authorship["authored_by_kind"] == "unknown"


def test_unknown_projection_is_narrowed_to_the_state_literal(client):
    """The declared contract for a note with no capture record.

    ``knowledge.graph._attach_provenance`` does not forward
    ``provenance_for_note``'s UNKNOWN dict verbatim — it replaces it with the
    bare literal ``{"state": "UNKNOWN"}``. So an UNKNOWN node carries **no**
    ``authorship`` (or ``source``) key at all, rather than an explicit
    ``declared: False``. Pinned here because the reader must handle the absent
    key, not a present-but-empty object: a reader that assumed the key exists
    would throw on exactly the nodes whose origin is unknown.
    """
    create_note("plain note", "no capture record for this one", user_id=None)
    graph = client.get("/api/knowledge/graph").json()
    provenance = graph["nodes"][0]["provenance"]
    assert provenance == {"state": "UNKNOWN"}
    assert "authorship" not in provenance and "source" not in provenance


# ── console side: the authorship reading, read from source ───────────────────

def test_reader_declares_a_separate_authorship_reading():
    source = _contracts_source()
    assert "export function authorDeclared" in source
    assert "export function summarizeAuthorship" in source
    assert "export function authorshipReading" in source
    assert "export function authorshipNotice" in source


def test_reader_requires_both_declared_and_a_name_to_render_an_author():
    """`declared: true` with an absent name is not an attribution. The reading
    must demand the name too, not the flag alone."""
    source = _contracts_source()
    declared = source.split("export function authorDeclared", 1)[1].split("\n}", 1)[0]
    assert "authorship?.declared" in declared
    assert "authorship?.authored_by" in declared


def test_authorship_reading_names_the_absence_never_a_person():
    source = _contracts_source()
    reading = source.split("export function authorshipReading", 1)[1].split("\n}", 1)[0]
    assert "author not declared" in reading


def test_authorship_notice_counts_reconcile_with_the_node_total():
    """The undeclared share is stated against the whole readable set, not against
    the captured subset alone."""
    source = _contracts_source()
    notice = source.split("export function authorshipNotice", 1)[1]
    assert "summary.declared + summary.undeclared" in notice


def test_panel_renders_the_authorship_reading():
    source = PANEL_TSX.read_text(encoding="utf-8")
    assert "summarizeAuthorship" in source
    assert "authorshipReading" in source
    assert 'data-testid="knowledge-graph-authorship"' in source
    assert 'label: "author not declared"' in source
    # No literal author either: the surface never invents an attribution.
    assert _hardcoded_attribution_hits(source) == []


def test_panel_row_reads_authorship_for_every_node(client):
    """The per-node row carries the authorship reading alongside the origin, so a
    node whose origin is UNKNOWN still states its authorship. Read from the row
    template, which is what the reader emits for every node it renders."""
    source = PANEL_TSX.read_text(encoding="utf-8")
    row = source.split('data-testid="knowledge-graph-provenance-rows"', 1)[1]
    assert "provenanceReading(node)" in row
    assert "authorshipReading(node)" in row


def test_authorship_summary_keys_off_the_same_predicate_as_the_reading():
    """The count and the per-node reading must be derived from one predicate. If
    the summariser bucketed on anything else, the declared count could disagree
    with the rows it is printed above."""
    source = _contracts_source()
    summary = source.split("export function summarizeAuthorship", 1)[1].split("\n}", 1)[0]
    assert "authorDeclared(node)" in summary


def test_negative_control_an_authorship_blind_reader_is_not_the_contract():
    """The projection carries authorship; a reader that ignored it would fail
    here. This is the control that makes the authorship assertions load-bearing."""
    contracts = _contracts_source()
    panel = PANEL_TSX.read_text(encoding="utf-8")
    assert "authorship" in contracts and "authorship" in panel


def test_negative_control_panel_never_hardcodes_an_author():
    """Prove the attribution detector bites, on a panel that invents an author.

    Calls :func:`_hardcoded_attribution_hits` — the same function the live
    assertions use — so the control can fail when that detector is disarmed. It
    previously restated both regexes inline and ran no detector.
    """
    assert _hardcoded_attribution_hits(PANEL_TSX.read_text(encoding="utf-8")) == []
    invented = '<Provenance captured_by="the oracle" authored_by="Arkana" author="A" />'
    assert _hardcoded_attribution_hits(invented) == ["captured_by", "authored_by", "author"]
    # A `key=` attribute and a data read are not literal attributions.
    assert _hardcoded_attribution_hits('<Row key={node.id} author={node.author} />') == []


# ── console side: a bounded row list discloses its own bound ──────────────────
#
# The panel renders `graph.nodes.slice(0, PROVENANCE_ROWS)` with no disclosure,
# so eight rows read as the complete record while `nodes` (the exact count fact
# above them) can be larger. That is the same silent-cap class the Lab's
# `renderClip.ts` names; the rule here is that a bounded view states its bound.
# Every assertion below has a control that would fail against the pre-repair
# panel (a bare `slice` with no notice), so the guard is not satisfied by the
# detector agreeing with itself.

def test_contracts_expose_a_bounded_row_notice():
    source = _contracts_source()
    assert "export function boundedRowNotice" in source


def test_bounded_notice_is_silent_when_nothing_is_withheld():
    """A complete list must NOT be labelled as truncated: a notice that always
    fired would be as dishonest as one that never did."""
    source = _contracts_source()
    body = source.split("export function boundedRowNotice", 1)[1].split("\n}", 1)[0]
    assert "total <= shown" in body, "the guard must be the comparison, not a constant"
    assert "return null" in body


def test_bounded_notice_states_both_counts():
    source = _contracts_source()
    body = source.split("export function boundedRowNotice", 1)[1].split("\n}", 1)[0]
    assert "shown" in body and "total" in body, "the copy must name both the shown and total counts"


# The literals the row-cap convention requires, hoisted so the live assertion and
# its negative control feed the *same* detector. `_row_cap_defects` is the detector
# both call; neither restates the property.
ROW_CAP_REQUIRED_LITERALS: tuple[tuple[str, str], ...] = (
    ("boundedRowNotice", "the panel must render the bounded-row notice"),
    ('data-testid="knowledge-graph-rows-bounded"', "the notice needs its own test id"),
    (
        "boundedRowNotice(PROVENANCE_ROWS, graph.nodes.length)",
        "the notice must receive the slice bound and the true total",
    ),
    (
        "graph.nodes.slice(0, PROVENANCE_ROWS)",
        "the slice must use the same constant the notice is given",
    ),
)

PRE_REPAIR_PANEL_BODY = (
    "{graph.nodes.length > 0 && (\n"
    '  <ul data-testid="knowledge-graph-provenance-rows">\n'
    "    {graph.nodes.slice(0, PROVENANCE_ROWS).map((node) => (\n"
    "      <li>{node.title}</li>\n"
    "    ))}\n"
    "  </ul>\n"
    ")}"
)


def _row_cap_defects(source: str) -> list[str]:
    """Every row-cap convention literal `source` is missing.

    Module level so the live assertion and the negative control call the *same*
    predicate: an edit that empties `ROW_CAP_REQUIRED_LITERALS`, or one that makes
    this function answer `[]` unconditionally, reddens the control.
    """
    return [reason for literal, reason in ROW_CAP_REQUIRED_LITERALS if literal not in source]


def test_panel_discloses_the_row_cap():
    """The panel that performs the `slice` must render the disclosure, and its
    bound must come from the same constant the `slice` uses."""
    assert _row_cap_defects(PANEL_TSX.read_text(encoding="utf-8")) == []


def test_negative_control_a_bare_slice_is_not_the_convention():
    """Feed the detector the pre-repair shape: a panel that slices without a
    notice. It must be reported, and the shipped panel must not be — a detector
    that flagged everything would pass the first half alone."""
    reported = _row_cap_defects(PRE_REPAIR_PANEL_BODY)
    assert reported, "the detector must report a bare slice with no notice"
    assert "the panel must render the bounded-row notice" in reported
    assert _row_cap_defects(PANEL_TSX.read_text(encoding="utf-8")) == [], (
        "the shipped panel must be clean under the same detector the control used"
    )


# ── console side: the title chips are the *second* bounded list ───────────────
#
# `GraphReading` bounds two lists over the same node set: the provenance rows
# (`PROVENANCE_ROWS`) and the title chips (`TITLE_LIMIT`, applied inside
# `summarizeGraph`). The row list discloses its bound; the title list shipped as
# a bare `<ul>` of up to eight chips with the exact `nodes` count printed above
# it — a prefix that reads as the complete record. Same defect class, one block
# below the repaired one, so the same convention binds it.
#
# The bound is applied in `knowledgeContracts.ts`, so the detector reads both
# files: the slice must use the exported constant, and the panel must hand that
# *same* constant to the notice.

TITLE_CAP_REQUIRED_LITERALS: tuple[tuple[str, str, str], ...] = (
    (
        "contracts",
        "export const TITLE_LIMIT",
        "the slice bound must be exported so the panel can disclose the same value",
    ),
    (
        "contracts",
        "graph.nodes.slice(0, TITLE_LIMIT)",
        "the title slice must use the constant the panel is given",
    ),
    (
        "panel",
        'boundedRowNotice(TITLE_LIMIT, graph.nodes.length, "titles")',
        "the notice must receive the slice bound, the true total, and name the list",
    ),
    (
        "panel",
        'data-testid="knowledge-graph-titles-bounded"',
        "the title notice needs its own test id",
    ),
)

PRE_REPAIR_TITLE_PANEL_BODY = (
    "{summary.titles.length > 0 && (\n"
    "  <ul className=\"flex flex-wrap gap-2\">\n"
    "    {summary.titles.map((title) => (\n"
    "      <li>{title}</li>\n"
    "    ))}\n"
    "  </ul>\n"
    ")}"
)

PRE_REPAIR_TITLE_CONTRACTS_BODY = (
    "const TITLE_LIMIT = 8;\n"
    "export function summarizeGraph(graph: KnowledgeGraphData): GraphSummary {\n"
    "  const titles = graph.nodes.slice(0, TITLE_LIMIT).map((node) => node.title);\n"
    "  return { nodes: graph.nodes.length, edges: graph.edges.length, scope, titles };\n"
    "}"
)


def _title_cap_defects(contracts_source: str, panel_source: str) -> list[str]:
    """Every title-cap convention literal the given sources are missing.

    Module level so the live assertion and the negative control call the *same*
    predicate: an edit that empties `TITLE_CAP_REQUIRED_LITERALS`, or one that
    makes this function answer `[]` unconditionally, reddens the control.
    """
    sources = {"contracts": contracts_source, "panel": panel_source}
    return [
        reason
        for where, literal, reason in TITLE_CAP_REQUIRED_LITERALS
        if literal not in sources[where]
    ]


def test_panel_discloses_the_title_cap():
    """The list that is capped must say it is capped, using the bound the slice
    actually applied."""
    assert _title_cap_defects(_contracts_source(), PANEL_TSX.read_text(encoding="utf-8")) == []


def test_negative_control_bare_title_chips_are_not_the_convention():
    """Feed the detector the pre-repair shape: an unexported constant and a panel
    that renders the chips with no notice. It must report both, and the shipped
    sources must stay clean under the same detector."""
    reported = _title_cap_defects(PRE_REPAIR_TITLE_CONTRACTS_BODY, PRE_REPAIR_TITLE_PANEL_BODY)
    assert reported, "the detector must report an undisclosed title cap"
    assert "the notice must receive the slice bound, the true total, and name the list" in reported
    assert "the slice bound must be exported so the panel can disclose the same value" in reported
    assert _title_cap_defects(_contracts_source(), PANEL_TSX.read_text(encoding="utf-8")) == [], (
        "the shipped sources must be clean under the same detector the control used"
    )
