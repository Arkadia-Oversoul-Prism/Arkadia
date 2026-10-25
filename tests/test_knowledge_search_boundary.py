"""Workstream 3 — Knowledge OS search contract, ownership boundary and panel states.

Binds the *verified* ``POST /api/knowledge/search`` handler
(``api.knowledge_routes.py::search`` -> ``knowledge.search.unified_search``) to
its request/response schema, its optional-auth identity resolution, and the
ownership predicate that separates an owner's private material from the public
corpus.

Contract under test (read from the handler, not invented):

  * request  ``{query: str, modes?: [str], top_k: int = 20}``
  * response a mapping of *mode name* -> list of retrieved records
  * auth     ``_optional_user_id`` -> ``api.auth.get_current_user``, which is an
             **optional** dependency: an anonymous caller is a real caller and
             must receive the public corpus only (never a 401, never all rows)
  * owner    ``knowledge.search._notes_owner_sql`` -> own OR public when
             authenticated, public-only otherwise

Three defects were measured on this endpoint before the repairs below and each
gets a regression pin plus a negative control:

  1. ``knowledge/schema.sql`` declared ``CREATE TABLE IF NOT EXISTS references``
     with an unquoted SQL reserved word. SQLite raised ``syntax error``,
     ``_apply_schema`` swallowed it, the table was never created, and the
     endpoint returned **500 ``no such table: references``** for the *default*
     mode set and for ``modes=["reference"]`` — observed live at
     ``https://arkadia-qzu4.onrender.com``.
  2. ``unified_search`` called ``project_search`` and ``timeline_search``
     **without** ``user_id``, so an anonymous caller received every owner's
     private projects and timeline events.
  3. ``unified_search`` did not pass ``user_id`` to ``graph_search`` even though
     that function already accepted it.

Token mechanics: with no Firebase service account the auth layer runs in
dev-mode and decodes an unsigned JWT payload for identity. The guard below skips
rather than silently passing if that precondition is not met.
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
from knowledge.db import execute, get_connection
from knowledge.vault import create_note, create_project

pytestmark = pytest.mark.skipif(
    not auth._dev_mode,
    reason="identity tokens require the auth layer's dev-mode (no Firebase service account)",
)

ROOT = Path(__file__).resolve().parents[1]
SEARCH_SRC = ROOT / "knowledge" / "search.py"
SCHEMA_SRC = ROOT / "knowledge" / "schema.sql"
PANEL = ROOT / "web" / "arkadia_console" / "src" / "components" / "knowledge" / "KnowledgeSearchPanel.tsx"
CONTRACTS = ROOT / "web" / "arkadia_console" / "src" / "pages" / "knowledge" / "knowledgeContracts.ts"
PAGE = ROOT / "web" / "arkadia_console" / "src" / "pages" / "KnowledgePage.tsx"

USER_A = "ws3-search-user-a"
USER_B = "ws3-search-user-b"
PRIVATE_A = "ARKADIA_PRIVATE_SEARCH_CANARY_WS3_A"
PRIVATE_B = "ARKADIA_PRIVATE_SEARCH_CANARY_WS3_B"
PUBLIC_MARK = "ARKADIA_PUBLIC_SEARCH_MARKER_WS3"
PROJECT_A = "ARKADIA_PRIVATE_PROJECT_WS3_A"
PROJECT_PUBLIC = "ARKADIA_PUBLIC_PROJECT_WS3"


def _token(uid: str) -> str:
    payload = base64.urlsafe_b64encode(json.dumps({"user_id": uid}).encode()).rstrip(b"=").decode()
    return f"header.{payload}.signature"


def _auth(uid: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(uid)}"}


@pytest.fixture(autouse=True)
def _fresh_store():
    conn = get_connection()
    for table in ("graph_edges", "timeline", "chunks", "embeddings", "note_tags",
                  "notes", "threads", "projects", '"references"'):
        try:
            conn.execute(f"DELETE FROM {table}")
        except Exception:
            pass
    conn.commit()
    yield


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = FastAPI()
    app.include_router(knowledge_router)
    return TestClient(app)


def _seed_notes() -> None:
    create_note(title=PRIVATE_A, content=f"private alpha {PRIVATE_A}", user_id=USER_A)
    create_note(title=PRIVATE_B, content=f"private alpha {PRIVATE_B}", user_id=USER_B)
    create_note(title=PUBLIC_MARK, content="open alpha corpus", user_id=None)


def _seed_projects_events() -> None:
    create_project(PROJECT_A, "confidential alpha roadmap", user_id=USER_A)
    create_project(PROJECT_PUBLIC, "public alpha roadmap", user_id=None)
    execute(
        "INSERT INTO timeline (event_type, payload, user_id) VALUES (?, ?, ?)",
        ("decision", json.dumps({"note": "alpha private decision"}), USER_A),
    )


def _titles(records: list[dict]) -> set[str]:
    return {str(r.get("title")) for r in records}


# ── request / response schema ────────────────────────────────────────────────

def test_search_returns_a_mapping_of_mode_to_records(client):
    _seed_notes()
    body = client.post("/api/knowledge/search", json={"query": "alpha", "modes": ["fulltext"], "top_k": 5}).json()
    assert isinstance(body, dict) and isinstance(body["fulltext"], list)


def test_search_returns_only_the_modes_requested(client):
    _seed_notes()
    body = client.post("/api/knowledge/search", json={"query": "alpha", "modes": ["fulltext"], "top_k": 5}).json()
    assert set(body) == {"fulltext"}


def test_search_default_modes_are_served_not_a_500(client):
    """Regression pin for the reserved-word ``references`` table.

    ``unified_search`` defaults to every mode except ``graph``, which includes
    ``reference``. Before the repair this was a live 500
    (``no such table: references``); an explicit ``modes=["reference"]`` call is
    the minimal reproduction.
    """
    _seed_notes()
    default = client.post("/api/knowledge/search", json={"query": "alpha", "top_k": 5})
    assert default.status_code == 200, default.text
    assert "reference" in default.json(), "the default mode set must include the reference mode"

    explicit = client.post("/api/knowledge/search", json={"query": "alpha", "modes": ["reference"], "top_k": 5})
    assert explicit.status_code == 200, explicit.text
    assert isinstance(explicit.json()["reference"], list)


def test_references_table_is_materialised_by_the_schema(client):
    """The root cause: the DDL statement must actually execute."""
    rows = execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'references'")
    assert rows, "the `references` table must exist — the DDL silently failed before the repair"


def test_reference_search_reads_the_quoted_table(client):
    note = create_note(title=PUBLIC_MARK, content="open", user_id=None)
    execute(
        'INSERT INTO "references" (source_note_id, target_ref, ref_type, label) VALUES (?, ?, ?, ?)',
        (note["id"], "https://example.org/alpha-reference", "url", "alpha reference"),
    )
    body = client.post("/api/knowledge/search", json={"query": "alpha-reference", "modes": ["reference"], "top_k": 5}).json()
    assert any("alpha-reference" in str(r.get("target_ref", "")) for r in body["reference"])


# ── private / public separation (notes) ──────────────────────────────────────

def test_anonymous_search_excludes_private_notes(client):
    _seed_notes()
    body = client.post("/api/knowledge/search", json={"query": "alpha", "modes": ["fulltext"], "top_k": 10}).json()
    titles = _titles(body["fulltext"])
    assert PUBLIC_MARK in titles, "the public corpus must remain readable (positive control)"
    assert PRIVATE_A not in titles and PRIVATE_B not in titles


def test_authenticated_search_is_scoped_to_owner_and_public(client):
    _seed_notes()
    body = client.post(
        "/api/knowledge/search", json={"query": "alpha", "modes": ["fulltext"], "top_k": 10}, headers=_auth(USER_A)
    ).json()
    titles = _titles(body["fulltext"])
    assert PRIVATE_A in titles, "the owner must still see their own material (positive control)"
    assert PUBLIC_MARK in titles
    assert PRIVATE_B not in titles, "another owner's private material must never appear"


def test_search_does_not_leak_across_owners(client):
    _seed_notes()
    a = _titles(client.post("/api/knowledge/search", json={"query": "alpha", "modes": ["fulltext"]}, headers=_auth(USER_A)).json()["fulltext"])
    b = _titles(client.post("/api/knowledge/search", json={"query": "alpha", "modes": ["fulltext"]}, headers=_auth(USER_B)).json()["fulltext"])
    assert PRIVATE_A in a and PRIVATE_A not in b
    assert PRIVATE_B in b and PRIVATE_B not in a


# ── private / public separation (projects and timeline) ──────────────────────
#
# Regression pins for the un-threaded ``user_id``. Before the repair every
# caller — including an anonymous one — received all owners' rows.

def test_project_mode_does_not_leak_private_projects(client):
    _seed_projects_events()
    anon = client.post("/api/knowledge/search", json={"query": "alpha", "modes": ["project"]}).json()["project"]
    assert PROJECT_PUBLIC in {r["name"] for r in anon}
    assert PROJECT_A not in {r["name"] for r in anon}, "an anonymous caller must not read a private project"

    other = client.post(
        "/api/knowledge/search", json={"query": "alpha", "modes": ["project"]}, headers=_auth(USER_B)
    ).json()["project"]
    assert PROJECT_A not in {r["name"] for r in other}, "a non-owner must not read another owner's private project"

    owner = client.post(
        "/api/knowledge/search", json={"query": "alpha", "modes": ["project"]}, headers=_auth(USER_A)
    ).json()["project"]
    assert PROJECT_A in {r["name"] for r in owner}, "the owner must still see their own project (positive control)"


def test_timeline_mode_does_not_leak_private_events(client):
    _seed_projects_events()
    anon = client.post("/api/knowledge/search", json={"query": "alpha", "modes": ["timeline"]}).json()["timeline"]
    assert anon == [], "the timeline is strictly owner-scoped: anonymous must read nothing"

    other = client.post(
        "/api/knowledge/search", json={"query": "alpha", "modes": ["timeline"]}, headers=_auth(USER_B)
    ).json()["timeline"]
    assert all(e.get("user_id") != USER_A for e in other), "a non-owner must not read another owner's events"

    owner = client.post(
        "/api/knowledge/search", json={"query": "alpha", "modes": ["timeline"]}, headers=_auth(USER_A)
    ).json()["timeline"]
    assert any(e.get("user_id") == USER_A for e in owner), "the owner must still see their own events (positive control)"


# ── no-fabrication: an unanswered scope is not an invented result ────────────

def test_search_with_no_matching_rows_is_an_empty_list_not_a_fabrication(client):
    _seed_notes()
    body = client.post(
        "/api/knowledge/search", json={"query": "zzz-no-such-term-zzz", "modes": ["fulltext", "people"]}
    ).json()
    assert body["fulltext"] == [] and body["people"] == []


# ── source-level guards for the repaired defects ─────────────────────────────

_RESERVED_DDL = re.compile(r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+(?P<name>\w+)\s*\(")
_SQL_RESERVED = {"references", "index", "order", "group", "select", "from", "where", "table", "values"}


def _unquoted_reserved_ddl(text: str) -> list[str]:
    """Table names declared unquoted that SQLite rejects as reserved words."""
    return [m.group("name") for m in _RESERVED_DDL.finditer(text) if m.group("name").lower() in _SQL_RESERVED]


def test_no_unquoted_reserved_word_table_is_declared():
    assert _unquoted_reserved_ddl(SCHEMA_SRC.read_text(encoding="utf-8")) == []


def test_detector_flags_the_pre_repair_ddl():
    """Negative control: the detector must bite on the exact pre-repair shape."""
    stale = "CREATE TABLE IF NOT EXISTS references (\n    id INTEGER\n);"
    assert _unquoted_reserved_ddl(stale) == ["references"]
    clean = 'CREATE TABLE IF NOT EXISTS "references" (\n    id INTEGER\n);'
    assert _unquoted_reserved_ddl(clean) == []


_UNSCOPED_CALL = re.compile(
    r"results\[[^\]]+\]\s*=\s*(project_search|timeline_search|people_search|graph_search)\("
)


def _call_arguments(text: str, open_paren: int) -> str:
    """The argument text of a call, balanced across nested parentheses.

    A naive ``[^)]*`` stops at the first ``)`` and misses ``user_id`` when an
    argument itself contains a call (e.g. ``limit=min(top_k, 50)``) — which would
    report a correctly-scoped dispatch as unscoped.
    """
    depth = 0
    for index in range(open_paren, len(text)):
        char = text[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return text[open_paren + 1:index]
    return text[open_paren + 1:]


def _unscoped_search_calls(text: str) -> list[str]:
    """``unified_search`` dispatch calls that omit ``user_id``.

    The ownership predicate is applied by the inner searches, so a dispatch that
    does not forward ``user_id`` silently serves every owner's rows.
    """
    found = []
    for match in _UNSCOPED_CALL.finditer(text):
        if "user_id=" not in _call_arguments(text, match.end() - 1):
            found.append(match.group(1))
    return found


def test_unified_search_forwards_user_id_to_every_scoped_mode():
    body = SEARCH_SRC.read_text(encoding="utf-8")
    assert _unscoped_search_calls(body) == [], "every owner-scoped mode must forward user_id"


def test_detector_flags_an_unscoped_dispatch():
    """Negative control: the pre-repair dispatch shape must be reported."""
    stale = 'results["project"] = project_search(query, limit=10)'
    assert _unscoped_search_calls(stale) == ["project_search"]
    clean = 'results["project"] = project_search(query, limit=10, user_id=user_id)'
    assert _unscoped_search_calls(clean) == []


# ── the request's top_k reaches every mode ───────────────────────────────────
#
# ``project``, ``people`` and ``reference`` were dispatched with a hardcoded
# ``limit=10``, so the request's ``top_k`` was accepted and then discarded: with
# 25 matching rows each returned exactly 10 at ``top_k=5``, ``10`` *and* ``50``.
# ``semantic``/``fulltext``/``tag``/``timeline`` forwarded it, so the panel's
# ``top_k: 20`` was honoured for some modes and silently ignored for others.

BOUND_MARK = "ARKADIA_BOUND_CANARY_WS3"
BOUND_ROWS = 25


def _seed_bound_rows() -> None:
    """More matching rows than the old hardcoded ceiling, in all three modes."""
    note = create_note(title=f"{BOUND_MARK} anchor", content="anchor", user_id=None)
    for index in range(BOUND_ROWS):
        create_project(f"{BOUND_MARK} project {index}", f"bound canary {index}", user_id=None)
        execute(
            'INSERT INTO "references" (source_note_id, target_ref, label) VALUES (?, ?, ?)',
            (note["id"], f"{BOUND_MARK}-reference-{index}", f"bound canary {index}"),
        )


def _bound_counts(client, top_k: int) -> dict[str, int]:
    body = client.post(
        "/api/knowledge/search",
        json={"query": BOUND_MARK, "modes": ["project", "reference"], "top_k": top_k},
    ).json()
    return {mode: len(records) for mode, records in body.items()}


@pytest.mark.parametrize("top_k", [5, 20, 100])
def test_every_mode_honours_the_requested_top_k(client, top_k):
    """Each mode returns ``min(top_k, matching)`` — the request's bound, not a constant."""
    _seed_bound_rows()
    counts = _bound_counts(client, top_k)
    expected = min(top_k, BOUND_ROWS)
    for mode, count in counts.items():
        assert count == expected, f"mode {mode!r} returned {count}, expected {expected} at top_k={top_k}"


