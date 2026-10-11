"""Workstream 3 — Knowledge OS projects reader: contract, owner boundary, honest states.

Binds the *declared* ``GET /api/knowledge/projects`` contract to its handler and
ownership predicate, then binds the feature-local reader to that contract.

Contract under test (read from the handler, not invented):

  * ``GET /api/knowledge/projects`` -> ``api.knowledge_routes.list_projects``
    -> ``knowledge.vault.list_projects``; a bare list, ``ORDER BY updated_at DESC``
  * ``GET /api/knowledge/projects/{name_or_uuid}`` -> ``::get_project``; ``404``
    when the project is not readable by the caller
  * identity is resolved with the *optional* auth dependency
    (``api.knowledge_routes._optional_user_id``)
  * ownership predicate ``knowledge.vault._project_owner_clause``:
    authenticated ``(user_id = ? OR user_id IS NULL)``; anonymous ``user_id IS NULL``

This reader is the **third** ownership shape in the subsystem, and it is *not*
the timeline's. There **is** a public corpus here, so an anonymous caller
legitimately reads projects; the anonymous scope is not empty by construction.
The consequence the panel must get right is the opposite of the timeline's: a
``[]`` here is always a genuine empty read, and a *public-only* answer to a
signed-in viewer is the boundary working, not a partial result. The negative
control below proves the pin can tell those apart.

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
from knowledge.vault import create_project

pytestmark = pytest.mark.skipif(
    not auth._dev_mode,
    reason="identity tokens require the auth layer's dev-mode (no Firebase service account)",
)

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "web" / "arkadia_console" / "src"
VAULT_SOURCE = ROOT / "knowledge" / "vault.py"
PANEL = CONSOLE / "components" / "knowledge" / "KnowledgeProjectsPanel.tsx"
CONTRACTS = CONSOLE / "pages" / "knowledge" / "knowledgeContracts.ts"

USER_A = "ws3-projects-user-a"
USER_B = "ws3-projects-user-b"
PRIVATE_A = "ARKADIA_PROJECT_CANARY_WS3_USER_A"
PRIVATE_B = "ARKADIA_PROJECT_CANARY_WS3_USER_B"
PUBLIC_PROJECT = "ARKADIA_PUBLIC_PROJECT_WS3"


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


def _seed() -> None:
    create_project(PRIVATE_A, "private a", user_id=USER_A)
    create_project(PRIVATE_B, "private b", user_id=USER_B)
    create_project(PUBLIC_PROJECT, "open corpus", user_id=None)


def _names(payload: list[dict]) -> set[str]:
    return {project["name"] for project in payload}


# ── contract shape ───────────────────────────────────────────────────────────

def test_projects_contract_returns_a_list_of_rows(client):
    _seed()
    body = client.get("/api/knowledge/projects", headers=_auth(USER_A)).json()
    assert isinstance(body, list), "the reader returns a bare list, not a wrapper object"
    assert body, "positive control: the seeded owner must have readable projects"
    assert set(body[0]) >= {
        "id", "uuid", "name", "description", "user_id", "tags", "status", "created_at", "updated_at",
    }


def test_projects_order_by_updated_at_descending(client):
    """``list_projects`` orders by ``updated_at DESC`` -- newest first."""
    _seed()
    stamps = [project["updated_at"] for project in client.get("/api/knowledge/projects", headers=_auth(USER_A)).json()]
    assert stamps == sorted(stamps, reverse=True)


def test_tags_column_is_a_json_string_on_the_wire(client):
    """The reader stores tags as JSON text; the panel parses it rather than
    assuming an array."""
    _seed()
    body = client.get("/api/knowledge/projects", headers=_auth(USER_A)).json()
    assert all(isinstance(project["tags"], str) for project in body), (
        "the contract carries tags as a JSON string; a declared array would be wrong"
    )


# ── owner boundary: a public corpus DOES exist on this reader ────────────────

def test_anonymous_reads_the_public_corpus(client):
    """Unlike the timeline, anonymous is a meaningful scope here, not `1 = 0`."""
    _seed()
    response = client.get("/api/knowledge/projects")
    assert response.status_code == 200
    names = _names(response.json())
    assert PUBLIC_PROJECT in names, "the public corpus is readable without identity on this reader"
    assert PRIVATE_A not in names and PRIVATE_B not in names


def test_authenticated_scope_is_own_plus_public(client):
    _seed()
    names = _names(client.get("/api/knowledge/projects", headers=_auth(USER_A)).json())
    assert PRIVATE_A in names, "positive control: the owner sees their own private project"
    assert PUBLIC_PROJECT in names
    assert PRIVATE_B not in names


def test_projects_do_not_leak_across_users(client):
    """The primary cross-owner leakage control."""
    _seed()
    a_names = _names(client.get("/api/knowledge/projects", headers=_auth(USER_A)).json())
    b_names = _names(client.get("/api/knowledge/projects", headers=_auth(USER_B)).json())
    assert PRIVATE_A in a_names and PRIVATE_A not in b_names, "B must not read A's private project"
    assert PRIVATE_B in b_names and PRIVATE_B not in a_names, "A must not read B's private project"


# ── the single-project read is fail-closed ───────────────────────────────────

def test_single_project_read_denies_non_owner_with_404(client):
    """Fail-closed: a non-owner gets `404`, not a distinguishable `403`."""
    _seed()
    assert client.get(f"/api/knowledge/projects/{PRIVATE_A}").status_code == 404
    assert client.get(f"/api/knowledge/projects/{PRIVATE_A}", headers=_auth(USER_B)).status_code == 404
    assert client.get(f"/api/knowledge/projects/{PRIVATE_A}", headers=_auth(USER_A)).status_code == 200


def test_single_project_read_is_not_a_public_corpus_backdoor(client):
    """A public project is readable, but a private one is not addressed by name."""
    _seed()
    assert client.get(f"/api/knowledge/projects/{PUBLIC_PROJECT}").status_code == 200
    # Same endpoint, private target: refused for every non-owner, including anonymous.
    for headers in ({}, _auth(USER_B)):
        assert client.get(f"/api/knowledge/projects/{PRIVATE_A}", headers=headers).status_code == 404


# ── empty is a real empty read here (the opposite of the timeline) ───────────

def test_empty_scope_is_a_genuine_empty_read(client):
    """No rows at all: the public corpus is empty, so `[]` means empty.

    This is the distinction that separates this reader from the timeline. There
    the anonymous `[]` was a refusal; here it is a true empty corpus, and the
    panel says so.
    """
    assert client.get("/api/knowledge/projects").json() == []
    assert client.get("/api/knowledge/projects", headers=_auth(USER_A)).json() == []

    contracts = CONTRACTS.read_text(encoding="utf-8")
    assert "classifyProjectScope" in contracts
    assert re.search(r'"public"', contracts) and re.search(r'"scoped"', contracts)


def test_public_only_answer_to_an_owner_is_reported_not_treated_as_partial(client):
    """An authenticated viewer seeing only the public corpus is the boundary
    working. The panel must report `public`, not present it as missing data."""
    create_project(PUBLIC_PROJECT, "open", user_id=None)
    names = _names(client.get("/api/knowledge/projects", headers=_auth(USER_A)).json())
    assert names == {PUBLIC_PROJECT}
    contracts = CONTRACTS.read_text(encoding="utf-8")
    assert "projectNotice" in contracts
    assert "Only public-corpus projects" in contracts


def test_failed_read_is_not_rendered_as_an_empty_project_list():
    panel = PANEL.read_text(encoding="utf-8")
    contracts = CONTRACTS.read_text(encoding="utf-8")
    assert "isKnowledgeProjects" in panel, "the panel must validate the payload"
    assert "ApiError" in panel, "an unrecognised body must raise, not render empty"
    assert "ContractState" in panel, "auth/unavailable/error states are distinct components"
    assert "isKnowledgeProjects" in contracts


# ── source detectors (each has a negative control below) ─────────────────────

_ANON_CLAUSE = re.compile(r"def _project_owner_clause.*?return \"([^\"]+)\", \(\)", re.DOTALL)


def anonymous_project_clause(source: str) -> str | None:
    """The anonymous owner clause, when it is not the public-corpus predicate.

    The invariant on this reader is that anonymous is scoped to the public
    corpus (`user_id IS NULL`) -- *not* that it is empty. A wildcard clause is a
    cross-owner leak; the timeline's fail-closed clause would be the wrong
    contract here.
    """
    match = _ANON_CLAUSE.search(source)
    if not match:
        return None
    return match.group(1).strip()


def inline_endpoint_path(source: str) -> list[str]:
    """Path literals a feature module inlines instead of using the registry."""
    return re.findall(r'"/(?:api|solspire)/[^"]*"', source)


def strip_comments(source: str) -> str:
    """A module's code with its block and line comments removed."""
    without_blocks = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?m)^\s*//.*$", "", without_blocks)


