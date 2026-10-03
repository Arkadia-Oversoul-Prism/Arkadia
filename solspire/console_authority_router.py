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
    content_base64: str


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
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "ok": result["ok"],
        "execution_attempt": attempt.to_dict(),
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
    root = Path(os.environ.get("SOLSPIRE_DATA_DIR", "data")) / "console_captures" / user["uid"]
    root.mkdir(parents=True, exist_ok=True)
    target = root / safe_id
    target.write_bytes(raw)
    store = EnterpriseOrchestrationStore()
    event = store.operational_event(
        subject=user["uid"],
        enterprise_id="solariun",
        event_type="INPUT_RECEIVED",
        payload={
            "capture_id": safe_id,
            "kind": body.kind,
            "mime_type": body.mime_type,
            "size_bytes": body.size_bytes,
            "sha256": body.sha256,
            "captured_at": body.captured_at,
            "artifact_ref": f"console-capture:{user['uid']}:{safe_id}",
        },
        correlation_id=f"console-capture:{safe_id}",
    )
    return {
        "ok": True,
        "capture_id": safe_id,
        "artifact_ref": f"console-capture:{user['uid']}:{safe_id}",
        "work_event": event.to_dict(),
        "reconciled": True,
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
            verifier=body.verifier,
            verdict=body.verdict,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "verification": verification.to_dict()}
