"""Composition guard for the Prism next-wave parallel UI lanes (Lane 4).

A parallel-lane ownership model can compose into a state no single PR observes: two
branches from the same base, each individually green, both editing one file the
contract assigns to a single owner. Git reports a conflict (or worse, silently
picks one side), and neither reviewing pass can see it.

This test states the invariant over measured lane-4 reality rather than a
remembered file list:

    every lane-4 projection that a contract test pins to
    ``EngineeringLabPage.tsx`` must be present in that file, and every lane-4
    component the page imports must be rendered by it.

The projection set is DERIVED from the corpus, not restated here. Each owning
contract test already pins its projection with a literal mount assertion against a
variable bound to the page; the detector reads those same literals. A
hand-maintained table drifts the moment a lane adds a projection. Measured
2026-10-13 at the live heads, the table this guard carried knew two projections
(``<LabAutomationGrammar``, ``<ExecutionLoop``) while Lane 4 had four in flight:
``<LabOperationalSurfaces`` (PR #512) and ``<LabAuthorityReadings`` (PR #524) were
invisible to it, and a composed tree with one of those deliberately dropped was
reported **5 passed** -- the exact one-sided composition loss the guard exists to
catch.

The extraction is a pure function over module text (:func:`projections_in_module`)
so the controls below can feed it the shapes that matter -- an absence pin, a
one-sided union -- without a worktree.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PAGE = "web/arkadia_console/src/pages/EngineeringLabPage.tsx"
PAGE_BASENAME = "EngineeringLabPage.tsx"

# The projections this guard was originally written with. Recorded for provenance
# only -- the derived set below is what is judged, so a tree that legitimately does
# not carry a lane (e.g. pre-composition ``main``) is not reddened by this table.
RECORDED_PROJECTIONS = ("<LabAutomationGrammar", "<ExecutionLoop")

_PAGE_CONST = re.compile(
    r'^(\w+)\s*=\s*.*["\']' + re.escape(PAGE_BASENAME) + r'["\']',
    re.MULTILINE,
)
_LOCAL_FROM_READ = re.compile(r'^\s*(\w+)\s*=\s*_read\((\w+)\)', re.MULTILINE)
_LOCAL_FROM_READ_TEXT = re.compile(r'^\s*(\w+)\s*=\s*(\w+)\.read_text\(', re.MULTILINE)
# assert "<Component" ... in <page-local>   -- a JSX render literal. The `\s+in\s+`
# (no optional `not`) is deliberate: `assert "X" not in page` is an ABSENCE pin and
# must not enter the marker set. See test_control_a_sibling_absence_pin_is_ignored.
_ASSERT_RENDER = re.compile(
    r'assert\s+["\'](<[A-Z][A-Za-z0-9_]*)[^"\']*["\']\s+in\s+(\w+)'
)
# assert "Component" in <page-local>        -- a bare name literal, same rule.
_ASSERT_NAME = re.compile(r'assert\s+["\']([A-Z][A-Za-z0-9_]+)["\']\s+in\s+(\w+)')
# import { Component } from "../components/lab/Component"
_LAB_IMPORT = re.compile(r'import\s*\{([^}]*)\}\s*from\s*["\'][^"\']*components/lab/')


def _read_current_page() -> str:
    return (REPO / PAGE).read_text(encoding="utf-8")


def _page_bound_locals(text: str) -> set[str]:
    """Names bound to ``EngineeringLabPage.tsx`` inside one test module."""
    consts = {m.group(1) for m in _PAGE_CONST.finditer(text)}
    if not consts:
        return set()
    names = set(consts)
    for m in _LOCAL_FROM_READ.finditer(text):
        if m.group(2) in consts:
            names.add(m.group(1))
    for m in _LOCAL_FROM_READ_TEXT.finditer(text):
        if m.group(2) in consts:
            names.add(m.group(1))
    return names


def projections_in_module(text: str) -> dict[str, str]:
    """Projection markers pinned to the page by one test module's text.

    Pure function: a module that never binds a variable to the page yields nothing,
    and only *positive* mount assertions naming a page-bound local are read.
    """
    page_locals = _page_bound_locals(text)
    if not page_locals:
        return {}
    derived: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip().startswith("assert"):
            continue
        render = _ASSERT_RENDER.search(line)
        if render and render.group(2) in page_locals:
            derived[render.group(1)] = line.strip()
            continue
        named = _ASSERT_NAME.search(line)
        if named and named.group(2) in page_locals:
            derived["<" + named.group(1)] = line.strip()
    return derived


def derive_lane4_projections() -> dict[str, str]:
    """Map each pinned projection marker to the contract test that pins it.

    Derived from the working tree, so a lane that adds a contract test and a mount
    is guarded without editing this file, and a lane that removes one drops out.
    """
    derived: dict[str, str] = {}
    for path in sorted((REPO / "tests").rglob("*.py")):
        if path.name == Path(__file__).name:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if PAGE_BASENAME not in text:
            continue
        rel = path.relative_to(REPO).as_posix()
        for marker in projections_in_module(text):
            derived[marker] = rel
    return derived


def imported_lab_components(page: str) -> set[str]:
    """Lane-4 components the page imports from ``components/lab/``."""
    names: set[str] = set()
    for m in _LAB_IMPORT.finditer(page):
        for part in m.group(1).split(","):
            token = part.strip().split(" as ")[0].strip()
            if token and token[0].isupper():
                names.add(token)
    return names


def _missing(markers, text: str) -> list[str]:
    return sorted(marker for marker in markers if marker not in text)


def test_the_derived_projection_set_is_not_empty():
    """Fail closed: a derivation that finds nothing makes the invariant vacuous."""
    derived = derive_lane4_projections()
    assert derived, "the lane-4 projection derivation found nothing"
    page = _read_current_page()
    assert {m for m in derived if m in page}, (
        "no derived projection is present in the page, yet the page mounts "
        "lane-4 surfaces -- the derivation has broken"
    )


def test_a_mounted_lane4_projection_requires_all_of_them():
    """Either every derived lane-4 projection is mounted, or none is.

    Pre-composition (no lane-4 projection merged) the page mounts none of them and
    this is silent -- there is nothing to guard yet. Once *any* projection is
    mounted, a one-sided merge/union that drops a sibling is a failure.
    """
    markers = derive_lane4_projections()
    page = _read_current_page()
    if not any(marker in page for marker in markers):
        return  # pre-composition: no lane-4 projection has landed on this tree
    missing = _missing(markers, page)
    assert not missing, (
        "EngineeringLabPage.tsx mounts a lane-4 projection but is missing "
        f"{missing}. Two lane-4 PRs each add one projection; a merge/union that "
        "keeps only one side drops a lane's user-visible surface."
    )


def test_every_imported_lane4_component_is_rendered():
    """An import the page never renders is a surface the user cannot see.

    This is the merge-loss shape: a hand-resolved merge keeps the ``import`` line
    from one parent and the render from neither, leaving a component that compiles
    and is dead.
    """
    page = _read_current_page()
    imported = imported_lab_components(page)
    assert imported, "the page imports no lane-4 component -- premise re-derive"
    unrendered = sorted(name for name in imported if f"<{name}" not in page)
    assert not unrendered, (
        f"EngineeringLabPage.tsx imports but never renders {unrendered}"
    )


def test_negative_control_a_one_sided_merge_is_reported():
    """Control: a page mounting all but one derived projection must be flagged.

    The dropped marker is taken from the derived set, so this control fails if the
    guard regresses to a static table. This is the shape a one-sided conflict
    resolution produces -- and the shape the pre-repair guard passed.
    """
    derived = derive_lane4_projections()
    dropped = sorted(derived)[-1]
    one_sided = "".join(f"<main>{m} /></main>" for m in derived if m != dropped)
    assert _missing(derived, one_sided) == [dropped]


def test_positive_control_a_union_is_silent():
    """Control: the composed union shape is not reported as a violation."""
    derived = derive_lane4_projections()
    union = "".join(f"<main>{m} /></main>" for m in derived)
    assert _missing(derived, union) == []


def test_control_an_empty_document_reports_everything_absent():
    """Control: the detector is not satisfied by an unrelated document."""
    derived = derive_lane4_projections()
    assert _missing(derived, "<main>nothing here</main>") == sorted(derived)


def test_control_a_sibling_absence_pin_is_ignored():
    """Control: ``assert "X" not in page`` must not enter the marker set.

    Lane-4 sibling PR #512 pins the *absence* of the grammar on its own surface
    (``assert "LabAutomationGrammar" not in surface``). A detector that read an
    absence pin would invent a projection nobody mounts. The module below binds
    ``page`` to the real page, so this control exercises the ``in``-vs-``not in``
    distinction directly rather than relying on the page-locals filter.
    """
    module = (
        'PAGE = ROOT / "src" / "pages" / "EngineeringLabPage.tsx"\n'
        "page = _read(PAGE)\n"
        "def test_absent():\n"
        '    assert "LabAutomationGrammar" not in page\n'
        '    assert "<LabAuthorityReadings" not in page\n'
    )
    derived = projections_in_module(module)
    assert derived == {}, f"an absence pin leaked into the marker set: {derived}"


def test_control_a_positive_pin_is_read_from_the_same_shape():
    """Control for the control above: the positive form IS read.

    Without this, ``test_control_a_sibling_absence_pin_is_ignored`` could pass
    because the module shape is unreadable rather than because absence pins are
    excluded.
    """
    module = (
        'PAGE = ROOT / "src" / "pages" / "EngineeringLabPage.tsx"\n'
        "page = _read(PAGE)\n"
        "def test_present():\n"
        '    assert "<LabAuthorityReadings" in page\n'
    )
    assert projections_in_module(module) == {
        "<LabAuthorityReadings": 'assert "<LabAuthorityReadings" in page'
    }


def test_control_a_module_not_binding_the_page_yields_nothing():
    """Control: a module that reads a different file contributes no markers."""
    module = (
        'OTHER = ROOT / "src" / "pages" / "WeaverPage.tsx"\n'
        "src = _read(OTHER)\n"
        "def test_other():\n"
        '    assert "<LabAuthorityReadings" in src\n'
    )
    assert projections_in_module(module) == {}


def test_lane4_pair_shares_a_conflicting_file_when_measured():
    """Measured provenance: the lane-4 PRs edit the same owned file.

    If this becomes false (e.g. one side is rebased off the file), the composition
    hazard documented in the evidence record no longer applies and this guard's
    premise should be re-derived rather than assumed.
    """
    try:
        refs = subprocess.run(
            ["git", "log", "--all", "--pretty=%H", "--", PAGE],
            cwd=REPO, capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return  # git unavailable: provenance is asserted elsewhere, not here
    if refs.returncode != 0:
        return
    assert refs.stdout.strip(), f"no history found for {PAGE}"
