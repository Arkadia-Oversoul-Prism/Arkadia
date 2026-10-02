"""Persistent sovereign field for the authenticated Arkadia sovereign.

This is a durable projection/configuration surface bound to the Firebase subject.
It is not a second identity system, graph authority, provenance store, or execution
path. The field is created idempotently whenever a sovereign session resolves it.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from typing import Any

from solspire.workspace_manager import get_workspace_manager

_DB_PATH = os.environ.get("SOLSPIRE_PROJECTS_DB") or os.path.join(
    os.environ.get("SOLSPIRE_DATA_DIR", "data"), "solspire_projects.db"
)

FIELD_SCHEMA_VERSION = 1
BUYER_STATUSES = (
    "UNCONTACTED",
    "CONTACTED",
    "CONVERSATION",
    "REQUIREMENT_CAPTURED",
    "PRICE_CONFIRMED",
    "BUYER_COMMITMENT",
    "SUPPLIER_CONFIRMED",
    "ECONOMICS_CLOSED",
    "READY_TO_EXECUTE",
    "EXECUTED",
    "SETTLED",
)


def _db() -> sqlite3.Connection:
    directory = os.path.dirname(_DB_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sovereign_fields (
            field_id TEXT PRIMARY KEY,
            subject_ref TEXT NOT NULL UNIQUE,
            workspace_ref TEXT NOT NULL,
            schema_version INTEGER NOT NULL,
            field_kind TEXT NOT NULL,
            surfaces_json TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sovereign_buyer_recon (
            candidate_id TEXT PRIMARY KEY,
            field_id TEXT NOT NULL,
            enterprise_id TEXT,
            prospect TEXT NOT NULL,
            location TEXT NOT NULL DEFAULT 'UNKNOWN',
            buyer_type TEXT NOT NULL DEFAULT 'UNKNOWN',
            contact_route TEXT NOT NULL DEFAULT 'UNKNOWN',
            commodity TEXT NOT NULL DEFAULT 'UNKNOWN',
            estimated_demand TEXT NOT NULL DEFAULT 'UNKNOWN',
            procurement_frequency TEXT NOT NULL DEFAULT 'UNKNOWN',
            decision_maker TEXT NOT NULL DEFAULT 'UNKNOWN',
            current_price TEXT NOT NULL DEFAULT 'UNKNOWN',
            quantity TEXT NOT NULL DEFAULT 'UNKNOWN',
            specification TEXT NOT NULL DEFAULT 'UNKNOWN',
            delivery_point TEXT NOT NULL DEFAULT 'UNKNOWN',
            delivery_window TEXT NOT NULL DEFAULT 'UNKNOWN',
            payment_terms TEXT NOT NULL DEFAULT 'UNKNOWN',
            supplier TEXT NOT NULL DEFAULT 'UNKNOWN',
            source_price TEXT NOT NULL DEFAULT 'UNKNOWN',
            available_quantity TEXT NOT NULL DEFAULT 'UNKNOWN',
            logistics_quote TEXT NOT NULL DEFAULT 'UNKNOWN',
            landed_cost TEXT NOT NULL DEFAULT 'UNKNOWN',
            buyer_price TEXT NOT NULL DEFAULT 'UNKNOWN',
            expected_gross_margin TEXT NOT NULL DEFAULT 'UNKNOWN',
            capital_required TEXT NOT NULL DEFAULT 'UNKNOWN',
            evidence_status TEXT NOT NULL DEFAULT 'UNKNOWN',
            status TEXT NOT NULL DEFAULT 'UNCONTACTED',
            why_this_prospect TEXT NOT NULL DEFAULT 'UNKNOWN',
            notes TEXT NOT NULL DEFAULT '',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            FOREIGN KEY(field_id) REFERENCES sovereign_fields(field_id)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_sovereign_buyer_field ON sovereign_buyer_recon(field_id, updated_at)"
    )
    conn.commit()
    return conn


def ensure_field(subject_ref: str) -> dict[str, Any]:
    subject_ref = (subject_ref or "").strip()
    if not subject_ref:
        raise ValueError("Canonical subject reference must not be empty")

    workspace = get_workspace_manager().get_or_create(
        subject_ref, display_name="SolSpire Sovereign Workspace"
    )
    now = time.time()
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM sovereign_fields WHERE subject_ref=?",
            (subject_ref,),
        ).fetchone()
        if row:
            return _decode_field(row)

        field = {
            "field_id": str(uuid.uuid4()),
            "subject_ref": subject_ref,
            "workspace_ref": workspace.id,
            "schema_version": FIELD_SCHEMA_VERSION,
            "field_kind": "SOVEREIGN_HIDDEN_OS",
            "surfaces": {
                "buyer_recon": {
                    "enabled": True,
                    "status_lanes": list(BUYER_STATUSES),
                    "purpose": "Demand discovery and transaction acquisition before commercial confirmation.",
                },
                "enterprise_dashboard": {
                    "projection": True,
                    "authorization": False,
                    "execution": False,
                },
            },
            "created_at": now,
            "updated_at": now,
        }
        conn.execute(
            """
            INSERT INTO sovereign_fields
            (field_id, subject_ref, workspace_ref, schema_version, field_kind,
             surfaces_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                field["field_id"], subject_ref, workspace.id, FIELD_SCHEMA_VERSION,
                field["field_kind"], json.dumps(field["surfaces"], ensure_ascii=False),
                now, now,
            ),
        )
        return field


