"""UI and API contract checks for sovereign project instantiation."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_project_template_endpoint_is_part_of_canonical_solspire_router():
    source = (ROOT / "solspire/console_router.py").read_text()
    assert '@router.get("/project-templates")' in source
    assert "instantiate_project_metadata(body.template_id, body.metadata)" in source


def test_projects_ui_uses_server_owned_template_catalog():
    source = (ROOT / "web/public_prism/src/components/solspire/ProjectsWorkspace.tsx").read_text()
    assert "apiFetch('/solspire/project-templates'" in source
    assert 'aria-label="Project template"' in source
    assert "template_id: templateId" in source
    assert "runtime integration is verified separately" in source


def test_arkana_injects_bounded_project_context_and_scopes_threads():
    source = (ROOT / "web/public_prism/src/components/ArkanaCommune.tsx").read_text()
    overlay = (ROOT / "web/public_prism/src/components/solspire/SolSpireExperience.tsx").read_text()
    assert "projectContextId" in source
    assert "ACTIVE_THREAD_KEY}:project:" in source
    assert "[ARKADIA PROJECT CONTEXT SNAPSHOT" in source
    assert "unavailable_sources" in overlay
    assert "/solspire/projects/${pack.projectId}/tasks" in overlay
    assert "/solspire/projects/${pack.projectId}/memory" in overlay
    assert "Number(project.id)" not in overlay


def test_project_overview_surfaces_runtime_status_without_claiming_all_modules_are_live():
    source = (ROOT / "web/public_prism/src/pages/ProjectOverview.tsx").read_text()
    assert 'data-testid="solariun-project-runtime"' in source
    assert "Requested capabilities are targets" in source
    assert "runtimeBindings.sandbox?.state" in source
    assert "onTabChange('weaver')" in source

def test_project_canvas_uses_existing_lab_runtime_and_project_scope():
    dashboard = (ROOT / "web/public_prism/src/pages/ProjectDashboard.tsx").read_text()
    canvas = (ROOT / "web/public_prism/src/components/solspire/ProjectAgenticCanvas.tsx").read_text()
    routes = (ROOT / "api/lab_routes.py").read_text()
    store = (ROOT / "lab/engineering_lab/store.py").read_text()
    assert "'canvas'" in dashboard
    assert "project_ref: project.id" in canvas
    assert "Authorize read-only run" in canvas
    assert "write_allowed: false" in canvas
    assert "role: 'WEAVER'" in canvas
    assert "capabilities: ['READ', 'PROPOSE']" in canvas
    assert "def _project_canvas_policy" in routes
    assert "prepare_project_workspace(subject_uid, project_id)" in routes
    assert "project_ref TEXT" in store
    assert "SOLSPIRE_CANVAS_ROOT" in (ROOT / "solspire/project_canvas.py").read_text()
