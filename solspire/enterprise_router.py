"""Generic SolSpire Enterprise onboarding and dashboard projection.

SolSpire is the enterprise layer. This module contains no tenant-specific
business, commodity, budget, or pilot data. It creates organizational structure
from human-provided onboarding context and preserves the existing authentication,
workspace, workload, WorkEvent, provenance, and execution boundaries.

LLM analysis is advisory. It can propose structure or identify missing context,
but it never creates authorization or executes consequential work.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.auth import require_auth
from solspire.workspace_manager import get_workspace_manager

_DB_PATH = os.environ.get("SOLSPIRE_PROJECTS_DB") or os.path.join(
    os.environ.get("SOLSPIRE_DATA_DIR", "data"), "solspire_projects.db"
)

STEP_NAMES = (
    "enterprise_context",
    "pilot_workload",
    "workstreams",
    "members",
    "operating_context",
    "week_one",
    "master_dashboard",
)


@dataclass(frozen=True)
class Enterprise:
    enterprise_id: str
    owner_subject_ref: str
    workspace_ref: str
    display_name: str
    legal_name: str
    lifecycle: str
    onboarding_step: int
    context: dict[str, Any]
    pilot_workload: dict[str, Any]
    workstreams: list[dict[str, Any]]
    members: list[dict[str, Any]]
    operating_context: dict[str, Any]
    week_one: dict[str, Any]
    dashboard_config: dict[str, Any]
    analysis: list[dict[str, Any]]
    created_at: float
    updated_at: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class StepPayload(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)


class AnalysisPayload(BaseModel):
    step: str
    context: dict[str, Any] = Field(default_factory=dict)


def _db() -> sqlite3.Connection:
    directory = os.path.dirname(_DB_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS enterprise_organizations (
            enterprise_id TEXT PRIMARY KEY,
            owner_subject_ref TEXT NOT NULL,
            workspace_ref TEXT NOT NULL,
            display_name TEXT NOT NULL,
            legal_name TEXT NOT NULL DEFAULT '',
            lifecycle TEXT NOT NULL DEFAULT 'ONBOARDING',
            onboarding_step INTEGER NOT NULL DEFAULT 1,
            context_json TEXT NOT NULL DEFAULT '{}',
            pilot_workload_json TEXT NOT NULL DEFAULT '{}',
            workstreams_json TEXT NOT NULL DEFAULT '[]',
            members_json TEXT NOT NULL DEFAULT '[]',
            operating_context_json TEXT NOT NULL DEFAULT '{}',
            week_one_json TEXT NOT NULL DEFAULT '{}',
            dashboard_config_json TEXT NOT NULL DEFAULT '{}',
            analysis_json TEXT NOT NULL DEFAULT '[]',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_enterprise_owner ON enterprise_workspaces(owner_subject_ref, updated_at)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_enterprise_workspace ON enterprise_workspaces(workspace_ref)"
    )
    conn.commit()
    return conn


def _decode(row: sqlite3.Row) -> Enterprise:
    def obj(name: str) -> Any:
        return json.loads(row[name] or "{}")
    def arr(name: str) -> list[dict[str, Any]]:
        return json.loads(row[name] or "[]")
    return Enterprise(
        enterprise_id=row["enterprise_id"],
        owner_subject_ref=row["owner_subject_ref"],
        workspace_ref=row["workspace_ref"],
        display_name=row["display_name"],
        legal_name=row["legal_name"],
        lifecycle=row["lifecycle"],
        onboarding_step=int(row["onboarding_step"]),
        context=obj("context_json"),
        pilot_workload=obj("pilot_workload_json"),
        workstreams=arr("workstreams_json"),
        members=arr("members_json"),
        operating_context=obj("operating_context_json"),
        week_one=obj("week_one_json"),
        dashboard_config=obj("dashboard_config_json"),
        analysis=arr("analysis_json"),
        created_at=float(row["created_at"]),
        updated_at=float(row["updated_at"]),
    )


def _get(conn: sqlite3.Connection, enterprise_id: str, subject_ref: str) -> Enterprise | None:
    row = conn.execute(
        "SELECT * FROM enterprise_workspaces WHERE enterprise_id=? AND owner_subject_ref=?",
        (enterprise_id, subject_ref),
    ).fetchone()
    return _decode(row) if row else None


class EnterpriseManager:
    def create(self, *, subject_ref: str, display_name: str = "") -> Enterprise:
        workspace = get_workspace_manager().get_or_create(
            subject_ref, display_name="SolSpire Enterprise Workspace"
        )
        now = time.time()
        enterprise_id = str(uuid.uuid4())
        name = display_name.strip() or "New Enterprise"
        with _db() as conn:
            conn.execute(
                """INSERT INTO enterprise_workspaces
                (enterprise_id, owner_subject_ref, workspace_ref, display_name, legal_name,
                 lifecycle, onboarding_step, context_json, pilot_workload_json,
                 workstreams_json, members_json, operating_context_json, week_one_json,
                 dashboard_config_json, analysis_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, '', 'ONBOARDING', 1, '{}', '{}', '[]', '[]', '{}', '{}', '{}', '[]', ?, ?)""",
                (enterprise_id, subject_ref, workspace.id, name, now, now),
            )
            return _get(conn, enterprise_id, subject_ref)  # type: ignore[return-value]

    def list(self, *, subject_ref: str) -> list[Enterprise]:
        with _db() as conn:
            rows = conn.execute(
                "SELECT * FROM enterprise_workspaces WHERE owner_subject_ref=? ORDER BY updated_at DESC",
                (subject_ref,),
            ).fetchall()
        return [_decode(row) for row in rows]

    def get(self, *, subject_ref: str, enterprise_id: str) -> Enterprise:
        with _db() as conn:
            enterprise = _get(conn, enterprise_id, subject_ref)
        if not enterprise:
            raise HTTPException(status_code=404, detail="Enterprise workspace not found")
        return enterprise

    def save_step(self, *, subject_ref: str, enterprise_id: str, step: int, data: dict[str, Any]) -> Enterprise:
        if step < 1 or step > 7:
            raise HTTPException(status_code=400, detail="Onboarding step must be 1 through 7")
        with _db() as conn:
            enterprise = _get(conn, enterprise_id, subject_ref)
            if not enterprise:
                raise HTTPException(status_code=404, detail="Enterprise workspace not found")
            column = (
                "context_json", "pilot_workload_json", "workstreams_json",
                "members_json", "operating_context_json", "week_one_json",
                "dashboard_config_json"
            )[step - 1]
            encoded = json.dumps(data, ensure_ascii=False)
            legal_name = data.get("legal_name", enterprise.legal_name) if step == 1 else enterprise.legal_name
            display_name = data.get("display_name", enterprise.display_name) if step == 1 else enterprise.display_name
            next_step = max(enterprise.onboarding_step, step)
            lifecycle = "READY_FOR_OPERATIONS" if step == 7 else "ONBOARDING"
            conn.execute(
                f"""UPDATE enterprise_workspaces
                    SET {column}=?, legal_name=?, display_name=?, onboarding_step=?,
                        lifecycle=?, updated_at=? WHERE enterprise_id=? AND owner_subject_ref=?""",
                (encoded, legal_name, display_name, next_step, lifecycle, time.time(), enterprise_id, subject_ref),
            )
            return _get(conn, enterprise_id, subject_ref)  # type: ignore[return-value]

    def record_analysis(self, *, subject_ref: str, enterprise_id: str, item: dict[str, Any]) -> Enterprise:
        with _db() as conn:
            enterprise = _get(conn, enterprise_id, subject_ref)
            if not enterprise:
                raise HTTPException(status_code=404, detail="Enterprise workspace not found")
            analyses = [*enterprise.analysis, item]
            conn.execute(
                "UPDATE enterprise_workspaces SET analysis_json=?, updated_at=? WHERE enterprise_id=? AND owner_subject_ref=?",
                (json.dumps(analyses, ensure_ascii=False), time.time(), enterprise_id, subject_ref),
            )
            return _get(conn, enterprise_id, subject_ref)  # type: ignore[return-value]

    def dashboard(self, *, subject_ref: str, enterprise_id: str) -> dict[str, Any]:
        e = self.get(subject_ref=subject_ref, enterprise_id=enterprise_id)
        oc = e.operating_context
        return {
            "enterprise": {
                "id": e.enterprise_id,
                "name": e.display_name,
                "legal_name": e.legal_name or "UNKNOWN",
                "lifecycle": e.lifecycle,
                "onboarding_step": e.onboarding_step,
                "workspace_ref": e.workspace_ref,
            },
            "control": {
                "pilot_workload": e.pilot_workload or {"status": "UNKNOWN"},
                "operating_context": oc or {"status": "UNKNOWN"},
                "workstreams": e.workstreams,
                "members": e.members,
                "week_one": e.week_one,
            },
            "financial": {
                "currency": oc.get("currency", "UNKNOWN"),
                "budget_total": oc.get("budget_total", "UNKNOWN"),
                "allocations": oc.get("allocations", []),
                "committed": "UNKNOWN",
                "spent": "UNKNOWN",
                "remaining": "UNKNOWN",
            },
            "dashboard_config": e.dashboard_config,
            "ai_analysis": e.analysis,
            "truthfulness": {
                "rule": "Enterprise dashboard is a projection over governed enterprise context; it is not an authorization or execution boundary.",
                "unknown_policy": "UNKNOWN is preserved whenever the enterprise has not supplied or produced governed evidence.",
            },
        }


_MANAGER = EnterpriseManager()
router = APIRouter(
    prefix="/enterprise",
    tags=["SolSpire Enterprise"],
    dependencies=[Depends(require_auth)],
)


@router.post("/workspaces")
async def create_enterprise(body: dict[str, Any] | None = None, user: dict = Depends(require_auth)):
    body = body or {}
    enterprise = _MANAGER.create(
        subject_ref=user["uid"],
        display_name=str(body.get("display_name") or ""),
    )
    return {"enterprise": enterprise.to_dict(), "onboarding_steps": list(enumerate(STEP_NAMES, start=1))}


@router.get("/workspaces")
async def list_enterprises(user: dict = Depends(require_auth)):
    return {"enterprises": [e.to_dict() for e in _MANAGER.list(subject_ref=user["uid"])]}


@router.get("/workspaces/{enterprise_id}")
async def get_enterprise(enterprise_id: str, user: dict = Depends(require_auth)):
    return {"enterprise": _MANAGER.get(subject_ref=user["uid"], enterprise_id=enterprise_id).to_dict()}


@router.put("/workspaces/{enterprise_id}/steps/{step}")
async def save_enterprise_step(
    enterprise_id: str,
    step: int,
    body: StepPayload,
    user: dict = Depends(require_auth),
):
    enterprise = _MANAGER.save_step(
        subject_ref=user["uid"], enterprise_id=enterprise_id, step=step, data=body.data
    )
    return {"enterprise": enterprise.to_dict()}


@router.get("/workspaces/{enterprise_id}/dashboard")
async def get_enterprise_dashboard(enterprise_id: str, user: dict = Depends(require_auth)):
    return _MANAGER.dashboard(subject_ref=user["uid"], enterprise_id=enterprise_id)


@router.post("/workspaces/{enterprise_id}/analysis")
async def record_enterprise_analysis(
    enterprise_id: str,
    body: AnalysisPayload,
    user: dict = Depends(require_auth),
):
    # This route stores advisory analysis supplied by the existing Arkana/LLM
    # channel. It deliberately does not execute or authorize the recommendation.
    item = {
        "analysis_id": str(uuid.uuid4()),
        "step": body.step,
        "context": body.context,
        "status": "ADVISORY_INPUT",
        "created_at": time.time(),
    }
    enterprise = _MANAGER.record_analysis(
        subject_ref=user["uid"], enterprise_id=enterprise_id, item=item
    )
    return {"enterprise": enterprise.to_dict(), "analysis": item}


__all__ = ["router", "EnterpriseManager", "STEP_NAMES"]
