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

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.auth import require_auth, require_sovereign
from solspire.workspace_manager import get_workspace_manager
from solspire import eden_ops_02 as e02
from solspire.sovereign_field import (
    BUYER_STATUSES,
    create_buyer_candidate,
    ensure_field,
    list_buyer_recon,
    update_buyer_candidate,
)
from kernel.doc_extract import extract_text

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
        "CREATE INDEX IF NOT EXISTS idx_enterprise_owner ON enterprise_organizations(owner_subject_ref, updated_at)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_enterprise_workspace ON enterprise_organizations(workspace_ref)"
    )
    conn.execute("""
        CREATE TABLE IF NOT EXISTS enterprise_attachments (
            attachment_id TEXT PRIMARY KEY,
            enterprise_id TEXT NOT NULL,
            owner_subject_ref TEXT NOT NULL,
            original_name TEXT NOT NULL,
            stored_path TEXT NOT NULL,
            content_type TEXT NOT NULL DEFAULT 'application/octet-stream',
            size_bytes INTEGER NOT NULL DEFAULT 0,
            extracted_text TEXT NOT NULL DEFAULT '',
            extraction_status TEXT NOT NULL DEFAULT 'EXTRACTED',
            created_at REAL NOT NULL
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_enterprise_attachment_owner ON enterprise_attachments(enterprise_id, owner_subject_ref, created_at)"
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
        "SELECT * FROM enterprise_organizations WHERE enterprise_id=?",
        (enterprise_id,),
    ).fetchone()
    if not row:
        return None
    owner = row["owner_subject_ref"]
    if not e02.can_access_enterprise(
        enterprise_id=enterprise_id, caller_uid=subject_ref, owner_uid=owner
    ):
        return None
    return _decode(row)


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
                """INSERT INTO enterprise_organizations
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
                "SELECT * FROM enterprise_organizations ORDER BY updated_at DESC"
            ).fetchall()
        return [
            _decode(row)
            for row in rows
            if row["owner_subject_ref"] == subject_ref
            or e02.is_active_member(enterprise_id=row["enterprise_id"], uid=subject_ref)
        ]

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
            if enterprise.owner_subject_ref != subject_ref:
                raise HTTPException(status_code=403, detail="Owner only")
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
                f"""UPDATE enterprise_organizations
                    SET {column}=?, legal_name=?, display_name=?, onboarding_step=?,
                        lifecycle=?, updated_at=? WHERE enterprise_id=? AND owner_subject_ref=?""",
                (encoded, legal_name, display_name, next_step, lifecycle, time.time(), enterprise_id, subject_ref),
            )
            return _get(conn, enterprise_id, subject_ref)  # type: ignore[return-value]

    def instantiate_eden_food_systems(self, *, subject_ref: str) -> Enterprise:
        """Instantiate Eden Food Systems as the first real SolSpire enterprise pilot.

        Uses only existing enterprise columns (context, pilot_workload, workstreams,
        members, operating_context, week_one, dashboard_config). Does not create a
        parallel Eden database, shell, auth layer, or financial authority.
        Budget allocations are context, not committed/spent evidence.
        """
        enterprise = self.create(
            subject_ref=subject_ref,
            display_name="Eden Food Systems",
        )
        eid = enterprise.enterprise_id

        # Step 1 — enterprise identity / context
        enterprise = self.save_step(
            subject_ref=subject_ref,
            enterprise_id=eid,
            step=1,
            data={
                "display_name": "Eden Food Systems",
                "legal_name": "Eden Food Systems",
                "organization_type": "company",
                "stage": "early",
                "industry": "agriculture",
                "mission": (
                    "Move Eden from market intelligence into one controlled, measurable "
                    "commercial transaction while establishing the minimum repeatable "
                    "operating system."
                ),
                "template": "eden-food-systems-pilot-cycle-01",
            },
        )

        # Step 2 — pilot workload
        enterprise = self.save_step(
            subject_ref=subject_ref,
            enterprise_id=eid,
            step=2,
            data={
                "workload_id": "EDEN-PILOT-CYCLE-01",
                "title": "₦1m Controlled Food Systems Pilot — Cycle 01",
                "workload_type": "operations",
                "objective": (
                    "Source → Prepare → Market → Move → Sell → Reconcile → Learn "
                    "for one controlled commodity transaction."
                ),
                "duration_weeks": 4,
                "capital_ngn": 1_000_000,
                "commodity_universe": ["Irish Potato", "Dry Onion", "Cabbage"],
                "status": "READYING",
            },
        )

        # Step 3 — seven active workstreams (+ reserve as budget control note)
        workstreams = [
            {"id": "D01", "name": "Procurement & Commodity Operations", "budget_ngn": 500_000, "status": "UNASSIGNED"},
            {"id": "D02", "name": "Logistics & Distribution", "budget_ngn": 120_000, "status": "UNASSIGNED"},
            {"id": "D03", "name": "Packaging, Quality & Handling", "budget_ngn": 45_000, "status": "UNASSIGNED"},
            {"id": "D04", "name": "Marketing & Customer Acquisition", "budget_ngn": 75_000, "status": "UNASSIGNED"},
            {"id": "D05", "name": "Brand, Content & Customer Experience", "budget_ngn": 35_000, "status": "UNASSIGNED"},
            {"id": "D06", "name": "Digital Operations & Communications", "budget_ngn": 25_000, "status": "UNASSIGNED"},
            {"id": "D07", "name": "Operations Management & Finance", "budget_ngn": 130_000, "status": "UNASSIGNED"},
        ]
        # save_step expects dict for StepPayload path; store list under items + mirror
        # for dashboard consumers that expect an array at workstreams_json.
        with _db() as conn:
            conn.execute(
                "UPDATE enterprise_organizations SET workstreams_json=?, onboarding_step=?, updated_at=? "
                "WHERE enterprise_id=? AND owner_subject_ref=?",
                (
                    json.dumps(workstreams, ensure_ascii=False),
                    max(enterprise.onboarding_step, 3),
                    time.time(),
                    eid,
                    subject_ref,
                ),
            )
            enterprise = _get(conn, eid, subject_ref)  # type: ignore[assignment]

        # Step 4 — members: roles explicit; people UNASSIGNED until real humans bind
        members = [
            {"role": "Chief of Operations", "status": "UNASSIGNED", "workstream_ids": ["D07"]},
            {"role": "Procurement Lead", "status": "UNASSIGNED", "workstream_ids": ["D01"]},
            {"role": "Logistics Lead", "status": "UNASSIGNED", "workstream_ids": ["D02"]},
            {"role": "Quality & Handling Lead", "status": "UNASSIGNED", "workstream_ids": ["D03"]},
            {"role": "Marketing Lead", "status": "UNASSIGNED", "workstream_ids": ["D04"]},
            {"role": "Brand & CX Lead", "status": "UNASSIGNED", "workstream_ids": ["D05"]},
            {"role": "Digital Operations Lead", "status": "UNASSIGNED", "workstream_ids": ["D06"]},
            {"role": "Customer Care", "status": "UNASSIGNED", "workstream_ids": ["D07"]},
            {"role": "Finance / Records", "status": "UNASSIGNED", "workstream_ids": ["D07"]},
        ]
        with _db() as conn:
            conn.execute(
                "UPDATE enterprise_organizations SET members_json=?, onboarding_step=?, updated_at=? "
                "WHERE enterprise_id=? AND owner_subject_ref=?",
                (
                    json.dumps(members, ensure_ascii=False),
                    max(enterprise.onboarding_step, 4),
                    time.time(),
                    eid,
                    subject_ref,
                ),
            )
            enterprise = _get(conn, eid, subject_ref)  # type: ignore[assignment]

        # Step 5 — operating context (budget is allocation context, not spend evidence)
        enterprise = self.save_step(
            subject_ref=subject_ref,
            enterprise_id=eid,
            step=5,
            data={
                "currency": "NGN",
                "budget_total": 1_000_000,
                "allocations": [
                    {"name": "Procurement & Commodity Operations", "amount": 500_000},
                    {"name": "Logistics & Distribution", "amount": 120_000},
                    {"name": "Packaging, Quality & Handling", "amount": 45_000},
                    {"name": "Marketing & Customer Acquisition", "amount": 75_000},
                    {"name": "Brand, Content & Customer Experience", "amount": 35_000},
                    {"name": "Digital Operations & Communications", "amount": 25_000},
                    {"name": "Operations Management & Finance", "amount": 130_000},
                    {"name": "Contingency Reserve", "amount": 70_000},
                ],
                "contingency_reserve_ngn": 70_000,
                "duration_weeks": 4,
                "operating_model": "Source → Prepare → Market → Move → Sell → Reconcile → Learn",
                "commodity_universe": ["Irish Potato", "Dry Onion", "Cabbage"],
            },
        )

        # Step 6 — week 1 cadence
        enterprise = self.save_step(
            subject_ref=subject_ref,
            enterprise_id=eid,
            step=6,
            data={
                "week": 1,
                "theme": "BUILD THE OPERATING MACHINE",
                "days": {
                    "monday": [
                        "Confirm pilot objective",
                        "Confirm ₦1m budget map",
                        "Confirm seven workstreams",
                        "Assign available owners (else UNASSIGNED)",
                        "Review commodity intelligence",
                        "Define customer segments",
                        "Create digital operating workspace",
                    ],
                    "tuesday": [
                        "Supplier verification starts",
                        "Buyer mapping",
                        "Logistics quotations",
                        "Quality specifications",
                        "Brand foundation",
                    ],
                    "wednesday": [
                        "Supplier shortlist",
                        "Buyer shortlist",
                        "Marketing assets",
                        "WhatsApp structure",
                    ],
                    "thursday": ["Commercial reconciliation"],
                    "friday": ["Pilot readiness review (GREEN/AMBER/RED)"],
                },
            },
        )

        # Step 7 — dashboard projection config
        enterprise = self.save_step(
            subject_ref=subject_ref,
            enterprise_id=eid,
            step=7,
            data={
                "focus": ["workload", "workstreams", "budget", "objectives", "evidence"],
                "views": ["workload", "workstreams", "people", "budget", "objectives", "evidence"],
                "critical_path_fields": [
                    "commodity", "supplier", "buyer", "logistics", "quality", "marketing", "finance"
                ],
                "evidence_fields": ["work_events", "attachments", "unknowns"],
                "gates": {
                    "supplier": "UNKNOWN",
                    "buyer": "UNKNOWN",
                    "commodity": "UNKNOWN",
                    "logistics": "UNKNOWN",
                    "marketing": "UNKNOWN",
                    "finance": "UNKNOWN",
                },
            },
        )
        return enterprise

    def record_analysis(self, *, subject_ref: str, enterprise_id: str, item: dict[str, Any]) -> Enterprise:
        with _db() as conn:
            enterprise = _get(conn, enterprise_id, subject_ref)
            if not enterprise:
                raise HTTPException(status_code=404, detail="Enterprise workspace not found")
            if enterprise.owner_subject_ref != subject_ref:
                raise HTTPException(status_code=403, detail="Owner only")
            analyses = [*enterprise.analysis, item]
            conn.execute(
                "UPDATE enterprise_organizations SET analysis_json=?, updated_at=? WHERE enterprise_id=? AND owner_subject_ref=?",
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


@router.post("/workspaces/templates/eden-food-systems")
async def instantiate_eden_food_systems(user: dict = Depends(require_auth)):
    """Instantiate Eden Food Systems pilot on the authenticated subject.

    Solariun remains the personal canvas. This endpoint only creates a SolSpire
    enterprise instance owned by the caller. Product entitlement is not invented here.
    """
    enterprise = _MANAGER.instantiate_eden_food_systems(subject_ref=user["uid"])
    dashboard = _MANAGER.dashboard(subject_ref=user["uid"], enterprise_id=enterprise.enterprise_id)
    return {
        "enterprise": enterprise.to_dict(),
        "dashboard": dashboard,
        "template": "eden-food-systems-pilot-cycle-01",
        "boundary": {
            "solariun": "personal intelligence canvas — not the Eden office",
            "solspire": "enterprise operating console — Eden lives here",
            "financial": "budget allocations are context; committed/spent/remaining remain UNKNOWN without evidence",
            "authority": "identity and ownership are not execution authorization",
        },
    }


@router.get("/workspaces")
async def list_enterprises(user: dict = Depends(require_auth)):
    return {"enterprises": [e02.public_enterprise_payload(e.to_dict(), caller_uid=user["uid"]) for e in _MANAGER.list(subject_ref=user["uid"])]}


@router.get("/workspaces/{enterprise_id}")
async def get_enterprise(enterprise_id: str, user: dict = Depends(require_auth)):
    enterprise = _MANAGER.get(subject_ref=user["uid"], enterprise_id=enterprise_id)
    return {"enterprise": e02.public_enterprise_payload(enterprise.to_dict(), caller_uid=user["uid"])}


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
    dashboard = _MANAGER.dashboard(subject_ref=user["uid"], enterprise_id=enterprise_id)
    if e02.owner_uid_for_enterprise(enterprise_id=enterprise_id) != user["uid"]:
        dashboard["control"]["members"] = [m.to_dict() for m in e02.list_members_public(enterprise_id=enterprise_id)]
        dashboard.pop("ai_analysis", None)
    return dashboard


@router.get("/sovereign-field")
async def get_sovereign_field(user: dict = Depends(require_sovereign)):
    """Resolve the persistent sovereign field for this authenticated sovereign."""
    field = ensure_field(user["uid"])
    return {
        "field": field,
        "buyer_recon": list_buyer_recon(user["uid"]),
        "status_lanes": list(BUYER_STATUSES),
        "truthfulness": {
            "identity": "Firebase uid is the canonical subject boundary.",
            "authority": "Sovereign access permits this field; it does not authorize transactions.",
            "unknown_policy": "Unverified commercial facts remain UNKNOWN.",
        },
    }


@router.post("/sovereign-field/buyer-recon")
async def add_sovereign_buyer_candidate(body: dict[str, Any], user: dict = Depends(require_sovereign)):
    try:
        candidate = create_buyer_candidate(user["uid"], body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"candidate": candidate}


@router.patch("/sovereign-field/buyer-recon/{candidate_id}")
async def edit_sovereign_buyer_candidate(
    candidate_id: str,
    body: dict[str, Any],
    user: dict = Depends(require_sovereign),
):
    try:
        candidate = update_buyer_candidate(user["uid"], candidate_id, body)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"candidate": candidate}


