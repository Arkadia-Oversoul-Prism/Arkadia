"""Workstream 3 — Knowledge OS single-project reader: contract, refusal boundary, honest states.

The project collection reader (`KnowledgeProjectsPanel` →
`GET /api/knowledge/projects`) is proven by `test_knowledge_projects_boundary.py`.
This guard covers the **detail** read that was recorded as the lane's next
bounded task and, unlike the collection, is missing from the console:

  * read shape — the route the reader composes is the one the canonical app serves
    (`GET /api/knowledge/projects/{name_or_uuid}`);
  * refusal boundary — a non-owner and a nonexistent id are *indistinguishable*
    (`404`), so the reader must not render one as an ordinary transport fault;
  * honest states — a failed read must never appear as an empty/detail-less result;
  * the reader composes its path from the registry entry (no second contract) and
    there is no N-request fan-out on mount.

The negative controls exercise the same detectors the live assertions use, so the
pin can be shown to bite on the defect it names.

Token mechanics: with no Firebase service account the auth layer runs in dev-mode
and decodes an unsigned JWT payload for identity. The guard skips (rather than
silently passing) if that precondition is not met.
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
DETAIL = CONSOLE / "components" / "knowledge" / "KnowledgeProjectDetail.tsx"
PANEL = CONSOLE / "components" / "knowledge" / "KnowledgeProjectsPanel.tsx"
CONTRACTS = CONSOLE / "pages" / "knowledge" / "knowledgeContracts.ts"
ENDPOINTS = CONSOLE / "lib" / "endpoints.ts"

USER_A = "ws3-detail-user-a"
USER_B = "ws3-detail-user-b"
PRIVATE_A = "ARKADIA_DETAIL_PROJECT_A"
PRIVATE_B = "ARKADIA_DETAIL_PROJECT_B"
PUBLIC_PROJECT = "ARKADIA_DETAIL_PUBLIC"


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


# ── the route the reader composes is the route the app serves ────────────────

def _collection_path() -> str:
    text = ENDPOINTS.read_text(encoding="utf-8")
    match = re.search(r'knowledgeProjects:\s*"([^"]+)"', text)
    assert match, "endpoints.ts must declare knowledgeProjects"
    return match.group(1)


def test_detail_route_is_served_by_the_canonical_app():
    """The reader composes a sub-resource of the collection entry; that composed
    route must be a handler, or the reader 404s in production while building
    cleanly."""
    from api.main import app

    served = set(app.openapi()["paths"].keys())
    template = f"{_collection_path()}/{{name_or_uuid}}"
    assert template in served, (
        f"the reader composes {template!r} but the canonical app does not serve it"
    )


def test_detail_returns_the_same_row_shape_as_the_collection(client):
    """Positive control: the owner reads their own project, and the row carries
    the fields the detail panel renders."""
    _seed()
    body = client.get(f"/api/knowledge/projects/{PRIVATE_A}", headers=_auth(USER_A)).json()
    assert isinstance(body, dict), "the detail read returns a row, not a list wrapper"
    assert set(body) >= {"uuid", "name", "description", "user_id", "tags", "status", "created_at", "updated_at"}


# ── the refusal boundary: a non-owner and a missing id are indistinguishable ──

def test_non_owner_and_missing_id_are_the_same_404(client):
    _seed()
    non_owner = client.get(f"/api/knowledge/projects/{PRIVATE_A}", headers=_auth(USER_B))
    missing = client.get("/api/knowledge/projects/ARKADIA_NO_SUCH_PROJECT", headers=_auth(USER_A))
    assert non_owner.status_code == 404
    assert missing.status_code == 404, "an absent id must not be a distinguishable status"
    assert non_owner.status_code == missing.status_code, (
        "the handler does not distinguish 'not readable' from 'does not exist'; neither may a reader"
    )


def test_anonymous_cannot_address_a_private_project(client):
    _seed()
    assert client.get(f"/api/knowledge/projects/{PRIVATE_A}").status_code == 404


def test_public_project_is_readable_without_identity(client):
    """The public corpus exists on this reader, so an anonymous detail read of a
    public project is legitimate."""
    _seed()
    response = client.get(f"/api/knowledge/projects/{PUBLIC_PROJECT}")
    assert response.status_code == 200
    assert response.json()["name"] == PUBLIC_PROJECT


# ── honest states in the reader ──────────────────────────────────────────────

def test_reader_reports_refusal_without_presenting_it_as_a_transport_fault():
    """A `404` is a boundary answer, not an outage. The reader must branch on the
    NOT_FOUND kind and render the dedicated refusal copy."""
    source = DETAIL.read_text(encoding="utf-8")
    assert 'kind === "NOT_FOUND"' in source, "the reader must branch on the 404 boundary kind"
    assert "projectRefusalNotice" in source, "the refusal must use the shared boundary copy"
    contracts = CONTRACTS.read_text(encoding="utf-8")
    assert "projectRefusalNotice" in contracts
    assert "cannot tell the two apart" in contracts, (
        "the refusal copy must state the indistinguishability, not invent which case it was"
    )


def test_failed_detail_read_is_not_rendered_as_a_project():
    source = DETAIL.read_text(encoding="utf-8")
    assert "isKnowledgeProject" in source, "the reader must validate the payload"
    assert "ApiError" in source, "an unrecognised body must raise, not render as a project"
    assert "ContractState" in source, "auth/unavailable/error states are distinct components"


def test_reader_composes_its_path_from_the_registry():
    """One registry (§3.1): the detail path is the collection entry plus an
    encoded identifier, not a page-local literal."""
    source = DETAIL.read_text(encoding="utf-8")
    assert "endpoints.knowledgeProjects" in source, "the base must come from the registry entry"
    assert "encodeURIComponent(identifier)" in source, "the id must be percent-encoded"
    assert detail_path_literals(source) == [], "the reader must not inline its endpoint path"


def test_no_naive_fanout_on_the_project_list():
    """The detail read is interaction-gated: a list entry must render it only when
    selected, so one mount does not fire N detail requests."""
    source = PANEL.read_text(encoding="utf-8")
    assert "KnowledgeProjectDetail" in source
    assert re.search(r"isOpen\s*&&", source), "the detail must be gated behind the selected state"
    assert re.search(r"onClick=\{[^}]*setSelected", source), "selection must be a user action"


# ── source detectors (each has a negative control below) ─────────────────────

def detail_path_literals(source: str) -> list[str]:
    """Path literals the detail reader inlines instead of using the registry."""
    return re.findall(r'"/(?:api|solspire)/[^"]*"', strip_comments(source))


def strip_comments(source: str) -> str:
    """A module's code with its block and line comments removed."""
    without_blocks = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?m)^\s*//.*$", "", without_blocks)


def test_reader_has_no_inline_endpoint_path():
    assert detail_path_literals(DETAIL.read_text(encoding="utf-8")) == []


def test_detector_flags_an_inline_endpoint_path():
    assert detail_path_literals('const p = "/api/knowledge/projects/x";') == [
        '"/api/knowledge/projects/x"'
    ]
    assert detail_path_literals("const p = endpoints.knowledgeProjects;") == []


def test_detector_ignores_a_comment_but_flags_real_code():
    prose_only = '/* GET /api/knowledge/projects/{id} is the detail route */\nconst x = 1;'
    assert detail_path_literals(prose_only) == []
    inline = 'const p = "/api/knowledge/projects/" + id;'
    assert detail_path_literals(inline) != []
