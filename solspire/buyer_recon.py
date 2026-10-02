"""Persistent Buyer Recon Board bound to the canonical SolSpire workspace.

This is the upstream demand-discovery substrate for Eden Food Systems.
It is not a CRM, authority layer, or execution path. Every board is owned by
the authenticated Firebase subject through the canonical workspace.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any

_DB_PATH = os.environ.get("SOLSPIRE_PROJECTS_DB") or os.path.join(
    os.environ.get("SOLSPIRE_DATA_DIR", "data"), "solspire_projects.db"
)

STATUSES = (
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


@dataclass(frozen=True)
class BuyerReconBoard:
    id: str
    workspace_ref: str
    subject_ref: str
    board_type: str
    display_name: str
    lifecycle: str
    created_at: float
    updated_at: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BuyerReconEntry:
    id: str
    board_id: str
    subject_ref: str
    prospect: str
    location: str
    buyer_type: str
    contact_route: str
    commodity: str
    estimated_demand: str
    procurement_frequency: str
    decision_maker: str
    current_price: str
    quantity: str
    specification: str
    delivery_point: str
    delivery_window: str
    payment_terms: str
    supplier: str
    source_price: str
    available_quantity: str
    logistics_quote: str
    packaging_qc_cost: str
    landed_cost: str
    buyer_price: str
    expected_gross_margin: str
    capital_required: str
    evidence_status: str
    evidence: list[dict[str, Any]]
    why_this_prospect: str
    status: str
    notes: str
    created_at: float
    updated_at: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _db() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS buyer_recon_boards (
            id TEXT PRIMARY KEY,
            workspace_ref TEXT NOT NULL UNIQUE,
            subject_ref TEXT NOT NULL UNIQUE,
            board_type TEXT NOT NULL,
            display_name TEXT NOT NULL,
            lifecycle TEXT NOT NULL DEFAULT 'active',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS buyer_recon_entries (
            id TEXT PRIMARY KEY,
            board_id TEXT NOT NULL,
            subject_ref TEXT NOT NULL,
            prospect TEXT NOT NULL,
            location TEXT NOT NULL DEFAULT '',
            buyer_type TEXT NOT NULL DEFAULT '',
            contact_route TEXT NOT NULL DEFAULT '',
            commodity TEXT NOT NULL DEFAULT '',
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
            packaging_qc_cost TEXT NOT NULL DEFAULT 'UNKNOWN',
            landed_cost TEXT NOT NULL DEFAULT 'UNKNOWN',
            buyer_price TEXT NOT NULL DEFAULT 'UNKNOWN',
            expected_gross_margin TEXT NOT NULL DEFAULT 'UNKNOWN',
            capital_required TEXT NOT NULL DEFAULT 'UNKNOWN',
            evidence_status TEXT NOT NULL DEFAULT 'NONE',
            evidence_json TEXT NOT NULL DEFAULT '[]',
            why_this_prospect TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'UNCONTACTED',
            notes TEXT NOT NULL DEFAULT '',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            FOREIGN KEY(board_id) REFERENCES buyer_recon_boards(id)
        )
        """
    )
    conn.commit()
    return conn


