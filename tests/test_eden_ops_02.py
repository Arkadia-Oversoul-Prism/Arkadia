"""EDEN-OPS-02 — team access, task, and control-room contracts."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from solspire import eden_ops_02 as e02
from solspire.eden_ops import EDEN_DESKS, EdenOps
from weaver.enterprise_orchestration import EnterpriseOrchestrationStore


OWNER = "owner-uid"
MEMBER = "member-uid"
STRANGER = "stranger-uid"
ENTERPRISE = "eden-01"


def _setup(tmp_path, monkeypatch):
    db = str(tmp_path / "eden_ops_02.db")
    monkeypatch.setattr(e02, "_DB_PATH", db)
    import solspire.eden_ops as eden_mod
    import weaver.enterprise_orchestration as ew_mod
    monkeypatch.setattr(eden_mod, "_DB_PATH", db)
    monkeypatch.setattr(ew_mod, "_DB_PATH", db)
    e02.set_handle_resolvers(
        lambda raw: str(raw).lstrip("@").lower(),
        lambda handle: {"jessica": MEMBER}.get(handle),
    )
    return db


def _enterprise_row(db):
    with sqlite3.connect(db) as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS enterprise_organizations (
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
            )"""
        )
        c.execute(
            """INSERT INTO enterprise_organizations
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                ENTERPRISE, OWNER, "workspace-01", "Eden Food Systems", "Eden",
                "READY_FOR_OPERATIONS", 7, "{}", "{}", "[]", "[]", "{}",
                "{}", "{}", "[]", 1.0, 1.0,
            ),
        )


def test_owner_member_and_stranger_access(tmp_path, monkeypatch):
    db = _setup(tmp_path, monkeypatch)
    _enterprise_row(db)
    e02.add_member_by_handle(
        enterprise_id=ENTERPRISE, owner_uid=OWNER, caller_uid=OWNER,
        handle="@jessica", desk="Procurement", human_name="Jessica",
    )
    assert e02.can_access_enterprise(
        enterprise_id=ENTERPRISE, caller_uid=OWNER, owner_uid=OWNER
    )
    assert e02.can_access_enterprise(
        enterprise_id=ENTERPRISE, caller_uid=MEMBER, owner_uid=OWNER
    )
    assert not e02.can_access_enterprise(
        enterprise_id=ENTERPRISE, caller_uid=STRANGER, owner_uid=OWNER
    )


def test_membership_validation_and_idempotence(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    with pytest.raises(ValueError):
        e02.add_member_by_handle(
            enterprise_id=ENTERPRISE, owner_uid=OWNER, caller_uid=OWNER,
            handle="!", desk="Procurement",
        )
    with pytest.raises(LookupError):
        e02.add_member_by_handle(
            enterprise_id=ENTERPRISE, owner_uid=OWNER, caller_uid=OWNER,
            handle="@unknown", desk="Procurement",
        )
    with pytest.raises(ValueError):
        e02.add_member_by_handle(
            enterprise_id=ENTERPRISE, owner_uid=OWNER, caller_uid=OWNER,
            handle="@jessica", desk="Unknown Desk",
        )
    first = e02.add_member_by_handle(
        enterprise_id=ENTERPRISE, owner_uid=OWNER, caller_uid=OWNER,
        handle="@jessica", desk="Procurement", human_name="Jessica",
    )
    second = e02.add_member_by_handle(
        enterprise_id=ENTERPRISE, owner_uid=OWNER, caller_uid=OWNER,
        handle="@jessica", desk="Procurement", human_name="Jessica",
    )
    assert first.to_dict() == second.to_dict()


def test_placeholder_subjects_grant_no_access_and_public_payload_redacts_uid(tmp_path, monkeypatch):
    db = _setup(tmp_path, monkeypatch)
    e02.bind_desk = getattr(e02, "bind_desk", None)
    with e02._db() as c:
        c.execute(
            "INSERT INTO eden_role_bindings VALUES (?,?,?,?,?,?,?)",
            ("legacy-1", ENTERPRISE, "architect", "Divine Favour Yusuf", "Procurement", 1, None),
        )
        c.execute(
            "INSERT INTO eden_role_bindings VALUES (?,?,?,?,?,?,?)",
            ("legacy-2", ENTERPRISE, "jessica", "Jessica", "Logistics", 1, None),
        )
    assert not e02.is_active_member(enterprise_id=ENTERPRISE, uid="architect")
    assert not e02.is_active_member(enterprise_id=ENTERPRISE, uid="jessica")
    payload = e02.public_enterprise_payload(
        {"enterprise_id": ENTERPRISE, "owner_subject_ref": OWNER, "members": []},
        caller_uid=MEMBER,
    )
    raw = json.dumps(payload)
    assert OWNER not in raw
    assert MEMBER not in raw


def test_unbind_removes_access(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    e02.add_member_by_handle(
        enterprise_id=ENTERPRISE, owner_uid=OWNER, caller_uid=OWNER,
        handle="@jessica", desk="Procurement",
    )
    assert e02.is_active_member(enterprise_id=ENTERPRISE, uid=MEMBER)
    e02.remove_member_desk(
        enterprise_id=ENTERPRISE, owner_uid=OWNER, caller_uid=OWNER,
        handle="@jessica", desk="Procurement",
    )
    assert not e02.is_active_member(enterprise_id=ENTERPRISE, uid=MEMBER)


def test_seed_is_idempotent_and_matches_seed_file(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    path = Path(e02._seed_path())
    seed = json.loads(path.read_text(encoding="utf-8"))
    assert len(seed) == 14
    assert e02.seed_tasks(enterprise_id=ENTERPRISE) == 14
    assert e02.seed_tasks(enterprise_id=ENTERPRISE) == 0
    assert len(e02.list_tasks(enterprise_id=ENTERPRISE)) == len(seed)


def test_member_can_update_own_desk_but_not_other_desk(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    e02.add_member_by_handle(
        enterprise_id=ENTERPRISE, owner_uid=OWNER, caller_uid=OWNER,
        handle="@jessica", desk="Procurement",
    )
    e02.seed_tasks(enterprise_id=ENTERPRISE)
    own = e02.list_tasks(enterprise_id=ENTERPRISE, desk="Procurement")[0]
    other = e02.list_tasks(enterprise_id=ENTERPRISE, desk="Logistics")[0]
    updated = e02.update_task(
        enterprise_id=ENTERPRISE, task_id=own.task_id, caller_uid=MEMBER,
        owner_uid=OWNER, status="DOING",
    )
    assert updated.status == "DOING"
    with pytest.raises(PermissionError):
        e02.update_task(
            enterprise_id=ENTERPRISE, task_id=other.task_id, caller_uid=MEMBER,
            owner_uid=OWNER, status="DOING",
        )


def test_done_and_blocked_require_evidence(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    e02.seed_tasks(enterprise_id=ENTERPRISE)
    task = e02.list_tasks(enterprise_id=ENTERPRISE)[0]
    with pytest.raises(ValueError):
        e02.update_task(
            enterprise_id=ENTERPRISE, task_id=task.task_id, caller_uid=OWNER,
            owner_uid=OWNER, status="DONE",
        )
    with pytest.raises(ValueError):
        e02.update_task(
            enterprise_id=ENTERPRISE, task_id=task.task_id, caller_uid=OWNER,
            owner_uid=OWNER, status="BLOCKED",
        )
    done = e02.update_task(
        enterprise_id=ENTERPRISE, task_id=task.task_id, caller_uid=OWNER,
        owner_uid=OWNER, status="DONE", evidence_note="Evidence attached",
    )
    assert done.status == "DONE"


def test_authenticated_uid_is_server_derived_for_task_updates(tmp_path, monkeypatch):
    db = _setup(tmp_path, monkeypatch)
    e02.seed_tasks(enterprise_id=ENTERPRISE)
    task = e02.list_tasks(enterprise_id=ENTERPRISE)[0]
    updated = e02.update_task(
        enterprise_id=ENTERPRISE, task_id=task.task_id, caller_uid=MEMBER,
        owner_uid=MEMBER, status="DOING",
    )
    with sqlite3.connect(db) as c:
        row = c.execute(
            "SELECT updated_by, owner_subject FROM enterprise_tasks WHERE task_id=?",
            (task.task_id,),
        ).fetchone()
    assert row[0] == MEMBER
    assert row[0] != OWNER
    assert updated.to_public_dict().get("owner_subject") is None


def test_control_room_unknowns_are_explicit_without_evidence(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    room = e02.control_room(
        enterprise_id=ENTERPRISE, subject_for_projection=OWNER,
    )
    for key in ("buy_price", "sell_price"):
        assert room["zones"]["commercial"][key]["state"] == "UNKNOWN"
        assert room["zones"]["commercial"][key]["value"] == "UNKNOWN"
    for key in ("committed", "spent", "recovered"):
        assert room["zones"]["money"][key]["state"] == "UNKNOWN"
        assert room["zones"]["money"][key]["value"] == "UNKNOWN"


def test_verified_evidence_promotes_only_supported_value(tmp_path, monkeypatch):
    db = _setup(tmp_path, monkeypatch)
    store = EnterpriseOrchestrationStore()
    ops = EdenOps(store=store)
    ops.living_cell_supplier_path(
        subject=OWNER, enterprise_id=ENTERPRISE, verified_price_ngn_per_kg=1200
    )
    room = e02.control_room(
        enterprise_id=ENTERPRISE, subject_for_projection=OWNER, store=store
    )
    assert room["zones"]["commercial"]["buy_price"] == {
        "value": "₦1200/kg", "state": "RECORDED"
    }
    assert room["zones"]["commercial"]["sell_price"]["state"] == "UNKNOWN"
    assert room["zones"]["money"]["spent"]["state"] == "UNKNOWN"


def test_member_payload_contains_no_firebase_uid(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    e02.add_member_by_handle(
        enterprise_id=ENTERPRISE, owner_uid=OWNER, caller_uid=OWNER,
        handle="@jessica", desk="Procurement",
    )
    payload = {
        "member": e02.add_member_by_handle(
            enterprise_id=ENTERPRISE, owner_uid=OWNER, caller_uid=OWNER,
            handle="@jessica", desk="Logistics", human_name="Jessica",
        ).to_dict()
    }
    raw = json.dumps(payload)
    assert OWNER not in raw
    assert MEMBER not in raw
    assert all(k in payload["member"] for k in ("handle", "human_name", "desk"))


def test_all_seven_operational_desks_are_supported_and_reserve_is_not_a_desk(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    assert len(EDEN_DESKS) == 7
    assert "Contingency/Reserve" not in EDEN_DESKS
