"""PRISM Workstream 4 - lane-4 render integrity (orphaned projection guard).

A lane-4 component that is *defined* but never imported-and-rendered is a
capability that reached no surface. This is not a hypothetical: measured on
``main`` @ ``3ca8582a``, ``components/lab/ExecutionLoop.tsx`` exported the
canonical work-loop projection and ``grep -rn "ExecutionLoop"`` over
``web/arkadia_console/src`` returned the definition alone. The same defect class
appears in a subtler form after a hand-resolved merge, where the import line is
taken from one parent and the render from the other: a **dangling import** that
still counts as zero rendered surfaces (see ``AGENTS.md`` merge-loss forensics).

The invariant is derived from the corpus, not restated as a file list:

    every component exported by a lane-4 feature module
    (``src/components/lab``, ``src/components/weaver``) is imported by some
    other module **and** rendered there as JSX.

A hand-maintained table drifts the moment a lane adds a projection, and a guard
that only knew the components of its own wave would bless the next orphan. The
detector is a pure function over a ``{path: text}`` map so the controls below can
feed it the shapes that matter - a never-consumed component, and an
import-without-render - without a worktree.

Both are negative controls: a detector that cannot report the orphan it exists to
catch is decoration, and the pre-mount ``EngineeringLabPage`` is fed to it
verbatim so the control bites on the real defect rather than a synthetic one.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSOLE_SRC = ROOT / "web" / "arkadia_console" / "src"
PAGE = CONSOLE_SRC / "pages" / "EngineeringLabPage.tsx"
LOOP_COMPONENT = CONSOLE_SRC / "components" / "lab" / "ExecutionLoop.tsx"

#: The feature-local directories this lane owns. A projection in either must be
#: reachable; nothing outside them is judged (a page is a leaf, not a projection).
LANE_DIRS = ("components/lab", "components/weaver")

_EXPORT = re.compile(r"^export\s+function\s+([A-Z]\w*)\s*\(", re.MULTILINE)
_TS_SUFFIXES = (".ts", ".tsx")


def exported_components(text: str) -> list[str]:
    """PascalCase components a module exports as a function declaration."""
    return _EXPORT.findall(text)


def _imports(text: str, name: str) -> bool:
    """Whether *text* imports the named binding (named or aliased import)."""
    return bool(
        re.search(r"import\s*\{[^}]*\b" + re.escape(name) + r"\b", text)
        or re.search(r"\b" + re.escape(name) + r"\s*,\s*\{", text)
    )


def _renders(text: str, name: str) -> bool:
    """Whether *text* renders the binding as JSX."""
    return bool(re.search(r"<" + re.escape(name) + r"[\s/>]", text))


def orphaned_projections(sources: dict[str, str]) -> list[tuple[str, str]]:
    """``(path, component)`` for every lane-4 export no other module renders.

    A component counts as reached only when a *different* module both imports the
    binding and renders it. An import with no render is a dangling import and is
    reported - it is the merge-loss shape, not a mount.
    """
    orphans: list[tuple[str, str]] = []
    for path, text in sorted(sources.items()):
        if not path.endswith(_TS_SUFFIXES):
            continue
        if not any(part in path for part in LANE_DIRS):
            continue
        for name in exported_components(text):
            reached = any(
                other != path and _imports(other_text, name) and _renders(other_text, name)
                for other, other_text in sources.items()
            )
            if not reached:
                orphans.append((path, name))
    return orphans


def _console_sources() -> dict[str, str]:
    return {
        str(p.relative_to(ROOT)).replace("\\", "/"): p.read_text(encoding="utf-8")
        for p in CONSOLE_SRC.rglob("*")
        if p.is_file() and p.suffix in _TS_SUFFIXES
    }


# ---------------------------------------------------------------------------
# The invariant
# ---------------------------------------------------------------------------


def test_no_lane4_projection_is_orphaned():
    orphans = orphaned_projections(_console_sources())
    assert orphans == [], (
        "lane-4 components exported but never imported-and-rendered: "
        + ", ".join(f"{name} ({path})" for path, name in orphans)
    )


def test_the_canonical_loop_is_rendered_by_the_lab_page():
    """The specific capability this slice recovered stays mounted."""
    page = PAGE.read_text(encoding="utf-8")
    assert "ExecutionLoop" in page
    assert _imports(page, "ExecutionLoop")
    assert _renders(page, "ExecutionLoop")


def test_the_mount_reads_the_loop_from_the_declared_overview():
    """Stages come from the registry's overview read, not an invented list."""
    page = PAGE.read_text(encoding="utf-8")
    assert "endpoints.labEngineeringOverview" in page
    assert re.search(r"stages\s*=\s*\{[^}]*\b\w*[Ll]oop\w*\s*\(", page), (
        "the loop surface must be handed stages derived from the overview payload"
    )


# ---------------------------------------------------------------------------
# Negative controls - the detector must report the defect it exists to catch
# ---------------------------------------------------------------------------


def test_control_a_component_with_no_consumer_is_reported():
    sources = {
        "src/components/lab/Orphan.tsx": "export function Orphan() {\n  return null;\n}\n",
    }
    assert orphaned_projections(sources) == [("src/components/lab/Orphan.tsx", "Orphan")]


def test_control_an_import_without_a_render_is_still_orphaned():
    sources = {
        "src/components/lab/Orphan.tsx": "export function Orphan() {\n  return null;\n}\n",
        "src/pages/P.tsx": 'import { Orphan } from "../components/lab/Orphan";\n\nexport function P() {\n  return null;\n}\n',
    }
    assert orphaned_projections(sources) == [("src/components/lab/Orphan.tsx", "Orphan")]


def test_control_the_real_pre_mount_page_reports_the_canonical_loop():
    """Feed the detector the measured pre-mount page, not a synthetic stand-in.

    Before this slice the page carried no ``ExecutionLoop`` line at all and the
    detector reported the component; afterwards the same tree minus exactly the
    mount lines must report it again. Both directions are the real file, so the
    control cannot be satisfied by a fixture that does not resemble the defect.
    """
    key = str(PAGE.relative_to(ROOT)).replace("\\", "/")
    loop_key = str(LOOP_COMPONENT.relative_to(ROOT)).replace("\\", "/")
    sources = _console_sources()
    stripped = "\n".join(
        line for line in sources[key].splitlines() if "ExecutionLoop" not in line
    )
    sources[key] = stripped
    assert (loop_key, "ExecutionLoop") in orphaned_projections(sources)


def test_control_a_rendered_component_is_not_reported():
    sources = {
        "src/components/lab/Kept.tsx": "export function Kept() {\n  return null;\n}\n",
        "src/pages/P.tsx": 'import { Kept } from "../components/lab/Kept";\n\nexport function P() {\n  return <Kept />;\n}\n',
    }
    assert orphaned_projections(sources) == []
