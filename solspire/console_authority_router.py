"""Native Console authority bridge.

Connects an authenticated Solariun proposal to the existing ARK-WEAVER-01
enterprise chain without collapsing ACCEPTED into AUTHORIZED.

Firebase identity is the only subject/actor source accepted by this boundary.
"""
from __future__ import annotations

from typing import Any
import base64
import hashlib
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.auth import require_auth
from solspire.proposal_manager import get_proposal_manager
from solspire.workspace_manager import get_workspace_manager
from solspire.workevent_manager import get_workevent_manager
from solspire.eden_ops import EdenOps
from weaver.enterprise_orchestration import EnterpriseOrchestrationStore
from weaver.console_adapter import WeaverConsoleAdapter

router = APIRouter(prefix="/authority", tags=["Arkadia Console Authority"])


class AuthorizationRequest(BaseModel):
    scope: dict[str, Any] = Field(default_factory=dict)
    constraints: dict[str, Any] = Field(default_factory=dict)


class ExecutionRequest(BaseModel):
    tool_channel: str
    request_payload: dict[str, Any] = Field(default_factory=dict)


class EvidenceRequest(BaseModel):
    evidence_type: str
    content_or_ref: Any
    source_ref: str | None = None


class CaptureRequest(BaseModel):
    capture_id: str
    kind: str
    mime_type: str
    size_bytes: int
    sha256: str
    captured_at: str
    content_base64: str | None = None


class VerificationRequest(BaseModel):
    claim: str
    evidence_refs: list[str]
    verdict: str
    verifier: str = "human-console"


def _authority_identity(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "uid": user["uid"],
        "role": user.get("role"),
        "access_level": user.get("access_level", 0),
    }


