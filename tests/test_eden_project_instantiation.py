"""Contract tests for sovereign Eden instantiation."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_eden_instantiation_is_authenticated_and_owner_bound():
    source = (ROOT / "solspire/console_router.py").read_text()
    assert '@router.post("/projects/instantiate-eden")' in source
    assert "Depends(require_auth)" in source
    assert 'owner_uid=user["uid"]' in source
    assert 'p.name.strip().lower() == "eden food systems"' in source


def test_eden_seed_populates_canonical_project_substrate_not_a_second_store():
    source = (ROOT / "solspire/eden_seed.py").read_text()
    assert "create_file(project_id" in source
    assert "add_memory(project_id" in source
    assert "create_task(project_id" in source
    assert "SOLSPIRE_PROJECTS_DB" not in source


def test_eden_runtime_is_generic_weaver_and_arkana():
    source = (ROOT / "solspire/console_router.py").read_text()
    assert '"generic project-level runtime"' in source
    assert '"generic project-scoped conversational interface"' in source
    assert '"living_larder projection; live capability remains separately verified"' in source


def test_arkana_reads_canonical_project_runtime_context():
    source = (ROOT / "web/public_prism/src/components/solspire/SolSpireExperience.tsx").read_text()
    assert "/solspire/projects/" + "${pack.projectId}" + "/runtime-context" in source