"""M02 — ReasoMate Truth.

Route-level tests for the M02 acceptance boundary:

  * ``/reasomate`` resolves to ReasoMate and never silently resolves to Oracle;
  * ReasoMate is mounted as a NovaNet lens AND as a direct route, both rendering
    the same surface (no drift between entry points);
  * ReasoMate is a lens over the existing conversational runtime — it introduces
    no second chat endpoint, memory store, or identity system;
  * the private conversation stays authenticated and user-scoped.

The frontend has no JSX test runner in this repository (``package.json`` defines
no test script); the established convention for asserting frontend structure is
source inspection, as in ``tests/test_prism_interior_shell.py``. Backend
authentication/isolation is exercised for real through ``TestClient``.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "web/public_prism/src/App.tsx"
REASOMATE_PAGE = ROOT / "web/public_prism/src/pages/ReasoMatePage.tsx"
REASOMATE_SURFACE = ROOT / "web/public_prism/src/components/ReasoMateSurface.tsx"
NEXUS_PAGE = ROOT / "web/public_prism/src/pages/NexusPage.tsx"
NAV = ROOT / "web/public_prism/src/components/ArkadiaNavigation.tsx"
ARKANA_COMMUNE = ROOT / "web/public_prism/src/components/ArkanaCommune.tsx"
PRISM_SHELL = ROOT / "web/public_prism/src/components/PrismInteriorShell.tsx"

SURFACE_MARKER = 'data-testid="reasomate-private-surface"'


def _app() -> str:
    return APP.read_text()


def _code_only(text: str) -> str:
    """Strip block and line comments so assertions target code, not prose."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"^\s*//.*$", "", text, flags=re.M)
    return text


def _block(source: str, start: str, end: str) -> str:
    """Return the source slice from the index of ``start`` to the next ``end``."""
    i = source.find(start)
    assert i != -1, f"expected to find {start!r}"
    j = source.find(end, i)
    assert j != -1, f"expected to find {end!r} after {start!r}"
    return source[i:j]


# ── Direct route handling ────────────────────────────────────────────────────

def test_reasomate_is_a_direct_route_not_an_oracle_alias():
    app = _app()
    compatibility = _block(app, "const compatibility: Record<string, { view: View", "if (compatibility[path])")
    direct = _block(app, "const direct: Record<string, View>", "const view = direct[path]")

    assert "'/reasomate'" not in compatibility, (
        "/reasomate must not be a compatibility alias — that is the Oracle collapse M02 corrects"
    )
    assert re.search(r"'/reasomate'\s*:\s*'reasomate'", direct), (
        "/reasomate must be registered as its own direct route"
    )


def test_route_for_view_maps_reasomate_to_its_own_path():
    app = _app()
    body = _block(app, "function routeForView(", "function resolvePath(")
    assert re.search(r"reasomate\s*:\s*'/reasomate'", body), (
        "routeForView must map the reasomate view to /reasomate; otherwise the URL "
        "rewrites to '/' and the surface is unreachable by address"
    )


def test_navigation_does_not_collapse_reasomate_into_oracle():
    app = _app()
    body = _block(app, "const handleNavigate = (requested: View)", "setView(next.view)")
    assert "requested === 'reasomate'" not in body, (
        "handleNavigate must not redirect reasomate into another view"
    )
    assert "view:'commune'" not in body and "view: 'commune'" not in body, (
        "handleNavigate must not retarget any navigation to the Oracle view"
    )


def test_oracle_remains_oracle():
    app = _app()
    routes = _block(app, "function routeForView(", "function resolvePath(")
    assert re.search(r"commune\s*:\s*'/oracle'", routes)
    direct = _block(app, "const direct: Record<string, View>", "const view = direct[path]")
    assert re.search(r"'/oracle'\s*:\s*'commune'", direct)
    assert "'/commune': 'commune'" in direct


def test_reasomate_view_is_mounted_and_distinct_from_oracle():
    app = _app()
    assert "view === 'reasomate'" in app
    block = _block(app, "{view === 'reasomate'", "</motion.div>")
    assert "ReasoMatePage" in block, "the reasomate view must mount ReasoMatePage"
    assert "ArkanaCommune" not in block, (
        "the reasomate view must not mount the Oracle component directly"
    )


# ── NovaNet integration: one surface, two entry points ───────────────────────

def test_novanet_hub_renders_the_same_reasomate_surface():
    nexus = NEXUS_PAGE.read_text()
    assert "import ReasoMatePage from './ReasoMatePage'" in nexus
    assert "<ReasoMatePage />" in nexus


def test_direct_route_and_hub_share_one_surface():
    page = REASOMATE_PAGE.read_text()
    surface = REASOMATE_SURFACE.read_text()
    assert "ReasoMateSurface" in page, (
        "ReasoMatePage must delegate to the shared surface so the /reasomate route "
        "and the NovaNet tab cannot drift into different surfaces"
    )
    assert SURFACE_MARKER in surface


def test_public_feed_tab_does_not_claim_the_private_messenger():
    nexus = NEXUS_PAGE.read_text()
    novanet_tab = _block(nexus, "{ id: 'novanet'", "},")
    assert "ReasoMate" not in novanet_tab, (
        "the public NovaNet feed tab must not advertise the private ReasoMate messenger"
    )


