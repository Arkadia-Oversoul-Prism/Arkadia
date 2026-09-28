"""EDEN-OPS-02 — Team access, shared tasks, control-room projection.

Stacks on EDEN-OPS-01. Reuses eden_role_bindings with Firebase UID subjects.
Does not modify WorkEvent schema, K15→K3, api/auth.py internals, or LAYER_MAP.

UID never leaves the server on member-facing payloads.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from solspire.eden_ops import EDEN_DESKS, EdenOps
from weaver.enterprise_orchestration import EnterpriseOrchestrationStore

_DB_PATH = os.environ.get("SOLSPIRE_PROJECTS_DB") or os.path.join(
    os.environ.get("SOLSPIRE_DATA_DIR", "data"), "solspire_projects.db"
)

_HANDLE_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,31}$")
TASK_STATUSES = {"TODO", "DOING", "BLOCKED", "DONE"}

_resolve_uid: Callable[[str], str | None] | None = None
_normalize_handle: Callable[[str | None], str] | None = None


def set_handle_resolvers(
    normalize: Callable[[str | None], str] | None,
    resolve: Callable[[str], str | None] | None,
) -> None:
    global _normalize_handle, _resolve_uid
    _normalize_handle = normalize
    _resolve_uid = resolve


def _default_normalize_handle(raw: str | None) -> str:
    if raw is None:
        raise ValueError("Handle is required")
    h = str(raw).strip()
    if h.startswith("@"):
        h = h[1:]
    h = h.lower().strip()
    if not h or not _HANDLE_RE.match(h):
        raise ValueError("Invalid handle format")
    return h


def normalize_handle(raw: str | None) -> str:
    fn = _normalize_handle or _default_normalize_handle
    return fn(raw)


def resolve_uid_by_handle(handle: str) -> str | None:
    if _resolve_uid:
        return _resolve_uid(handle)
    try:
        from api.auth import resolve_uid_by_handle as real  # type: ignore
        return real(handle)
    except Exception:
        return None


def _now() -> float:
    return time.time()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _db() -> sqlite3.Connection:
    directory = os.path.dirname(_DB_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS eden_role_bindings (
            id TEXT PRIMARY KEY,
            enterprise_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            human_name TEXT NOT NULL,
            desk TEXT NOT NULL,
            bound_at REAL NOT NULL,
            unbound_at REAL,
            UNIQUE(enterprise_id, subject, desk)
        );
        CREATE TABLE IF NOT EXISTS enterprise_tasks (
            task_id TEXT PRIMARY KEY,
            enterprise_id TEXT NOT NULL,
            desk TEXT NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL,
            owner_subject TEXT,
            day_ref TEXT,
            seed_key TEXT,
            evidence_note TEXT,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            updated_by TEXT,
            UNIQUE(enterprise_id, seed_key)
        );
        CREATE INDEX IF NOT EXISTS idx_e02_bindings
            ON eden_role_bindings(enterprise_id, subject, unbound_at);
        CREATE INDEX IF NOT EXISTS idx_e02_tasks
            ON enterprise_tasks(enterprise_id, desk, status);
        """
    )
    conn.commit()
    return conn


@dataclass(frozen=True)
class MemberPublic:
    handle: str
    human_name: str
    desk: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def is_active_member(*, enterprise_id: str, uid: str) -> bool:
    if not uid or uid in {"architect", "jessica"}:
        return False
    with _db() as c:
        row = c.execute(
            "SELECT 1 FROM eden_role_bindings "
            "WHERE enterprise_id=? AND subject=? AND unbound_at IS NULL LIMIT 1",
            (enterprise_id, uid),
        ).fetchone()
    return row is not None


def can_access_enterprise(*, enterprise_id: str, caller_uid: str, owner_uid: str) -> bool:
    if not caller_uid:
        return False
    if caller_uid == owner_uid:
        return True
    return is_active_member(enterprise_id=enterprise_id, uid=caller_uid)


def add_member_by_handle(
    *, enterprise_id: str, owner_uid: str, caller_uid: str, handle: str, desk: str,
    human_name: str | None = None,
) -> MemberPublic:
    if caller_uid != owner_uid:
        raise PermissionError("only owner may add members")
    if desk not in EDEN_DESKS:
        raise ValueError(f"unknown desk: {desk}")
    canon = normalize_handle(handle)
    uid = resolve_uid_by_handle(canon)
    if not uid:
        raise LookupError("unknown handle")
    name = (human_name or canon).strip() or canon
    now = _now()
    with _db() as c:
        existing = c.execute(
            "SELECT id FROM eden_role_bindings "
            "WHERE enterprise_id=? AND subject=? AND desk=? AND unbound_at IS NULL",
            (enterprise_id, uid, desk),
        ).fetchone()
        if existing:
            return MemberPublic(handle=canon, human_name=name, desk=desk)
        prior = c.execute(
            "SELECT id FROM eden_role_bindings WHERE enterprise_id=? AND subject=? AND desk=?",
            (enterprise_id, uid, desk),
        ).fetchone()
        if prior:
            c.execute(
                "UPDATE eden_role_bindings SET unbound_at=NULL, human_name=?, bound_at=? WHERE id=?",
                (name, now, prior["id"]),
            )
        else:
            c.execute(
                "INSERT INTO eden_role_bindings VALUES (?,?,?,?,?,?,?)",
                (_id("bind"), enterprise_id, uid, name, desk, now, None),
            )
    return MemberPublic(handle=canon, human_name=name, desk=desk)