def test_top_k_below_the_old_ceiling_is_not_over_delivered(client):
    """Positive control for the pin above: the pre-repair code returned 10 here.

    ``min(top_k, rows)`` alone would also pass if the ceiling moved to some other
    constant, so the discriminating case is a bound *below* the old hardcoded 10.
    """
    _seed_bound_rows()
    assert _bound_counts(client, 5) == {"project": 5, "reference": 5}


def test_non_positive_top_k_reads_no_rows_rather_than_every_row(client):
    """SQLite reads a negative ``LIMIT`` as *unlimited*.

    A repair that forwarded ``top_k`` verbatim would turn ``top_k=-1`` into an
    unbounded read of the whole store, so the bound is floored at 0.
    """
    _seed_bound_rows()
    assert _bound_counts(client, 0) == {"project": 0, "reference": 0}
    assert _bound_counts(client, -1) == {"project": 0, "reference": 0}


_HARDCODED_LIMIT_CALL = re.compile(
    r"results\[[^\]]+\]\s*=\s*(project_search|people_search|reference_search)\([^)]*\blimit\s*=\s*\d+"
)


def _hardcoded_limit_calls(text: str) -> list[str]:
    """``unified_search`` dispatches that pin a literal ``limit`` instead of ``top_k``.

    A literal here is not merely a default: it overrides the caller's ``top_k``,
    so the request's bound is accepted and discarded for that mode only.
    """
    return [match.group(1) for match in _HARDCODED_LIMIT_CALL.finditer(text)]


