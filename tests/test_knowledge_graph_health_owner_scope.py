"""Workstream 3 — Knowledge graph analytics: owner scope + the silent-error defect.

Two production-observed defects on the K3-B/K3-C graph surfaces:

  1. ``knowledge.graph_health`` evaluated every check over the *whole* store, so
     ``GET /api/knowledge/graph/health`` and ``GET /api/knowledge/relationships``
     described — and named — notes the caller cannot read. The contract is
     owner-or-public: authenticated callers see ``user_id = ? OR user_id IS NULL``,
     anonymous callers see the public ``user_id IS NULL`` corpus only.
  2. ``graph_health._count`` read ``list(row)[0]`` from a row that ``knowledge.db``
     returns as a **dict**, so it yielded the *column name* (``'COUNT(*)'``) rather
     than the count. ``evaluate_graph_health`` then failed on the first division
     (``unsupported operand type(s) for /: 'str' and 'str'``) and, because it
     catches ``Exception``, returned ``{"overall": "error", "checks": {}}`` — the
     production surface reported a permanent error instead of a health verdict.
     Measured on base: ``_count("SELECT COUNT(*) FROM notes")`` -> ``'COUNT(*)'``.

Contract under test (read from the handlers, not invented):

  * ``GET /api/knowledge/graph/health`` -> ``api.knowledge_routes.graph_health``
    -> ``knowledge.graph_health.evaluate_graph_health``
  * ``GET /api/knowledge/relationships`` -> ``api.knowledge_routes.graph_relationships``
  * identity via the *optional* auth dependency
    (``api.knowledge_routes._optional_user_id``), so anonymous is a real caller
  * ownership predicate ``knowledge.graph_health._note_owner_clause``, and edges
    participate only when **both** endpoints are accessible

The negative controls below prove the assertions can bite: the same fixture
measured through the *unscoped* queries returns different numbers, and the
cross-owner edge is invisible to both owners.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import api.auth as auth
from api.knowledge_routes import router as knowledge_router
from knowledge.db import execute, get_connection
import knowledge.graph_health as gh

pytestmark = pytest.mark.skipif(
    not auth._dev_mode,
    reason="identity tokens require the auth layer's dev-mode (no Firebase service account)",
)

ROOT = Path(__file__).resolve().parents[1]
HEALTH_SOURCE = ROOT / "knowledge" / "graph_health.py"

USER_A = "ws3-graph-user-a"
USER_B = "ws3-graph-user-b"
CANARY_A = "ARKADIA_GRAPH_CANARY_WS3_USER_A"
CANARY_B = "ARKADIA_GRAPH_CANARY_WS3_USER_B"


def _token(uid: str) -> str:
    payload = base64.urlsafe_b64encode(json.dumps({"user_id": uid}).encode()).rstrip(b"=").decode()
    return f"header.{payload}.signature"


def _auth(uid: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(uid)}"}


@pytest.fixture(autouse=True)
def _fresh_store():
    """Clear the sandboxed knowledge store so each test owns its rows."""
    conn = get_connection()
    for table in ("graph_edges", "timeline", "chunks", "embeddings", "note_tags", "notes", "threads", "projects"):
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


def _note(title: str, user_id: str | None) -> int:
    import uuid as _uuid
    execute(
        "INSERT INTO notes (uuid, title, content, vault_path, note_type, user_id) "
        "VALUES (?, ?, '', ?, 'note', ?)",
        (str(_uuid.uuid4()), title, f"notes/{_uuid.uuid4()}.md", user_id),
    )
    from knowledge.db import execute_one
    return execute_one("SELECT MAX(id) as i FROM notes")["i"]


def _seed() -> dict[str, int]:
    """Two owners, a public note, and a cross-owner edge that must stay invisible.

    A3 -- B3 is the load-bearing edge: it joins an A-owned node to a B-owned node,
    so an unscoped component count sees one graph where each owner sees their own.
    """
    ids = {
        "public": _note(CANARY_A + "_PUBLIC", None),
        "a1": _note(CANARY_A + "_1", USER_A),
        "a2": _note(CANARY_A + "_2", USER_A),
        "a3": _note(CANARY_A + "_3", USER_A),
        "b1": _note(CANARY_B + "_1", USER_B),
        "b2": _note(CANARY_B + "_2", USER_B),
        "b3": _note(CANARY_B + "_3", USER_B),
    }
    execute("INSERT INTO graph_edges (source_note_id, target_note_id, relationship) VALUES (?,?,?)", (ids["a1"], ids["a2"], "references"))
    execute("INSERT INTO graph_edges (source_note_id, target_note_id, relationship) VALUES (?,?,?)", (ids["b1"], ids["b2"], "references"))
    execute("INSERT INTO graph_edges (source_note_id, target_note_id, relationship) VALUES (?,?,?)", (ids["a3"], ids["b3"], "references"))
    return ids


# ── defect 2: the silent error ───────────────────────────────────────────────

def test_count_reads_a_value_not_a_column_name():
    """``_count`` must return the count, not the column name.

    The shipped revision used ``list(row)[0]`` on a dict row, which yields the
    *key* (``'n'``), not the value; ``evaluate_graph_health`` then failed on the
    first division and swallowed it into ``{"overall": "error", "checks": {}}``.
    """
    _seed()
    value = gh._count("SELECT COUNT(*) as n FROM notes")
    assert isinstance(value, int), (
        f"_count returned {value!r} ({type(value).__name__}); knowledge.db yields dict rows, "
        "so a positional read yields the column name, not the count"
    )
    assert value == 7, "positive control: the seven seeded notes are counted"


def test_graph_health_is_a_verdict_not_a_swallowed_error():
    """The health surface must not report a permanent error on a healthy store."""
    _seed()
    result = gh.evaluate_graph_health()
    assert "error" not in result, (
        f"evaluate_graph_health swallowed an exception: {result.get('error')!r}"
    )
    assert result["overall"] in {"ok", "warn"}, "a seeded store yields a real verdict"
    assert set(result["checks"]) == {
        "orphan_nodes", "duplicate_nodes", "invalid_references",
        "ontology_violations", "embedding_completeness", "graph_connectivity",
    }


# ── defect 1: owner scope ────────────────────────────────────────────────────

def test_graph_health_endpoint_is_scoped_to_the_caller(client):
    _seed()
    body = client.get("/api/knowledge/graph/health", headers=_auth(USER_A)).json()
    assert body.get("error") is None, body
    orphans = body["checks"]["orphan_nodes"]
    assert orphans["total_nodes"] == 4, (
        "USER_A can read the public note plus their own three; the other owner's "
        f"three must not be counted (got {orphans['total_nodes']})"
    )
    assert body["checks"]["graph_connectivity"]["components"] == 1, (
        "only A1--A2 is accessible to USER_A; the cross-owner A3--B3 edge must not "
        "join B's component into the caller's view"
    )


def test_relationships_route_counts_only_accessible_edges(client):
    _seed()
    body = client.get("/api/knowledge/relationships", headers=_auth(USER_A)).json()
    summary = body.get("summary", {})
    assert summary.get("total_nodes") == 4, body
    assert summary.get("total_relationships") == 1, (
        "only A1--A2 has both endpoints accessible to USER_A; the cross-owner A3--B3 "
        f"edge must not be counted (got {summary.get('total_relationships')})"
    )
    assert summary.get("connected_components") == 1, (
        "the cross-owner edge must not merge B's component into the caller's graph"
    )
    assert [entry["count"] for entry in body.get("relationship_distribution", [])] == [1]


def test_relationships_route_never_names_another_owners_note(client):
    """Top-connected nodes carry titles, so this is a disclosure surface."""
    _seed()
    body = client.get("/api/knowledge/relationships", headers=_auth(USER_A)).json()
    titles = [node.get("title") or "" for node in body.get("top_connected_nodes", [])]
    assert titles, "positive control: the route returns the caller's own nodes"
    assert not any(CANARY_B in title for title in titles), (
        f"another owner's title leaked through top_connected_nodes: {titles}"
    )


def test_anonymous_caller_sees_only_the_public_corpus(client):
    """Anonymous is a real caller, not a refused one."""
    _seed()
    response = client.get("/api/knowledge/graph/health")
    assert response.status_code == 200
    body = response.json()
    assert body["checks"]["orphan_nodes"]["total_nodes"] == 1, (
        "the anonymous scope is `user_id IS NULL` -- the single public note, no private notes"
    )
    assert body["checks"]["graph_connectivity"]["components"] == 0, (
        "the public note has no edges, so the anonymous graph has no components"
    )


def test_negative_control_unscoped_queries_disagree_with_the_scoped_answers(client):
    """Prove the scope is what produces the numbers above, not the fixture.

    The pre-repair queries are re-run verbatim; if they agreed with the scoped
    answer the assertions above would be vacuous.
    """
    _seed()
    from knowledge.db import execute_one
    unscoped_nodes = execute_one("SELECT COUNT(*) as n FROM notes")["n"]
    unscoped_edges = execute_one("SELECT COUNT(*) as n FROM graph_edges")["n"]
    scoped_nodes = execute_one(
        "SELECT COUNT(*) as n FROM notes WHERE (user_id = ? OR user_id IS NULL)", (USER_A,)
    )["n"]

    assert unscoped_nodes == 7 and scoped_nodes == 4, "the fixture discriminates"
    assert unscoped_edges == 3, "the cross-owner edge exists and is visible unscoped"
    assert unscoped_nodes != scoped_nodes, (
        "a store where scoped and unscoped agree cannot detect a missing scope"
    )


def test_source_keeps_the_scope_on_every_graph_read():
    """Guard the source itself: a later edit must not silently drop the predicate."""
    source = HEALTH_SOURCE.read_text()
    assert "_note_owner_clause" in source, "the ownership predicate must live in graph_health"
    for check in (
        "_check_orphan_nodes", "_check_duplicate_nodes", "_check_ontology_violations",
        "_check_embedding_completeness", "_check_graph_connectivity",
    ):
        assert f"def {check}(user_id" in source, f"{check} must accept the caller identity"