def remove_member_desk(
    *, enterprise_id: str, owner_uid: str, caller_uid: str, handle: str, desk: str,
) -> None:
    if caller_uid != owner_uid:
        raise PermissionError("only owner may remove members")
    canon = normalize_handle(handle)
    uid = resolve_uid_by_handle(canon)
    if not uid:
        raise LookupError("unknown handle")
    with _db() as c:
        c.execute(
            "UPDATE eden_role_bindings SET unbound_at=? "
            "WHERE enterprise_id=? AND subject=? AND desk=? AND unbound_at IS NULL",
            (_now(), enterprise_id, uid, desk),
        )


def list_members_public(*, enterprise_id: str) -> list[MemberPublic]:
    with _db() as c:
        rows = c.execute(
            "SELECT subject, human_name, desk FROM eden_role_bindings "
            "WHERE enterprise_id=? AND unbound_at IS NULL ORDER BY desk",
            (enterprise_id,),
        ).fetchall()
    out: list[MemberPublic] = []
    for r in rows:
        if r["subject"] in {"architect", "jessica"}:
            continue
        out.append(MemberPublic(handle="member", human_name=r["human_name"], desk=r["desk"]))
    return out


def member_desks(*, enterprise_id: str, uid: str) -> list[str]:
    with _db() as c:
        rows = c.execute(
            "SELECT desk FROM eden_role_bindings "
            "WHERE enterprise_id=? AND subject=? AND unbound_at IS NULL",
            (enterprise_id, uid),
        ).fetchall()
    return [r["desk"] for r in rows]


@dataclass
class Task:
    task_id: str
    enterprise_id: str
    desk: str
    title: str
    status: str
    owner_subject: str | None
    day_ref: str | None
    seed_key: str | None
    evidence_note: str | None
    created_at: float
    updated_at: float
    updated_by: str | None

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "enterprise_id": self.enterprise_id,
            "desk": self.desk,
            "title": self.title,
            "status": self.status,
            "day_ref": self.day_ref,
            "seed_key": self.seed_key,
            "evidence_note": self.evidence_note,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def _seed_path() -> Path:
    return Path(__file__).resolve().parents[1] / "enterprises" / "eden-food-systems" / "tasks.seed.json"


def seed_tasks(*, enterprise_id: str) -> int:
    path = _seed_path()
    if not path.is_file():
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    now = _now()
    inserted = 0
    with _db() as c:
        for item in data:
            seed_key = item["seed_key"]
            exists = c.execute(
                "SELECT 1 FROM enterprise_tasks WHERE enterprise_id=? AND seed_key=?",
                (enterprise_id, seed_key),
            ).fetchone()
            if exists:
                continue
            c.execute(
                "INSERT INTO enterprise_tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (_id("task"), enterprise_id, item["desk"], item["title"], "TODO", None,
                 item.get("day_ref"), seed_key, None, now, now, None),
            )
            inserted += 1
    return inserted


def list_tasks(*, enterprise_id: str, desk: str | None = None) -> list[Task]:
    with _db() as c:
        if desk:
            rows = c.execute(
                "SELECT * FROM enterprise_tasks WHERE enterprise_id=? AND desk=? ORDER BY day_ref, title",
                (enterprise_id, desk),
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT * FROM enterprise_tasks WHERE enterprise_id=? ORDER BY desk, day_ref, title",
                (enterprise_id,),
            ).fetchall()
    return [_row_task(r) for r in rows]


def _row_task(r: sqlite3.Row) -> Task:
    return Task(
        task_id=r["task_id"], enterprise_id=r["enterprise_id"], desk=r["desk"],
        title=r["title"], status=r["status"], owner_subject=r["owner_subject"],
        day_ref=r["day_ref"], seed_key=r["seed_key"], evidence_note=r["evidence_note"],
        created_at=r["created_at"], updated_at=r["updated_at"], updated_by=r["updated_by"],
    )


