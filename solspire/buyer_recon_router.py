"""Authenticated Eden Buyer Recon Board routes.

The board is automatically instantiated from the canonical SolSpire workspace
for the authenticated subject. It is reconnaissance state only; it does not
authorize, activate, execute, settle, or mutate the transaction engine.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from api.auth import require_auth, require_project_owner
from solspire.workspace_manager import get_workspace_manager
from solspire.buyer_recon import STATUSES, get_buyer_recon_manager

router = APIRouter(prefix="/buyer-recon", tags=["Eden Buyer Recon"])


class BuyerReconEntryInput(BaseModel):
    model_config = ConfigDict(extra="allow")
    prospect: str
    location: str = ""
    buyer_type: str = ""
    contact_route: str = ""
    commodity: str = ""
    estimated_demand: str = "UNKNOWN"
    procurement_frequency: str = "UNKNOWN"
    decision_maker: str = "UNKNOWN"
    current_price: str = "UNKNOWN"
    quantity: str = "UNKNOWN"
    specification: str = "UNKNOWN"
    delivery_point: str = "UNKNOWN"
    delivery_window: str = "UNKNOWN"
    payment_terms: str = "UNKNOWN"
    supplier: str = "UNKNOWN"
    source_price: str = "UNKNOWN"
    available_quantity: str = "UNKNOWN"
    logistics_quote: str = "UNKNOWN"
    packaging_qc_cost: str = "UNKNOWN"
    landed_cost: str = "UNKNOWN"
    buyer_price: str = "UNKNOWN"
    expected_gross_margin: str = "UNKNOWN"
    capital_required: str = "UNKNOWN"
    evidence_status: str = "NONE"
    evidence: list[dict[str, Any]] = []
    why_this_prospect: str = ""
    status: str = "UNCONTACTED"
    notes: str = ""


class BuyerReconEntryPatch(BaseModel):
    model_config = ConfigDict(extra="allow")
    pass


def _board(user: dict[str, Any]):
    workspace = get_workspace_manager().get_or_create(user["uid"])
    return get_buyer_recon_manager().get_or_create(workspace.id, user["uid"])


def _project_board(project_id: str, user: dict[str, Any]):
    # Ownership is enforced by the dependency before this function runs.
    workspace = get_workspace_manager().get_or_create(user["uid"])
    return get_buyer_recon_manager().get_or_create(
        f"{workspace.id}:project:{project_id}", user["uid"]
    )


@router.get("")
async def get_buyer_recon(user: dict = Depends(require_auth)) -> dict[str, Any]:
    board = _board(user)
    entries = get_buyer_recon_manager().list_entries(board.id, user["uid"])
    return {
        "board": board.to_dict(),
        "entries": [e.to_dict() for e in entries],
        "statuses": list(STATUSES),
        "persistence": {
            "scope": "canonical_workspace",
            "subject_binding": "authenticated_firebase_uid",
            "instantiated": True,
        },
        "authority": {
            "reconnaissance_only": True,
            "execution_authority": "NONE",
            "budget_authority": "NONE",
        },
    }


@router.post("/entries", status_code=201)
async def create_buyer_recon_entry(
    body: BuyerReconEntryInput, user: dict = Depends(require_auth)
) -> dict[str, Any]:
    board = _board(user)
    try:
        entry = get_buyer_recon_manager().create_entry(board, body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"entry": entry.to_dict()}


@router.patch("/entries/{entry_id}")
async def update_buyer_recon_entry(
    entry_id: str, body: BuyerReconEntryPatch, user: dict = Depends(require_auth)
) -> dict[str, Any]:
    try:
        entry = get_buyer_recon_manager().update_entry(
            entry_id, user["uid"], body.model_dump(exclude_unset=True)
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Buyer recon entry not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"entry": entry.to_dict()}


@router.get("/projects/{project_id}")
async def get_project_buyer_recon(
    project_id: str, user: dict = Depends(require_project_owner)
) -> dict[str, Any]:
    board = _project_board(project_id, user)
    entries = get_buyer_recon_manager().list_entries(board.id, user["uid"])
    return {
        "board": board.to_dict(),
        "project_id": project_id,
        "entries": [e.to_dict() for e in entries],
        "statuses": list(STATUSES),
        "persistence": {
            "scope": "project",
            "subject_binding": "authenticated_firebase_uid",
            "project_binding": True,
            "instantiated": True,
        },
        "authority": {
            "reconnaissance_only": True,
            "execution_authority": "NONE",
            "budget_authority": "NONE",
        },
    }


@router.post("/projects/{project_id}/entries", status_code=201)
async def create_project_buyer_recon_entry(
    project_id: str, body: BuyerReconEntryInput, user: dict = Depends(require_project_owner)
) -> dict[str, Any]:
    board = _project_board(project_id, user)
    try:
        entry = get_buyer_recon_manager().create_entry(board, body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"entry": entry.to_dict()}


@router.patch("/projects/{project_id}/entries/{entry_id}")
async def update_project_buyer_recon_entry(
    project_id: str, entry_id: str, body: BuyerReconEntryPatch,
    user: dict = Depends(require_project_owner)
) -> dict[str, Any]:
    board = _project_board(project_id, user)
    try:
        # The manager's subject binding plus project-specific board keeps records
        # isolated even though entries share the canonical SQLite store.
        entry = get_buyer_recon_manager().update_entry(
            entry_id, user["uid"], body.model_dump(exclude_unset=True)
        )
        if entry.board_id != board.id:
            raise KeyError(entry_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project buyer recon entry not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"entry": entry.to_dict()}