def _decode_field(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "field_id": row["field_id"],
        "subject_ref": row["subject_ref"],
        "workspace_ref": row["workspace_ref"],
        "schema_version": int(row["schema_version"]),
        "field_kind": row["field_kind"],
        "surfaces": json.loads(row["surfaces_json"] or "{}"),
        "created_at": float(row["created_at"]),
        "updated_at": float(row["updated_at"]),
    }


def list_buyer_recon(subject_ref: str) -> list[dict[str, Any]]:
    field = ensure_field(subject_ref)
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM sovereign_buyer_recon WHERE field_id=? ORDER BY updated_at DESC",
            (field["field_id"],),
        ).fetchall()
    return [dict(row) for row in rows]


def create_buyer_candidate(subject_ref: str, data: dict[str, Any]) -> dict[str, Any]:
    field = ensure_field(subject_ref)
    prospect = str(data.get("prospect") or "").strip()
    if not prospect:
        raise ValueError("prospect is required")

    candidate_id = str(uuid.uuid4())
    now = time.time()
    allowed = {
        "enterprise_id", "location", "buyer_type", "contact_route", "commodity",
        "estimated_demand", "procurement_frequency", "decision_maker",
        "current_price", "quantity", "specification", "delivery_point",
        "delivery_window", "payment_terms", "supplier", "source_price",
        "available_quantity", "logistics_quote", "landed_cost", "buyer_price",
        "expected_gross_margin", "capital_required", "evidence_status",
        "status", "why_this_prospect", "notes",
    }
    values = {key: str(data.get(key) or "UNKNOWN") for key in allowed}
    values["enterprise_id"] = data.get("enterprise_id")
    values["status"] = values["status"] if values["status"] in BUYER_STATUSES else "UNCONTACTED"

    columns = ["candidate_id", "field_id", "prospect", *values.keys(), "created_at", "updated_at"]
    params = [candidate_id, field["field_id"], prospect, *values.values(), now, now]
    placeholders = ",".join("?" for _ in columns)
    with _db() as conn:
        conn.execute(
            f"INSERT INTO sovereign_buyer_recon ({','.join(columns)}) VALUES ({placeholders})",
            params,
        )
        row = conn.execute(
            "SELECT * FROM sovereign_buyer_recon WHERE candidate_id=? AND field_id=?",
            (candidate_id, field["field_id"]),
        ).fetchone()
    return dict(row)


def update_buyer_candidate(subject_ref: str, candidate_id: str, data: dict[str, Any]) -> dict[str, Any]:
    field = ensure_field(subject_ref)
    allowed = {
        "enterprise_id", "location", "buyer_type", "contact_route", "commodity",
        "estimated_demand", "procurement_frequency", "decision_maker",
        "current_price", "quantity", "specification", "delivery_point",
        "delivery_window", "payment_terms", "supplier", "source_price",
        "available_quantity", "logistics_quote", "landed_cost", "buyer_price",
        "expected_gross_margin", "capital_required", "evidence_status",
        "status", "why_this_prospect", "notes",
    }
    updates = {key: data[key] for key in data if key in allowed}
    if "status" in updates and updates["status"] not in BUYER_STATUSES:
        raise ValueError("Invalid buyer recon status")
    if not updates:
        raise ValueError("No mutable buyer recon fields supplied")
    updates["updated_at"] = time.time()

    assignments = ", ".join(f"{key}=?" for key in updates)
    params = [updates[key] for key in updates]
    params.extend([candidate_id, field["field_id"]])
    with _db() as conn:
        cur = conn.execute(
            f"UPDATE sovereign_buyer_recon SET {assignments} WHERE candidate_id=? AND field_id=?",
            params,
        )
        if cur.rowcount != 1:
            raise KeyError("Buyer recon candidate not found")
        row = conn.execute(
            "SELECT * FROM sovereign_buyer_recon WHERE candidate_id=? AND field_id=?",
            (candidate_id, field["field_id"]),
        ).fetchone()
    return dict(row)


__all__ = [
    "BUYER_STATUSES",
    "ensure_field",
    "list_buyer_recon",
    "create_buyer_candidate",
    "update_buyer_candidate",
]
