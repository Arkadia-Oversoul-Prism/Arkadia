"""Issue #437 follow-up — the timeline *window* must not be labelled as the log.

PR #442 fixed the defect #437 measured: `knowledge.timeline.query` now selects
the newest `limit` rows in a subquery and re-sorts ascending, so the final row of
a default read *is* the log's newest event and the panel's `latest` fact is true
past 100 events.

Two claims in the same reader were left behind by that repair, and this slice
addresses them:

1. The facts table still labelled `events[0]` as **`first`**. Under the newest
   window that row is only the oldest event *still shown*; the log's first event
   is not in the response. `first` is the same class of false claim as the
   `latest` mislabel #437 removed.
2. The window extent was not stated anywhere in the reader. Main's static
   paragraph mentions an offset query, but nothing derives from the response
   whether the window is saturated, so a partial page reads as the whole log.

`events[length - 1]` remains `latest` and is *pinned true* here — the property
#442 established is asserted, not assumed.

Every claim below is measured against the live handler over ASGI; there are no
mocks. The primary control is
`test_latest_label_is_true_past_the_window_limit`, and the reader-side controls
are proven to bite by reverting the panel to its pre-repair labels.

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
PANEL = CONSOLE / "components" / "knowledge" / "KnowledgeTimelinePanel.tsx"
CONTRACTS = CONSOLE / "pages" / "knowledge" / "knowledgeContracts.ts"

USER_A = "ws3-window-user-a"
USER_B = "ws3-window-user-b"

# Strictly more than the handler's default window, so "the oldest page" and "the
# newest page" are different sets and a defect cannot hide behind a coincidence.
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
    return [tl.record("decision", {"tag": tag, "seq": seq}, user_id=uid) for seq in range(count)]


def _ids(body: list[dict]) -> list[int]:
    return [event["id"] for event in body]


# ── the window contract #442 established, pinned here ────────────────────────

def test_latest_label_is_true_past_the_window_limit(client):
    """The primary control: `latest` must be the log's newest event, not the page's.

    This is the property issue #437 asked for. Asserting it here means the reader
    change below is built on a *measured* contract rather than on main's prose.
    """
    ids = _seed_owner(USER_A, OVERFLOW, "A")

    body = client.get("/api/knowledge/timeline", headers=_auth(USER_A)).json()
    assert len(body) == WINDOW
    assert body[-1]["id"] == ids[-1], (
        "the window must end at the newest event, or the panel's `latest` fact is false"
    )


def test_window_is_the_newest_not_the_oldest_page(client):
    ids = _seed_owner(USER_A, OVERFLOW, "A")
    body = client.get("/api/knowledge/timeline", headers=_auth(USER_A)).json()
    assert _ids(body) == ids[-WINDOW:], "the newest page, in ascending order"
    assert ids[0] not in _ids(body), "the oldest event is beyond the window and must not be shown"


def test_window_stays_chronological(client):
    _seed_owner(USER_A, OVERFLOW, "A")
    got = _ids(client.get("/api/knowledge/timeline", headers=_auth(USER_A)).json())
    assert got == sorted(got), "the contract returns ascending id even for the newest window"


def test_offset_pages_backwards_from_the_newest_event(client):
    ids = _seed_owner(USER_A, OVERFLOW, "A")
    newest = _ids(client.get("/api/knowledge/timeline", headers=_auth(USER_A)).json())
    older = _ids(client.get("/api/knowledge/timeline?offset=100", headers=_auth(USER_A)).json())

    assert newest == ids[-WINDOW:]
    assert older == ids[: OVERFLOW - WINDOW], "offset=100 returns the rows older than the window"
    assert set(newest).isdisjoint(older), "paging must not repeat rows"
    assert max(older) < min(newest), "the second page is strictly older than the first"


def test_window_start_is_not_the_log_start(client):
    """The fact the panel must stop asserting as `first`.

    A reader asking for 100 of 130 events cannot know the log's first event; the
    first row of the window is a different id, which is exactly why an
    unqualified `first` label would be false.
    """
    ids = _seed_owner(USER_A, OVERFLOW, "A")
    body = _ids(client.get("/api/knowledge/timeline", headers=_auth(USER_A)).json())
    assert body[0] != ids[0], "the window's first row is not the log's first event"
    assert body[0] == ids[-WINDOW]


# ── the owner boundary is intact under a windowed read ───────────────────────

def test_window_is_owner_scoped_past_the_limit(client):
    a_ids = _seed_owner(USER_A, OVERFLOW, "A")
    _seed_owner(USER_B, OVERFLOW, "B")

    body = client.get("/api/knowledge/timeline", headers=_auth(USER_A)).json()
    assert _ids(body) == a_ids[-WINDOW:]
    assert all(event["user_id"] == USER_A for event in body)
    assert {event["payload"]["tag"] for event in body} == {"A"}


def test_anonymous_window_is_still_fail_closed_past_the_limit(client):
    _seed_owner(USER_A, OVERFLOW, "A")
    response = client.get("/api/knowledge/timeline")
    assert response.status_code == 200
    assert response.json() == [], "the anonymous scope remains empty regardless of window direction"


def test_unknown_identity_window_reads_nothing(client):
    _seed_owner(USER_A, OVERFLOW, "A")
    assert client.get("/api/knowledge/timeline", headers=_auth("ws3-window-nobody")).json() == []


def test_event_type_filter_windows_the_filtered_set_within_scope(client):
    _seed_owner(USER_A, OVERFLOW, "A")
    for seq in range(5):
        tl.record("sync", {"tag": "A-sync", "seq": seq}, user_id=USER_A)

    body = client.get("/api/knowledge/timeline?event_type=sync", headers=_auth(USER_A)).json()
    assert [event["event_type"] for event in body] == ["sync"] * 5
    assert client.get("/api/knowledge/timeline?event_type=sync", headers=_auth(USER_B)).json() == []


def test_limit_ceiling_is_still_enforced(client):
    _seed_owner(USER_A, OVERFLOW, "A")
    assert client.get("/api/knowledge/timeline?limit=501", headers=_auth(USER_A)).status_code == 422


# ── the reader must not claim absolutes it cannot see ────────────────────────

def test_panel_requests_the_window_it_describes():
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


def test_saturated_and_complete_copy_differ():
    contracts = CONTRACTS.read_text(encoding="utf-8")
    assert re.search(r"isWindowSaturated\(window\)\s*\?", contracts), (
        "timelineWindowNotice must branch on saturation"
    )
    assert "Showing all" in contracts and "Showing the newest" in contracts, (
        "a partial page and the whole log must never share wording"
    )


# ── source detectors (each has a negative control below) ─────────────────────

_FIRST_LABEL = re.compile(r'label:\s*"first"')


def mislabels_window_start_as_log_start(source: str) -> bool:
    """Does the reader label the window's oldest row as the log's *first* event?

    A windowed read cannot know the log's first event, so an unqualified `first`
    label is the same class of false claim as the `latest` mislabel issue #437
    removed.
    """
    return _FIRST_LABEL.search(source) is not None


def declares_window_extent(source: str) -> bool:
    """Does the reader *call* the window-extent helpers, not merely import them?

    An import satisfies a naive substring check even after the call site is
    deleted: the module still names the helper while rendering nothing from it.
    Match the invocations so the guard measures behaviour, not vocabulary.
    """
    calls = re.findall(r"\b(isWindowSaturated|timelineWindowNotice)\s*\(", source)
    return {"isWindowSaturated", "timelineWindowNotice"} <= set(calls)


def test_panel_does_not_label_the_window_start_as_the_log_start():
    assert mislabels_window_start_as_log_start(PANEL.read_text(encoding="utf-8")) is False


def test_detector_flags_the_pre_repair_first_label():
    """The exact shape left on main after #442."""
    pre_repair = '{ label: "events shown", value: String(events.length) },\n{ label: "first", value: events[0].created_at },'
    assert mislabels_window_start_as_log_start(pre_repair) is True, (
        "the detector must report the `first` label that a windowed read cannot justify"
    )


def test_panel_declares_the_window_extent():
    assert declares_window_extent(PANEL.read_text(encoding="utf-8")) is True


def test_detector_flags_a_reader_with_no_window_extent():
    pre_repair = '{ label: "latest", value: latest.created_at },'
    assert declares_window_extent(pre_repair) is False, (
        "a reader that never derives saturation would pass vacuously without this control"
    )
    imported_only = (
        'import { isWindowSaturated, timelineWindowNotice } from "./contracts";\n'
        'const latest = events[events.length - 1];'
    )
    assert declares_window_extent(imported_only) is False, (
        "an import is not a call: the detector must not pass a reader that renders nothing "
        "from the helpers it names"
    )


def test_latest_is_still_rendered_from_the_last_row():
    """The #442 property must not be traded away while fixing the start label."""
    panel = PANEL.read_text(encoding="utf-8")
    assert "events[events.length - 1]" in panel, "the panel must still read `latest` from the final row"
    assert re.search(r'label:\s*"latest"', panel)