@router.post("/proposals/{proposal_id}/authorize")
async def authorize_proposal(
    proposal_id: str,
    body: AuthorizationRequest | None = None,
    user: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    """Human gesture -> HAE -> Authorization.

    The SolSpire proposal must already be ACCEPTED. ACCEPTED is not itself
    authorization. A distinct canonical ARK-WEAVER-01 proposal is materialized
    from the accepted proposal and bound to the same correlation lineage.
    """
    manager = get_proposal_manager()
    proposal = manager.get_proposal(proposal_id, user["uid"])
    if proposal is None:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if proposal.proposal_status != "ACCEPTED":
        raise HTTPException(
            status_code=409,
            detail=f"Proposal must be ACCEPTED before authorization; current={proposal.proposal_status}",
        )
    if proposal.authorization_ref:
        raise HTTPException(status_code=409, detail="Proposal is already authorized")

    workspace = get_workspace_manager().get_for_subject(user["uid"])
    if workspace is None or workspace.id != proposal.workspace_ref:
        raise HTTPException(status_code=409, detail="Canonical workspace not found")

    identity = _authority_identity(user)
    role = str(identity.get("role") or "").strip().lower()
    try:
        access_level = int(identity.get("access_level", 0))
    except (TypeError, ValueError):
        access_level = 0
    if role != "flamekeeper" and access_level < 3:
        raise HTTPException(status_code=403, detail="Govern authority required")

    store = EnterpriseOrchestrationStore()
    enterprise = store.proposal(
        subject=user["uid"],
        enterprise_id=workspace.id,
        objective=proposal.objective,
        rationale=proposal.scope,
        recommended_actions=[proposal.requested_decision] if proposal.requested_decision else [],
        required_authority="human",
        tool_selections=[],
        correlation_id=f"solariun-proposal:{proposal.proposal_id}:v{proposal.proposal_version}",
    )
    # The enterprise proposal owns the causal chain; the SolSpire proposal
    # carries only a reference back to the resulting authorization.
    scope = body.scope or {"tools": ["git.status"]}
    constraints = body.constraints or {
        "read_only": True,
        "repository_root": ".",
        "network": False,
    }
    result = EdenOps(store).decide_proposal(
        subject=user["uid"],
        proposal_id=enterprise.id,
        action="APPROVE",
        actor=user["uid"],
        actor_identity=identity,
        authentication_context="firebase_id_token",
        authorization_scope=scope,
        authorization_constraints=constraints,
    )
    authorization = result["authorization"]
    manager.bind_authorization(
        proposal_id=proposal.proposal_id,
        subject_ref=user["uid"],
        authorization_ref=authorization.id,
    )
    return {
        "ok": True,
        "human_authority_event": result["authority_event"].to_dict(),
        "authorization": authorization.to_dict(),
        "enterprise_proposal": enterprise.to_dict(),
        "solariun_proposal": manager.get_proposal(proposal.proposal_id, user["uid"]).to_dict(),
        "chain": [
            "HumanAuthorityEvent",
            "Authorization",
            "Weaver execution boundary",
            "Evidence",
            "Verification",
        ],
        "execution_authorized": True,
        "note": "Authorization permits a governed execution attempt. It does not claim execution, evidence, or verification.",
    }


@router.post("/authorizations/{authorization_id}/execute")
async def create_execution_attempt(
    authorization_id: str,
    body: ExecutionRequest,
    user: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    """Create the real ARK-WEAVER-01 execution attempt record.

    This endpoint does not fabricate success or evidence. Actual tool execution
    remains a separate runtime concern; the returned attempt is ATTEMPTED.
    """
    store = EnterpriseOrchestrationStore()
    try:
        attempt = store.execution_attempt(
            subject=user["uid"],
            authorization_id=authorization_id,
            tool_channel=body.tool_channel,
            request_payload=body.request_payload,
            result_status="ATTEMPTED",
        )
        adapter = WeaverConsoleAdapter(store=store)
        result = adapter.dispatch(
            subject=user["uid"],
            authorization_id=authorization_id,
            execution_attempt_id=attempt.id,
            tool_channel=body.tool_channel,
            request_payload=body.request_payload,
        )
        # The adapter completes the canonical attempt after recording evidence.
        # Refresh the returned object so the response reports persisted state,
        # not the stale ATTEMPTED object created before dispatch.
        completed_attempt = store.complete_execution_attempt(
            subject=user["uid"],
            execution_attempt_id=attempt.id,
            result_status=result["execution"]["status"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "ok": result["ok"],
        "execution_attempt": completed_attempt.to_dict(),
        "execution": result["execution"],
        "evidence": result["evidence"],
        "boundary": "Tool dispatch is real. Verification remains a separate human act.",
    }


@router.post("/executions/{execution_id}/evidence")
async def record_execution_evidence(
    execution_id: str,
    body: EvidenceRequest,
    user: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    store = EnterpriseOrchestrationStore()
    try:
        evidence = store.evidence(
            subject=user["uid"],
            execution_attempt_id=execution_id,
            evidence_type=body.evidence_type,
            content_or_ref=body.content_or_ref,
            source_ref=body.source_ref,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "ok": True,
        "evidence": evidence.to_dict(),
        "boundary": "Evidence exists independently. Verification is still required.",
    }


@router.post("/captures")
async def sync_capture(
    body: CaptureRequest,
    user: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    """Reconcile one durable native capture into the canonical field."""
    if body.size_bytes < 0 or body.size_bytes > 6 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="capture exceeds 6 MiB sync limit")
    raw = None
    if body.content_base64:
        try:
            raw = base64.b64decode(body.content_base64, validate=True)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="invalid capture encoding") from exc
        if len(raw) != body.size_bytes:
            raise HTTPException(status_code=400, detail="capture size mismatch")
        digest = hashlib.sha256(raw).hexdigest()
        if digest != body.sha256:
            raise HTTPException(status_code=400, detail="capture digest mismatch")
    safe_id = "".join(ch for ch in body.capture_id if ch.isalnum() or ch in "-_")[:80]
    if not safe_id:
        raise HTTPException(status_code=400, detail="capture_id required")
    # A metadata-only capture (no bytes) is a device-local record: it must not
    # claim server-side content.
    artifact_ref = (
        f"console-capture:{user['uid']}:{safe_id}"
        if raw is not None
        else f"device-local-capture:{user['uid']}:{safe_id}"
    )
    workspace = get_workspace_manager().get_for_subject(user["uid"])
    if workspace is None:
        raise HTTPException(status_code=409, detail="Canonical workspace not found")

    # Capture reconciliation is idempotent by authenticated subject + stable
    # device capture id. The same retry must return the same canonical
    # WorkEvent; a reused id with different capture metadata/digest is a
    # deterministic conflict, never a second WorkEvent.
    event_id = "CAPTURE-" + hashlib.sha256(
        f"{user['uid']}:{safe_id}".encode("utf-8")
    ).hexdigest()[:32]
    state_after_ref = f"sha256:{body.sha256}"
    scope_ref = (
        f"capture-meta:{body.kind}:{body.mime_type}:{body.size_bytes}:"
        f"{body.captured_at}"
    )
    workevents = get_workevent_manager()
    existing = workevents.get(event_id, user["uid"])
    if existing is not None:
        if (
            existing.workspace_ref != workspace.id
            or existing.event_type != "CONSOLE_CAPTURE"
            or existing.artifact_refs != [artifact_ref]
            or existing.state_after_ref != state_after_ref
            or existing.scope_ref != scope_ref
        ):
            raise HTTPException(
                status_code=409,
                detail="capture_id already reconciled with different capture content or metadata",
            )
        return {
            "ok": True,
            "capture_id": safe_id,
            "artifact_ref": artifact_ref,
            "work_event": existing.to_dict(),
            "reconciled": True,
            "idempotent_replay": True,
        }

    from time import time
    event = workevents.create(
        subject_ref=user["uid"],
        workspace_ref=workspace.id,
        event_type="CONSOLE_CAPTURE",
        occurred_at=time(),
        work_event_id=event_id,
        actor_ref=user["uid"],
        artifact_refs=[artifact_ref],
        state_after_ref=state_after_ref,
        scope_ref=scope_ref,
        status="RECORDED",
    )
    return {
        "ok": True,
        "capture_id": safe_id,
        "artifact_ref": artifact_ref,
        "work_event": event.to_dict(),
        "reconciled": True,
        "idempotent_replay": False,
    }


@router.post("/verification")
async def verify_execution(
    body: VerificationRequest,
    user: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    store = EnterpriseOrchestrationStore()
    try:
        verification = store.verify(
            subject=user["uid"],
            claim=body.claim,
            evidence_refs=body.evidence_refs,
            verifier=f"firebase:{user['uid']}",
            verdict=body.verdict,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "verification": verification.to_dict()}
