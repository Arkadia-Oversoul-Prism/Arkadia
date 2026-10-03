"""Canonical project-instantiation profiles for SolSpire.

Templates configure a project on the existing SolSpire project model. They do
not create a second project store, grant authority, or claim that an integration
is live merely because it is named in a profile.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any


_TEMPLATE_VERSION = "1.0.0"
_SYSTEM_METADATA_KEY = "project_runtime"

_CAPABILITIES = [
    "files",
    "knowledge",
    "conversations",
    "tasks",
    "workflows",
    "events",
    "daily_pulse",
    "workevents",
    "decisions",
    "evidence",
    "weaver",
    "arkana",
]

_TEMPLATES: dict[str, dict[str, Any]] = {
    "enterprise": {
        "id": "enterprise",
        "name": "Enterprise Project",
        "description": "A reusable project workspace with governed work, knowledge, conversations, evidence and review.",
        "default_name": "",
        "version": _TEMPLATE_VERSION,
        "capability_targets": list(_CAPABILITIES),
        "domain_module": None,
        "domain_status": "not_configured",
    },
    "eden-food-systems": {
        "id": "eden-food-systems",
        "name": "Eden Food Systems",
        "description": "A real-business pilot for sourcing, buyer coordination, logistics, delivery and financial reconciliation.",
        "default_name": "Eden Food Systems",
        "version": _TEMPLATE_VERSION,
        "capability_targets": list(_CAPABILITIES) + ["living_larder"],
        "domain_module": "living_larder",
        "domain_status": "requires_live_capability_verification",
    },
}


def list_project_templates() -> list[dict[str, Any]]:
    """Return a copy of the supported project template catalog."""
    return [deepcopy(template) for template in _TEMPLATES.values()]


def resolve_project_template(template_id: str | None) -> dict[str, Any]:
    """Resolve a known template, defaulting new projects to enterprise."""
    key = (template_id or "enterprise").strip()
    template = _TEMPLATES.get(key)
    if template is None:
        raise ValueError(f"Unknown project template: {key}")
    return deepcopy(template)


def instantiate_project_metadata(
    template_id: str | None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Bind template configuration to the existing project's metadata field.

    The system-owned project_runtime key cannot be supplied or overridden by a
    client. The remaining user metadata is preserved without interpretation.
    """
    supplied = dict(metadata or {})
    if _SYSTEM_METADATA_KEY in supplied:
        raise ValueError(f"'{_SYSTEM_METADATA_KEY}' is system-managed")
    template = resolve_project_template(template_id)
    supplied[_SYSTEM_METADATA_KEY] = {
        "contract_version": "1",
        "template_id": template["id"],
        "template_version": template["version"],
        "requested_capabilities": list(template["capability_targets"]),
        "runtime": {
            "operational_engine": {"name": "weaver", "state": "requires_live_probe"},
            "conversation_interface": {"name": "arkana", "state": "requires_live_probe"},
            "sandbox": {"required": True, "state": "disposable_container_candidate_patch_v1"},
        },
        "verification": {
            "contract": "solspire.integration-health.v1",
            "endpoint": "/solspire/projects/{project_id}/integration-health",
            "template_configuration_is_not_live_proof": True,
        },
        "governance": {
            "project_scope_required": True,
            "human_authorization_required_for_consequential_actions": True,
        },
        "domain": {
            "module": template["domain_module"],
            "state": template["domain_status"],
        },
    }
    return supplied


__all__ = [
    "instantiate_project_metadata",
    "list_project_templates",
    "resolve_project_template",
]
