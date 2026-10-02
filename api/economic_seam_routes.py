from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Request
from api.auth import require_auth, require_sovereign
from economic_seams.engine import get_status, list_opportunities, scan_once
from economic_seams.correlation import Evidence, TransactionFacts, assess_seam, persist_assessment

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


@router.post("/assess")
async def assess(request: Request, user: dict = Depends(require_sovereign)):
    """Assess submitted evidence and transaction facts; sovereign-only, no execution."""
    try:
        body = await request.json()
        evidence = [Evidence(**item) for item in body.get("evidence", [])]
        facts = TransactionFacts(**body.get("facts", {}))
        title = str(body.get("title", "")).strip()
        seam_type = str(body.get("seam_type", "")).strip()
        if not title or not seam_type or not evidence:
            raise ValueError("title, seam_type and at least one evidence record are required")
        result = assess_seam(title=title, seam_type=seam_type, evidence=evidence, facts=facts)
        # Persist the explicit assessment to the existing opportunity store.
        from economic_seams.engine import _db
        connection = _db()
        opportunity_id = persist_assessment(connection, result)
        connection.commit()
        connection.close()
        result["opportunity_id"] = opportunity_id
        result["reviewed_by_subject"] = user.get("uid")
        return result
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid seam assessment: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Seam assessment failed: {exc}")
