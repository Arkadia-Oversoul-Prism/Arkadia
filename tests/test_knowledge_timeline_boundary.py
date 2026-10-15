"""Workstream 3 — Knowledge OS timeline reader: contract, owner boundary, honest states.

Binds the *declared* ``GET /api/knowledge/timeline`` contract to its real
handler, ownership predicate and persistence, then binds the feature-local
reader to that contract.

Contract under test (read from the handler, not invented):

  * ``GET /api/knowledge/timeline`` -> ``api.knowledge_routes.get_timeline``
    -> ``knowledge.timeline.query``
  * query parameters ``event_type``, ``project_id``, ``note_id``, ``since``,
    ``until``, ``limit`` (default 100, ``le=500``), ``offset``; ascending ``id``
  * identity is resolved with the *optional* auth dependency
    (``api.knowledge_routes._optional_user_id``), so an anonymous caller is a
    real caller
  * ownership predicate ``knowledge.timeline._timeline_owner_clause``:
    authenticated ``user_id = ?``; anonymous ``1 = 0``

The boundary on this reader is **stricter** than on the graph/search readers:
there is no public corpus, so an anonymous answer is always ``200 []``. That
``[]`` is therefore ambiguous at the transport level — it is what both "this
owner's log is empty" and "this caller owns nothing readable" look like — which
is exactly why the reader must not present it as an empty log without knowing
the viewer's identity. ``test_empty_and_unreadable_are_distinguishable`` pins
that distinction and the negative control below proves the pin can bite.

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
from knowledge import timeline as tl
from knowledge.db import get_connection

pytestmark = pytest.mark.skipif(
    not auth._dev_mode,
    reason="identity tokens require the auth layer's dev-mode (no Firebase service account)",
)

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "web" / "arkadia_console" / "src"
TIMELINE_SOURCE = ROOT / "knowledge" / "timeline.py"
ROUTES = ROOT / "api" / "knowledge_routes.py"
PANEL = CONSOLE / "components" / "knowledge" / "KnowledgeTimelinePanel.tsx"
CONTRACTS = CONSOLE / "pages" / "knowledge" / "knowledgeContracts.ts"

USER_A = "ws3-timeline-user-a"
USER_B = "ws3-timeline-user-b"
CANARY_A = "ARKADIA_TIMELINE_CANARY_WS3_USER_A"
CANARY_B = "ARKADIA_TIMELINE_CANARY_WS3_USER_B"


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
    """Two owners with distinguishable private events."""
    tl.record("decision", {"marker": CANARY_A}, user_id=USER_A)
    tl.record("sync", {"marker": CANARY_A, "second": True}, user_id=USER_A)
    tl.record("decision", {"marker": CANARY_B}, user_id=USER_B)


def _markers(events: list[dict]) -> set[str]:
    return {
        (event.get("payload") or {}).get("marker")
        for event in events
        if isinstance(event.get("payload"), dict)
    }


# ── contract shape ───────────────────────────────────────────────────────────

def test_timeline_contract_returns_a_list_of_events(client):
    _seed()
    body = client.get("/api/knowledge/timeline", headers=_auth(USER_A)).json()
    assert isinstance(body, list), "the reader returns a bare list, not a wrapper object"
    assert body, "positive control: the seeded owner must have readable events"
    assert set(body[0]) >= {
        "id", "event_type", "payload", "note_id", "project_id",
        "provider", "persona", "user_id", "created_at",
    }


def test_timeline_orders_ascending_by_id(client):
    _seed()
    ids = [event["id"] for event in client.get("/api/knowledge/timeline", headers=_auth(USER_A)).json()]
    assert ids == sorted(ids), "query() orders by id ASC; a reordered read is not the declared contract"


def test_timeline_payload_is_decoded_not_a_json_string(client):
    _seed()
    body = client.get("/api/knowledge/timeline", headers=_auth(USER_A)).json()
    assert all(isinstance(event["payload"], dict) for event in body), (
        "the reader decodes the JSON payload column; a string body would mean the "
        "shape the client declares is wrong"
    )


# ── owner boundary ───────────────────────────────────────────────────────────

def test_anonymous_timeline_is_answered_empty_not_refused(client):
    """The reader uses the *optional* auth dependency: anonymous is a real caller.

    A ``401`` here would be a different contract. Pin the measured one, and pin
    that it carries no material.
    """
    _seed()
    response = client.get("/api/knowledge/timeline")
    assert response.status_code == 200
    assert response.json() == [], "the anonymous scope is `1 = 0` -- no events, no leak"


def test_authenticated_timeline_is_scoped_to_owner(client):
    _seed()
    body = client.get("/api/knowledge/timeline", headers=_auth(USER_A)).json()
    assert _markers(body) == {CANARY_A}, "an owner must see exactly their own events"
    assert all(event["user_id"] == USER_A for event in body)


def test_timeline_does_not_leak_across_users(client):
    """The primary cross-owner leakage control."""
    _seed()
    a_markers = _markers(client.get("/api/knowledge/timeline", headers=_auth(USER_A)).json())
    b_markers = _markers(client.get("/api/knowledge/timeline", headers=_auth(USER_B)).json())
    assert CANARY_A in a_markers and CANARY_A not in b_markers, "B must not read A's events"
    assert CANARY_B in b_markers and CANARY_B not in a_markers, "A must not read B's events"


def test_unknown_identity_reads_nothing_rather_than_everything(client):
    """A caller whose uid owns no events is the `[]` case, not a wildcard.

    This is the shape a naive ``WHERE 1 = 1`` would get wrong: the unowned rows
    below would all be returned.
    """
    _seed()
    tl.record("error", {"marker": "ARKADIA_UNOWNED_WS3"}, user_id=None)
    body = client.get("/api/knowledge/timeline", headers=_auth("ws3-timeline-nobody")).json()
    assert body == []
    assert "ARKADIA_UNOWNED_WS3" not in _markers(body)


def test_events_inherit_owner_from_their_note(client):
    """``record`` stamps the note's owner, so a note-linked event is not unowned."""
    from knowledge.vault import create_note

    note = create_note(title="A note", content="x", user_id=USER_A)
    tl.record("knowledge_created", {"marker": CANARY_A}, note_id=note["id"])
    body = client.get("/api/knowledge/timeline", headers=_auth(USER_A)).json()
    assert _markers(body) == {CANARY_A}
    assert client.get("/api/knowledge/timeline", headers=_auth(USER_B)).json() == []


