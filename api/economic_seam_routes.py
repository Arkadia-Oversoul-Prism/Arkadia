from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from api.auth import require_auth, require_sovereign
from economic_seams.engine import get_status, list_opportunities, scan_once

router = APIRouter(prefix="/api/economic-seams", tags=["economic-seams"])

@router.get("/status")
async def status(user: dict = Depends(require_auth)):
    return get_status()

@router.get("/opportunities")
async def opportunities(limit: int = 100, status: str | None = None, user: dict = Depends(require_auth)):
    return {"opportunities": list_opportunities(limit, status)}

@router.post("/scan")
async def scan(user: dict = Depends(require_sovereign)):
    try:
        return scan_once()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Economic seam scan failed: {exc}")
