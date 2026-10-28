"""Lane 2 (NovaNet) — the public field must state completeness, not truncate silently.

`GET /api/transmissions` caps `limit` at 50 and returns the **uncapped** `total`:

    limit = max(1, min(int(limit), 100))
    return {"transmissions": posts[offset:offset + limit], "total": len(posts)}

The field panel rendered `field.data.transmissions` and headed itself with
`${field.data.total} transmissions`. Past 50 posts the header therefore stated a
count the list below it could not contain, and nothing said so: an incomplete
render presented as the whole field. This is the same truthfulness class the
echoes panel beside it already satisfies (`ECHO_DISPLAY_LIMIT` + a notice).

This guard measures both halves:

  * the **backend** half is *executed* — 60 posts are seeded through the real
    store and the real route is read, so the cap is a measurement, not a reading
    of the source;
  * the **frontend** half is a pure source detector over the real
    `NovaNetPage.tsx`, carrying a negative control that reproduces the
    pre-change silent-cap render and asserts the detector flags it.

Ownership: this test and the source it pins are Lane 2 (NovaNet). It reads only
NovaNet files and the transmissions route, and asserts nothing about another
lane's owned surface.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import api.transmissions as tx

ROOT = Path(__file__).resolve().parents[1]
NOVANET = ROOT / "web/arkadia_console/src/pages/NovaNetPage.tsx"

SOURCE = NOVANET.read_text(encoding="utf-8")

# The field panel's render branch: from the empty-state test to the fallback
# contract state. Scoping the detector to this region keeps it from reading the
# echoes panel, which has its own bound and its own notice.
FIELD_START = 'field.data.transmissions.length === 0'
FIELD_END = '<ContractState state={field.state}'


def field_block(src: str) -> str:
    start = src.index(FIELD_START)
    end = src.index(FIELD_END, start)
    return src[start:end]


def find_silent_cap(src: str) -> list[str]:
    """Return the defects of a field panel that renders a page as if it were the whole.

    Pure source detector, so it can be proven against the pre-change form.
    """
    block = field_block(src)
    problems: list[str] = []
    if "novanet-transmissions-truncation" not in block:
        problems.append("no truncation notice rendered when the render is bounded")
    if "FIELD_PAGE_LIMIT" not in src:
        problems.append("the requested page size is not single-sourced (a bare literal drifts)")
    if ".total" not in block:
        problems.append("the panel does not state the field total")
    if "field.data.total > field.data.transmissions.length" not in block:
        problems.append("the truncation notice is not conditioned on the total exceeding the render")
    return problems


def drop_retrieval_control(src: str) -> str:
    """Remove the older-page control's JSX block, keeping the notice it accompanies.

    Located by the control's own guard expression and removed by balanced braces,
    not by a comment marker: a reconstruction anchored on prose breaks the moment
    the prose moves, and a negative control that raises is not a control.
    """
    anchor = "{fieldOffset + field.data.transmissions.length < field.data.total && ("
    start = src.find(anchor)
    if start < 0:
        return src
    depth = 0
    for i in range(start, len(src)):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                return src[:start] + src[i + 1 :]
    return src


def find_unretrievable_disclosure(src: str) -> list[str]:
    """Return the defects of a field that discloses a truncation it cannot remedy.

    A notice that names a remainder the surface offers no way to read is a
    disclosure without a remedy: the reader is told the field is larger than the
    page and left holding the page.

    The property is *the window can still move while a remainder exists* — not
    "the growth stops somewhere". An earlier revision of this detector required
    the growth to be capped by the handler's own `limit` ceiling, which encodes
    the opposite of the property: the ceiling bounds **one request**, not the
    field, so capping the window at it retires the control while a remainder is
    still named. That is the defect this detector now measures, and
    `test_negative_control_detector_flags_a_window_that_retires_early` feeds it
    the shipped form that had exactly that shape.
    """
    block = field_block(src)
    problems: list[str] = []
    if "novanet-transmissions-more" not in block:
        problems.append("the truncation notice offers no way to retrieve the remainder")
    if "useState(0)" not in src:
        problems.append("the window position is not state, so no control can move it")
    if "setFieldOffset" not in block:
        problems.append("no control moves the window")
    # The window must advance by a page, not by a step that stops short of the
    # field: the request carries `limit` and `offset` together, so every page of
    # the field is one more read regardless of the handler's per-request clamp.
    if "?limit=${FIELD_PAGE_LIMIT}&offset=${fieldOffset}" not in src:
        problems.append("the request does not carry a window offset, so it can only re-read one page")
    # The control's own guard must compare the window's end against the total. A
    # guard on any other quantity (the page size, a request ceiling) retires the
    # control while the notice still names a remainder.
    if "fieldOffset + field.data.transmissions.length < field.data.total" not in block:
        problems.append("the older-page control retires on a quantity other than the field's end")
    return problems


# ------------------------------------------------------------------ backend


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(tx, "DATA_FILE", str(tmp_path / "transmissions.json"))
    app = FastAPI()
    app.include_router(tx.router)
    return TestClient(app)


def _seed(n: int) -> None:
    tx._save(
        [
            {
                "id": f"p{i}",
                "owner_uid": None,
                "content": f"transmission {i}",
                "timestamp": i,
                "reactions": {"heart": 0, "fire": 0, "star": 0, "mind": 0},
                "comments": [],
                "reposts": 0,
            }
            for i in range(n)
        ]
    )


def test_the_default_page_is_capped_while_the_total_is_not(client):
    """The defect's premise, executed rather than read: 60 stored, 50 returned."""
    _seed(60)
    body = client.get("/api/transmissions").json()
    assert body["total"] == 60, "the total is the uncapped count of the field"
    assert len(body["transmissions"]) == 50, "the default page is capped"
    assert len(body["transmissions"]) < body["total"], (
        "the render is a page of the field, not the whole of it"
    )


