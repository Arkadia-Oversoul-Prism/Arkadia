from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "web/public_prism/src/App.tsx"
FRAME = ROOT / "web/public_prism/src/components/ExperienceConsolidationFrame.tsx"
REPAIR_CSS = ROOT / "web/public_prism/src/components/experience-repair.css"
PROJECTS = ROOT / "web/public_prism/src/components/solspire/ProjectsWorkspace.tsx"


def test_outer_experience_frame_is_not_a_second_navigation_shell():
    src = FRAME.read_text()
    assert "experience-repair.css" in src
    assert "experience-surface-nav" not in src
    assert "SearchPanel" not in src
    assert "CONTEXT INSPECTOR" not in src


def test_app_keeps_spiral_command_as_distinct_route():
    src = APP.read_text()
    assert "'/sci': {view:'sci'}" in src
    assert 'surface="Spiral Command"' in src
    assert "<SpiralCommandInterface" in src


def test_repair_restores_single_desktop_spine_and_single_mobile_rail():
    css = REPAIR_CSS.read_text()
    assert ".solspire-sidebar" in css
    assert "width: 68px" in css
    assert "@media (max-width: 700px)" in css
    assert "bottom: 0 !important" in css
    assert ".solspire-prism-rail" in css
    assert "display: none !important" in css


def test_project_surface_has_real_api_backed_loading_and_creation():
    src = PROJECTS.read_text()
    assert "apiFetch('/solspire/projects'" in src
    assert "method: 'POST'" in src
    assert "setProjects(data.projects || [])" in src
    assert "onOpenProject(project)" in src


def test_repair_does_not_introduce_forbidden_substrate():
    for path in (FRAME, REPAIR_CSS):
        src = path.read_text().lower()
        assert "create table" not in src
        assert "graph database" not in src
        assert "intent object schema" not in src
        assert "autonomous merge" not in src
        assert "autonomous deploy" not in src
