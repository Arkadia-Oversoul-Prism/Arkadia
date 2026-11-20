"""Executive Office API — Gate 1 identity and governance routes.

Two distinct authentication surfaces, deliberately not merged:

  * Founder control routes use `api.auth.require_auth` (verified Firebase
    human identity) plus an access-level check. These are the only routes that
    can grant, suspend or revoke a delegation.
  * Machine routes use `require_executive_principal` (broker token + live
    delegation). A Firebase human token cannot call them, and a machine token
    cannot call the Founder routes.

No route here commissions the agent, creates a GitHub App, binds a workspace
automatically, or activates L3 delegation. A grant is an explicit Founder act
against an already-existing workspace.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.auth import require_auth
from executive_office.broker import BrokerUnavailable, ExecutiveIdentityBroker
from executive_office.control import FounderDelegationControl
from executive_office.knowledge_access import curated_context
from executive_office.registry import DelegationRegistry
from executive_office.revocation import revoke_delegation_cascade
from executive_office.tokens import ExecutivePrincipal, require_executive_principal
from solspire.workspace_manager import get_workspace_manager

router = APIRouter(prefix="/solspire/executive", tags=["executive-office"])


def _is_machine_token(request: Request) -> bool:
    """True when the bearer token is a broker machine token.

    Checked structurally (unverified header/claims) so it works even in
    dev-mode, where `require_auth` skips signature verification. A machine
    token must never be accepted as a human Founder identity, in any
    environment.
    """
    import jwt as _jwt

    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return False
    token = header[7:].strip()
    if not token:
        return False
    try:
        unverified = _jwt.get_unverified_header(token)
    except Exception:
        return False
    if unverified.get("kid") == "eo-broker-ed25519-1":
        return True
    try:
        claims = _jwt.decode(token, options={"verify_signature": False})
    except Exception:
        return False
    subject = str(claims.get("sub") or "")
    return subject.startswith("service:") or claims.get("principal_type") == "machine_service"


async def require_founder_human(request: Request, user: dict[str, Any] = Depends(require_auth)) -> dict[str, Any]:
    """Human Founder identity, with machine tokens explicitly refused.

    `require_auth` is permissive in dev-mode by design (it returns a synthetic
    guest profile). That is acceptable for ordinary console routes, but the
    delegation control surface must never treat a machine token as a Founder.
    """
    if _is_machine_token(request):
        raise HTTPException(status_code=403, detail="machine tokens cannot act as a Founder")
    return user


# ── request models ───────────────────────────────────────────────────────────

class GrantRequest(BaseModel):
    workspace_id: str = Field(..., description="An existing canonical SolSpire workspace id")
    capabilities: list[str]
    resources: list[str]
    expires_in_seconds: int = Field(..., gt=0, le=90 * 24 * 3600)
    knowledge_collection: list[str] | None = None


class ReasonRequest(BaseModel):
    reason: str | None = None


# ── Founder control surface (human auth) ─────────────────────────────────────

@router.get("/delegations")
async def list_delegations(user: dict[str, Any] = Depends(require_founder_human)) -> dict[str, Any]:
    """List the authenticated Founder's own delegations."""
    registry = DelegationRegistry()
    delegations = registry.list_for_owner(str(user.get("uid") or ""))
    return {
        "ok": True,
        "delegations": [d.to_dict() for d in delegations],
        "principal_commissioned": any(d.is_serviceable() for d in delegations),
    }