# ── query parameters ─────────────────────────────────────────────────────────

def test_event_type_filter_is_owner_scoped_too(client):
    _seed()
    body = client.get("/api/knowledge/timeline?event_type=sync", headers=_auth(USER_A)).json()
    assert [event["event_type"] for event in body] == ["sync"]
    assert _markers(body) == {CANARY_A}
    # The filter must not widen the scope: B has no `sync` event.
    assert client.get("/api/knowledge/timeline?event_type=sync", headers=_auth(USER_B)).json() == []


def test_limit_and_offset_page_within_the_owner_scope(client):
    _seed()
    page = client.get("/api/knowledge/timeline?limit=1", headers=_auth(USER_A)).json()
    assert len(page) == 1
    rest = client.get("/api/knowledge/timeline?limit=1&offset=1", headers=_auth(USER_A)).json()
    assert len(rest) == 1
    assert page[0]["id"] != rest[0]["id"], "offset must advance within the owner's own events"


def test_limit_ceiling_is_enforced_by_the_handler(client):
    """``Query(100, le=500)`` -- an over-limit request is refused, not silently clamped."""
    _seed()
    assert client.get("/api/knowledge/timeline?limit=501", headers=_auth(USER_A)).status_code == 422


# ── empty versus failed reads ────────────────────────────────────────────────