class BuyerReconManager:
    def get_or_create(self, workspace_ref: str, subject_ref: str) -> BuyerReconBoard:
        if not workspace_ref or not subject_ref:
            raise ValueError("Workspace and subject references are required")
        with _db() as conn:
            row = conn.execute(
                "SELECT * FROM buyer_recon_boards WHERE workspace_ref=? AND subject_ref=?",
                (workspace_ref, subject_ref),
            ).fetchone()
            if row:
                return self._board(row)
            now = time.time()
            board = BuyerReconBoard(
                id=str(uuid.uuid4()),
                workspace_ref=workspace_ref,
                subject_ref=subject_ref,
                board_type="eden_buyer_recon",
                display_name="Eden Buyer Recon",
                lifecycle="active",
                created_at=now,
                updated_at=now,
            )
            conn.execute(
                """INSERT INTO buyer_recon_boards
                (id,workspace_ref,subject_ref,board_type,display_name,lifecycle,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?)""",
                (board.id, board.workspace_ref, board.subject_ref, board.board_type,
                 board.display_name, board.lifecycle, board.created_at, board.updated_at),
            )
            return board

    def list_entries(self, board_id: str, subject_ref: str) -> list[BuyerReconEntry]:
        with _db() as conn:
            rows = conn.execute(
                "SELECT * FROM buyer_recon_entries WHERE board_id=? AND subject_ref=? ORDER BY updated_at DESC",
                (board_id, subject_ref),
            ).fetchall()
        return [self._entry(row) for row in rows]

    def create_entry(self, board: BuyerReconBoard, data: dict[str, Any]) -> BuyerReconEntry:
        prospect = str(data.get("prospect") or "").strip()
        if not prospect:
            raise ValueError("prospect is required")
        status = str(data.get("status") or "UNCONTACTED").strip().upper()
        if status not in STATUSES:
            raise ValueError("invalid status")
        now = time.time()
        entry = BuyerReconEntry(
            id=str(uuid.uuid4()), board_id=board.id, subject_ref=board.subject_ref,
            prospect=prospect, location=str(data.get("location") or ""),
            buyer_type=str(data.get("buyer_type") or ""), contact_route=str(data.get("contact_route") or ""),
            commodity=str(data.get("commodity") or ""), estimated_demand=str(data.get("estimated_demand") or "UNKNOWN"),
            procurement_frequency=str(data.get("procurement_frequency") or "UNKNOWN"),
            decision_maker=str(data.get("decision_maker") or "UNKNOWN"), current_price=str(data.get("current_price") or "UNKNOWN"),
            quantity=str(data.get("quantity") or "UNKNOWN"), specification=str(data.get("specification") or "UNKNOWN"),
            delivery_point=str(data.get("delivery_point") or "UNKNOWN"), delivery_window=str(data.get("delivery_window") or "UNKNOWN"),
            payment_terms=str(data.get("payment_terms") or "UNKNOWN"), supplier=str(data.get("supplier") or "UNKNOWN"),
            source_price=str(data.get("source_price") or "UNKNOWN"), available_quantity=str(data.get("available_quantity") or "UNKNOWN"),
            logistics_quote=str(data.get("logistics_quote") or "UNKNOWN"), packaging_qc_cost=str(data.get("packaging_qc_cost") or "UNKNOWN"),
            landed_cost=str(data.get("landed_cost") or "UNKNOWN"), buyer_price=str(data.get("buyer_price") or "UNKNOWN"),
            expected_gross_margin=str(data.get("expected_gross_margin") or "UNKNOWN"), capital_required=str(data.get("capital_required") or "UNKNOWN"),
            evidence_status=str(data.get("evidence_status") or "NONE"), evidence=list(data.get("evidence") or []),
            why_this_prospect=str(data.get("why_this_prospect") or ""), status=status, notes=str(data.get("notes") or ""),
            created_at=now, updated_at=now,
        )
        with _db() as conn:
            conn.execute(
                """INSERT INTO buyer_recon_entries
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (entry.id,entry.board_id,entry.subject_ref,entry.prospect,entry.location,entry.buyer_type,
                 entry.contact_route,entry.commodity,entry.estimated_demand,entry.procurement_frequency,
                 entry.decision_maker,entry.current_price,entry.quantity,entry.specification,entry.delivery_point,
                 entry.delivery_window,entry.payment_terms,entry.supplier,entry.source_price,entry.available_quantity,
                 entry.logistics_quote,entry.packaging_qc_cost,entry.landed_cost,entry.buyer_price,
                 entry.expected_gross_margin,entry.capital_required,entry.evidence_status,json.dumps(entry.evidence),
                 entry.why_this_prospect,entry.status,entry.notes,entry.created_at,entry.updated_at),
            )
        return entry

    def update_entry(self, entry_id: str, subject_ref: str, patch: dict[str, Any]) -> BuyerReconEntry:
        allowed = set(BuyerReconEntry.__dataclass_fields__) - {"id","board_id","subject_ref","created_at","updated_at","evidence"}
        status = patch.get("status")
        if status is not None:
            status = str(status).upper()
            if status not in STATUSES:
                raise ValueError("invalid status")
        with _db() as conn:
            row = conn.execute("SELECT * FROM buyer_recon_entries WHERE id=? AND subject_ref=?", (entry_id, subject_ref)).fetchone()
            if not row:
                raise KeyError(entry_id)
            current = self._entry(row).to_dict()
            for key, value in patch.items():
                if key in allowed:
                    current[key] = str(value) if value is not None else ""
            if "evidence" in patch:
                current["evidence_json"] = json.dumps(patch["evidence"] or [])
            current["updated_at"] = time.time()
            sets = []
            values = []
            for key, value in current.items():
                if key in {"id","board_id","subject_ref","created_at"}:
                    continue
                dbkey = "evidence_json" if key == "evidence" else key
                if dbkey == "evidence_json":
                    value = json.dumps(current.get("evidence") or patch.get("evidence") or [])
                sets.append(f"{dbkey}=?"); values.append(value)
            values.extend([entry_id, subject_ref])
            conn.execute(f"UPDATE buyer_recon_entries SET {','.join(sets)} WHERE id=? AND subject_ref=?", values)
            row = conn.execute("SELECT * FROM buyer_recon_entries WHERE id=? AND subject_ref=?", (entry_id, subject_ref)).fetchone()
        return self._entry(row)

    @staticmethod
    def _board(row: sqlite3.Row) -> BuyerReconBoard:
        return BuyerReconBoard(**dict(row))

    @staticmethod
    def _entry(row: sqlite3.Row) -> BuyerReconEntry:
        d = dict(row)
        try:
            d["evidence"] = json.loads(d.pop("evidence_json") or "[]")
        except json.JSONDecodeError:
            d["evidence"] = []
        return BuyerReconEntry(**d)


_GLOBAL = BuyerReconManager()

def get_buyer_recon_manager() -> BuyerReconManager:
    return _GLOBAL

__all__ = ["BuyerReconBoard","BuyerReconEntry","BuyerReconManager","STATUSES","get_buyer_recon_manager"]
