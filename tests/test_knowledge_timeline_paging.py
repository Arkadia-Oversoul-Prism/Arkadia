"""Knowledge timeline paging — the reader may page *backwards* into older events.

The timeline reader (`web/arkadia_console/.../KnowledgeTimelinePanel.tsx`) showed a
single newest window and stated, in prose, that "older events require an explicit
offset query" — but offered no control that performed one. The measured backend
contract (`test_knowledge_timeline_window.py`) already pages backwards from the
newest event: `offset = shown` returns the next page *strictly older* than
everything displayed. This slice lets the reader use that contract.

Ownership is Lane 3 (Solariun / Knowledge OS). No shared file is touched: the
change is feature-local to `components/knowledge/KnowledgeTimelinePanel.tsx` and
`pages/knowledge/knowledgeContracts.ts`.

What is asserted:

1. The backend *supports a multi-page walk* to the start — newest page, an older
   page, then a short final page — so the paging the reader describes is real.
   This is measured against the live handler over ASGI; there are no mocks.
2. The owner boundary holds across every page, not only the first.
3. The reader derives its paging state from the *response* (`classifyOlderPage`),
   merges older pages *beneath* the newest window without duplicating rows, and
   states two distinct outcomes ("more" vs "start") that never share wording.

Source detectors each carry a negative control, following the convention of the
sibling console guards.
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
PANEL = CONSOLE / "components" / "knowledge" / "KnowledgeTimelinePanel.tsx"
CONTRACTS = CONSOLE / "pages" / "knowledge" / "knowledgeContracts.ts"

USER_A = "ws3-paging-user-a"
USER_B = "ws3-paging-user-b"

# More than two full windows, so a third page is necessarily short: "the start of
# the log" is a reachable state, not a coincidence.
TOTAL = 130
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
    return [tl.record("decision", {"tag": tag, "seq": seq}, user_id=uid) for seq in range(count)]


def _ids(body: list[dict]) -> list[int]:
    return [event["id"] for event in body]


def _walk_older(client: TestClient, uid: str) -> list[list[int]]:
    """Page backwards until a short page is returned; return the id pages."""
    pages: list[list[int]] = []
    offset = 0
    while True:
        page = _ids(client.get(f"/api/knowledge/timeline?limit={WINDOW}&offset={offset}", headers=_auth(uid)).json())
        pages.append(page)
        if len(page) < WINDOW:
            return pages
        offset += len(page)


# ── the backend supports a multi-page walk to the start ─────────────────────

def test_paging_reaches_the_start_of_the_log(client):
    """130 events, a 100-window: page 1 = newest 100, page 2 = the older 30, then stop."""
    ids = _seed_owner(USER_A, TOTAL, "A")
    pages = _walk_older(client, USER_A)

    assert [len(p) for p in pages] == [WINDOW, TOTAL - WINDOW], (
        "the second page is short of the limit, which is the backend's stop signal"
    )
    # Every page is disjoint and the union is the whole log, in order.
    assert max(pages[1]) < min(pages[0]), "older pages are strictly older than the newest window"
    assert sorted(pages[0] + pages[1]) == ids, "paging reaches every event exactly once"


def test_second_page_is_the_events_the_window_excluded(client):
    ids = _seed_owner(USER_A, TOTAL, "A")
    newest = _ids(client.get(f"/api/knowledge/timeline?limit={WINDOW}", headers=_auth(USER_A)).json())
    older = _ids(client.get(f"/api/knowledge/timeline?limit={WINDOW}&offset={WINDOW}", headers=_auth(USER_A)).json())

    assert newest == ids[-WINDOW:]
    assert older == ids[: TOTAL - WINDOW]
    assert ids[0] in older, "the oldest event is reachable, not merely absent from the window"
    assert set(newest).isdisjoint(older), "paging must not repeat rows"


def test_third_page_is_empty_once_the_log_is_read(client):
    _seed_owner(USER_A, TOTAL, "A")
    beyond = client.get(f"/api/knowledge/timeline?limit={WINDOW}&offset={TOTAL}", headers=_auth(USER_A)).json()
    assert beyond == [], "past the start the backend returns nothing, so the reader's stop is honest"


# ── the owner boundary holds on every page, not only the first ──────────────

def test_every_page_is_owner_scoped(client):
    a_ids = _seed_owner(USER_A, TOTAL, "A")
    _seed_owner(USER_B, TOTAL, "B")

    pages = _walk_older(client, USER_A)
    assert sorted(pages[0] + pages[1]) == a_ids
    assert all(event["user_id"] == USER_A for page in
               [client.get(f"/api/knowledge/timeline?limit={WINDOW}&offset={o}", headers=_auth(USER_A)).json()
                for o in (0, WINDOW)]
               for event in page)


def test_anonymous_paging_remains_empty(client):
    _seed_owner(USER_A, TOTAL, "A")
    for offset in (0, WINDOW):
        response = client.get(f"/api/knowledge/timeline?limit={WINDOW}&offset={offset}")
        assert response.status_code == 200
        assert response.json() == [], "the anonymous scope stays empty on every page"


def test_event_type_filter_applies_to_every_page(client):
    _seed_owner(USER_A, TOTAL, "A")
    sync_ids = [tl.record("sync", {"seq": seq}, user_id=USER_A) for seq in range(5)]

    for offset in (0, WINDOW):
        body = client.get(
            f"/api/knowledge/timeline?limit={WINDOW}&offset={offset}&event_type=sync", headers=_auth(USER_A)
        ).json()
        assert _ids(body) == (sync_ids if offset == 0 else []), (
            "the filter is applied before the window, so the five sync events sit on the first page"
        )


# ── the reader derives its paging state from the response, not prose ────────

_NOTICE_CALL = re.compile(r"\bolderEventsNotice\s*\(")
_CLASSIFY_CALL = re.compile(r"\bclassifyOlderPage\s*\(")
_MERGE_CALL = re.compile(r"\bmergeOlderEvents\s*\(")

PANEL_MINIMAL = (
    'const [older, setOlder] = useState<TimelineEvent[]>([]);\n'
    'const page = await readTimeline(path);\n'
    '{olderEventsNotice(resolvedPage)}\n'
    'setPageState(classifyOlderPage(page.length, TIMELINE_WINDOW_LIMIT));\n'
    'setOlder((prev) => mergeOlderEvents(prev, page));\n'
)


def _calls(source: str, pattern: re.Pattern[str]) -> bool:
    """Does the reader *call* the helper, not merely import it?

    An import satisfies a naive substring check even after the call site is
    deleted: the module still names the helper while rendering nothing from it.
    """
    return pattern.search(source) is not None


def test_panel_pages_backwards_with_the_declared_helpers():
    panel = PANEL.read_text(encoding="utf-8")
    assert _calls(panel, _NOTICE_CALL), "the paging control must render the notice"
    assert _calls(panel, _CLASSIFY_CALL), "the next state must derive from the response length"
    assert _calls(panel, _MERGE_CALL), "older pages must merge beneath the newest window"


def test_panel_requests_the_offset_through_the_declared_helper():
    panel = PANEL.read_text(encoding="utf-8")
    assert re.search(r"offset=\$\{olderOffset\(", panel), (
        "the request must derive its offset from olderOffset, not a bare literal"
    )


def test_contract_states_two_distinct_outcomes():
    contracts = CONTRACTS.read_text(encoding="utf-8")
    assert 'export type OlderPage' in contracts and '"more"' in contracts and '"start"' in contracts
    assert re.search(r"page === \"more\"\s*\?", contracts), "the notice must branch on the paging state"


def test_notice_copy_differs_between_more_and_start():
    contracts = CONTRACTS.read_text(encoding="utf-8")
    assert "Older events exist beyond this window" in contracts
    assert "no older events to load" in contracts, (
        "a reader that can still page and one that has reached the start must never share wording"
    )


# ── source detectors, each proven to bite by a negative control ─────────────

def test_detector_flags_a_reader_with_no_paging_control():
    pre_repair = 'const latest = events[events.length - 1];'
    assert _calls(pre_repair, _NOTICE_CALL) is False
    assert _calls(pre_repair, _CLASSIFY_CALL) is False
    assert _calls(pre_repair, _MERGE_CALL) is False


def test_detector_flags_an_import_without_a_call():
    imported_only = (
        'import { olderEventsNotice, classifyOlderPage, mergeOlderEvents } from "./contracts";\n'
        'const latest = events[events.length - 1];'
    )
    assert _calls(imported_only, _NOTICE_CALL) is False, (
        "an import is not a call: the detector must not pass a reader that renders nothing "
        "from the helpers it names"
    )


def test_detector_passes_the_paging_reader():
    assert _calls(PANEL_MINIMAL, _NOTICE_CALL) is True
    assert _calls(PANEL_MINIMAL, _CLASSIFY_CALL) is True
    assert _calls(PANEL_MINIMAL, _MERGE_CALL) is True


# ── read-only and authority-free, like the surrounding console surfaces ─────

def test_panel_opens_no_new_transport_or_authority():
    panel = PANEL.read_text(encoding="utf-8")
    assert "fetch(" not in panel, "the reader uses apiRequest through useHydration; it opens no transport"
    assert re.search(r"\bapiRequest\b", panel), "reads still go through the shared client"
    assert "token" not in panel.lower() or "Bearer" not in panel, "the reader invents no authority"


# ── an unresolved session must not be reported as a settled sign-out ────────
#
# The reader is owner-scoped (`knowledge.timeline._timeline_owner_clause`):
# authenticated -> `user_id = ?`, anonymous -> `1 = 0`. Firebase restores a
# session asynchronously, so the client is briefly *neither* signed in nor signed
# out. Treating that window as "anonymous" makes the panel assert "no identity is
# present" about a viewer who has one — a claim the client cannot yet make. The
# scope vocabulary therefore carries a third value, `pending`, derived from the
# auth context's own `identityState`.

_PENDING_LITERAL = re.compile(r'"pending"')


def test_scope_vocabulary_carries_the_pending_state():
    contracts = CONTRACTS.read_text(encoding="utf-8")
    assert re.search(r'export type TimelineScope = [^;]*"pending"', contracts), (
        "the reader's scope must name the unresolved-identity state explicitly"
    )
    assert re.search(r'export type TimelineViewer = ViewerKind \| "pending"', contracts), (
        "the viewer type must extend the shared ViewerKind rather than replace it"
    )


def test_classify_timeline_scope_resolves_pending_distinctly():
    contracts = CONTRACTS.read_text(encoding="utf-8")
    # The classifier must *branch* on the pending viewer; a ternary with only two
    # arms would silently fold pending into unscoped.
    assert re.search(r'viewer === "pending"\s*\?\s*"pending"', contracts), (
        "classifyTimelineScope must return the pending scope, not fall through to unscoped"
    )


def test_empty_copy_gives_pending_its_own_wording():
    contracts = CONTRACTS.read_text(encoding="utf-8")
    assert "your session is still resolving" in contracts, "pending needs its own empty-read copy"
    assert 'if (scope === "pending")' in contracts, (
        "the empty notice must branch on pending, not share the unscoped arm"
    )
    # The pending notice and the settled-anonymous notice must never share wording:
    # one states the session is unresolved, the other states no identity is present.
    assert "no identity is present, so nothing was readable" in contracts


def test_panel_derives_pending_from_the_auth_identity_state():
    panel = PANEL.read_text(encoding="utf-8")
    assert "identityState" in panel, "the panel must read the auth context's identity state"
    assert re.search(r'identityState === "loading"', panel), (
        "an unresolved session is the auth context's loading state"
    )
    assert re.search(r':\s*"anonymous"', panel), "a resolved signed-out viewer stays anonymous"


def test_detector_flags_the_pre_repair_two_state_viewer():
    """Negative control: the shape before this slice folds pending into anonymous."""
    pre_repair_panel = (
        'const { isAuthenticated } = useAuth();\n'
        'const viewer: ViewerKind = isAuthenticated ? "authenticated" : "anonymous";\n'
    )
    assert "identityState" not in pre_repair_panel
    assert not re.search(r'identityState === "loading"', pre_repair_panel), (
        "the detector must not pass a viewer that never consults the identity state"
    )
    pre_repair_contracts = 'export type TimelineScope = "owner" | "unscoped";'
    assert not _PENDING_LITERAL.search(pre_repair_contracts), (
        "the detector must not pass a scope vocabulary with no pending member"
    )

