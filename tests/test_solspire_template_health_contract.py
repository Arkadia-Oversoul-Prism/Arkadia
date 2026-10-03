from __future__ import annotations

from solspire.project_templates import instantiate_project_metadata, list_project_templates


def test_templates_declare_live_verification_without_claiming_capability():
    templates = list_project_templates()
    assert templates
    metadata = instantiate_project_metadata(templates[0]["id"], {})
    verification = metadata["project_runtime"]["verification"]
    assert verification["contract"] == "solspire.integration-health.v1"
    assert verification["endpoint"] == "/solspire/projects/{project_id}/integration-health"
    assert verification["template_configuration_is_not_live_proof"] is True


def test_template_creation_returns_real_integration_health_result():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    source = (root / "solspire/console_router.py").read_text(encoding="utf-8")
    health = (root / "solspire/integration_health.py").read_text(encoding="utf-8")
    assert 'health = project_integration_health(subject_uid=user["uid"], project=p.to_dict())' in source
    assert '"integration_health": health' in source
    assert '"contract": "solspire.integration-health.v1"' in health
    assert '"all_required_available"' in health
    assert '"UNBOUND"' in health and '"UNAVAILABLE"' in health
