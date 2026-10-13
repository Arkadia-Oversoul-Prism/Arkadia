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
