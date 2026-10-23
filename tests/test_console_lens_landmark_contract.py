"""The shared lens strip must be a labelled navigation landmark (Slice A).

`SurfaceLenses` is the one sub-view switcher every lens-bearing surface renders
(`NovaNetPage`, `SolariunPage`). It rendered as an anonymous `<div>` of buttons:
a screen-reader user reaching it heard a run of unlabelled controls with no
statement of what region they were in or what the strip switches. The archived
Prism rendered the same rail as a labelled landmark
(`PrismInteriorShell.tsx`: `<nav aria-label="NovaNet primary navigation">`), so
the accessible region is a recovered capability, not an invention.

The fix is deliberately narrow: the strip becomes `<nav aria-label=...>`, and the
label is *derived* from the surface registry (`SURFACE_BY_ID[surface].name`)
rather than hardcoded, so the one route/surface declaration stays the single
source of that vocabulary — a second hardcoded name list is the duplicate-model
class directive §5.1 forbids.

This guard is disjoint from `tests/test_console_shell_nav_contract.py`, which
pins the *shell's* skip link and focus hand-off and the lens strip's
navigability/decorative-control rule. It does not assert the strip's landmark or
accessible name; that is this file's subject.

Each detector carries a negative control proven on the live file, so a detector
that always passes is itself caught.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "web" / "arkadia_console" / "src"
LENSES_PATH = SRC / "components" / "SurfaceLenses.tsx"
SURFACES_PATH = SRC / "lib" / "surfaces.ts"

LENSES = LENSES_PATH.read_text(encoding="utf-8")
SURFACES = SURFACES_PATH.read_text(encoding="utf-8")

# The container testid is a template literal: `data-testid={`${surface}-lenses`}`.
CONTAINER_TESTID = re.compile(r"data-testid=\{`\$\{surface\}-lenses`\}")


def _opening_tag_at(src: str, start: int) -> tuple[str, str] | None:
    """The (tag_name, full_text) of the JSX opening tag beginning at ``start``.

    Reads to the matching ``>`` while skipping over ``{...}`` expressions so an
    inline ``=>`` handler or a ``${...}`` template does not terminate the tag.
    """
    m = re.match(r"<([A-Za-z][\w.]*)", src[start:])
    if not m:
        return None
    tag_name = m.group(1)
    i = start + m.end()
    depth = 0
    while i < len(src):
        c = src[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == ">" and depth == 0:
            return tag_name, src[start : i + 1]
        i += 1
    return None


def _lens_strip_tag(src: str) -> tuple[str, str] | None:
    """The opening tag of the element carrying the lens-strip container testid."""
    m = CONTAINER_TESTID.search(src)
    if not m:
        return None
    start = src.rfind("<", 0, m.start())
    if start == -1:
        return None
    return _opening_tag_at(src, start)


def _landmark_defects(src: str) -> list[str]:
    """Reasons the lens strip is not a labelled navigation landmark. Empty == sound.

    Three parts fail independently: the element must exist, it must be a
    ``<nav>`` (a region a screen-reader user can jump to), and it must carry an
    accessible name so the region is announced as something specific.
    """
    tag = _lens_strip_tag(src)
    if tag is None:
        return ["no lens strip carrying the container testid"]
    tag_name, tag_text = tag
    defects = []
    if tag_name != "nav":
        defects.append(f"lens strip is <{tag_name}>, not a <nav> landmark")
    if "aria-label" not in tag_text:
        defects.append("lens strip has no accessible name (aria-label)")
    return defects


def _label_is_registry_derived(src: str) -> bool:
    """True when the accessible name is derived from the surface registry.

    A hardcoded label would be a second surface-name list — the duplicate-model
    class directive §5.1 forbids. The name must come from `SURFACE_BY_ID`.
    """
    tag = _lens_strip_tag(src)
    if tag is None:
        return False
    _, tag_text = tag
    return "SURFACE_BY_ID[surface].name" in tag_text


# ---------------------------------------------------------------------------
# The invariant
# ---------------------------------------------------------------------------


def test_lens_strip_is_a_labelled_navigation_landmark():
    assert _landmark_defects(LENSES) == [], _landmark_defects(LENSES)


def test_lens_strip_name_is_derived_from_the_surface_registry():
    assert _label_is_registry_derived(LENSES), (
        "the lens strip's accessible name must derive from SURFACE_BY_ID, not a "
        "hardcoded surface-name list"
    )
    assert "SURFACE_BY_ID" in LENSES, "SurfaceLenses must import the surface registry"


def test_every_lens_bearing_surface_gets_a_distinct_accessible_name():
    """The label is `SURFACE_BY_ID[surface].name`, so the two lens surfaces the
    console renders today (NovaNet, Solariun) announce distinct regions. A label
    that did not vary with `surface` would make the landmark useless."""
    names = re.findall(r'name: "([^"]+)"', SURFACES)
    assert "NovaNet" in names and "Solariun" in names, names
    assert "SURFACE_BY_ID[surface].name" in LENSES


# ---------------------------------------------------------------------------
# Detector controls — proven on the live file, not only on synthetic strings
# ---------------------------------------------------------------------------


def test_detector_flags_the_pre_repair_anonymous_div():
    """Negative control: the exact pre-repair shape — the strip as an anonymous
    `<div>` — must be reported."""
    stale = LENSES.replace("<nav\n", "<div\n", 1).replace("</nav>", "</div>")
    assert stale != LENSES, "control did not mutate SurfaceLenses.tsx -- detector unproven"
    defects = _landmark_defects(stale)
    assert any("not a <nav>" in d for d in defects), defects


def test_detector_flags_a_nav_with_no_accessible_name():
    """Negative control: a `<nav>` without a name is a landmark a screen reader
    announces as an unlabelled "navigation" region."""
    stripped = LENSES.replace('      aria-label={`${SURFACE_BY_ID[surface].name} views`}\n', "")
    assert stripped != LENSES, "control did not remove the aria-label -- detector unproven"
    defects = _landmark_defects(stripped)
    assert any("no accessible name" in d for d in defects), defects


def test_detector_flags_a_hardcoded_surface_name():
    """Negative control: a literal name instead of the registry lookup is a second
    surface-name list and must not be accepted as registry-derived."""
    hardcoded = LENSES.replace("${SURFACE_BY_ID[surface].name} views", "NovaNet views")
    assert hardcoded != LENSES, "control did not hardcode the name -- detector unproven"
    assert not _label_is_registry_derived(hardcoded)


def test_detector_reads_the_whole_tag_when_the_label_is_a_template():
    """The label is a template literal carrying `${...}`; a naive ``<[^>]*>`` match
    would stop early. The scanner must read the whole opening tag."""
    tag = _lens_strip_tag(LENSES)
    assert tag is not None, tag
    tag_name, tag_text = tag
    assert tag_name == "nav"
    assert "aria-label" in tag_text and "SURFACE_BY_ID[surface].name" in tag_text