def test_a_full_page_reports_no_shortfall(client):
    """At or below the cap there is nothing to disclose — the notice must stay off."""
    _seed(50)
    body = client.get("/api/transmissions").json()
    assert len(body["transmissions"]) == body["total"] == 50


def test_requested_page_size_is_honoured_up_to_the_handler_ceiling(client):
    """`FIELD_PAGE_LIMIT` is a request, so the handler must accept it verbatim."""
    _seed(60)
    body = client.get(f"/api/transmissions?limit={50}").json()
    assert len(body["transmissions"]) == 50
    # The handler's own ceiling is 100; asking past it is clamped, not an error.
    clamped = client.get("/api/transmissions?limit=500").json()
    assert len(clamped["transmissions"]) == 60


# ----------------------------------------------------------------- frontend


def test_field_panel_states_total_and_notices_truncation():
    assert find_silent_cap(SOURCE) == [], find_silent_cap(SOURCE)


def test_page_size_is_single_sourced_and_drives_the_request():
    # The bound is declared once and the request uses that name, so the fetched
    # page and the notice cannot drift apart. The path is a *registry-derived
    # binding*, not an inline path: the Lane 1 registry contract
    # (`test_every_page_read_uses_the_registry_not_an_inline_path`) requires that
    # shape, so this guard pins it too rather than letting the fix redden Lane 1.
    # The window position is state because the remainder must stay reachable, so
    # the request carries `fieldOffset` — moved by one declared page at a time,
    # never by a second literal and never capped at the handler's per-request
    # clamp (which bounds one read, not the field).
    assert "const FIELD_PAGE_LIMIT = 50;" in SOURCE
    assert "const [fieldOffset, setFieldOffset] = useState(0);" in SOURCE
    assert (
        "const fieldPath = `${endpoints.transmissions}?limit=${FIELD_PAGE_LIMIT}&offset=${fieldOffset}`;"
        in SOURCE
    )
    assert "useHydration<TransmissionList>(\n    fieldPath," in SOURCE
    assert FIELD_START in SOURCE


def test_the_field_path_is_registry_derived_not_inline():
    """The slice must not reintroduce a page-local endpoint contract."""
    assert re.search(r"const fieldPath = `\$\{endpoints\.transmissions\}", SOURCE)
    # The argument handed to useHydration must be the binding, never a template
    # literal written at the call site.
    assert "useHydration<TransmissionList>(\n    `" not in SOURCE


