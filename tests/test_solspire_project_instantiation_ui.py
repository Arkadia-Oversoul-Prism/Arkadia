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
