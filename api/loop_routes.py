"""Phase 5-8 Kernel API routes: Jobs + Goals.

Extracted from api/main.py to restore the 2600-line architecture budget
(tests/architecture/test_layer_boundaries.py::test_api_main_line_count_within_budget).
Route paths and response shapes are unchanged.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from api.auth import require_auth

#: Every route on this router mutates or exposes kernel-loop state: the job
#: queue executes tools, and the goal scheduler starts recurring runs. None of
#: it is public, so the whole router requires authentication.
router = APIRouter(tags=["Kernel Loop"], dependencies=[Depends(require_auth)])


def _job_store():
    from kernel.jobs import get_store
    return get_store()


def _goal_store():
    from kernel.goals import get_store
    return get_store()


# ── Jobs ─────────────────────────────────────────────────────────────────────

@router.get("/api/jobs")
async def list_jobs(status: str | None = None, limit: int = 100):
    store = _job_store()
    valid = {"pending", "running", "completed", "failed"}
    s = status if status in valid else None
    jobs = store.list(limit=limit, status=s)
    return {"jobs": jobs, "stats": store.stats()}


@router.post("/api/job/create")
async def create_job(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    intent = body.get("intent") or body
    if not isinstance(intent, dict):
        raise HTTPException(status_code=400, detail="intent must be an object")
    job = _job_store().create(intent, source=body.get("source", "api"))
    return {"job_id": job["job_id"], "status": job["status"]}


@router.get("/api/job/{job_id}")
async def get_job(job_id: str):
    job = _job_store().get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


@router.get("/api/job/{job_id}/trace")
async def get_job_trace(job_id: str):
    job = _job_store().get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    trace = job.get("trace")
    if trace is None:
        raise HTTPException(status_code=404, detail="No trace recorded for this job yet")
    return {"job_id": job_id, "status": job.get("status"), "trace": trace}


# ── Goals ─────────────────────────────────────────────────────────────────────

@router.get("/api/goals")
async def list_goals(status: str | None = None):
    from kernel.goals import VALID_STATUSES
    s = status if status in VALID_STATUSES else None
    goals = _goal_store().list(status=s)
    active_count = sum(1 for g in goals if g.get("status") == "active")
    return {"goals": goals, "count": len(goals), "active": active_count}


@router.post("/api/goals")
async def create_goal(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    description = body.get("description", "").strip()
    if not description:
        raise HTTPException(status_code=400, detail="description is required")
    try:
        goal = _goal_store().create(
            description,
            cadence_seconds=float(body.get("cadence_seconds", 300)),
            max_runs_per_hour=int(body.get("max_runs_per_hour", 6)),
            start_now=bool(body.get("start_now", True)),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "Goal created", "goal": goal}


@router.patch("/api/goals/{goal_id}")
async def update_goal(goal_id: str, request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    allowed = {"description", "status", "cadence_seconds", "max_runs_per_hour"}
    fields = {k: v for k, v in body.items() if k in allowed}
    if not fields:
        raise HTTPException(status_code=400, detail="No updatable fields provided")
    try:
        goal = _goal_store().update(goal_id, **fields)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if goal is None:
        raise HTTPException(status_code=404, detail=f"Goal {goal_id} not found")
    return {"message": "Goal updated", "goal": goal}


@router.delete("/api/goals/{goal_id}")
async def delete_goal(goal_id: str):
    deleted = _goal_store().delete(goal_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Goal {goal_id} not found")
    return {"message": "Goal deleted", "goal_id": goal_id}