def test_reasomate_is_reachable_from_navigation_surfaces():
    nav = NAV.read_text()
    shell = PRISM_SHELL.read_text()
    assert "reasomate: 'ReasoMate'" in nav
    assert "'reasomate'" in nav
    assert "key: 'reasomate'" in shell


# ── Conversation runtime: a lens, not a second chat system ───────────────────

def test_surface_reuses_the_canonical_runtime_without_a_second_chat_path():
    code = _code_only(REASOMATE_SURFACE.read_text())
    assert "ArkanaCommune" in code, (
        "the Arkana lens must reuse the canonical Oracle runtime component"
    )
    assert "commune/resonance" not in code, (
        "the surface must not open its own conversational endpoint"
    )
    assert "/api/messages" not in code, (
        "the surface must not open its own messaging endpoint"
    )
    assert "fetch(" not in code, (
        "the surface must compose canonical components rather than own transport"
    )


def test_oracle_runtime_uses_the_shared_session_key():
    commune = ARKANA_COMMUNE.read_text()
    assert "arkanaSessionId" in commune, (
        "the Arkana runtime must key its thread on the shared session id so ReasoMate "
        "and Oracle describe one longitudinal conversation"
    )


def test_no_second_memory_store_is_introduced():
    surface = REASOMATE_SURFACE.read_text()
    assert "localStorage" not in surface, (
        "ReasoMate must not introduce a second memory store; memory belongs to the "
        "existing Knowledge OS substrate"
    )


def test_no_second_identity_system_is_introduced():
    surface = REASOMATE_SURFACE.read_text()
    assert "useAuth" in surface, "the surface must scope to the existing authenticated identity"
    for forbidden in ("firebase", "signInWith", "createUser", "verifyIdToken"):
        assert forbidden not in surface, f"no parallel identity system: found {forbidden!r}"


# ── Authentication and user scoping of the private conversation ──────────────

def _client_factory(tmp_path, monkeypatch):
    """Per-node TestClients over the real messages router.

    ``require_auth`` is overridden ONCE with a header-driven resolver: the
    override is process-global, so resolving identity from the request (rather
    than installing one override per client) is what actually keeps the clients
    scoped to distinct uids.
    """
    monkeypatch.setattr("api.messages._MSG_DIR", str(tmp_path / "messages"))
    os.makedirs(tmp_path / "messages", exist_ok=True)

    from api.auth import require_auth
    from api.main import app

    # `Request` must be resolvable from module globals: this file uses
    # `from __future__ import annotations`, so the annotation below is a string
    # that FastAPI resolves against this module's globals, not the local scope.
    async def _auth(request: Request):
        uid = request.headers.get("x-test-uid")
        if not uid:
            raise HTTPException(status_code=401, detail="Unauthenticated")
        return {"uid": uid, "email": f"{uid}@test.local", "display_name": uid}

    app.dependency_overrides[require_auth] = _auth

    def make(uid: str) -> TestClient:
        return TestClient(app, headers={"x-test-uid": uid})

    return make


def test_private_conversation_requires_authentication(tmp_path, monkeypatch):
    monkeypatch.setattr("api.messages._MSG_DIR", str(tmp_path / "messages"))
    from api.main import app

    app.dependency_overrides.clear()
    anon = TestClient(app)
    assert anon.get("/api/messages/inbox").status_code == 401
    assert anon.post("/api/messages", json={"recipient_uid": "someone", "content": "hi"}).status_code == 401
    assert anon.get("/api/messages/thread/someone").status_code == 401


def test_conversation_persists_through_the_existing_runtime(tmp_path, monkeypatch):
    make = _client_factory(tmp_path, monkeypatch)
    alice = make("uid-alice")
    bob = make("uid-bob")

    sent = alice.post("/api/messages", json={"recipient_uid": "uid-bob", "content": "hello bob"})
    assert sent.status_code == 200, sent.text
    assert sent.json()["message"]["sender_uid"] == "uid-alice"

    thread = bob.get("/api/messages/thread/uid-alice")
    assert thread.status_code == 200
    contents = [m["content"] for m in thread.json()["messages"]]
    assert "hello bob" in contents, "the conversation must be retrievable by the recipient"

    inbox = bob.get("/api/messages/inbox").json()["conversations"]
    peers = {c["peer_uid"] for c in inbox}
    assert "uid-alice" in peers, "the conversation must surface in the recipient's inbox"


def test_cross_user_isolation_holds(tmp_path, monkeypatch):
    make = _client_factory(tmp_path, monkeypatch)
    alice = make("uid-alice")
    bob = make("uid-bob")
    carol = make("uid-carol")

    assert alice.post("/api/messages", json={"recipient_uid": "uid-bob", "content": "private a-b"}).status_code == 200

    carol_inbox = carol.get("/api/messages/inbox").json()["conversations"]
    assert carol_inbox == [], "an uninvolved node must not see that a conversation exists"

    carol_thread = carol.get("/api/messages/thread/uid-alice").json()["messages"]
    assert carol_thread == [], "an uninvolved node must not read the thread contents"

    assert alice.post(
        "/api/messages", json={"recipient_uid": "uid-bob", "content": "spoof", "sender_uid": "uid-carol"}
    ).json()["message"]["sender_uid"] == "uid-alice", (
        "the sender must always come from authentication, never the request body"
    )