"""Lane 2 (NovaNet) — the echoes panel must state completeness, not truncate silently.

The Crystal-Matrix echoes panel renders a bounded subset of `EchoesFeed.public`
per read. Before this guard the bound was a bare `slice(0, 8)` with no total and
no notice, so a reader could not tell the panel was showing a subset — an
incomplete render presented as if it were the whole stream. This is the same
truthfulness class the transmissions panel already satisfies (it renders all).

Ownership: this test and the source it pins are Lane 2 (NovaNet). It reads only
NovaNet files and asserts nothing about another lane's owned surface.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOVANET = ROOT / "web/arkadia_console/src/pages/NovaNetPage.tsx"

SOURCE = NOVANET.read_text()


def find_silent_cap(src: str) -> list[str]:
    """Return the defects of a panel that caps its render without stating the total.

    Pure source detector, so it can be proven against the pre-change form.
    """
    problems: list[str] = []
    if "novanet-echoes-truncation" not in src:
        problems.append("no truncation notice rendered when the render is bounded")
    if "ECHO_DISPLAY_LIMIT" not in src:
        problems.append("render bound is not single-sourced (a bare slice count drifts)")
    if "public.length" not in src:
        problems.append("the panel does not state the public total")
    if not ("length > ECHO_DISPLAY_LIMIT" in src or "length >  ECHO_DISPLAY_LIMIT" in src):
        problems.append("the truncation notice is not conditioned on the total exceeding the bound")
    return problems


def test_echoes_panel_states_total_and_notices_truncation():
    assert find_silent_cap(SOURCE) == [], find_silent_cap(SOURCE)


def test_render_bound_is_single_sourced_and_slices_by_it():
    # The cap is declared once and the slice uses that name, so the rendered
    # subset, the stated total and the notice cannot drift apart.
    assert "const ECHO_DISPLAY_LIMIT = 8;" in SOURCE
    assert "public.slice(0, ECHO_DISPLAY_LIMIT)" in SOURCE
    assert "public.slice(0, 8)" not in SOURCE


def test_negative_control_detector_flags_the_pre_change_form():
    """The detector must flag the exact silent-cap shape it was written to remove."""
    old = SOURCE.replace(
        "public.slice(0, ECHO_DISPLAY_LIMIT)",
        "public.slice(0, 8)",
    ).replace("ECHO_DISPLAY_LIMIT", "8")
    # Strip the notice and the derived total, reproducing the pre-change render.
    old = old.replace("novanet-echoes-truncation", "removed")
    old = old.replace("length > 8", "length > 0")
    problems = find_silent_cap(old)
    assert problems, "detector failed to flag the pre-change silent-cap render"
    assert any("truncation notice" in p for p in problems)


# ---------------------------------------------------------------------------
# Echo display completeness — every field the handler derives reaches the reader.
# ---------------------------------------------------------------------------

ECHOES_START = 'data-testid="novanet-echoes"'
ECHOES_END = "novanet-echoes-truncation"

#: The display fields `GET /api/echoes` derives for every public echo
#: (`api/main.py::echoes_feed`): `title`, `category`, `preview` (the scroll body
#: truncated to 200 characters), `source`, and `resonance`. All five are present
#: on every entry, so a field the panel omits is content the reader never sees.
ECHO_DISPLAY_FIELDS = ("title", "category", "preview", "source", "resonance")


def echo_block(src: str) -> str:
    """The echoes list region, so the detector cannot read the field panel."""
    start = src.index(ECHOES_START)
    end = src.index(ECHOES_END, start)
    return src[start:end]


def find_unrendered_echo_fields(src: str) -> list[str]:
    """Return handler-supplied echo fields the panel receives but never renders.

    The panel's job is to show what the feed carries. A field the handler derives
    for every entry and the panel silently drops is content the reader cannot see:
    an echo's headline without its substance reads as an empty entry. Pure source
    detector, so it can be proven against the pre-change form.
    """
    block = echo_block(src)
    return [
        f"the panel renders no `{field}`, so the handler's value is invisible"
        for field in ECHO_DISPLAY_FIELDS
        if f"e.{field}" not in block
    ]


def drop_preview_block(src: str) -> str:
    """Remove the preview's JSX block by balanced braces, not by a prose anchor."""
    anchor = "{e.preview && ("
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


def test_every_handler_supplied_echo_field_is_rendered():
    """An echo's declared facets must reach the reader, not stop at the type."""
    assert find_unrendered_echo_fields(SOURCE) == [], find_unrendered_echo_fields(SOURCE)


def test_negative_control_detector_flags_the_dropped_echo_substance():
    """The detector must flag the exact pre-change render: title only.

    Before this guard the panel rendered `title`, `source` and `resonance` and
    dropped `category` and `preview`, so an echo's substance — the handler's own
    200-character body preview — was invisible. A detector silent here is not
    measuring render completeness at all.
    """
    old = drop_preview_block(SOURCE).replace(" · {e.category} ·", " ·")
    problems = find_unrendered_echo_fields(old)
    assert problems, "detector failed to flag an echo panel that drops the handler's preview"
    assert any("preview" in p for p in problems)
    assert any("category" in p for p in problems)
    # ...and the silent-cap detector still passes it, proving the two measure
    # different properties rather than one re-stating the other.
    assert find_silent_cap(old) == []