def test_empty_and_unreadable_are_distinguishable(client):
    """A ``[]`` is ambiguous; the scope vocabulary is what resolves it.

    The reader cannot tell from the body whether the server filtered, so the
    classification is derived from the viewer's identity. Both directions are
    asserted: an owner's empty log is `owner`, an anonymous `[]` is `unscoped`.
    """
    _seed()
    contracts = CONTRACTS.read_text(encoding="utf-8")
    assert "classifyTimelineScope" in contracts
    assert re.search(r'"owner"', contracts) and re.search(r'"unscoped"', contracts)

    # Owner with no events of their own -> genuine empty log.
    assert client.get("/api/knowledge/timeline", headers=_auth("ws3-timeline-nobody")).json() == []
    # Anonymous -> the same `[]`, but a refusal, not an empty log.
    assert client.get("/api/knowledge/timeline").json() == []

    # The two notices must not be the same string, or the distinction is lost.
    owner_notice = re.search(r'return scope === "owner"\s*\?\s*"([^"]+)"', contracts)
    unscoped_notice = re.search(r'\?\s*"([^"]+)"\s*:\s*"([^"]+)"', contracts)
    assert owner_notice and unscoped_notice, "emptyTimelineNotice must branch on scope"
    assert owner_notice.group(1) != unscoped_notice.group(2)


def test_failed_read_is_not_rendered_as_an_empty_timeline():
    """A transport failure and an unrecognised body must both be errors."""
    panel = PANEL.read_text(encoding="utf-8")
    contracts = CONTRACTS.read_text(encoding="utf-8")
    assert "isTimelineEvents" in panel, "the panel must validate the payload"
    assert "ApiError" in panel, "an unrecognised body must raise, not render empty"
    assert "ContractState" in panel, "auth/unavailable/error states are distinct components"
    assert "emptyTimelineNotice" in panel, "the empty branch is scope-aware"
    assert "isTimelineEvents" in contracts


# ── source detectors (each has a negative control below) ─────────────────────

_ANON_CLAUSE = re.compile(r"def _timeline_owner_clause.*?return \"([^\"]+)\", \[\]", re.DOTALL)


def permissive_owner_clause(source: str) -> str | None:
    """The anonymous owner clause if it is *not* the fail-closed ``1 = 0``.

    The reader's boundary is only real if the anonymous branch matches nothing.
    Any other clause (``1 = 1``, a public-corpus OR, a missing filter) is a leak.
    """
    match = _ANON_CLAUSE.search(source)
    if not match:
        return None
    clause = match.group(1).strip()
    return None if clause.replace(" ", "") == "1=0" else clause


def inline_endpoint_path(source: str) -> list[str]:
    """Path literals a feature module inlines instead of using the registry."""
    return re.findall(r'"/(?:api|solspire)/[^"]*"', source)


def test_owner_clause_is_fail_closed():
    assert permissive_owner_clause(TIMELINE_SOURCE.read_text(encoding="utf-8")) is None


def test_detector_flags_a_permissive_owner_clause():
    """The pre-repair shape a naive reader would have."""
    leaky = 'def _timeline_owner_clause(user_id):\n    if user_id:\n        return "user_id = ?", [user_id]\n    return "1 = 1", []\n'
    assert permissive_owner_clause(leaky) == "1 = 1", "the detector must report a wildcard clause"
    public_corpus = 'def _timeline_owner_clause(user_id):\n    if user_id:\n        return "user_id = ?", [user_id]\n    return "user_id IS NULL", []\n'
    assert permissive_owner_clause(public_corpus) == "user_id IS NULL", (
        "a public-corpus clause is not this reader's contract and must be reported"
    )


def test_panel_uses_the_registry_and_the_shared_client():
    panel = PANEL.read_text(encoding="utf-8")
    assert "endpoints.knowledgeTimeline" in panel
    assert 'from "../../lib/apiClient"' in panel
    assert 'from "../../lib/useHydration"' in panel
    assert inline_endpoint_path(panel) == [], "the panel must not inline its endpoint path"


def test_detector_flags_an_inline_endpoint_path():
    assert inline_endpoint_path('const p = "/api/knowledge/timeline";') == ['"/api/knowledge/timeline"']
    assert inline_endpoint_path('const p = endpoints.knowledgeTimeline;') == []


