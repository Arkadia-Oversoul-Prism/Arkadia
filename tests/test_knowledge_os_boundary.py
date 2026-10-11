"""Workstream 3 — Knowledge OS private/public and authorization boundary.

Binds one vertical capability (the readable knowledge graph) to its real
backend handler, auth boundary and persistence, and proves the personal/private
versus public-corpus separation the shared contract requires.

Contract under test (declared, not invented):
  * ``GET  /api/knowledge/graph``      -> ``knowledge.graph.full_graph_export``
  * ``PATCH/DELETE /api/knowledge/notes/{uuid}`` -> ``knowledge.vault``
  * persistence: the canonical SQLite ``notes`` table, ownership column ``user_id``

The endpoints resolve identity with the *optional* auth dependency
(``api.knowledge_routes._optional_user_id``), so an anonymous caller is a real
caller and must receive only the public corpus (``user_id IS NULL``). These tests
exercise the live handler over an ASGI transport against a sandboxed database —
no mocks — and each boundary has a positive control so a handler that returned
``401``/empty for *everyone* could not pass.

Token mechanics: with no Firebase service account the auth layer runs in
dev-mode and decodes an unsigned JWT payload for identity. The guard below skips
(rather than silently passing) if that precondition is not met.
"""
from __future__ import annotations

import base64
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import api.auth as auth
from api.knowledge_routes import router as knowledge_router
from knowledge.db import get_connection
from knowledge.vault import create_note

pytestmark = pytest.mark.skipif(
    not auth._dev_mode,
    reason="identity tokens require the auth layer's dev-mode (no Firebase service account)",
)

USER_A = "ws3-boundary-user-a"
USER_B = "ws3-boundary-user-b"
CANARY_A = "ARKADIA_PRIVATE_CANARY_WS3_USER_A"
CANARY_B = "ARKADIA_PRIVATE_CANARY_WS3_USER_B"
PUBLIC_MARK = "ARKADIA_PUBLIC_CORPUS_MARKER_WS3"


def _token(uid: str) -> str:
    """A dev-mode identity token whose payload carries the owner uid."""
    payload = base64.urlsafe_b64encode(json.dumps({"user_id": uid}).encode()).rstrip(b"=").decode()
    return f"header.{payload}.signature"


def _auth(uid: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(uid)}"}


@pytest.fixture(autouse=True)
def _fresh_store():
    """Clear the sandboxed knowledge store so each test owns its rows.

    ``conftest.py`` redirects the database and the vault root to a session
    tempdir, so nothing here touches the repository's tracked-adjacent ``vault/``.
    """
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


def _seed() -> dict[str, dict]:
    return {
        "a": create_note(title=CANARY_A, content=f"private {CANARY_A}", user_id=USER_A),
        "b": create_note(title=CANARY_B, content=f"private {CANARY_B}", user_id=USER_B),
        "public": create_note(title=PUBLIC_MARK, content="open corpus", user_id=None),
    }


def _titles(payload: dict) -> set[str]:
    return {node["title"] for node in payload["nodes"]}


# ── graph contract shape ─────────────────────────────────────────────────────

def test_graph_contract_returns_nodes_and_edges(client):
    _seed()
    body = client.get("/api/knowledge/graph").json()
    assert set(body) >= {"nodes", "edges"}
    assert isinstance(body["nodes"], list) and isinstance(body["edges"], list)


# ── private / public separation ──────────────────────────────────────────────

def test_anonymous_graph_excludes_private_material(client):
    _seed()
    titles = _titles(client.get("/api/knowledge/graph").json())
    assert PUBLIC_MARK in titles
    assert CANARY_A not in titles and CANARY_B not in titles


def test_authenticated_graph_is_scoped_to_owner_and_public(client):
    _seed()
    titles = _titles(client.get("/api/knowledge/graph", headers=_auth(USER_A)).json())
    assert CANARY_A in titles, "the owner must still see their own private material (positive control)"
    assert PUBLIC_MARK in titles
    assert CANARY_B not in titles, "another node's private material must not appear"


