"""Workstream 3 — Knowledge OS notes reader: contract, owner boundary, honest states.

Binds the *declared* ``GET /api/knowledge/notes`` read contract to its handler and
ownership predicate, at the HTTP layer the console actually speaks.

Contract under test (read from the handler, not invented):

  * ``GET /api/knowledge/notes`` -> ``api.knowledge_routes.list_notes``
    -> ``knowledge.vault.list_notes``; a bare list, ``ORDER BY created_at DESC``
  * ``GET /api/knowledge/notes/{note_uuid}`` -> ``::get_note``; ``404`` when the
    note is not readable by the caller
  * identity is resolved with the *optional* auth dependency
    (``api.knowledge_routes._optional_user_id``)
  * ownership predicate ``knowledge.vault._note_owner_clause``:
    authenticated ``(user_id = ? OR user_id IS NULL)``; anonymous ``user_id IS NULL``

Why this guard exists
---------------------
The notes *reader* is the one knowledge surface with **no** boundary guard. Its
siblings each have one (``test_knowledge_projects_boundary.py``,
``test_knowledge_timeline_boundary.py``, ``test_knowledge_search_boundary.py``,
``test_knowledge_status_read_boundary.py``), and the existing notes coverage pins
the **vault function** — ``tests/test_isolation.py::test_list_notes_ownership``
calls ``list_notes(user_id=...)`` directly — never the **handler wiring** that
derives that ``user_id`` from the request.

That gap is load-bearing, and it is measured, not assumed. Deleting
``user_id=await _optional_user_id(request)`` from the ``list_notes`` handler
leaves every pre-existing knowledge guard green (measured 130 passed at `main`
`4ff76c15`: the eight sibling knowledge boundary guards listed above, run
together, with this reader's own wiring replaced by `user_id=None`), because a
vault-level call with an explicit ``user_id`` never exercises the identity path.
The reader would then answer *anonymous scope* to every caller — a signed-in
owner silently loses their own private notes, and the failure is invisible to the
suite. The cross-owner control below is the pin that catches it.

This reader is the **same** ownership shape as projects: there **is** a public
corpus here, so an anonymous caller legitimately reads notes and a ``[]`` is a
genuine empty read — not the timeline's ``1 = 0`` refusal.

Token mechanics: with no Firebase service account the auth layer runs in
dev-mode and decodes an unsigned JWT payload for identity. The guard below skips
(rather than silently passing) if that precondition is not met.
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
from knowledge.db import get_connection
from knowledge.vault import create_note

pytestmark = pytest.mark.skipif(
    not auth._dev_mode,
    reason="identity tokens require the auth layer's dev-mode (no Firebase service account)",
)

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "web" / "arkadia_console" / "src"
ROUTES_SOURCE = ROOT / "api" / "knowledge_routes.py"
VAULT_SOURCE = ROOT / "knowledge" / "vault.py"

USER_A = "ws3-notes-user-a"
USER_B = "ws3-notes-user-b"
PRIVATE_A = "ARKADIA_NOTE_CANARY_WS3_USER_A"
PRIVATE_B = "ARKADIA_NOTE_CANARY_WS3_USER_B"
PUBLIC_NOTE = "ARKADIA_PUBLIC_NOTE_WS3"


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


def _seed() -> dict[str, dict]:
    return {
        "a": create_note(PRIVATE_A, "private a", user_id=USER_A),
        "b": create_note(PRIVATE_B, "private b", user_id=USER_B),
        "public": create_note(PUBLIC_NOTE, "open corpus", user_id=None),
    }


def _titles(payload: list[dict]) -> set[str]:
    return {note["title"] for note in payload}


# ── contract shape ───────────────────────────────────────────────────────────

def test_notes_contract_returns_a_list_of_rows(client):
    _seed()
    body = client.get("/api/knowledge/notes", headers=_auth(USER_A)).json()
    assert isinstance(body, list), "the reader returns a bare list, not a wrapper object"
    assert body, "positive control: the seeded owner must have readable notes"
    assert set(body[0]) >= {"id", "uuid", "title", "content", "user_id", "note_type", "created_at"}


def test_notes_order_by_created_at_descending(client):
    """``list_notes`` orders by ``created_at DESC`` -- newest first."""
    _seed()
    stamps = [note["created_at"] for note in client.get("/api/knowledge/notes", headers=_auth(USER_A)).json()]
    assert stamps == sorted(stamps, reverse=True)


# ── owner boundary: a public corpus DOES exist on this reader ────────────────

def test_anonymous_reads_the_public_corpus(client):
    """Unlike the timeline, anonymous is a meaningful scope here, not `1 = 0`."""
    _seed()
    response = client.get("/api/knowledge/notes")
    assert response.status_code == 200
    titles = _titles(response.json())
    assert PUBLIC_NOTE in titles, "the public corpus is readable without identity on this reader"
    assert PRIVATE_A not in titles and PRIVATE_B not in titles


def test_authenticated_scope_is_own_plus_public(client):
    """The handler must forward the caller's identity into the vault predicate.

    This is the pin for the measured gap: a handler that dropped
    ``user_id=await _optional_user_id(request)`` answers the *anonymous* scope to
    everyone, and the owner silently loses their own private notes.
    """
    _seed()
    titles = _titles(client.get("/api/knowledge/notes", headers=_auth(USER_A)).json())
    assert PRIVATE_A in titles, "positive control: the owner sees their own private note"
    assert PUBLIC_NOTE in titles
    assert PRIVATE_B not in titles


def test_notes_do_not_leak_across_users(client):
    """The primary cross-owner leakage control."""
    _seed()
    a_titles = _titles(client.get("/api/knowledge/notes", headers=_auth(USER_A)).json())
    b_titles = _titles(client.get("/api/knowledge/notes", headers=_auth(USER_B)).json())
    assert PRIVATE_A in a_titles and PRIVATE_A not in b_titles, "B must not read A's private note"
    assert PRIVATE_B in b_titles and PRIVATE_B not in a_titles, "A must not read B's private note"


def test_authenticated_read_is_not_the_anonymous_scope(client):
    """A signed-in caller must not be served the anonymous answer.

    Negative control for the wiring gap: if the handler forgot the identity, these
    two answers would be identical and the owner's own note would vanish.
    """
    _seed()
    anon = _titles(client.get("/api/knowledge/notes").json())
    owner = _titles(client.get("/api/knowledge/notes", headers=_auth(USER_A)).json())
    assert owner != anon, "an authenticated read must differ from the anonymous scope"
    assert owner - anon == {PRIVATE_A}, "the only extra note an owner sees is their own private one"


# ── the single-note read is fail-closed ──────────────────────────────────────

def test_single_note_read_denies_non_owner_with_404(client):
    """Fail-closed: a non-owner gets `404`, not a distinguishable `403`."""
    seeded = _seed()
    uuid = seeded["a"]["uuid"]
    assert client.get(f"/api/knowledge/notes/{uuid}").status_code == 404
    assert client.get(f"/api/knowledge/notes/{uuid}", headers=_auth(USER_B)).status_code == 404
    assert client.get(f"/api/knowledge/notes/{uuid}", headers=_auth(USER_A)).status_code == 200


def test_single_note_read_is_not_a_public_corpus_backdoor(client):
    """A public note is readable, but a private one is not addressed by uuid."""
    seeded = _seed()
    assert client.get(f"/api/knowledge/notes/{seeded['public']['uuid']}").status_code == 200
    for headers in ({}, _auth(USER_B)):
        assert client.get(f"/api/knowledge/notes/{seeded['a']['uuid']}", headers=headers).status_code == 404


# ── mutation stays owner-only (the write half of the same boundary) ──────────

def test_private_note_mutation_requires_authentication(client):
    seeded = _seed()
    uuid = seeded["a"]["uuid"]
    assert client.patch(f"/api/knowledge/notes/{uuid}", json={"title": "x"}).status_code == 401
    assert client.delete(f"/api/knowledge/notes/{uuid}").status_code == 401


def test_private_note_mutation_denies_non_owner(client):
    seeded = _seed()
    uuid = seeded["a"]["uuid"]
    assert client.patch(f"/api/knowledge/notes/{uuid}", json={"title": "x"}, headers=_auth(USER_B)).status_code == 404
    assert client.delete(f"/api/knowledge/notes/{uuid}", headers=_auth(USER_B)).status_code == 404


# ── empty is a real empty read here (the opposite of the timeline) ───────────

def test_empty_scope_is_a_genuine_empty_read(client):
    """No rows at all: the public corpus is empty, so `[]` means empty."""
    assert client.get("/api/knowledge/notes").json() == []
    assert client.get("/api/knowledge/notes", headers=_auth(USER_A)).json() == []


# ── the source pin: the handler must derive identity from the request ────────

def test_list_handler_forwards_the_request_identity_to_the_vault():
    """A source-level pin for the wiring the behavioral controls above measure.

    The vault predicate is already covered by ``tests/test_isolation.py``, which
    calls it with an explicit ``user_id``. What nothing pinned is that the *route*
    obtains that ``user_id`` from the request at all.
    """
    source = ROUTES_SOURCE.read_text(encoding="utf-8")
    handler = source.split('@router.get("/notes")', 1)[1].split('@router.get("/notes/{note_uuid}")', 1)[0]
    assert "await _optional_user_id(request)" in handler, (
        "the notes list handler must resolve identity from the request; "
        "without it every caller is served the anonymous scope"
    )
    assert re.search(r"list_notes\([^)]*user_id=", handler, re.S), (
        "the resolved identity must be forwarded into list_notes"
    )
    assert "_note_owner_clause" in VAULT_SOURCE.read_text(encoding="utf-8")


def test_notes_reader_is_served_alongside_the_mounted_knowledge_panels(client):
    """The reader is served, and the console's knowledge page is its serving surface.

    The console has **no** notes consumer today — the archived Prism rendered one at
    ``ProjectsView.tsx`` — and the canonical registry declares no ``notes`` path. That
    is recorded here rather than papered over: this guard binds the *backend* contract
    the sibling readers already rely on, and the missing reader is a separate bounded
    slice whose path declaration belongs to the registry owner (Workstream 1).
    """
    assert client.get("/api/knowledge/notes").status_code == 200
    page = (CONSOLE / "pages" / "KnowledgePage.tsx").read_text(encoding="utf-8")
    for panel in ("KnowledgeProjectsPanel", "KnowledgeTimelinePanel", "KnowledgeGraphPanel"):
        assert panel in page, f"the knowledge page mounts {panel}; the readers share one surface"
