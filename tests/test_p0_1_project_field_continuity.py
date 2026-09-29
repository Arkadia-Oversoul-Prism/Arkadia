"""P0.1 Project Field Continuity — selectSection keeps project for mapped lenses."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "web/public_prism/src/components/solspire/SolSpireExperience.tsx"


def test_project_lens_map_exists():
    src = EXP.read_text()
    assert "PROJECT_LENS_TO_TAB" in src
    for lens in ("files", "tasks", "conversations", "memory", "knowledge", "weaver", "observatory"):
        assert f"{lens}:" in src or f"'{lens}'" in src


def test_select_section_preserves_project_for_mapped_lenses():
    src = EXP.read_text()
    assert "P0.1 Project Field Continuity" in src or "field continuity" in src.lower() or "PROJECT_LENS_TO_TAB" in src
    # Must not always null project
    assert "if(project && next in PROJECT_LENS_TO_TAB)" in src or "if (project && next in PROJECT_LENS_TO_TAB)" in src
    assert "setProject(null)" in src  # still clears for non-mapped


def test_dashboard_remounts_on_tab_change():
    src = EXP.read_text()
    assert "key={`${project.id}:${projectTab}`}" in src or 'key={`${project.id}:${projectTab}`}' in src


def test_non_project_lenses_still_clear():
    """projects / commercial / settings leave project context via fall-through."""
    src = EXP.read_text()
    # fall-through path still clears
    assert "setProject(null)" in src
    assert "setProjectTab('overview')" in src


def test_field_continuity_marker():
    src = EXP.read_text()
    assert 'data-field-continuity="p0.1"' in src
