"""Plan execution route.

Extracted from api/main.py to hold the 2600-line architecture budget
(tests/architecture/test_layer_boundaries.py::test_api_main_line_count_within_budget).
Route path and response shape are unchanged; authentication was added.

Plan execution runs the kernel planner and then executes the resulting steps —
it is a consequential operation, so it requires authentication. The plan is
validated against the tool registry before execution (``validate_plan``), which
also repairs the prior import of ``execute_plan`` from ``kernel.execution``
(where it does not exist) to ``kernel.planner`` (where it does).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from api.auth import require_auth

router = APIRouter(tags=["Plan"])


@router.post("/api/plan/run")
async def run_plan(request: Request, user: dict = Depends(require_auth)):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    user_input = body.get("input", "").strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="input is required")
    try:
        from kernel.planner import plan_or_fallback, validate_plan, execute_plan
        plan = plan_or_fallback(user_input)
        ok, reason = validate_plan(plan)
        if not ok:
            raise HTTPException(status_code=400, detail=f"Invalid plan: {reason}")
        result = execute_plan(plan)
        return {
            "success": bool(result.get("success")),
            "summary": result.get("summary", ""),
            "steps":   result.get("steps", []),
            "plan":    plan,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
