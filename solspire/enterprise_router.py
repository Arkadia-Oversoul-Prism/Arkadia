"""Bounded Eden enterprise workspace and master-dashboard projection.

This module composes the existing authenticated SolSpire workspace, workload,
WorkEvent, Pulse and Synthesis surfaces into one tenant/workspace projection.
It is not a new authority, provenance, execution, or sovereign identity path.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any

from api.auth import require_sovereign
from fastapi import APIRouter, Depends, HTTPException

from solspire.workspace_manager import get_workspace_manager
from solspire.workload_manager import get_workload_manager
from solspire.pulse_manager import get_pulse_manager
from solspire.synthesis_manager import get_synthesis_manager

_DB_PATH = os.environ.get("SOLSPIRE_PROJECTS_DB") or os.path.join(
    os.environ.get("SOLSPIRE_DATA_DIR", "data"), "solspire_projects.db"
)

WORKSTREAMS = (
    ("procurement", "Procurement & Commodity Operations", 500_000),
    ("logistics", "Logistics & Distribution", 120_000),
    ("quality", "Packaging, Quality & Handling", 45_000),
    ("marketing", "Marketing & Customer Acquisition", 75_000),
    ("brand", "Brand, Content & Customer Experience", 35_000),
    ("digital", "Digital Operations & Communications", 25_000),
    ("operations", "Operations Management & Finance", 130_000),
    ("reserve", "Contingency / Reserve", 70_000),
)

WEEK1_TASKS = (
    ("monday", "COO / Pilot Director", "Confirm pilot objective, ₦1m budget, departments, leads, and master dashboard."),
    ("monday", "Procurement & Commodity Operations", "Review commodity intelligence and shortlist commodities."),
    ("monday", "Marketing & Customer Acquisition", "Define customer segments."),
    ("monday", "Digital Operations & Communications", "Create the operating workspace."),
    ("tuesday", "Procurement & Commodity Operations", "Run supplier calls and capture current prices."),
    ("tuesday", "Logistics & Distribution", "Map routes and obtain transport quotes."),
    ("tuesday", "Packaging, Quality & Handling", "Define commodity specification and handling requirements."),
    ("tuesday", "Marketing & Customer Acquisition", "Map customers and buyers."),
    ("tuesday", "Brand, Content & Customer Experience", "Prepare first brand/customer-facing assets."),
    ("wednesday", "Procurement & Commodity Operations", "Produce supplier shortlist."),
    ("wednesday", "Marketing & Customer Acquisition", "Produce buyer shortlist."),
    ("wednesday", "Brand, Content & Customer Experience", "Prepare first campaign assets."),
    ("wednesday", "Digital Operations & Communications", "Establish WhatsApp operating structure."),
    ("thursday", "Operations Management & Finance", "Reconcile supplier price, buyer price, quantity, logistics, packaging, marketing, and operating cost."),
    ("friday", "COO / Pilot Director", "Run pilot readiness review: GREEN / AMBER / RED."),
    ("saturday", "COO / Pilot Director", "Resolve red readiness items and confirm the critical path."),
    ("sunday", "COO / Pilot Director", "Review the critical path and prepare the next operating week."),
)

@dataclass(frozen=True)
class EnterpriseWorkspace:
    enterprise_id: str
    workspace_ref: str
    tenant_type: str
    tenant_name: str
    display_name: str
    product_tier: str
    product_role: str
    authority_effect: str
    status: str
    budget_total: int
    created_at: float
    updated_at: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def _db() -> sqlite3.Connection:
    directory = os.path.dirname(_DB_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS enterprise_workspaces (
            enterprise_id TEXT PRIMARY KEY,
            workspace_ref TEXT NOT NULL UNIQUE,
            tenant_type TEXT NOT NULL,
            tenant_name TEXT NOT NULL,
            display_name TEXT NOT NULL,
            product_tier TEXT NOT NULL,
            product_role TEXT NOT NULL,
            authority_effect TEXT NOT NULL,
            status TEXT NOT NULL,
            budget_total INTEGER NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS enterprise_workstreams (
            workstream_id TEXT PRIMARY KEY,
            enterprise_id TEXT NOT NULL,
            slug TEXT NOT NULL,
            name TEXT NOT NULL,
            budget INTEGER NOT NULL,
            status TEXT NOT NULL,
            UNIQUE(enterprise_id, slug)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS enterprise_tasks (
            task_id TEXT PRIMARY KEY,
            enterprise_id TEXT NOT NULL,
            workstream_id TEXT,
            day TEXT NOT NULL,
            owner_role TEXT NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL,
            evidence_refs TEXT NOT NULL DEFAULT '[]',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_enterprise_tasks ON enterprise_tasks(enterprise_id, day, status)")
    conn.commit()
    return conn

def _workspace(row: sqlite3.Row) -> EnterpriseWorkspace:
    return EnterpriseWorkspace(
        enterprise_id=row["enterprise_id"], workspace_ref=row["workspace_ref"],
        tenant_type=row["tenant_type"], tenant_name=row["tenant_name"],
        display_name=row["display_name"], product_tier=row["product_tier"],
        product_role=row["product_role"], authority_effect=row["authority_effect"],
        status=row["status"], budget_total=int(row["budget_total"]),
        created_at=float(row["created_at"]), updated_at=float(row["updated_at"]),
    )

class EdenEnterpriseManager:
    def bootstrap(self, *, subject_ref: str) -> dict[str, Any]:
        ws = get_workspace_manager().get_or_create(
            subject_ref, display_name="Eden Food Systems Enterprise Workspace"
        )
        now = time.time()
        conn = _db()
        try:
            row = conn.execute(
                "SELECT * FROM enterprise_workspaces WHERE workspace_ref=?", (ws.id,)
            ).fetchone()
            if row is None:
                enterprise_id = str(uuid.uuid4())
                conn.execute(
                    """INSERT INTO enterprise_workspaces
                    (enterprise_id, workspace_ref, tenant_type, tenant_name, display_name,
                     product_tier, product_role, authority_effect, status, budget_total, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (enterprise_id, ws.id, "tenant", "Eden Food Systems",
                     "Eden Food Systems Enterprise Workspace", "ENTERPRISE",
                     "SOVEREIGN_ACCESS_PRODUCT_ROLE",
                     "DESCRIPTIVE_ONLY__DOES_NOT_AUTHORIZE_MUTATION",
                     "ACTIVE", 1_000_000, now, now),
                )
            else:
                enterprise_id = row["enterprise_id"]

            for slug, name, budget in WORKSTREAMS:
                conn.execute(
                    """INSERT OR IGNORE INTO enterprise_workstreams
                    (workstream_id, enterprise_id, slug, name, budget, status)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (str(uuid.uuid5(uuid.NAMESPACE_URL, f"arkadia:{enterprise_id}:{slug}")),
                     enterprise_id, slug, name, budget, "NOT_STARTED"),
                )

            ids = {
                r["name"]: r["workstream_id"]
                for r in conn.execute(
                    "SELECT name, workstream_id FROM enterprise_workstreams WHERE enterprise_id=?",
                    (enterprise_id,),
                ).fetchall()
            }
            existing = conn.execute(
                "SELECT COUNT(*) AS count FROM enterprise_tasks WHERE enterprise_id=?", (enterprise_id,)
            ).fetchone()["count"]
            if int(existing) == 0:
                for day, owner, title in WEEK1_TASKS:
                    ws_id = ids.get(owner)
                    if ws_id is None and owner == "COO / Pilot Director":
                        ws_id = ids["Operations Management & Finance"]
                    conn.execute(
                        """INSERT INTO enterprise_tasks
                        (task_id, enterprise_id, workstream_id, day, owner_role, title, status, evidence_refs, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, '[]', ?, ?)""",
                        (str(uuid.uuid4()), enterprise_id, ws_id, day, owner, title, "NOT_STARTED", now, now),
                    )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM enterprise_workspaces WHERE enterprise_id=?", (enterprise_id,)
            ).fetchone()
            return {"workspace": _workspace(row).to_dict(), "workspace_ref": ws.id}
        finally:
            conn.close()

    def dashboard(self, *, subject_ref: str) -> dict[str, Any]:
        ws = get_workspace_manager().get_for_subject(subject_ref)
        if ws is None:
            raise HTTPException(status_code=409, detail="Canonical SolSpire workspace not found")
        conn = _db()
        try:
            enterprise = conn.execute(
                "SELECT * FROM enterprise_workspaces WHERE workspace_ref=?", (ws.id,)
            ).fetchone()
            if enterprise is None:
                raise HTTPException(status_code=404, detail="Eden enterprise workspace not provisioned")
            eid = enterprise["enterprise_id"]
            workstreams = conn.execute(
                "SELECT slug, name, budget, status FROM enterprise_workstreams WHERE enterprise_id=? ORDER BY rowid",
                (eid,),
            ).fetchall()
            tasks = conn.execute(
                "SELECT task_id, day, owner_role, title, status, evidence_refs FROM enterprise_tasks WHERE enterprise_id=? ORDER BY rowid",
                (eid,),
            ).fetchall()
        finally:
            conn.close()

        workload = get_workload_manager().get_for_subject(subject_ref, ws.id)
        pulse = get_pulse_manager().get_for_subject_date(
            subject_ref, ws.id, __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%d")
        )
        synthesis = get_synthesis_manager().get_current_week(subject_ref, ws.id)

        task_rows = []
        for row in tasks:
            task_rows.append({
                "task_id": row["task_id"], "day": row["day"], "owner_role": row["owner_role"],
                "title": row["title"], "status": row["status"],
                "evidence_refs": json.loads(row["evidence_refs"] or "[]"),
            })

        def value(label: str, data: Any, source: str | None = None) -> dict[str, Any]:
            if data is None or data == "":
                return {"label": label, "value": "UNKNOWN", "epistemic_status": "UNKNOWN", "source": source}
            return {"label": label, "value": data, "epistemic_status": "RECORDED", "source": source}

        dashboard = {
            "product": {
                "name": "Eden Food Systems",
                "surface": "SolSpire Enterprise Workspace",
                "tier": enterprise["product_tier"],
                "role": enterprise["product_role"],
                "authority_effect": enterprise["authority_effect"],
            },
            "commercial": [
                value("Commodity", None),
                value("Source", None),
                value("Destination", None),
                value("Buyer", None),
                value("Quantity", None),
                value("Buy price", None),
                value("Sell price", None),
            ],
            "money": [
                value("Opening capital", 1_000_000, "CAL-10: Eden pilot budget"),
                value("Committed", None),
                value("Spent", None),
                value("Remaining", None),
                value("Revenue", None),
                value("Recovered", None),
                value("Contribution", None),
            ],
            "operations": {
                "workstreams": [dict(r) for r in workstreams],
                "week1_tasks": task_rows,
            },
            "transaction": [
                value("Procurement", None),
                value("Loading", None),
                value("In transit", None),
                value("Delivered", None),
                value("Accepted", None),
                value("Paid", None),
                value("Reconciled", None),
            ],
            "critical_path": [
                value("Current phase", "1 · Commercial Confirmation", "CAL-10: Eden pilot phase clock"),
                value("Next decision", "Confirm a viable transaction candidate"),
                value("Blockers", None),
            ],
            "evidence": {
                "workspace": {"status": "RECORDED", "source": "SolSpire canonical workspace"},
                "workload": workload.to_dict() if workload else {"status": "UNKNOWN", "source": "SolSpire canonical workload"},
                "daily_pulse": pulse.to_dict() if pulse else {"status": "UNKNOWN", "source": "SolSpire Daily Pulse"},
                "weekly_synthesis": synthesis.to_dict() if synthesis else {"status": "UNKNOWN", "source": "SolSpire Weekly Synthesis"},
            },
            "truthfulness": {
                "rule": "Dashboard is a projection over governed objects. It does not authorize execution.",
                "unknown_policy": "UNKNOWN is preserved when no governed source exists.",
            },
        }
        return dashboard

    def get_for_subject(self, subject_ref: str) -> EnterpriseWorkspace | None:
        ws = get_workspace_manager().get_for_subject(subject_ref)
        if ws is None:
            return None
        conn = _db()
        try:
            row = conn.execute(
                "SELECT * FROM enterprise_workspaces WHERE workspace_ref=?", (ws.id,)
            ).fetchone()
        finally:
            conn.close()
        return _workspace(row) if row else None

_MANAGER = EdenEnterpriseManager()
router = APIRouter(
    prefix="/enterprise",
    tags=["SolSpire Enterprise"],
    dependencies=[Depends(require_sovereign)],
)

@router.post("/eden/bootstrap")
async def bootstrap_eden(user: dict = Depends(require_sovereign)) -> dict[str, Any]:
    return _MANAGER.bootstrap(subject_ref=user["uid"])

@router.get("/eden")
async def get_eden_workspace(user: dict = Depends(require_sovereign)) -> dict[str, Any]:
    workspace = _MANAGER.get_for_subject(user["uid"])
    if workspace is None:
        raise HTTPException(status_code=404, detail="Eden enterprise workspace not provisioned")
    return {"workspace": workspace.to_dict()}

@router.get("/eden/dashboard")
async def get_eden_dashboard(user: dict = Depends(require_sovereign)) -> dict[str, Any]:
    return _MANAGER.dashboard(subject_ref=user["uid"])

__all__ = ["router", "EdenEnterpriseManager"]
