"""M04 — one coherent project context; no parallel project model."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "web/public_prism/src/components/solspire/SolSpireExperience.tsx"
LIST = ROOT / "web/public_prism/src/components/solspire/ProjectsWorkspace.tsx"
SURF = ROOT / "web/public_prism/src/components/solspire/ProjectWorkspaceSurface.tsx"
DASH = ROOT / "web/public_prism/src/pages/ProjectDashboard.tsx"


def test_projects_lens_uses_projects_workspace():
    src = EXP.read_text()
    assert "ProjectsWorkspace" in src
    assert "onOpenProject" in src


def test_project_interior_is_project_dashboard():
    src = EXP.read_text()
    assert "ProjectDashboard" in src
    assert 'data-testid="solariun-project-context"' in src


def test_parallel_workspace_surface_delegates_to_dashboard():
    src = SURF.read_text()
    assert "ProjectDashboard" in src
    assert "function Knowledge" not in src
    assert "function Files" not in src


def test_projects_workspace_uses_solspire_api():
    src = LIST.read_text()
    assert "/solspire/projects" in src
    assert 'data-testid="solariun-projects-workspace"' in src


def test_no_second_project_store_in_frontend_list():
    src = LIST.read_text()
    assert "indexedDB" not in src.lower()
    assert "localStorage" not in src.lower()


def test_project_dashboard_is_canonical_interior():
    assert DASH.is_file()
    src = DASH.read_text()
    assert "export default function ProjectDashboard" in src
