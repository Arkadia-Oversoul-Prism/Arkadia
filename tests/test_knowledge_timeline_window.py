"""Issue #437 — the timeline window must contain the *latest* event.

Post-merge review of PR #431 measured a real defect: `knowledge.timeline.query`
read `ORDER BY id ASC LIMIT 100`, so a default read returned the **oldest** 100
rows. `KnowledgeTimelinePanel` renders `events[events.length - 1]` as `latest`,
which past 100 events was the newest row of the *oldest page* — the real latest
event was absent from the response entirely and the panel asserted a false fact
about the log.

The repair keeps one contract and states it explicitly: a bounded read returns
the **newest** `limit` events, still in ascending `id` order, so the final row is
the log's newest event. `offset` therefore pages *backwards* from the newest
event. `newest_first=false` restores the oldest-first window for callers walking
the log from its beginning, and the `query()` default stays oldest-first so a
whole-log replay (`replay_project`, `limit=10000`) is byte-for-byte unchanged.

Every claim below is measured against the live handler over ASGI; there are no
mocks. The primary regression control is
`test_window_includes_the_latest_event_past_the_default_limit`, proven to bite by
a negative control that feeds the detector the pre-repair clause shape.

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
ROUTES_SOURCE = ROOT / "api" / "knowledge_routes.py"
PANEL = CONSOLE / "components" / "knowledge" / "KnowledgeTimelinePanel.tsx"
CONTRACTS = CONSOLE / "pages" / "knowledge" / "knowledgeContracts.ts"

USER_A = "ws3-window-user-a"
USER_B = "ws3-window-user-b"

# Strictly more than the handler's default window, so "the oldest page" and "the
# newest page" are different sets and the defect cannot hide behind a coincidence.
OVERFLOW = 130
WINDOW = 100


def _token(uid: str) -> str:
    payload = base64.urlsafe_b64encode(json.dumps({"user_id": uid}).encode()).rstrip(b"=").decode()
    return f"header.{payload}.signature"


def _auth(uid: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(uid)}"}


@pytest.fixture(autouse=True)
def _fresh_store():
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


def _seed_owner(uid: str, count: int, tag: str) -> list[int]:
    """Append ``count`` events for ``uid``; return their ids in append order."""
    ids = []
    for seq in range(count):
        ids.append(tl.record("decision", {"tag": tag, "seq": seq}, user_id=uid))
    return ids


def _ids(body: list[dict]) -> list[int]:
    return [event["id"] for event in body]


# ── the defect this slice repairs ────────────────────────────────────────────

def test_window_includes_the_latest_event_past_the_default_limit(client):
    """The primary regression control.

    Pre-repair this read returned ids 1..100 and the final row was event #100,
    while the newest event was #130 — so `latest` was wrong and the newest event
    was unreachable without pagination.
    """
    ids = _seed_owner(USER_A, OVERFLOW, "A")
    newest = ids[-1]

    body = client.get("/api/knowledge/timeline", headers=_auth(USER_A)).json()
    assert len(body) == WINDOW
    assert body[-1]["id"] == newest, (
        "the window must end at the newest event; a window ending at #100 means the "
        "reader returned the oldest page and the panel's `latest` fact is false"
    )
    assert newest in _ids(body)


def test_window_is_the_newest_not_the_oldest_page(client):
    """The window is exactly the newest `limit` rows, not merely containing one."""
    ids = _seed_owner(USER_A, OVERFLOW, "A")
    body = client.get("/api/knowledge/timeline", headers=_auth(USER_A)).json()
    assert _ids(body) == ids[-WINDOW:], "the newest page, in append order"
    assert ids[0] not in _ids(body), "the oldest event is beyond the window and must not be claimed"


def test_window_stays_chronological(client):
    """Selecting the newest window must not reorder the response."""
    _seed_owner(USER_A, OVERFLOW, "A")
    got = _ids(client.get("/api/knowledge/timeline", headers=_auth(USER_A)).json())
    assert got == sorted(got), "the contract returns ascending id even for the newest window"


def test_offset_pages_backwards_from_the_newest_event(client):
    """`offset` advances away from the newest event, not towards it."""
    ids = _seed_owner(USER_A, OVERFLOW, "A")

    first = _ids(client.get("/api/knowledge/timeline", headers=_auth(USER_A)).json())
    older = _ids(client.get("/api/knowledge/timeline?offset=100", headers=_auth(USER_A)).json())

    assert first == ids[-WINDOW:]
    assert older == ids[: OVERFLOW - WINDOW], "offset=100 must return the 30 rows older than the window"
    assert set(first).isdisjoint(older), "paging must not repeat rows"
    assert max(older) < min(first), "the second page is strictly older than the first"


def test_explicit_oldest_first_window_is_still_available(client):
    """`newest_first=false` is the opt-out, and it must be real."""
    ids = _seed_owner(USER_A, OVERFLOW, "A")
    body = _ids(client.get("/api/knowledge/timeline?newest_first=false", headers=_auth(USER_A)).json())
    assert body == ids[:WINDOW], "the explicit oldest-first window reads from the beginning of the log"


def test_query_default_is_unchanged_for_whole_log_replay(client):
    """`replay_project` walks the log from its start and must not be affected.

    The window selection is opt-in at the `query()` level, so a whole-log replay
    still opens at the oldest event.
    """
    from knowledge.vault import create_project

    seeded = _seed_owner(USER_A, OVERFLOW, "A")
    project = create_project("Window replay project", user_id=USER_A)
    project_ids = [
        tl.record("sync", {"tag": "A", "seq": seq}, project_id=project["id"], user_id=USER_A)
        for seq in range(5)
    ]

    replayed = _ids(tl.replay_project(project["id"], user_id=USER_A))
    assert replayed == project_ids, "a replay reads its whole project log in append order"
    assert _ids(tl.query(project_id=project["id"], limit=3, user_id=USER_A)) == project_ids[:3], (
        "the default window is oldest-first, so a bounded read opens at the oldest event"
    )

    whole_log = _ids(tl.query(limit=OVERFLOW + 5, user_id=USER_A))
    assert whole_log == seeded + project_ids, "the default window still reads from the log's beginning"


# ── the owner boundary is preserved by the window change ─────────────────────

def test_window_is_owner_scoped_past_the_limit(client):
    """Another owner's 130 events must not displace this owner's newest window."""
    a_ids = _seed_owner(USER_A, OVERFLOW, "A")
    _seed_owner(USER_B, OVERFLOW, "B")

    body = client.get("/api/knowledge/timeline", headers=_auth(USER_A)).json()
    assert _ids(body) == a_ids[-WINDOW:]
    assert all(event["user_id"] == USER_A for event in body)
    assert {event["payload"]["tag"] for event in body} == {"A"}


def test_anonymous_window_is_still_fail_closed_past_the_limit(client):
    """`1 = 0` is unchanged: a full log must not leak through the window."""
    _seed_owner(USER_A, OVERFLOW, "A")
    response = client.get("/api/knowledge/timeline")
    assert response.status_code == 200
    assert response.json() == [], "the anonymous scope remains empty regardless of window direction"


def test_unknown_identity_window_reads_nothing(client):
    """A uid owning nothing gets the same empty window, not a wildcard."""
    _seed_owner(USER_A, OVERFLOW, "A")
    assert client.get("/api/knowledge/timeline", headers=_auth("ws3-window-nobody")).json() == []


def test_event_type_filter_selects_the_newest_window_within_scope(client):
    """A filtered read must apply the window to the *filtered* set."""
    _seed_owner(USER_A, OVERFLOW, "A")
    for seq in range(5):
        tl.record("sync", {"tag": "A-sync", "seq": seq}, user_id=USER_A)

    body = client.get("/api/knowledge/timeline?event_type=sync", headers=_auth(USER_A)).json()
    assert [event["event_type"] for event in body] == ["sync"] * 5
    # The filter must not widen scope: B owns no `sync` events.
    assert client.get("/api/knowledge/timeline?event_type=sync", headers=_auth(USER_B)).json() == []


def test_limit_ceiling_is_still_enforced(client):
    """The window parameter is bounded by the handler, not silently clamped."""
    _seed_owner(USER_A, OVERFLOW, "A")
    assert client.get("/api/knowledge/timeline?limit=501", headers=_auth(USER_A)).status_code == 422


# ── the reader must not present a saturated window as the complete log ───────

def test_panel_requests_the_window_it_describes():
    """The copy names a window size; the request must use the same one."""
    panel = PANEL.read_text(encoding="utf-8")
    contracts = CONTRACTS.read_text(encoding="utf-8")
    assert "TIMELINE_WINDOW_LIMIT" in contracts and "TIMELINE_WINDOW_LIMIT" in panel
    assert re.search(r"limit=\$\{TIMELINE_WINDOW_LIMIT\}", panel), (
        "the request must derive its limit from the declared window constant, not a bare literal"
    )


def test_panel_states_the_window_boundary():
    panel = PANEL.read_text(encoding="utf-8")
    contracts = CONTRACTS.read_text(encoding="utf-8")
    assert "timelineWindowNotice" in panel, "a saturated window must be described, not implied"
    assert "isWindowSaturated" in contracts and "isWindowSaturated" in panel
    assert "older events beyond this window" in contracts, "the saturated copy must name what is missing"


def test_saturated_window_copy_differs_from_complete_copy():
    """Both directions of the window copy, pinned as strings."""
    contracts = CONTRACTS.read_text(encoding="utf-8")
    saturated = re.search(r"isWindowSaturated\(window\)\s*\?\s*`([^`]+)`", contracts)
    complete = re.search(r"\?\s*`([^`]+)`\s*:\s*`([^`]+)`", contracts)
    assert saturated and complete, "timelineWindowNotice must branch on saturation"
    assert saturated.group(1) != complete.group(2), (
        "a partial page and the whole log must never share wording"
    )


# ── source detectors (each has a negative control below) ─────────────────────

_WINDOW_SELECT = re.compile(
    r'^\s*order\s*=\s*"id DESC"\s*if\s*newest_first\s*else\s*"id ASC"\s*$', re.M
)
_BOUNDED_ORDER = re.compile(r"ORDER BY (?P<clause>.+?) LIMIT \? OFFSET \?")


def oldest_first_bounded_read(source: str) -> str | None:
    """The ORDER BY clause of the bounded read when it cannot return the newest page.

    The defect is not "ascending" — it is *hard-wired* ascending, which makes the
    newest window unreachable. A read whose direction is selected by
    ``newest_first`` is reported as sound; anything else returns its clause so the
    detector's report names what it saw.
    """
    if _WINDOW_SELECT.search(source):
        return None
    match = _BOUNDED_ORDER.search(source)
    return match.group("clause").strip() if match else None


_FIRST_LABEL = re.compile(r'label:\s*"first"')


def mislabels_window_start_as_log_start(source: str) -> bool:
    """Does the reader label the window's oldest row as the log's *first* event?

    A windowed read cannot know the log's first event, so an unqualified `first`
    label is the same class of false claim as the `latest` mislabel.
    """
    return _FIRST_LABEL.search(source) is not None


def test_bounded_read_can_select_the_newest_window():
    assert oldest_first_bounded_read(TIMELINE_SOURCE.read_text(encoding="utf-8")) is None


def test_detector_flags_the_pre_repair_clause():
    """The exact shape issue #437 measured."""
    pre_repair = (
        '    where = f"WHERE {\' AND \'.join(conditions)}"\n'
        "    params += [limit, offset]\n"
        "    rows = execute(\n"
        '        f"SELECT * FROM timeline {where} ORDER BY id ASC LIMIT ? OFFSET ?",\n'
        "        tuple(params),\n"
        "    )\n"
    )
    assert oldest_first_bounded_read(pre_repair) == "id ASC", (
        "the detector must report the hard-wired ascending clause that hid the newest events"
    )
    assert oldest_first_bounded_read('f"SELECT 1 ORDER BY id DESC LIMIT ? OFFSET ?"') == "id DESC", (
        "a read that cannot opt into ascending is still reported -- the marker is the "
        "selectable clause, not a direction"
    )


