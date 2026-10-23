"""The shared ``Facts`` value column must survive a long unbroken token.

``Facts`` (``web/arkadia_console/src/components/ui.tsx``) is the one primitive
every surface uses to present contract readings, and its ``<dd>`` holds arbitrary
backend text: a 40-char revision SHA, an ``EVD-…`` evidence id, a session id, an
``authorization_ref``, or the raw ``JSON.stringify`` output that
``scalarOverview`` emits for an object-valued overview key
(``components/lab/labOperational.ts``). Twenty modules consume it.

The grid is ``grid-cols-[minmax(0,10rem)_1fr]``. The label track is capped, but a
bare ``1fr`` track still refuses to shrink below its content's intrinsic minimum
width, and ``dd`` had neither ``min-w-0`` nor ``break-words``. Measured in
Chromium 390x844 against the canonical deployment
``https://arkadia-qzu4.onrender.com`` (revision ``3cd81f76``, current ``main``):
substituting a 164-char unbroken value into the live ``dd`` took the *document*
from 0 to **405px** of horizontal overflow — the page, not just the cell. A
controlled A/B on that same live element, changing only the two classes, returned
0px.

This is a **latent** defect, stated precisely: the real values rendered at
measurement time were short (``arkadia``, ``one_reconciled_deployment``, the
revision SHA), so no live page overflowed. It is reachable because the value is
backend-controlled — a Lab overview key whose value is an object is stringified
verbatim, and a long objective or id needs no frontend change to appear. It is
therefore recorded as a latent defect with a proven trigger, not as an observed
live overflow.

The repair is confined to the one shared element: ``min-w-0 break-words`` on the
``dd``. ``min-w-0`` lets the track shrink below the token's intrinsic width and
``break-words`` (``overflow-wrap: break-word``) wraps it. Neither changes the
rendering of a value that already fits, so all twenty consumers are affected only
in the case that was broken.

Domain: the Arkadia Console (``web/arkadia_console``). Disjoint from
``test_console_shell_nav_contract.py`` (navigation/shell/design tokens: it pins
that no *page-local* hex literal bypasses the palette, which is a different
property from whether a shared primitive can overflow) and
``test_console_focus_ring_contract.py`` (the shared focus ring).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI_PATH = ROOT / "web" / "arkadia_console" / "src" / "components" / "ui.tsx"
UI = UI_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Detectors (module level, so the negative controls exercise the same code the
# live assertions use).
# ---------------------------------------------------------------------------


def _facts_body(ui_text: str) -> str | None:
    """The body of the ``Facts`` component, or None."""
    m = re.search(r"export function Facts\([^)]*\)\s*\{", ui_text)
    if not m:
        return None
    depth, i = 0, m.end() - 1
    while i < len(ui_text):
        if ui_text[i] == "{":
            depth += 1
        elif ui_text[i] == "}":
            depth -= 1
            if depth == 0:
                return ui_text[m.end() - 1 : i + 1]
        i += 1
    return None


def _facts_dd_tag(ui_text: str) -> str | None:
    """The ``<dd>`` opening tag of the ``Facts`` value column, or None."""
    body = _facts_body(ui_text)
    if body is None:
        return None
    m = re.search(r"<dd\b[^>]*>", body)
    return m.group(0) if m else None


def _facts_grid(ui_text: str) -> str | None:
    """The ``<dl>`` className of ``Facts``, or None."""
    body = _facts_body(ui_text)
    if body is None:
        return None
    m = re.search(r"<dl className=\"([^\"]+)\"", body)
    return m.group(1) if m else None


def _unwrappable_value_column_defects(ui_text: str) -> list[str]:
    """Reasons the ``Facts`` value column cannot wrap a long unbroken token.

    Two independent requirements, because either alone is insufficient:
    ``min-w-0`` lets the grid track shrink below the token's intrinsic minimum,
    and a break rule actually wraps the token once the track is narrow.
    """
    defects = []
    tag = _facts_dd_tag(ui_text)
    if tag is None:
        return ["Facts has no <dd> value column"]
    if "min-w-0" not in tag:
        defects.append(
            "the Facts value column has no min-w-0, so its grid track cannot shrink "
            "below the intrinsic width of a long unbroken token"
        )
    if not re.search(r"\bbreak-(words|all)\b", tag):
        defects.append(
            "the Facts value column has no break-words, so a token wider than the "
            "track overflows instead of wrapping"
        )
    # `whitespace-nowrap` (and `whitespace-pre`) suppress wrapping outright, so the
    # column can carry `break-words` and still overflow. Measured: adding
    # `whitespace-nowrap` after `break-words` left the earlier detector reporting no
    # defect at all, so the guard would have stayed green through a real regression.
    if re.search(r"\bwhitespace-(nowrap|pre)\b", tag):
        defects.append(
            "the Facts value column sets whitespace-nowrap/pre, which suppresses the "
            "wrapping break-words is there to provide"
        )
    return defects


# ---------------------------------------------------------------------------
# The value column wraps
# ---------------------------------------------------------------------------


def test_facts_value_column_can_wrap_a_long_unbroken_token():
    """The load-bearing assertion: a long token must not overflow the document."""
    assert _unwrappable_value_column_defects(UI) == [], _unwrappable_value_column_defects(UI)


def test_facts_grid_keeps_its_capped_label_track():
    """The repair must not change the label column: only the value track moves.

    A repair that removed the ``minmax(0,10rem)`` cap would fix the value column
    by letting the label column grow instead, changing the layout of every
    ``Facts`` reading.
    """
    grid = _facts_grid(UI)
    assert grid is not None, "Facts declares no <dl> grid"
    assert "minmax(0,10rem)" in grid, grid


def test_facts_is_still_the_single_shared_reading_primitive():
    """One primitive, not a per-surface fork: the guard pins the shared element."""
    assert UI_PATH.exists()
    assert re.search(r"export function Facts\(", UI), "Facts must remain an exported primitive"
    # The overflow defect belongs to the shared component; a page-local re-implementation
    # would be the duplicate-abstraction this repository forbids.
    assert UI.count("export function Facts(") == 1


# ---------------------------------------------------------------------------
# Negative controls — each detector must flag the defect it claims to detect.
# ---------------------------------------------------------------------------


def test_detector_flags_the_pre_repair_value_column():
    """Negative control: the exact pre-repair shape must be reported.

    This is the state measured on ``main`` ``3cd81f76`` and on the canonical
    deployment, where the 405px document overflow was reproduced.
    """
    stale = UI.replace('<dd className="min-w-0 break-words text-white/85">',
                       '<dd className="text-white/85">')
    assert stale != UI, "control did not mutate ui.tsx -- detector unproven"
    defects = _unwrappable_value_column_defects(stale)
    assert any("min-w-0" in d for d in defects), defects
    assert any("break-words" in d for d in defects), defects
    # The live tree must NOT be reported, or the detector is trivially true.
    assert _unwrappable_value_column_defects(UI) == []


def test_detector_flags_a_shrinkable_but_unwrappable_column():
    """Negative control: ``min-w-0`` alone leaves the token unwrappable.

    The two halves fail independently — this proves the break rule is load-bearing
    rather than assumed to follow from the shrink fix.
    """
    stale = UI.replace('<dd className="min-w-0 break-words text-white/85">',
                       '<dd className="min-w-0 text-white/85">')
    assert stale != UI, "control did not mutate ui.tsx -- detector unproven"
    defects = _unwrappable_value_column_defects(stale)
    assert any("break-words" in d for d in defects), defects
    assert not any("min-w-0" in d for d in defects), defects


def test_detector_flags_a_wrappable_but_unshrinkable_column():
    """Negative control: ``break-words`` alone cannot help a track that will not shrink."""
    stale = UI.replace('<dd className="min-w-0 break-words text-white/85">',
                       '<dd className="break-words text-white/85">')
    assert stale != UI, "control did not mutate ui.tsx -- detector unproven"
    defects = _unwrappable_value_column_defects(stale)
    assert any("min-w-0" in d for d in defects), defects
    assert not any("break-words" in d for d in defects), defects


def test_detector_flags_a_missing_value_column():
    """Negative control: a detector that cannot see the element must not pass it."""
    stale = re.sub(r"<dd\b[^>]*>\{row\.value\}</dd>", "<span>{row.value}</span>", UI)
    assert stale != UI, "control did not mutate ui.tsx -- detector unproven"
    assert _unwrappable_value_column_defects(stale) == ["Facts has no <dd> value column"]


def test_detector_flags_a_repaired_value_column_that_moved_the_label_cap():
    """Negative control: fixing the value track by uncapping the label track is not the repair."""
    stale = UI.replace("minmax(0,10rem)", "auto")
    assert stale != UI, "control did not mutate ui.tsx -- detector unproven"
    assert _facts_grid(stale) is not None
    assert "minmax(0,10rem)" not in _facts_grid(stale)


def test_detector_flags_a_column_whose_wrapping_is_suppressed():
    """Negative control: ``whitespace-nowrap`` defeats ``break-words``.

    The column then carries both classes and still overflows, so a guard that only
    looked for ``break-words`` reported no defect. Measured: this variant returned an
    empty defect list before the clause was added, while its own negative control
    still failed -- for the unrelated reason that the anchor string had moved. A
    control that fails for the wrong reason is indistinguishable from a catch.
    """
    stale = UI.replace(
        '<dd className="min-w-0 break-words text-white/85">',
        '<dd className="min-w-0 break-words whitespace-nowrap text-white/85">',
    )
    assert stale != UI, "control did not mutate ui.tsx -- detector unproven"
    defects = _unwrappable_value_column_defects(stale)
    # Exactly one defect, and it is the suppression -- `min-w-0` and `break-words`
    # are both still present, which is the point of the variant. Matching on the
    # distinctive clause ("sets whitespace-") rather than the substring
    # "break-words", which also appears inside the suppression message itself.
    assert len(defects) == 1, defects
    assert "sets whitespace-nowrap" in defects[0], defects


def test_negative_controls_anchor_on_the_live_source():
    """A control whose anchor is absent must not be mistaken for a catch.

    ``str.replace`` on a missing anchor returns the input unchanged, and the
    following ``assert any(...)`` then fails for the wrong reason. Asserting the
    anchor is present keeps a moved literal from reading as a detector hit.
    """
    anchors = [
        '<dd className="min-w-0 break-words text-white/85">',
        "minmax(0,10rem)",
        "export function Facts(",
    ]
    for a in anchors:
        assert a in UI, f"negative-control anchor has moved: {a!r}"