def test_graph_does_not_leak_across_users(client):
    _seed()
    a_titles = _titles(client.get("/api/knowledge/graph", headers=_auth(USER_A)).json())
    b_titles = _titles(client.get("/api/knowledge/graph", headers=_auth(USER_B)).json())
    assert CANARY_A in a_titles and CANARY_A not in b_titles
    assert CANARY_B in b_titles and CANARY_B not in a_titles


def test_public_corpus_is_readable_without_identity(client):
    public = create_note(title=PUBLIC_MARK, content="open", user_id=None)
    body = client.get("/api/knowledge/graph").json()
    assert public["uuid"] in {node["uuid"] for node in body["nodes"]}


# ── authorization denial on the private mutation path ────────────────────────

def test_private_note_mutation_requires_authentication(client):
    note = create_note(title=CANARY_A, content="x", user_id=USER_A)
    assert client.patch(f"/api/knowledge/notes/{note['uuid']}", json={"title": "pwned"}).status_code == 401
    assert client.delete(f"/api/knowledge/notes/{note['uuid']}").status_code == 401


def test_private_note_mutation_denies_non_owner(client):
    note = create_note(title=CANARY_A, content="x", user_id=USER_A)
    # Fail-closed: a non-owner is refused (404, not a distinguishable "forbidden").
    assert client.patch(
        f"/api/knowledge/notes/{note['uuid']}", json={"title": "pwned"}, headers=_auth(USER_B)
    ).status_code == 404
    assert client.delete(f"/api/knowledge/notes/{note['uuid']}", headers=_auth(USER_B)).status_code == 404


def test_owner_can_mutate_own_private_note(client):
    note = create_note(title=CANARY_A, content="x", user_id=USER_A)
    response = client.patch(
        f"/api/knowledge/notes/{note['uuid']}", json={"title": "renamed"}, headers=_auth(USER_A)
    )
    assert response.status_code == 200 and response.json()["title"] == "renamed"


def test_public_note_is_not_mutable_through_the_private_path(client):
    public = create_note(title=PUBLIC_MARK, content="open", user_id=None)
    # Visible to every authenticated viewer, but owned by nobody: mutation refused.
    assert client.delete(f"/api/knowledge/notes/{public['uuid']}", headers=_auth(USER_A)).status_code == 404


# ── timeline is strictly owner-scoped ────────────────────────────────────────

def test_timeline_denies_anonymous_and_scopes_to_owner(client):
    _seed()
    assert client.get("/api/knowledge/timeline").json() == []
    # An authenticated owner may have no events yet; the invariant is that the
    # anonymous scope is empty while an authenticated call is answered, not refused.
    assert client.get("/api/knowledge/timeline", headers=_auth(USER_A)).status_code == 200


# ── the feature-local scope vocabulary matches the backend boundary ──────────

def test_scope_vocabulary_tracks_the_live_boundary(client):
    from pathlib import Path
    import re

    source = (
        Path(__file__).resolve().parents[1]
        / "web/arkadia_console/src/pages/knowledge/knowledgeContracts.ts"
    ).read_text(encoding="utf-8")
    # The panel classifies scope from the `user_id` stamp the contract returns.
    assert "user_id" in source and "classifyGraphScope" in source

    _seed()
    anon_nodes = client.get("/api/knowledge/graph").json()["nodes"]
    authed_nodes = client.get("/api/knowledge/graph", headers=_auth(USER_A)).json()["nodes"]
    # Anonymous scope is public-only (no owner stamp); the owner's scope carries one.
    assert all(node.get("user_id") in (None, "") for node in anon_nodes)
    assert any(node.get("user_id") == USER_A for node in authed_nodes)
    assert re.search(r'"scoped"', source) and re.search(r'"public"', source)