def test_unified_search_pins_no_literal_mode_limit():
    body = SEARCH_SRC.read_text(encoding="utf-8")
    assert _hardcoded_limit_calls(body) == [], "a literal limit discards the request's top_k"


def test_detector_flags_the_pre_repair_hardcoded_limit():
    """Negative control: the detector must bite on the exact pre-repair shape."""
    stale = 'results["reference"] = reference_search(query, limit=10)'
    assert _hardcoded_limit_calls(stale) == ["reference_search"]
    clean = 'results["reference"] = reference_search(query, limit=mode_limit)'
    assert _hardcoded_limit_calls(clean) == []
    # A forwarded top_k is the repaired shape for the modes that already worked.
    forwarded = 'results["timeline"] = timeline_search(keyword=query, limit=min(top_k, 50), user_id=user_id)'
    assert _hardcoded_limit_calls(forwarded) == []


# ── the panel keeps the boundary server-side and honest states visible ───────

def _panel_source() -> str:
    return PANEL.read_text(encoding="utf-8")


def test_panel_does_not_reimplement_the_ownership_boundary_client_side():
    panel = _panel_source()
    assert "user_id" not in panel, "the boundary is the backend's; a client filter only looks like one"


def test_panel_does_not_fabricate_a_placeholder_record():
    panel = _panel_source()
    assert "Record ${" not in panel and "Sample" not in panel
    assert "isKnowledgeSearchData" in panel, "an unrecognised payload must be rejected, not rendered"