def strip_comments(source: str) -> str:
    """A module's code with its block and line comments removed.

    Ownership prose legitimately *names* the predicate; only code can apply one.
    Reading the code rather than the file is what keeps the detector from
    reddening on a comment that documents the boundary.
    """
    without_blocks = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?m)^\s*//.*$", "", without_blocks)


def test_panel_does_not_reimplement_the_ownership_boundary_client_side():
    """The server owns the predicate. A client-side filter could only *look* like
    a boundary while the response still carried the other owners' rows.

    ``user_id`` legitimately appears in the *contracts* module (it is part of the
    returned shape) but must not appear in the panel's *code*, where it would be
    a filter.
    """
    code = strip_comments(PANEL.read_text(encoding="utf-8"))
    assert "user_id" not in code
    assert ".filter(" not in code
    assert "user_id" in CONTRACTS.read_text(encoding="utf-8")


def test_detector_ignores_a_comment_but_flags_real_code():
    """Negative control for ``strip_comments``: prose must not satisfy the guard,
    and a genuine client-side filter must still be reported."""
    prose_only = "/* the predicate is user_id = ? for authenticated callers */\nconst x = 1;"
    assert "user_id" not in strip_comments(prose_only)
    filtering = "const mine = events.filter((e) => e.user_id === me);"
    assert "user_id" in strip_comments(filtering)


def test_default_page_includes_latest_event_after_more_than_100_owner_events(client):
    """The default page is the newest bounded window, rendered chronologically."""
    for index in range(125):
        tl.record("decision", {"marker": f"TIMELINE_PAGE_{index}"}, user_id=USER_A)

    latest_page = client.get("/api/knowledge/timeline", headers=_auth(USER_A)).json()
    ids = [event["id"] for event in latest_page]
    markers = _markers(latest_page)

    assert len(latest_page) == 100
    assert ids == sorted(ids), "the selected latest window remains chronological"
    assert latest_page[0]["payload"]["marker"] == "TIMELINE_PAGE_25"
    assert latest_page[-1]["payload"]["marker"] == "TIMELINE_PAGE_124"
    assert "TIMELINE_PAGE_124" in markers
    assert "TIMELINE_PAGE_0" not in markers

    older_page = client.get(
        "/api/knowledge/timeline?limit=100&offset=100",
        headers=_auth(USER_A),
    ).json()
    older_ids = [event["id"] for event in older_page]
    assert len(older_page) == 25
    assert older_ids == sorted(older_ids)
    assert max(older_ids) < min(ids)
    assert not set(older_ids).intersection(ids)

    # Anonymous remains fail-closed even when many private events exist.
    assert client.get("/api/knowledge/timeline").json() == []


# ── the read bound is a floor as well as a ceiling ───────────────────────────
#
# `le=500` bounds the top of the range but not the bottom, and SQLite reads
# `LIMIT -1` as "no limit". Measured on `main` @ `7580bd8` with 600 owner events:
# `GET /api/knowledge/timeline?limit=-1` answered **200** with **1200** rows (the
# seeded 600 plus the suite's), i.e. the whole readable log, while `limit=501` was
# correctly refused with 422. `GET /api/knowledge/timeline/recent?limit=-1` and
# `?limit=999999` were worse: `recent_timeline` declared a bare `limit: int = 20`
# with no bound at all, so **both** returned the entire log. The ceiling test
# above passed throughout -- it only ever probed `501`.

def _seed_many(count: int, uid: str = USER_A) -> None:
    for index in range(count):
        tl.record("decision", {"marker": f"TIMELINE_BOUND_{index}"}, user_id=uid)


def test_negative_limit_cannot_widen_the_read(client):
    """A negative row count must not become SQLite's unbounded ``LIMIT -1``."""
    _seed_many(600)
    response = client.get("/api/knowledge/timeline?limit=-1", headers=_auth(USER_A))
    assert response.status_code == 422, (
        "a negative limit must be refused, not forwarded to SQLite as 'no limit'"
    )