def update_task(
    *, enterprise_id: str, task_id: str, caller_uid: str, owner_uid: str,
    status: str | None = None, evidence_note: str | None = None, title: str | None = None,
) -> Task:
    with _db() as c:
        row = c.execute(
            "SELECT * FROM enterprise_tasks WHERE enterprise_id=? AND task_id=?",
            (enterprise_id, task_id),
        ).fetchone()
        if not row:
            raise LookupError("task not found")
        if caller_uid != owner_uid:
            desks = member_desks(enterprise_id=enterprise_id, uid=caller_uid)
            if row["desk"] not in desks:
                raise PermissionError("member may only update own-desk tasks")
        new_status = (status or row["status"]).upper()
        if new_status not in TASK_STATUSES:
            raise ValueError(f"invalid status: {new_status}")
        note = evidence_note if evidence_note is not None else row["evidence_note"]
        if new_status in {"DONE", "BLOCKED"} and not (note and str(note).strip()):
            raise ValueError(f"{new_status} requires non-empty evidence_note")
        new_title = title if title is not None else row["title"]
        now = _now()
        c.execute(
            "UPDATE enterprise_tasks SET status=?, evidence_note=?, title=?, updated_at=?, updated_by=? WHERE task_id=?",
            (new_status, note, new_title, now, caller_uid, task_id),
        )
        updated = c.execute("SELECT * FROM enterprise_tasks WHERE task_id=?", (task_id,)).fetchone()
    return _row_task(updated)


def task_counts(*, enterprise_id: str) -> dict[str, Any]:
    with _db() as c:
        rows = c.execute(
            "SELECT desk, status, COUNT(*) AS n FROM enterprise_tasks WHERE enterprise_id=? GROUP BY desk, status",
            (enterprise_id,),
        ).fetchall()
    by_desk: dict[str, dict[str, int]] = {}
    for r in rows:
        by_desk.setdefault(r["desk"], {})[r["status"]] = r["n"]
    return by_desk


@dataclass
class LabeledValue:
    value: Any
    state: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def control_room(
    *, enterprise_id: str, subject_for_projection: str,
    store: EnterpriseOrchestrationStore | None = None,
) -> dict[str, Any]:
    ops = EdenOps(store=store or EnterpriseOrchestrationStore())
    field = ops.project_field(subject=subject_for_projection, enterprise_id=enterprise_id)
    members = list_members_public(enterprise_id=enterprise_id)
    counts = task_counts(enterprise_id=enterprise_id)

    # Promote facts only from verified Evidence Records linked through the
    # existing execution → authorization → proposal enterprise chain.
    verified: list[dict[str, Any]] = []
    try:
        from weaver import enterprise_orchestration as ew
        with ew._db() as c:
            rows = c.execute(
                """SELECT e.content_or_ref, v.claim, v.verdict
                   FROM ew_evidence e
                   JOIN ew_verifications v ON instr(v.evidence_refs, e.id) > 0
                   JOIN ew_execution_attempts x ON x.id=e.execution_attempt_id
                   JOIN ew_authorizations a ON a.id=x.authorization_id
                   JOIN ew_proposals p ON p.id=a.proposal_id
                  WHERE p.enterprise_id=? AND v.verdict='VERIFIED'
                  ORDER BY v.verified_at DESC""",
                (enterprise_id,),
            ).fetchall()
        for row in rows:
            try:
                content = json.loads(row["content_or_ref"])
            except Exception:
                content = {}
            if isinstance(content, dict):
                verified.append(content)

        for content in verified:
            if "price_ngn_per_kg" in content and field.commercial["buy_price"] == "UNKNOWN":
                field.commercial["buy_price"] = f"₦{content['price_ngn_per_kg']}/kg"
            for key in ("supplier", "commodity", "buyer", "route", "sell_price"):
                if key in content and field.commercial.get(key) == "UNKNOWN":
                    field.commercial[key] = str(content[key])
            for key in ("committed", "spent", "recovered"):
                if key in content and field.capital.get(key) == "UNKNOWN":
                    field.capital[key] = str(content[key])
    except Exception:
        pass

    def label_commercial(key: str) -> LabeledValue:
        v = field.commercial.get(key, "UNKNOWN")
        if v == "UNKNOWN":
            return LabeledValue(value="UNKNOWN", state="UNKNOWN")
        return LabeledValue(value=v, state="RECORDED")

    def label_capital(key: str) -> LabeledValue:
        v = field.capital.get(key, "UNKNOWN")
        if key == "budget":
            return LabeledValue(value=v, state="ESTIMATED")
        if v == "UNKNOWN":
            return LabeledValue(value="UNKNOWN", state="UNKNOWN")
        return LabeledValue(value=v, state="RECORDED")

    return {
        "zones": {
            "command": {
                "enterprise_id": enterprise_id,
                "cycle": field.cycle,
                "bindings_count": len(members),
                "weaver": field.weaver_counters,
            },
            "commercial": {k: label_commercial(k).to_dict() for k in field.commercial},
            "money": {k: label_capital(k).to_dict() for k in field.capital},
            "desks": {
                "staffed": list(EDEN_DESKS),
                "members": [m.to_dict() for m in members],
                "reserve": {"label": "Contingency/Reserve", "role": "financial_control_only"},
            },
            "tasks": {"by_desk": counts},
            "next_gate": {
                "unknowns": field.weaver_counters.get("unknowns", 0),
                "awaiting_authority": field.weaver_counters.get("awaiting_authority", 0),
                "message": "Where evidence stops, the claim stops.",
            },
        }
    }