def test_anonymous_project_clause_is_the_public_corpus():
    clause = anonymous_project_clause(VAULT_SOURCE.read_text(encoding="utf-8"))
    assert clause is not None, "the reader must define an anonymous owner clause"
    assert clause.replace(" ", "") == "user_idISNULL", clause


def test_detector_flags_a_wildcard_project_clause():
    """The pre-repair shape that would leak every owner's projects."""
    leaky = 'def _project_owner_clause(user_id):\n    if user_id:\n        return "(user_id = ? OR user_id IS NULL)", (user_id,)\n    return "1 = 1", ()\n'
    assert anonymous_project_clause(leaky) == "1 = 1", "the detector must report a wildcard clause"
    fail_closed = 'def _project_owner_clause(user_id):\n    if user_id:\n        return "(user_id = ? OR user_id IS NULL)", (user_id,)\n    return "1 = 0", ()\n'
    assert anonymous_project_clause(fail_closed) == "1 = 0", (
        "the timeline's fail-closed clause is the wrong contract on this reader and "
        "must be reported rather than silently accepted"
    )


def test_panel_uses_the_registry_and_the_shared_client():
    panel = PANEL.read_text(encoding="utf-8")
    assert "endpoints.knowledgeProjects" in panel
    assert 'from "../../lib/apiClient"' in panel
    assert 'from "../../lib/useHydration"' in panel
    assert inline_endpoint_path(panel) == [], "the panel must not inline its endpoint path"


def test_detector_flags_an_inline_endpoint_path():
    assert inline_endpoint_path('const p = "/api/knowledge/projects";') == ['"/api/knowledge/projects"']
    assert inline_endpoint_path('const p = endpoints.knowledgeProjects;') == []


def test_panel_does_not_reimplement_the_ownership_boundary_client_side():
    """The server owns the predicate; a client-side filter could only *look* like
    a boundary while the response still carried the other owners' rows."""
    code = strip_comments(PANEL.read_text(encoding="utf-8"))
    assert ".filter((project) => project.user_id" not in code
    assert "user_id ?" in code or "user_id" in code, "the panel may *label* ownership, not filter on it"


def test_detector_ignores_a_comment_but_flags_real_code():
    prose_only = "/* the predicate is user_id IS NULL for anonymous callers */\nconst x = 1;"
    assert "user_id" not in strip_comments(prose_only)
    filtering = "const mine = projects.filter((p) => p.user_id === me);"
    assert "user_id" in strip_comments(filtering)