@router.post("/delegations")
async def grant_delegation(
    body: GrantRequest,
    user: dict[str, Any] = Depends(require_founder_human),
) -> dict[str, Any]:
    """Grant a bounded delegation. Founder-only.

    The workspace must already exist and belong to the authenticated Founder.
    This route never creates a workspace as a side effect of granting access.
    """
    import time

    founder_uid = str(user.get("uid") or "").strip()
    workspace = get_workspace_manager().get_for_subject(founder_uid)
    if workspace is None:
        raise HTTPException(
            status_code=409,
            detail="no existing canonical workspace for this Founder; create one first",
        )
    if workspace.id != body.workspace_id:
        raise HTTPException(
            status_code=403,
            detail="workspace_id does not match the Founder's canonical workspace",
        )

    control = FounderDelegationControl()
    try:
        delegation = control.grant(
            founder=user,
            owner_uid=founder_uid,
            workspace_id=workspace.id,
            capabilities=body.capabilities,
            resources=body.resources,
            expires_at=time.time() + body.expires_in_seconds,
            knowledge_collection=body.knowledge_collection,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "ok": True,
        "delegation": delegation.to_dict(),
        "note": "Delegation granted. The agent remains uncommissioned until a token is issued and used.",
    }


@router.post("/delegations/{delegation_id}/suspend")
async def suspend_delegation(
    delegation_id: str,
    body: ReasonRequest,
    user: dict[str, Any] = Depends(require_founder_human),
) -> dict[str, Any]:
    control = FounderDelegationControl()
    try:
        delegation = control.suspend(founder=user, delegation_id=delegation_id, reason=body.reason)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "delegation": delegation.to_dict()}


@router.post("/delegations/{delegation_id}/revoke")
async def revoke_delegation(
    delegation_id: str,
    body: ReasonRequest,
    user: dict[str, Any] = Depends(require_founder_human),
) -> dict[str, Any]:
    """Revoke a delegation and withdraw everything that depended on it."""
    founder_uid = str(user.get("uid") or "").strip()
    control = FounderDelegationControl()
    try:
        control._assert_owner(delegation_id, founder_uid)
        if int(user.get("access_level") or 0) < 3:
            raise PermissionError("Founder (access_level >= 3) required")
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = revoke_delegation_cascade(
        delegation_id=delegation_id,
        founder_uid=founder_uid,
        reason=body.reason or "founder revocation",
    )
    return {"ok": True, **result}


@router.post("/delegations/{delegation_id}/reactivate")
async def reactivate_delegation(
    delegation_id: str,
    body: ReasonRequest,
    user: dict[str, Any] = Depends(require_founder_human),
) -> dict[str, Any]:
    control = FounderDelegationControl()
    try:
        delegation = control.reactivate(founder=user, delegation_id=delegation_id, reason=body.reason)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "delegation": delegation.to_dict()}


# ── machine surface (broker token + live delegation) ────────────────────────

@router.get("/whoami")
async def whoami(
    principal: ExecutivePrincipal = Depends(require_executive_principal),
) -> dict[str, Any]:
    """The validated machine principal. Derived only from server-side state."""
    return {"ok": True, "principal": principal.to_dict()}


@router.get("/knowledge/curated")
async def curated_knowledge(
    principal: ExecutivePrincipal = Depends(require_executive_principal),
) -> dict[str, Any]:
    """Read only the curated Knowledge OS collection named by the delegation."""
    if not principal.has_capability("read_curated_knowledge"):
        raise HTTPException(status_code=403, detail="capability not granted: read_curated_knowledge")
    return {"ok": True, "context": curated_context(principal)}


@router.post("/token")
async def issue_token(
    user: dict[str, Any] = Depends(require_founder_human),
) -> dict[str, Any]:
    """Broker issuance endpoint.

    Authenticated by the Founder's human session, not left anonymous: an open
    issuance route would let anyone holding a delegation id mint credentials.
    The broker still refuses unless a serviceable delegation exists, and it
    never returns the signing key.

    In production the runtime that already holds the workload credential calls
    `ExecutiveIdentityBroker.issue()` in-process; this route exists so the
    Founder can inspect and exercise issuance deliberately.
    """
    broker = ExecutiveIdentityBroker()
    try:
        return {"ok": True, **broker.issue()}
    except BrokerUnavailable as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


__all__ = ["router"]