def test_negative_offset_is_refused_not_read_as_zero(client):
    _seed()
    assert client.get("/api/knowledge/timeline?offset=-5", headers=_auth(USER_A)).status_code == 422


def test_the_ceiling_still_holds_after_the_floor_was_added(client):
    """The floor must not replace the ceiling: both ends stay enforced."""
    _seed_many(600)
    assert client.get("/api/knowledge/timeline?limit=501", headers=_auth(USER_A)).status_code == 422
    assert client.get("/api/knowledge/timeline?limit=999999", headers=_auth(USER_A)).status_code == 422


def test_recent_reader_is_bounded_at_all(client):
    """``/timeline/recent`` declared no bound, so *any* oversized limit was honoured."""
    _seed_many(600)
    for limit in ("-1", "999999"):
        assert client.get(f"/api/knowledge/timeline/recent?limit={limit}", headers=_auth(USER_A)).status_code == 422, (
            f"recent limit={limit} must be refused"
        )
    # The declared default still works and still returns the newest window.
    body = client.get("/api/knowledge/timeline/recent", headers=_auth(USER_A)).json()
    assert len(body) == 20
    assert body == sorted(body, key=lambda event: event["id"])


def test_in_process_callers_cannot_bypass_the_route_bound():
    """The route is not the only caller: a module-level read must clamp too.

    ``knowledge.timeline.query``/``recent`` are called directly in-process
    (``api.echofeild`` uses ``recent``), so a handler-only fix would leave a
    second unbounded path. ``replay_project`` keeps its own wider 10000 ceiling.
    """
    _seed_many(600)
    assert len(tl.query(limit=-1, user_id=USER_A)) == 0
    assert len(tl.recent(limit=-1, user_id=USER_A)) == 0
    assert len(tl.query(limit=999999, user_id=USER_A)) == 600
    assert len(tl.replay_project(1, user_id=USER_A)) == 0


def test_detector_flags_an_unbounded_limit_declaration():
    """Negative control: the detector must bite on the pre-repair declarations."""
    pre_repair = "async def recent_timeline(request: Request, limit: int = 20):\n    ...\n"
    assert _unbounded_route_limit(_function_source(pre_repair, "recent_timeline")) is True
    # And must be silent on the repaired shape, or it is not a detector.
    repaired = (
        "async def recent_timeline(request: Request, "
        "limit: int = Query(20, ge=0, le=TIMELINE_MAX_LIMIT)):\n    ...\n"
    )
    assert _unbounded_route_limit(_function_source(repaired, "recent_timeline")) is False


def test_route_declares_a_floor_on_every_timeline_reader():
    """Source-level pin so the floor cannot be dropped without reddening."""
    source = ROUTES.read_text(encoding="utf-8")
    for reader in ("get_timeline", "recent_timeline"):
        signature = _function_source(source, reader)
        assert signature, f"{reader} must exist in the route module"
        assert "ge=0" in signature, f"{reader} must declare a lower bound on limit"
        assert not _unbounded_route_limit(signature), f"{reader} must not take a bare limit"


def _function_source(source: str, name: str) -> str:
    """Return the ``def <name>(...)`` parameter list, or '' when absent."""
    match = re.search(rf"def {re.escape(name)}\((.*?)\)\s*(?:->[^:]*)?:", source, re.S)
    return match.group(1) if match else ""


def _unbounded_route_limit(function_signature: str) -> bool:
    """True when a reader takes a bare ``limit: int`` with no bound at all.

    A bare integer default is the pre-repair shape; ``Query(...)`` with ``ge``/``le``
    is the repaired one. The detector reads the parameter, not the line, so it is
    insensitive to how the signature is wrapped.
    """
    match = re.search(r"limit\s*:\s*int\s*=\s*([^,)]*)", function_signature)
    if not match:
        return False
    return bool(re.fullmatch(r"\d+", match.group(1).strip()))