def test_negative_control_detector_flags_the_pre_change_form():
    """The detector must flag the exact silent-cap shape it was written to remove."""
    old = SOURCE.replace("field.data.total > field.data.transmissions.length", "field.data.total > 0")
    old = old.replace("novanet-transmissions-truncation", "removed")
    old = old.replace("FIELD_PAGE_LIMIT", "50")
    problems = find_silent_cap(old)
    assert problems, "detector failed to flag the pre-change silent-cap render"
    assert any("truncation notice" in p for p in problems)
    assert any("single-sourced" in p for p in problems)


def test_the_disclosed_remainder_is_retrievable():
    """A truncation notice the reader cannot act on is still a page presented as the field.

    The notice above satisfies `find_silent_cap` while leaving the remainder
    unreadable — the panel says "not rendered on this surface" and offers no way
    to render it. `GET /api/transmissions` serves `offset` as well as `limit`, so
    the remedy is a verified contract, not an invention: this node requires the
    window position to be state and a control to move it while a remainder exists.
    """
    assert find_unretrievable_disclosure(SOURCE) == [], find_unretrievable_disclosure(SOURCE)
    # The control retires on the field's own end, not on the handler's per-request
    # clamp: the clamp bounds one read, so a control guarded on it would vanish
    # with a remainder still named.
    assert "fieldOffset + field.data.transmissions.length < field.data.total" in SOURCE
    assert "setFieldOffset((offset) => offset + FIELD_PAGE_LIMIT)" in SOURCE


def test_negative_control_detector_flags_a_window_that_retires_early():
    """The detector must flag the exact shape this slice removes: a window whose
    control retires at the handler's per-request clamp while the notice still
    names a remainder.

    This is the shipped form reconstructed verbatim — `fieldPage` grown by
    `Math.min(page + FIELD_PAGE_LIMIT, TRANSMISSION_PAGE_CEILING)` and a control
    guarded on `fieldPage < TRANSMISSION_PAGE_CEILING`. Measured against the real
    handler with 150 posts stored, that ladder stops at `limit=100` with 50 posts
    still unrendered and no control left to reach them. A detector that passes
    this reconstruction is not measuring retrievability at all.
    """
    early = (
        SOURCE.replace(
            "const [fieldOffset, setFieldOffset] = useState(0);",
            "const [fieldPage, setFieldPage] = useState(FIELD_PAGE_LIMIT);",
        )
        .replace("?limit=${FIELD_PAGE_LIMIT}&offset=${fieldOffset}", "?limit=${fieldPage}")
        .replace(
            "fieldOffset + field.data.transmissions.length < field.data.total",
            "fieldPage < TRANSMISSION_PAGE_CEILING",
        )
        .replace(
            "setFieldOffset((offset) => offset + FIELD_PAGE_LIMIT)",
            "setFieldPage((page) => Math.min(page + FIELD_PAGE_LIMIT, TRANSMISSION_PAGE_CEILING))",
        )
    )
    # Keep the control in the reconstruction: this control is *present* and still
    # cannot reach the remainder, which is what distinguishes it from the bare
    # notice the other negative control covers.
    assert "novanet-transmissions-more" in early, "the reconstruction dropped the control"
    problems = find_unretrievable_disclosure(early)
    assert problems, "detector failed to flag a window that retires with a remainder named"
    assert any("retires on a quantity other than the field's end" in p for p in problems)
    assert any("does not carry a window offset" in p for p in problems)
    # ...and the silent-cap detector still passes it, proving the two measure
    # different properties rather than one re-stating the other.
    assert find_silent_cap(early) == []


def test_negative_control_detector_flags_a_notice_without_a_remedy():
    """The detector must flag the exact shape this slice removes: a bare notice.

    The reconstruction is the pre-change panel verbatim — a fixed window and a
    notice with no control — so a detector that is silent here is not measuring
    retrievability at all.
    """
    old = SOURCE.replace(
        "const [fieldOffset, setFieldOffset] = useState(0);",
        "const fieldOffset = 0;",
    ).replace("&offset=${fieldOffset}", "")
    # Drop the older-page control, keeping the notice it accompanies.
    old = drop_retrieval_control(old)
    assert "novanet-transmissions-more" not in old, "the reconstruction kept the control"
    problems = find_unretrievable_disclosure(old)
    assert problems, "detector failed to flag a notice with no way to retrieve the remainder"
    assert any("no way to retrieve" in p for p in problems)
    # ...and the silent-cap detector still passes it, proving the two measure
    # different properties rather than one re-stating the other.
    assert find_silent_cap(old) == []
