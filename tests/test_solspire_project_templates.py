"""Project templates configure the canonical project model without new stores."""
import pytest

from solspire.project_templates import (
    instantiate_project_metadata,
    list_project_templates,
    resolve_project_template,
)


def test_enterprise_is_the_default_template():
    profile = resolve_project_template(None)
    metadata = instantiate_project_metadata(None, {"purpose": "research"})

    assert profile["id"] == "enterprise"
    assert metadata["purpose"] == "research"
    assert metadata["project_runtime"]["template_id"] == "enterprise"
    assert metadata["project_runtime"]["runtime"]["operational_engine"]["name"] == "weaver"
    assert metadata["project_runtime"]["runtime"]["conversation_interface"]["name"] == "arkana"


def test_eden_template_declares_living_larder_without_claiming_it_is_live():
    metadata = instantiate_project_metadata("eden-food-systems", {})
    runtime = metadata["project_runtime"]

    assert runtime["template_id"] == "eden-food-systems"
    assert "living_larder" in runtime["requested_capabilities"]
    assert runtime["domain"]["module"] == "living_larder"
    assert runtime["domain"]["state"] == "requires_live_capability_verification"
    assert runtime["runtime"]["sandbox"]["state"] == "read_only_snapshot_v0_1"


def test_template_catalog_returns_independent_copies():
    first = list_project_templates()
    first[0]["capability_targets"].append("unapproved-capability")

    assert "unapproved-capability" not in resolve_project_template("enterprise")["capability_targets"]


def test_unknown_template_is_rejected():
    with pytest.raises(ValueError, match="Unknown project template"):
        instantiate_project_metadata("made-up-template", {})


def test_clients_cannot_override_system_runtime_contract():
    with pytest.raises(ValueError, match="system-managed"):
        instantiate_project_metadata("enterprise", {"project_runtime": {"human_authorization_required": False}})
