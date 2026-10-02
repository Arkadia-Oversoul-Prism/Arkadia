from __future__ import annotations

from datetime import datetime, timezone
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
    except Exception:
        raise HTTPException(status_code=502, detail="Economic seam scan failed; inspect server logs for source-level details.")


@router.post("/assess")
async def assess(request: Request, user: dict = Depends(require_sovereign)):
    """Assess a submitted bundle. Caller-supplied verification flags are never trusted."""
    try:
        body = await request.json()
        if not isinstance(body, dict):
            raise ValueError("request body must be an object")
        raw_evidence = body.get("evidence", [])
        raw_facts = body.get("facts", {})
        if not isinstance(raw_evidence, list) or not isinstance(raw_facts, dict):
            raise ValueError("evidence must be a list and facts must be an object")
        if not all(isinstance(item, dict) for item in raw_evidence):
            raise ValueError("each evidence record must be an object")
        evidence = [Evidence(**{**item, "independently_verified": False}) for item in raw_evidence]
        facts_input = dict(raw_facts)
        # The authenticated actor and server clock are the only source of
        # review identity. This records a review action but does not verify
        # submitted evidence or upgrade it to VERIFIED_CANDIDATE.
        requested_review = bool(facts_input.get("human_eligibility_review", False))
        facts_input["reviewer_uid"] = str(user.get("uid") or "") if requested_review else ""
        facts_input["reviewed_at"] = datetime.now(timezone.utc).isoformat() if requested_review else ""
        facts = TransactionFacts(**facts_input)
        title = str(body.get("title", "")).strip()
        seam_type = str(body.get("seam_type", "")).strip()
        if not title or not seam_type or not evidence:
            raise ValueError("title, seam_type and at least one evidence record are required")
        result = assess_seam(title=title, seam_type=seam_type, evidence=evidence, facts=facts)
        from economic_seams.engine import _db
        connection = _db()
        try:
            opportunity_id = persist_assessment(connection, result)
            connection.commit()
        finally:
            connection.close()
        result["opportunity_id"] = opportunity_id
        result["reviewed_by_subject"] = facts.reviewer_uid or None
        return result
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid seam assessment: {exc}")
    except Exception:
        raise HTTPException(status_code=500, detail="Seam assessment failed; inspect server logs for internal details.")
