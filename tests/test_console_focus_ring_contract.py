"""Keyboard focus must be visible, and motion must be reducible (Slice A).

Two capabilities the archived Prism carried in `index.css` were dropped by the
console rebuild (`c081d200`, "Frontend rebuild: archive Prism UI, scaffold
canonical Arkadia Console"), and neither has been restored:

  1. A shared focus ring —
     `button:focus-visible,a:focus-visible,input:focus-visible,textarea:focus-visible
      { outline:2px solid rgba(0,212,170,.65); outline-offset:2px }`.
     On the console, `grep -rn "focus-visible" web/arkadia_console` was **empty**:
     the only keyboard cue was Tailwind preflight's `:focus { outline: auto }`,
     which is UA-coloured (a light ring on Windows' default light UA stylesheet),
     not the design system's emerald, and is visibly inconsistent with the same
     control hovered.

  2. A reduced-motion escape —
     `@media(prefers-reduced-motion:reduce){ … animation-duration:.01ms … }`.
     On the console, `grep -rn "prefers-reduced-motion" web/arkadia_console` was
     **empty** while `animate-pulse` is used as the loading signal in
     `components/ui.tsx`, `pages/ArkanaPage.tsx` and
     `components/opportunities/ProjectOpportunityRadar.tsx`. A user who sets
     "reduce motion" keeps the pulses.

Both are recovered, not invented: each rule below is the archived Prism's own
rule, restated against the console's tokens (`outline-emerald/65` is the
`emerald: #00D4AA` token at the same alpha the archive used).

This guard is disjoint from `tests/test_console_shell_nav_contract.py`, which
pins the shell's skip link, its focus hand-off and the lens strip, and from
`tests/test_console_lens_landmark_contract.py`, which pins the strip's landmark.
Neither asserts the *visible focus indicator* or the motion query.

Each detector carries a negative control fed the exact pre-repair shape, so a
detector that always passes is itself caught.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_CSS_PATH = ROOT / "web" / "arkadia_console" / "src" / "index.css"

INDEX_CSS = INDEX_CSS_PATH.read_text(encoding="utf-8")

# The archived Prism's rule, kept verbatim in the module docstring above so the
# recovery is auditable against the source it came from.
ARCHIVE_FOCUS_RULE = (
    "button:focus-visible,a:focus-visible,input:focus-visible,textarea:focus-visible"
    "{outline:2px solid rgba(0,212,170,.65);outline-offset:2px}"
)

_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)


def _strip_comments(css: str) -> str:
    """Comments are not stylesheets. Two of them in `index.css` quote the
    archive's `:focus-visible` rule as documentation, so a detector that read
    raw text would report the *prose* as the fix."""
    return _COMMENT.sub("", css)


def _rules(css: str) -> list[tuple[str, str]]:
    """``(selector_list, body)`` for every rule, at any nesting depth.

    The ring is declared inside ``@layer base { … }``, so a flat top-level scan
    never sees it. Each rule's body is re-parsed when it contains a brace, which
    reaches the nested rule without a full CSS grammar.
    """
    out: list[tuple[str, str]] = []
    depth, selector_start, open_index = 0, 0, -1
    for i, c in enumerate(css):
        if c == "{":
            if depth == 0:
                open_index = i
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                out.append((css[selector_start:open_index], css[open_index + 1:i]))
                selector_start = i + 1
        elif depth == 0 and c == ";":
            selector_start = i + 1
    nested = [(s, b) for s, b in out if "{" in b]
    for _, body in nested:
        out.extend(_rules(body))
    return out


def _rule_bodies_for(css: str, needle: str) -> list[str]:
    """Bodies of rules whose selector list contains ``needle`` (e.g.
    ``:focus-visible``), comments removed first."""
    clean = _strip_comments(css)
    return [body for selector, body in _rules(clean) if needle in selector]


def _focus_visible_bodies(css: str) -> list[str]:
    return _rule_bodies_for(css, ":focus-visible")


def _focus_ring_defects(css: str) -> list[str]:
    """A shared, token-derived focus indicator for every interactive element.

    Defect if no ``:focus-visible`` rule declares an outline covering the
    interactive element selectors, or if any focus ring reaches for a raw hex
    colour instead of the design token (the page-local-hex class the design
    system forbids).
    """
    defects: list[str] = []
    bodies = _focus_visible_bodies(css)
    if not bodies:
        return ["no :focus-visible rule: keyboard focus falls back to the UA ring"]

    joined = "\n".join(bodies)
    for element in ("button", "a", "input", "textarea"):
        if not re.search(rf"(^|[\s,>+~]){element}\s*:\s*focus-visible", _strip_comments(css)):
            defects.append(f"no :focus-visible outline declared for <{element}>")
    if "outline" not in joined:
        defects.append(":focus-visible rule declares no outline")
    if "emerald" not in joined:
        defects.append("focus ring is not drawn from the emerald design token")
    if re.search(r"#[0-9A-Fa-f]{3,8}\b", joined):
        defects.append("focus ring uses a raw hex colour instead of a token")
    return defects


def _motion_defects(css: str) -> list[str]:
    """Every animation and transition must collapse under reduce-motion.

    Defect if the query is absent, or present but does not neutralise both
    ``animation-duration`` and ``transition-duration``.
    """
    clean = _strip_comments(css)
    m = re.search(r"@media\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)\s*\{", clean)
    if not m:
        return ["no @media (prefers-reduced-motion: reduce) block: pulses and "
                "transitions ignore the OS setting"]
    depth, i = 1, m.end()
    while i < len(clean) and depth:
        depth += clean[i] == "{"
        depth -= clean[i] == "}"
        i += 1
    body = clean[m.end():i]
    defects: list[str] = []
    for prop in ("animation-duration", "transition-duration"):
        if not re.search(rf"{prop}\s*:\s*0?\.0*1m?s", body):
            defects.append(f"reduce-motion block does not neutralise {prop}")
    return defects


# ---------------------------------------------------------------------------
# The contract
# ---------------------------------------------------------------------------


def test_keyboard_focus_takes_the_shared_emerald_ring():
    """Slice A: the console must not rely on the UA focus ring. It echoed a ring
    the archive styled; the console removed it."""
    assert _focus_ring_defects(INDEX_CSS) == [], _focus_ring_defects(INDEX_CSS)


def test_the_ring_covers_the_console_s_interactive_element_set():
    """The shell and pages focus ``a``, ``button``, ``input`` and ``textarea``
    (``grep -rn "<button\\|<a \\|<input\\|<textarea" web/arkadia_console/src``).
    A ring that covers only ``button`` leaves the skip link and every form field
    on the UA default. ``select`` is included for parity with the token set.
    """
    clean = _strip_comments(INDEX_CSS)
    for element in ("a", "button", "input", "select", "textarea"):
        assert re.search(rf"(^|[\s,>+~]){element}\s*:\s*focus-visible", clean), (
            f"<{element}>:focus-visible is not declared"
        )


def test_the_ring_is_not_applied_to_a_mouse_click():
    """``:focus-visible`` (not ``:focus``) is what keeps the ring off a pointer
    click. Styling bare ``:focus`` would ring every mouse-pressed button — a
    different, noisier interface, and not what the archive did."""
    clean = _strip_comments(INDEX_CSS)
    assert not re.search(r"(^|[\s,>+~])(a|button|input|select|textarea)\s*:\s*focus\s*\{", clean), (
        "a bare :focus rule rings pointer clicks; use :focus-visible"
    )


def test_reduced_motion_collapses_the_loading_pulses():
    """``animate-pulse`` is the console's loading signal in three files. A user
    who asks the OS for less motion must not keep it."""
    assert _motion_defects(INDEX_CSS) == [], _motion_defects(INDEX_CSS)


def test_the_motion_query_is_scoped_to_the_media_feature():
    """The archive's block is guarded by the media feature, not a class a page
    must remember to add. An unguarded ``.reduce-motion`` rule would only help
    components that opted in — the ones that forgot are the ones that matter."""
    assert "prefers-reduced-motion: reduce" in _strip_comments(INDEX_CSS)


def test_the_archive_rule_is_quoted_verbatim_for_auditability():
    """The recovery is auditable only if the rule it was recovered *from* is in
    the file. This pins the archive's own text, so a later edit cannot quietly
    re-point the provenance at something else."""
    assert ARCHIVE_FOCUS_RULE in (
        ROOT / "archive" / "frontend" / "arkadia-prism" / "web"
        / "public_prism" / "src" / "index.css"
    ).read_text(encoding="utf-8"), (
        "the archived Prism focus rule moved; update ARCHIVE_FOCUS_RULE"
    )


# ---------------------------------------------------------------------------
# Negative controls — each detector must flag the pre-repair shape.
# ---------------------------------------------------------------------------


def _pre_repair_css() -> str:
    """`index.css` as it stood before this slice: no focus ring, no motion
    query. Derived by removing both blocks from the live file, so the control
    cannot drift from the file it protects."""
    clean = _strip_comments(INDEX_CSS)
    no_motion = re.sub(
        r"@media\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)\s*\{.*?\n\}\n?",
        "",
        clean,
        flags=re.DOTALL,
    )
    no_ring = re.sub(r"@layer\s+base\s*\{.*?\n\}\n?", "", no_motion, flags=re.DOTALL)
    return no_ring


def test_detector_flags_the_pre_repair_stylesheet():
    """The exact pre-repair shape — a stylesheet with no ring and no motion
    query — must be reported by both detectors."""
    stale = _pre_repair_css()
    assert ":focus-visible" not in stale, "control did not remove the ring"
    assert "prefers-reduced-motion" not in stale, "control did not remove the motion query"
    assert _focus_ring_defects(stale), "ring detector missed the pre-repair file"
    assert _motion_defects(stale), "motion detector missed the pre-repair file"


def test_detector_flags_a_ring_that_is_not_token_derived():
    """Negative control: the archive's own rgba literal is not the console's
    token vocabulary. Grafting it back must not pass as token-derived."""
    hexed = INDEX_CSS.replace("outline-emerald/65", "outline-[#00D4AA]")
    assert hexed != INDEX_CSS, "control did not change the ring -- detector unproven"
    assert any("raw hex" in d for d in _focus_ring_defects(hexed)), _focus_ring_defects(hexed)


def test_detector_flags_a_ring_that_covers_only_buttons():
    """Negative control: a ring on ``button`` alone leaves the skip link and
    every form field on the UA default — the partial fix must be reported."""
    partial = re.sub(
        r"\n\s*a:focus-visible,\n\s*button:focus-visible,",
        "\n  button:focus-visible,",
        re.sub(r"\n\s*select:focus-visible,\n\s*textarea:focus-visible", "", INDEX_CSS),
    )
    assert partial != INDEX_CSS, "control did not narrow the ring -- detector unproven"
    defects = _focus_ring_defects(partial)
    assert any("<a>" in d or "<input>" in d or "<textarea>" in d for d in defects), defects


def test_detector_flags_a_motion_query_that_forgets_transitions():
    """Negative control: the console animates with ``transition`` too
    (``Shell.tsx``, ``SurfaceLenses.tsx``, ``HomePage.tsx``). A block that only
    stops animations still leaves every hover moving."""
    defected = re.sub(r"\n\s*transition-duration: 0\.01ms !important;", "", INDEX_CSS)
    assert defected != INDEX_CSS, "control did not drop transition-duration"
    assert any("transition-duration" in d for d in _motion_defects(defected)), _motion_defects(defected)


def test_detector_ignores_the_provenance_comment():
    """The docstring and the inline comment both name `:focus-visible`. A
    detector reading raw text would score the comment as the rule; the stripper
    must be what makes the assertion real."""
    comments_only = "/* " + ARCHIVE_FOCUS_RULE + " */\n@media(prefers-reduced-motion:reduce){}\n"
    assert _focus_visible_bodies(comments_only) == [], (
        "a commented-out rule was read as a declared rule"
    )
    assert _focus_ring_defects(comments_only), "comment-only file passed the ring detector"
