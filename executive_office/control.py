"""Founder-only delegation control surface — Gate 1A.

Grant, suspend, revoke and reactivate. Every action requires a verified human
Founder principal; the machine principal has no path into this module. The
Founder UID is taken from the authenticated session, never from request JSON.

This is a control surface, not an approval engine: it does not create
proposals, authorizations or execution records. Those stay in the canonical
SolSpire/Weaver chain.
"""
from __future__ import annotations

from typing import Any

from executive_office.policy import policy_identity
from executive_office.registry import Delegation, DelegationRegistry

#: Capabilities the initial read-only commissioning envelope may contain.
#: Anything not listed here cannot be granted through this surface.
GRANTABLE_CAPABILITIES = frozenset({
    "read_repository",
    "read_project_metadata",
    "read_operational_records",
    "read_curated_knowledge",
    "produce_internal_reports",
})

#: Capabilities that are human-only and can never appear in a delegation.
RESERVED_CAPABILITIES = frozenset({
    "authorize_proposal",
    "approve_request",
    "execute_payment",
    "sign_contract",
    "hire_or_terminate",
    "change_identity_policy",
    "change_credentials",
    "merge_protected_branch",
    "deploy_production",
    "disclose_confidential_data",
})


def _require_founder(founder: dict[str, Any] | None) -> str:
    """Resolve the Founder UID from a verified session, or refuse.

    The caller passes the profile returned by `api.auth.require_auth`; this
    function never accepts a UID from a request body.
    """
    if not founder:
        raise PermissionError("authenticated Founder session required")
    uid = str(founder.get("uid") or "").strip()
    if not uid:
        raise PermissionError("verified Founder uid required")
    if int(founder.get("access_level") or 0) < 3:
        raise PermissionError("Founder (access_level >= 3) required for delegation control")
    return uid


def _validate_capabilities(capabilities: Any) -> list[str]:
    if not isinstance(capabilities, list) or not capabilities:
        raise ValueError("capability_scope must be a non-empty list")
    requested = [str(item).strip() for item in capabilities if str(item).strip()]
    reserved = sorted(set(requested) & RESERVED_CAPABILITIES)
    if reserved:
        raise ValueError(f"reserved human-only capabilities cannot be delegated: {reserved}")
    unknown = sorted(set(requested) - GRANTABLE_CAPABILITIES)
    if unknown:
        raise ValueError(f"capabilities outside the grantable envelope: {unknown}")
    return requested


def _validate_resources(resources: Any) -> list[str]:
    if not isinstance(resources, list) or not resources:
        raise ValueError("resource_scope must be a non-empty list of explicit resource ids")
    cleaned = [str(item).strip() for item in resources if str(item).strip()]
    if not cleaned:
        raise ValueError("resource_scope must name at least one resource")
    if any(item in {"*", "all"} for item in cleaned):
        raise ValueError("wildcard resource scope is not permitted")
    return cleaned


class FounderDelegationControl:
    """The only write path into the delegation registry."""

    def __init__(self, registry: DelegationRegistry | None = None) -> None:
        self.registry = registry or DelegationRegistry()

    def grant(
        self,
        *,
        founder: dict[str, Any] | None,
        owner_uid: str,
        workspace_id: str,
        capabilities: Any,
        resources: Any,
        expires_at: float,
        knowledge_collection: list[str] | None = None,
    ) -> Delegation:
        """Create an ACTIVE read-only delegation bound to the current policy."""
        founder_uid = _require_founder(founder)
        # The owner must be the authenticated Founder. A different owner_uid is
        # an attempt to grant access to someone else's data.
        if str(owner_uid or "").strip() != founder_uid:
            raise PermissionError("owner_uid must equal the authenticated Founder uid")
        caps = _validate_capabilities(capabilities)
        res = _validate_resources(resources)
        identity = policy_identity()
        resource_scope: dict[str, Any] = {"resources": res}
        if knowledge_collection is not None:
            resource_scope["knowledge_collection"] = [
                str(note_id).strip() for note_id in knowledge_collection if str(note_id).strip()
            ]
        return self.registry.grant(
            owner_uid=founder_uid,
            workspace_id=str(workspace_id or "").strip(),
            policy_id=str(identity["policy_id"]),
            policy_version=int(identity["policy_version"]),
            policy_digest=str(identity["policy_digest"]),
            resource_scope=resource_scope,
            capability_scope={"capabilities": caps},
            expires_at=float(expires_at),
            founder_uid=founder_uid,
        )

    def suspend(self, *, founder: dict[str, Any] | None, delegation_id: str, reason: str | None = None) -> Delegation:
        founder_uid = _require_founder(founder)
        self._assert_owner(delegation_id, founder_uid)
        return self.registry.suspend(delegation_id=delegation_id, founder_uid=founder_uid, reason=reason)

    def revoke(self, *, founder: dict[str, Any] | None, delegation_id: str, reason: str | None = None) -> Delegation:
        founder_uid = _require_founder(founder)
        self._assert_owner(delegation_id, founder_uid)
        return self.registry.revoke(delegation_id=delegation_id, founder_uid=founder_uid, reason=reason)

    def reactivate(self, *, founder: dict[str, Any] | None, delegation_id: str, reason: str | None = None) -> Delegation:
        founder_uid = _require_founder(founder)
        self._assert_owner(delegation_id, founder_uid)
        return self.registry.reactivate(delegation_id=delegation_id, founder_uid=founder_uid, reason=reason)

    def _assert_owner(self, delegation_id: str, founder_uid: str) -> None:
        delegation = self.registry.find(delegation_id)
        if delegation is None:
            raise ValueError("unknown delegation")
        if delegation.owner_uid != founder_uid:
            raise PermissionError("only the delegating Founder may change this delegation")


__all__ = [
    "FounderDelegationControl",
    "GRANTABLE_CAPABILITIES",
    "RESERVED_CAPABILITIES",
]
