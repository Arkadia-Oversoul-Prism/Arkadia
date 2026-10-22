"""The mobile navigation strip must reveal its current-page item.

The console's mobile strip (``Shell.tsx``, ``md:hidden``) renders the same nine
surfaces as the desktop aside but in a single horizontally-scrolling row that is
wider than the viewport. Measured in Chromium at 390x844 against the canonical
deployment ``https://arkadia-qzu4.onrender.com`` (revision ``3cd81f76``, which is
current ``main``): the strip is 799px wide inside a 390px viewport — 409px of
overflow — and five of the nine items sit past the right edge.

The strip marks the current surface with ``aria-current="page"`` plus the surface
accent colour, and it *is* keyboard-reachable: the browser's native focus-scroll
reveals an item as you tab to it. What did not happen was a reveal on a
*programmatic* route change. Loading ``/about``, ``/weaver`` or ``/knowledge``
directly, clicking a Home portal, or navigating back/forward left the strip at
``scrollLeft: 0``, so the active item rendered off-screen: the user saw a
navigation strip with **no visible current-page indicator at all**. Measured
before the repair — ``/about``: active item at x=725..791 in a 0..390 box,
``scrollLeft: 0``, ``fullyVisible: false``. The same measurement reproduced on the
canonical deployment, so this is a product defect and not a local build artifact.

The repair is the smallest one consistent with the existing architecture: keep the
single horizontally-scrolling strip (do not add a hamburger, a second nav model, or
a new breakpoint) and, in an effect keyed on the current surface, adjust the
strip's ``scrollLeft`` so the active item is inside the visible band. Three
properties are load-bearing and each is asserted separately, because they fail
independently:

1. the strip is bound to a ref, or there is nothing to scroll;
2. a reveal runs on a route change (``[current]``), or it happens once and never
   follows later navigation;
3. the reveal moves the strip *horizontally only* — a ``scrollIntoView`` would also
   scroll the page vertically, and the shell already owns vertical position through
   its content-landmark focus;
4. the reveal re-runs when the strip's own box changes. A route change is not the
   only event that can hide the active item: narrowing the viewport grows the
   strip's scrollable range without moving ``scrollLeft``, stranding the active
   item off-screen again. Measured on the first cut of this repair, which keyed the
   reveal on ``[current]`` alone — **4/4** narrowings left the active item past the
   right edge (700→400, 600→360, 390→320, 767→300). The reveal is therefore a
   callback invoked from both a route effect and a ``ResizeObserver`` on the strip,
   and this property is asserted separately because a route-only reveal passes
   every other assertion here while still failing this case.

Domain: the Arkadia Console (``web/arkadia_console``). Disjoint from
``test_console_shell_nav_contract.py`` (navigation/shell/design invariants: one nav
model, one router, keyboard landmark) and ``test_console_endpoint_registry_contract.py``
(the endpoint registry). Neither asserts anything about the mobile strip's
active-item visibility, and no test in ``tests/`` named the strip's
``aria-label`` before this file — the mobile navigation was an unpinned surface.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL_PATH = ROOT / "web" / "arkadia_console" / "src" / "components" / "Shell.tsx"
SHELL = SHELL_PATH.read_text(encoding="utf-8")

#: The mobile strip's accessible name. The desktop aside uses "Primary navigation"
#: and the strip "Primary navigation (mobile)"; matching the mobile name keeps the
#: detector pointed at the strip rather than the aside.
MOBILE_NAV_LABEL = "Primary navigation (mobile)"


# ---------------------------------------------------------------------------
# Detectors (module level, so the negative controls exercise the same code the
# live assertions use).
# ---------------------------------------------------------------------------


def _opening_tag_at(src: str, start: int) -> str | None:
    """The full JSX opening tag beginning at ``start``.

    Scans to the matching ``>`` while tracking brace depth and string quotes, so a
    ``=>`` inside a JSX expression container does not terminate the tag early (a
    naive ``<[^>]*>`` match would cut the attribute list in half and hide the
    ``ref`` it is looking for).
    """
    i, depth, quote = start + 1, 0, None
    while i < len(src):
        c = src[i]
        if quote:
            if c == quote:
                quote = None
        elif c in "\"'`":
            quote = c
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == ">" and depth == 0:
            return src[start : i + 1]
        i += 1
    return None


def _mobile_nav_tag(shell_text: str) -> str | None:
    """The opening tag of the mobile navigation strip, or None."""
    i = shell_text.find(MOBILE_NAV_LABEL)
    if i == -1:
        return None
    start = shell_text.rfind("<", 0, i)
    if start == -1:
        return None
    return _opening_tag_at(shell_text, start)


def _strip_ref_name(shell_text: str) -> str | None:
    """The ref variable the mobile strip is bound to, or None."""
    tag = _mobile_nav_tag(shell_text)
    if tag is None:
        return None
    m = re.search(r"ref=\{(\w+)\}", tag)
    return m.group(1) if m else None


def _reveal_effect(shell_text: str, ref_name: str) -> str | None:
    """The ``useEffect`` that reveals the active item, or None.

    Identified by behaviour, not by position: the effect must be keyed on
    ``[current]`` and must reach the strip's ref. The reveal itself lives in a
    ``useCallback`` shared with the resize observer (see ``_reveal_callback``), so
    the effect invokes it by name; a self-contained effect is still accepted.
    """
    for m in re.finditer(r"useEffect\(\s*\(\)\s*=>\s*\{", shell_text):
        body = _balanced_braces(shell_text, m.end() - 1)
        if body is None:
            continue
        tail = shell_text[m.end() + len(body) - 1 :][:120]
        if not re.search(r",\s*\[current[,\]]", tail):
            continue
        if ref_name in body or "revealActiveItem" in body:
            return body
    return None


def _reveal_callback(shell_text: str, ref_name: str) -> str | None:
    """The callback that performs the reveal, or None.

    When the reveal is shared between the route effect and the resize observer it
    is a ``useCallback``; when it is owned by the route effect alone there is no
    callback and ``_reveal_effect`` carries the body. Returns the callback body
    when one exists, so the horizontal-only and marker assertions apply to
    whichever form the source uses.
    """
    m = re.search(r"const (\w+) = useCallback\(\s*\(\)\s*=>\s*\{", shell_text)
    if not m:
        return None
    body = _balanced_braces(shell_text, m.end() - 1)
    if body is None:
        return None
    if ref_name not in body:
        return None
    return body


def _reveal_body(shell_text: str, ref_name: str) -> str | None:
    """Whichever form carries the reveal: the callback if present, else the effect."""
    return _reveal_callback(shell_text, ref_name) or _reveal_effect(shell_text, ref_name)


def _balanced_braces(src: str, open_index: int) -> str | None:
    """The brace-balanced body starting at ``open_index`` (which must be ``{``)."""
    depth, i = 0, open_index
    while i < len(src):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                return src[open_index : i + 1]
        i += 1
    return None


def _reveal_defects(shell_text: str) -> list[str]:
    """Reasons the mobile strip does not reveal its active item. Empty == reveals.

    Four independent parts: a ref to scroll, a reveal keyed on the route, a
    horizontal-only movement, and a re-reveal when the strip's box changes.
    """
    defects = []
    tag = _mobile_nav_tag(shell_text)
    if tag is None:
        return [f"no mobile navigation strip carrying aria-label={MOBILE_NAV_LABEL!r}"]
    if "overflow-x-auto" not in tag:
        defects.append("the mobile strip is not horizontally scrollable (overflow-x-auto absent)")

    ref_name = _strip_ref_name(shell_text)
    if ref_name is None:
        defects.append("the mobile strip is not bound to a ref, so nothing can scroll it")
        return defects

    if _reveal_effect(shell_text, ref_name) is None:
        defects.append(
            f"no useEffect keyed on [current] reveals the active item through {ref_name}, "
            "so it is never revealed on a programmatic route change"
        )

    body = _reveal_body(shell_text, ref_name)
    if body is None:
        defects.append(
            f"no reveal body adjusts {ref_name}.scrollLeft, so the active item is "
            "never revealed"
        )
    else:
        # A reveal that scrolls the page as well as the strip changes the shell's
        # vertical position as a side effect of navigation.
        if "scrollIntoView" in body:
            defects.append("the reveal uses scrollIntoView, which also scrolls the page vertically")
        # `md:hidden` leaves the strip in the DOM with no layout box on desktop;
        # every rect reads 0 there, so an unguarded reveal computes a spurious
        # offset on a desktop route change.
        if "clientWidth" not in body:
            defects.append(
                "the reveal does not guard on the strip having a layout box, so it "
                "runs with zeroed rects on desktop (md:hidden)"
            )

    # Narrowing the viewport grows the strip's scrollable range without moving
    # `scrollLeft`, stranding the active item off-screen again. A route-only reveal
    # passes every assertion above and still fails this case (measured 4/4).
    if not re.search(r"ResizeObserver", shell_text):
        defects.append(
            "the reveal is not re-run when the strip's box changes, so narrowing the "
            "viewport strands the active item off-screen again"
        )
    elif _reveal_callback(shell_text, ref_name) is None:
        defects.append(
            "a ResizeObserver exists but the reveal is not a shared callback, so the "
            "observer cannot re-run the same reveal the route effect uses"
        )
    return defects


# ---------------------------------------------------------------------------
# The strip reveals its active item
# ---------------------------------------------------------------------------


def test_mobile_strip_is_horizontally_scrollable_and_ref_bound():
    """The strip is one scrolling row of the same surfaces — no second nav model."""
    tag = _mobile_nav_tag(SHELL)
    assert tag is not None, f"no mobile navigation strip in {SHELL_PATH.name}"
    assert "overflow-x-auto" in tag, tag
    assert "md:hidden" in tag, "the strip must be the mobile-only presentation"
    assert _strip_ref_name(SHELL) is not None, (
        "the strip must carry a ref so the active item can be scrolled into view"
    )


def test_active_item_is_revealed_on_a_route_change():
    """The load-bearing assertion: a route change must reveal the active item."""
    assert _reveal_defects(SHELL) == [], _reveal_defects(SHELL)


def test_active_item_is_re_revealed_when_the_strip_box_changes():
    """Narrowing the viewport must not strand the active item off-screen.

    Asserted separately from the route-change property because the first cut of this
    repair satisfied every other assertion here and still failed this case: keyed on
    ``[current]`` alone, the reveal never re-ran on a resize, and 4/4 narrowings left
    the active item past the right edge.
    """
    assert not any("box changes" in d or "shared callback" in d for d in _reveal_defects(SHELL)), (
        _reveal_defects(SHELL)
    )


def test_reveal_moves_the_strip_horizontally_only():
    """Vertical position belongs to the content-landmark focus, not to this effect."""
    ref_name = _strip_ref_name(SHELL)
    assert ref_name is not None
    body = _reveal_body(SHELL, ref_name)
    assert body is not None, "no reveal found"
    assert "scrollIntoView" not in body, (
        "scrollIntoView would also scroll the page vertically on every navigation"
    )
    assert "scrollLeft" in body


def test_reveal_targets_the_declared_active_marker():
    """The reveal must key off `aria-current="page"`, the marker the strip sets.

    A reveal that looked for some other selector would silently find nothing and
    the strip would go back to showing no current page.
    """
    ref_name = _strip_ref_name(SHELL)
    body = _reveal_body(SHELL, ref_name)
    assert body is not None
    assert 'aria-current="page"' in body, (
        "the reveal must locate the active item through the aria-current marker the "
        "strip itself sets, not a second independent notion of 'active'"
    )


# ---------------------------------------------------------------------------
# Negative controls — each detector must flag the defect it claims to detect.
# ---------------------------------------------------------------------------


def _strip_reveal_effect(shell_text: str) -> str:
    """The measured pre-repair shape: the strip with no reveal logic at all.

    Located structurally, not by a comment: the reveal is either a ``useCallback``
    or a ``useEffect``, and it sits immediately before the component's own
    ``return (``. Both bounds are searched *after* the shell's ``mainRef``
    declaration, because module-level components earlier in the file (``NavLink``)
    also end in ``return (`` and an unanchored search would slice the wrong span.
    """
    anchor = shell_text.find("const mainRef = useRef")
    assert anchor != -1, "control could not locate the shell body -- detector unproven"
    end = shell_text.find("  return (", anchor)
    assert end != -1, "control could not locate the component return -- detector unproven"
    starts = [i for i in (
        shell_text.find("  const revealActiveItem = useCallback", anchor),
        shell_text.find("  // The mobile strip is wider than the viewport", anchor),
    ) if i != -1]
    assert starts, "control could not locate the reveal block -- detector unproven"
    assert min(starts) < end, "control bounds are inverted -- detector unproven"
    stale = shell_text[: min(starts)] + shell_text[end:]
    assert stale != shell_text, "control did not mutate Shell.tsx -- detector unproven"
    return stale


def test_detector_flags_a_strip_with_no_reveal_effect():
    """Negative control: the exact pre-repair shape must be reported.

    This is the state measured on ``main`` ``3cd81f76`` and on the canonical
    deployment: the strip exists, is scrollable, carries ``aria-current``, and
    nothing ever scrolls it.
    """
    stale = _strip_reveal_effect(SHELL)
    defects = _reveal_defects(stale)
    assert any("never revealed" in d for d in defects), defects
    # The live tree must NOT be reported, or the detector is trivially true.
    assert _reveal_defects(SHELL) == []


def test_detector_flags_a_route_only_reveal_that_ignores_resize():
    """Negative control: the first cut of this repair, which failed 4/4 on narrowing.

    A reveal keyed on ``[current]`` alone satisfies every other assertion in this
    file — the ref, the marker, the horizontal-only movement, the layout-box guard —
    and still leaves the active item off-screen after the viewport narrows. If this
    detector did not exist, that regression would ship unnoticed.
    """
    stale = SHELL.replace("useCallback", "_unusedCallback")
    assert stale != SHELL, "control did not mutate Shell.tsx -- detector unproven"
    defects = _reveal_defects(stale)
    assert any("box changes" in d or "shared callback" in d for d in defects), defects


def test_detector_flags_an_unbound_strip():
    """Negative control: without a ref there is nothing to scroll."""
    stale = re.sub(r"ref=\{mobileNavRef\}\n", "", SHELL, count=1)
    assert stale != SHELL, "control did not mutate Shell.tsx -- detector unproven"
    assert any("not bound to a ref" in d for d in _reveal_defects(stale)), _reveal_defects(stale)


def test_detector_flags_a_reveal_that_does_not_follow_the_route():
    """Negative control: a reveal keyed on ``[]`` runs once and never again."""
    stale = SHELL.replace("  }, [current, revealActiveItem]);", "  }, []);")
    assert stale != SHELL, "control did not mutate Shell.tsx -- detector unproven"
    assert any("never revealed" in d for d in _reveal_defects(stale)), _reveal_defects(stale)


def test_detector_flags_a_vertical_scrolling_reveal():
    """Negative control: ``scrollIntoView`` couples navigation to page scroll."""
    ref_name = _strip_ref_name(SHELL)
    assert ref_name is not None
    stale = SHELL.replace(
        "      nav.scrollLeft += box.right - (navBox.right - pad);",
        "      active.scrollIntoView({ inline: \"nearest\", block: \"nearest\" });",
    )
    assert stale != SHELL, "control did not mutate Shell.tsx -- detector unproven"
    assert any("scrollIntoView" in d for d in _reveal_defects(stale)), _reveal_defects(stale)


def test_detector_flags_a_reveal_without_a_layout_box_guard():
    """Negative control: without the guard the reveal runs on desktop with zeroed rects."""
    stale = SHELL.replace("if (!nav || nav.clientWidth === 0) return;", "if (!nav) return;")
    assert stale != SHELL, "control did not mutate Shell.tsx -- detector unproven"
    assert any("layout box" in d for d in _reveal_defects(stale)), _reveal_defects(stale)


def test_detector_is_silent_on_a_correctly_repaired_strip():
    """Positive control: the repaired shape must not be reported."""
    assert _reveal_defects(SHELL) == []
    assert _strip_ref_name(SHELL) == "mobileNavRef"
