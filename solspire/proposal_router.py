"""Authenticated API surface for the bounded Proposal Feedback Loop."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.auth import require_auth
from solspire.proposal_manager import get_proposal_manager
from solspire.workspace_manager import get_workspace_manager

router = APIRouter(
    prefix="/proposals",
    tags=["SolSpire Proposals"],
    dependencies=[Depends(require_auth)],
)


class CreateProposalRequest(BaseModel):
    objective: str = ""
    scope: str = ""
    requested_decision: str = ""
    workload_ref: str | None = None
    assumptions: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)


class CreateFeedbackRequest(BaseModel):
    feedback_type: str = "observation"
    observation: str = ""
    recommendation: str = ""
    evidence_refs: list[str] = Field(default_factory=list)


@router.post("")
async def create_proposal(
    body: CreateProposalRequest | None = None,
    user: dict = Depends(require_auth),
) -> dict[str, Any]:
    workspace = get_workspace_manager().get_for_subject(user["uid"])
    if workspace is None:
        raise HTTPException(status_code=409, detail="Canonical workspace not found")
    payload = body or CreateProposalRequest()
    try:
        proposal = get_proposal_manager().create_proposal(
            subject_ref=user["uid"],
            workspace_ref=workspace.id,
            objective=payload.objective,
            scope=payload.scope,
            requested_decision=payload.requested_decision,
            workload_ref=payload.workload_ref,
            assumptions=payload.assumptions,
            alternatives=payload.alternatives,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "proposal": proposal.to_dict()}


@router.get("")
async def list_proposals(
    limit: int = Query(default=50, ge=1, le=200),
    user: dict = Depends(require_auth),
) -> dict[str, Any]:
    workspace = get_workspace_manager().get_for_subject(user["uid"])
    if workspace is None:
        raise HTTPException(status_code=409, detail="Canonical workspace not found")
    items = get_proposal_manager().list_proposals(user["uid"], workspace.id, limit)
    return {"proposals": [item.to_dict() for item in items], "count": len(items)}


@router.get("/{proposal_id}")
async def get_proposal(proposal_id: str, user: dict = Depends(require_auth)) -> dict[str, Any]:
    proposal = get_proposal_manager().get_proposal(proposal_id, user["uid"])
    if proposal is None:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return {"proposal": proposal.to_dict()}


@router.post("/{proposal_id}/feedback")
async def add_feedback(
    proposal_id: str,
    body: CreateFeedbackRequest | None = None,
    user: dict = Depends(require_auth),
) -> dict[str, Any]:
    workspace = get_workspace_manager().get_for_subject(user["uid"])
    if workspace is None:
        raise HTTPException(status_code=409, detail="Canonical workspace not found")
    payload = body or CreateFeedbackRequest()
    try:
        proposal, feedback = get_proposal_manager().add_feedback(
            proposal_id=proposal_id,
            subject_ref=user["uid"],
            workspace_ref=workspace.id,
            feedback_type=payload.feedback_type,
            observation=payload.observation,
            recommendation=payload.recommendation,
            evidence_refs=payload.evidence_refs,
        )
    except ValueError as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail=msg) from exc
        raise HTTPException(status_code=400, detail=msg) from exc
    return {
        "ok": True,
        "proposal": proposal.to_dict(),
        "feedback": feedback.to_dict(),
    }


@router.get("/{proposal_id}/feedback")
async def list_feedback(proposal_id: str, user: dict = Depends(require_auth)) -> dict[str, Any]:
    proposal = get_proposal_manager().get_proposal(proposal_id, user["uid"])
    if proposal is None:
        raise HTTPException(status_code=404, detail="Proposal not found")
    items = get_proposal_manager().list_feedback(proposal_id, user["uid"])
    return {"feedback": [item.to_dict() for item in items], "count": len(items)}


__all__ = ["router"]