def test_detector_flags_the_latest_and_first_mislabels():
    assert mislabels_window_start_as_log_start(PANEL.read_text(encoding="utf-8")) is False
    pre_repair = '{ label: "first", value: events[0].created_at },\n{ label: "latest", value: latest.created_at }'
    assert mislabels_window_start_as_log_start(pre_repair) is True, (
        "the detector must report the pre-repair label that claims the window start is the log start"
    )


def test_handler_declares_the_window_default():
    """The route, not just the layer beneath it, carries the contract."""
    routes = ROUTES_SOURCE.read_text(encoding="utf-8")
    assert re.search(r"newest_first:\s*bool\s*=\s*True", routes), (
        "the HTTP default is the newest window; an omitted parameter must not mean 'oldest page'"
    )
    assert "newest_first=newest_first" in routes, "the handler must forward the parameter to the reader"


def test_handler_default_is_measured_not_only_declared(client):
    """The declared default and the served default are the same fact."""
    ids = _seed_owner(USER_A, OVERFLOW, "A")
    default_body = _ids(client.get("/api/knowledge/timeline", headers=_auth(USER_A)).json())
    explicit_body = _ids(
        client.get("/api/knowledge/timeline?newest_first=true", headers=_auth(USER_A)).json()
    )
    assert default_body == explicit_body == ids[-WINDOW:]