def test_panel_declares_distinct_loading_empty_error_states():
    panel = _panel_source()
    for marker in ("Searching…", "returned no records", 'role="alert"'):
        assert marker in panel, f"missing honest state: {marker}"


def test_panel_uses_the_shared_client_and_no_hardcoded_host():
    panel = _panel_source()
    assert 'from "../../lib/apiClient"' in panel
    assert not re.search(r"https?://|VITE_API_URL", panel)


def test_contracts_guard_rejects_a_non_array_mode_value():
    contracts = CONTRACTS.read_text(encoding="utf-8")
    assert "isKnowledgeSearchData" in contracts and "Object.values(value).every(Array.isArray)" in contracts


def test_page_mounts_search_only_from_the_registry_entry():
    """The verified path must be reached through the shared registry.

    Workstream 1 owns ``lib/endpoints.ts``. The registry now carries
    ``knowledgeSearch`` (integrated in ``67696372``), so the page mounts the panel
    directly from the named registry entry. A page-local literal path is still the
    second-registry defect §3.1 forbids and must not appear as a request target.

    This pin was originally written for the *blocked* state, when the registry did
    not yet carry the entry; that intermediate state is superseded, not violated.
    """
    page = PAGE.read_text(encoding="utf-8")
    assert "KnowledgeSearchPanel" in page
    assert "endpoints.knowledgeSearch" in page
    # The literal path may appear as advertised display copy, never as a request target.
    assert 'apiRequest<unknown>("/api/knowledge/search"' not in page
    assert 'apiRequest("/api/knowledge/search"' not in page
