"""Document title per surface — PRR-07 (Lane F accessibility).

The canonical console rendered every route under one static `<title>ARKADIA</title>`,
so a screen-reader user navigating between surfaces heard no title change
(WCAG 2.4.2). The shell is the single owner of "which surface is current", so
it is where the title is derived — from the one surface table, not a second
list.

Domain: the Arkadia Console (`web/arkadia_console`), the primary application.
No route, auth, or backend contract changes; this is announcement metadata only.

What is asserted:

  * exactly one module writes `document.title`, and it is the shell;
  * the write happens in an effect keyed on the current surface, so navigation
    re-announces;
  * the value is derived from `SURFACE_BY_ID` (the one surface table) with the
    fixed product suffix, not a page-local map;
  * the shell still derives navigation only from `SURFACES` (this change must
    not introduce a second list).

Negative controls accompany the load-bearing detectors.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "web" / "arkadia_console" / "src"
SHELL_PATH = SRC / "components" / "Shell.tsx"

SHELL = SHELL_PATH.read_text(encoding="utf-8")


TITLE_WRITE_MARKER = "document.title"
SHELL_RELATIVE_PATH = "web/arkadia_console/src/components/Shell.tsx"


def _title_writers_in(sources: dict[str, str]) -> list[str]:
    """Modules that write ``document.title``, as sorted repo-relative paths.

    Takes its domain as an argument so a control can feed it a defective tree.
    A detector that reads the live tree directly shares no symbol with a
    control, so neutering it to ``return [SHELL_RELATIVE_PATH]`` leaves the
    live assertion satisfied and nothing reddens.
    """
    return sorted(p for p, text in sources.items() if TITLE_WRITE_MARKER in text)


def _live_tsx_sources() -> dict[str, str]:
    return {
        str(p.relative_to(ROOT)): p.read_text(encoding="utf-8")
        for p in sorted(SRC.rglob("*.ts*"))
    }


def _title_writers() -> list[str]:
    return _title_writers_in(_live_tsx_sources())


def _title_effect(text: str) -> re.Match[str] | None:
    return re.search(
        r"useEffect\(\(\) => \{\s*document\.title = `\$?\{?SURFACE_BY_ID\[current\]\.name\}?\s*· ARKADIA`;\s*\}, \[current\]\)",
        text,
    )


def test_the_shell_is_the_only_module_that_writes_the_document_title():
    assert _title_writers() == [SHELL_RELATIVE_PATH], (
        f"document.title must have one owner (the shell); found {_title_writers()}"
    )


def test_the_title_is_set_in_an_effect_keyed_on_the_current_surface():
    match = _title_effect(SHELL)
    assert match, (
        "the title must be written in an effect keyed on [current] — otherwise "
        "navigation is not re-announced"
    )


def test_the_title_is_derived_from_the_surface_table_not_a_second_list():
    assert "SURFACE_BY_ID[current].name" in SHELL
    assert "· ARKADIA" in SHELL


def test_the_shell_still_derives_navigation_only_from_the_surface_table():
    # This change must not smuggle a second list into the shell.
    assert "NAV_SURFACES = SURFACES.filter" in SHELL


def test_negative_control_detects_a_hardcoded_title_map():
    synthetic = "const TITLES = { home: 'Home · ARKADIA', weaver: 'Weaver · ARKADIA' };\ndocument.title = TITLES[current];"
    assert "SURFACE_BY_ID[current].name" not in synthetic
    assert _title_effect(synthetic) is None, "a page-local title map must be flagged"


def test_negative_control_detects_an_unkeyed_write():
    synthetic = "useEffect(() => { document.title = `${SURFACE_BY_ID[current].name} · ARKADIA`; }, []);"
    assert _title_effect(synthetic) is None, "an effect not keyed on [current] must be flagged"
    assert _title_effect(SHELL)


def test_negative_control_the_title_writer_sweep_is_bound_to_its_detector():
    """The sweep must be able to fail for an edit to the detector it depends on.

    Both polarities: a defective tree (a second writer) is reported, and the
    shipped tree is not. A detector neutered to report nothing fails the first;
    one that reports unconditionally fails the second.
    """
    defective = {
        SHELL_RELATIVE_PATH: "document.title = 'ARKADIA';",
        "web/arkadia_console/src/pages/WeaverPage.tsx": "document.title = 'Weaver';",
    }
    assert _title_writers_in(defective) == [
        SHELL_RELATIVE_PATH,
        "web/arkadia_console/src/pages/WeaverPage.tsx",
    ], "a second module writing document.title must be reported"
    assert _title_writers_in(_live_tsx_sources()) == [SHELL_RELATIVE_PATH], (
        "the shipped tree must have exactly one title writer"
    )