@router.get("/workspaces/{enterprise_id}/attachments")
async def list_enterprise_attachments(enterprise_id: str, user: dict = Depends(require_auth)):
    enterprise = _MANAGER.get(subject_ref=user["uid"], enterprise_id=enterprise_id)
    if enterprise.owner_subject_ref != user["uid"]:
        raise HTTPException(status_code=403, detail="Owner only")
    with _db() as conn:
        rows = conn.execute(
            """SELECT attachment_id, original_name, content_type, size_bytes,
                      extraction_status, extracted_text, created_at
               FROM enterprise_attachments
               WHERE enterprise_id=? AND owner_subject_ref=?
               ORDER BY created_at DESC""",
            (enterprise_id, user["uid"]),
        ).fetchall()
    return {"attachments": [dict(row) for row in rows]}


@router.post("/workspaces/{enterprise_id}/attachments")
async def upload_enterprise_attachment(
    enterprise_id: str,
    request: Request,
    user: dict = Depends(require_auth),
):
    enterprise = _MANAGER.get(subject_ref=user["uid"], enterprise_id=enterprise_id)
    if enterprise.owner_subject_ref != user["uid"]:
        raise HTTPException(status_code=403, detail="Owner only")
    form = await request.form()
    upload = form.get("file")
    if upload is None or not hasattr(upload, "filename"):
        raise HTTPException(status_code=400, detail="Attach a file using the 'file' field")
    raw = await upload.read()
    if not raw:
        raise HTTPException(status_code=400, detail="The attached file is empty")
    if len(raw) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Enterprise attachments are limited to 50 MB per file")

    filename = os.path.basename(str(upload.filename or "attachment"))
    attachment_id = str(uuid.uuid4())
    attachment_dir = os.path.join(
        os.environ.get("SOLSPIRE_DATA_DIR", "data"),
        "enterprise_attachments",
        enterprise_id,
    )
    os.makedirs(attachment_dir, exist_ok=True)
    stored_path = os.path.join(attachment_dir, attachment_id)
    with open(stored_path, "wb") as handle:
        handle.write(raw)

    extracted, detected_type = extract_text(filename, raw)
    content_type = str(getattr(upload, "content_type", None) or detected_type or "application/octet-stream")
    extraction_status = "EXTRACTED" if extracted and not extracted.startswith("[") else "BINARY_OR_PARTIAL"

    with _db() as conn:
        conn.execute(
            """INSERT INTO enterprise_attachments
               (attachment_id, enterprise_id, owner_subject_ref, original_name,
                stored_path, content_type, size_bytes, extracted_text,
                extraction_status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                attachment_id, enterprise_id, user["uid"], filename, stored_path,
                content_type, len(raw), extracted[:120000], extraction_status, time.time()
            ),
        )

    return {
        "attachment": {
            "attachment_id": attachment_id,
            "original_name": filename,
            "content_type": content_type,
            "size_bytes": len(raw),
            "extraction_status": extraction_status,
            "extracted_text": extracted[:120000],
        }
    }


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


from solspire.eden_ops_02_routes import register_eden_ops_02_routes
register_eden_ops_02_routes(router)

__all__ = ["router", "EnterpriseManager", "STEP_NAMES"]
