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
    # page and the notice cannot drift apart.
    assert "const FIELD_PAGE_LIMIT = 50;" in SOURCE
    assert "`${endpoints.transmissions}?limit=${FIELD_PAGE_LIMIT}`" in SOURCE
    assert FIELD_START in SOURCE


def test_negative_control_detector_flags_the_pre_change_form():
    """The detector must flag the exact silent-cap shape it was written to remove."""
    old = SOURCE.replace("field.data.total > field.data.transmissions.length", "field.data.total > 0")
    old = old.replace("novanet-transmissions-truncation", "removed")
    old = old.replace("FIELD_PAGE_LIMIT", "50")
    problems = find_silent_cap(old)
    assert problems, "detector failed to flag the pre-change silent-cap render"
    assert any("truncation notice" in p for p in problems)
    assert any("single-sourced" in p for p in problems)
