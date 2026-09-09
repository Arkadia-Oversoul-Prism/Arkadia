from __future__ import annotations

from fastapi import APIRouter, Depends

from api.auth import require_auth
from lab import build_overview

router = APIRouter(prefix="/api/lab", tags=["Engineering Lab"], dependencies=[Depends(require_auth)])


@router.get("/overview")
async def lab_overview() -> dict:
    """Deterministic, authenticated, read-only Engineering Lab snapshot."""
    return build_overview(".")
