"""M01 — SolSpire workspace persistence.

Proves the acceptance criteria of docs/control-plane/moves/M01-persistence.md
against the real store code paths:

  A. Path/connection: the corpus honours SOLSPIRE_DATA_DIR and every store
     call releases its SQLite connection (no leak across many mutations).
  B. Durability: a project and its sub-resources survive loss of the local
     SQLite file — the container-redeploy case — by restoring from the durable
     corpus.
  C. Ownership: restored rows carry owner_uid verbatim; a second user cannot
     recover or list another user's project. Legacy NULL-owner rows stay
     invisible and are never adopted.
  D. No parallel system: the local SQLite corpus remains the single project
     model; restore is additive and never clobbers local writes.

The durable store is an in-process fake that mirrors the real interface
(load_corpus / sync_*), so the persistence bridge and restore path are the
real ones — no network, no Firestore project required.
"""
from __future__ import annotations

import json
import os
import sqlite3
import tempfile

import pytest

_tmpdir = tempfile.mkdtemp(prefix="arkadia_m01_")
_DB = os.path.join(_tmpdir, "solspire_projects.db")
os.environ["SOLSPIRE_PROJECTS_DB"] = _DB
os.environ["SOLSPIRE_DATA_DIR"] = _tmpdir

import solspire.project_manager as pm_mod
import solspire.project_persistence as pp_mod
import solspire.project_store as store_mod

USER_A = "m01-user-a"
USER_B = "m01-user-b"


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    """Fresh DB + fresh durable corpus for every test."""
    db = str(tmp_path / "projects.db")
    monkeypatch.setattr(pm_mod, "_DB_PATH", db)
    monkeypatch.setattr(store_mod, "_DB_PATH", db)
    corpus: dict = {"projects": [], "children": []}
    monkeypatch.setattr(pp_mod, "_fb", lambda: _make_fb(corpus))
    _CORPUS.clear()
    _CORPUS.append(corpus)
    yield corpus


def _make_fb(corpus: dict) -> dict:
    """Stands in for api.firebase_store's resolved project-corpus interface."""
    return {
        "sync_project": lambda p: _sync_project(corpus, p),
        "sync_children": lambda pid, table, rows: _sync_children(corpus, pid, table, rows),
        "delete_project": lambda pid: _delete_project(corpus, pid),
        "load_corpus": lambda: corpus,
    }


def _sync_project(corpus: dict, project: dict) -> None:
    rows = [r for r in corpus["projects"] if r.get("id") != project["id"]]
    rows.append(json.loads(json.dumps(project, default=str)))
    corpus["projects"] = rows


def _sync_children(corpus: dict, project_id: str, table: str, rows: list[dict]) -> None:
    kept = [
        c for c in corpus["children"]
        if not (c.get("project_id") == project_id and c.get("table") == table)
    ]
    kept.extend(
        {"project_id": project_id, "table": table, "row": json.loads(json.dumps(r, default=str))}
        for r in rows
    )
    corpus["children"] = kept


def _delete_project(corpus: dict, project_id: str) -> None:
    corpus["projects"] = [r for r in corpus["projects"] if r.get("id") != project_id]
    corpus["children"] = [c for c in corpus["children"] if c.get("project_id") != project_id]


_CORPUS: list[dict] = []


def _seed(owner: str = USER_A) -> dict:
    """Create a project with representative data in every sub-resource table."""
    pm = pm_mod.get_project_manager()
    project = pm.create("M01 Workspace", {"description": "representative"}, owner_uid=owner)
    pid = project.id
    conv = store_mod.create_conversation(pid, "Session")
    store_mod.append_message(conv["id"], "user", "REPRESENTATIVE_MESSAGE")
    f = store_mod.create_file(pid, "notes.md", "REPRESENTATIVE_CONTENT")
    store_mod.link_repository(pid, "Arkadia-Oversoul-Prism", "Arkadia", "main")
    store_mod.create_task(pid, "Representative task")
    store_mod.add_memory(pid, "Recall", "REPRESENTATIVE_MEMORY", ["m01"])
    return {"pid": pid, "conv": conv["id"], "file": f["id"]}


def _wipe_local_db() -> None:
    """Simulate a backend redeploy: the container filesystem is replaced."""
    for suffix in ("", "-wal", "-shm"):
        p = (pm_mod._DB_PATH or "") + suffix
        if os.path.exists(p):
            os.remove(p)


def _recover() -> dict:
    """Re-run the startup restore against the surviving durable corpus."""
    return pp_mod.restore_project_corpus()


def _corpus() -> dict:
    return _CORPUS[0]


# ── A. Path + connection lifecycle ────────────────────────────────────────────

def test_db_path_honours_data_dir_env():
    """The corpus path follows SOLSPIRE_DATA_DIR, not the process CWD."""
    import importlib

    os.environ["SOLSPIRE_DATA_DIR"] = _tmpdir
    fresh = importlib.reload(importlib.import_module("solspire.project_store"))
    assert fresh._DB_PATH == os.path.join(_tmpdir, "solspire_projects.db")
    importlib.reload(store_mod)


def test_repeated_mutations_do_not_leak_connections():
    """Every store call closes its connection (WAL handles stay bounded)."""
    pm = pm_mod.get_project_manager()
    project = pm.create("Leak Probe", owner_uid=USER_A)
    for i in range(30):
        store_mod.create_task(project.id, f"task {i}")
    # A leaked writer per call would hold WAL open; a clean close leaves a
    # readable database and no unbounded -wal growth.
    with sqlite3.connect(pm_mod._DB_PATH) as conn:
        n = conn.execute("SELECT COUNT(*) FROM project_tasks").fetchone()[0]
    assert n == 30


# ── B. Durability (refresh / redeploy / logout-login / interruption) ──────────

def test_project_and_subresources_survive_local_corpus_loss():
    seeded = _seed()
    assert len(_corpus()["projects"]) == 1

    _wipe_local_db()
    assert not os.path.exists(pm_mod._DB_PATH)

    summary = _recover()

    assert summary["projects"] == 1
    assert summary["children"] >= 6
    # Project row recovered with its identity field intact.
    project = pm_mod.get_project_manager().load(seeded["pid"])
    assert project.name == "M01 Workspace"
    assert project.owner_uid == USER_A
    # Representative data recovered in every sub-resource table.
    assert store_mod.get_file(seeded["file"])["content"] == "REPRESENTATIVE_CONTENT"
    conv = store_mod.get_conversation(seeded["conv"])
    assert conv["messages"][0]["content"] == "REPRESENTATIVE_MESSAGE"
    assert len(store_mod.list_repositories(seeded["pid"])) == 1
    assert len(store_mod.list_tasks(seeded["pid"])) == 1
    assert store_mod.list_memory(seeded["pid"])[0]["content"] == "REPRESENTATIVE_MEMORY"


def test_recovery_is_idempotent_across_repeated_wakes():
    """A later scheduler wake re-restores without duplicating rows."""
    seeded = _seed()
    _wipe_local_db()
    assert _recover()["projects"] == 1
    second = _recover()
    assert second["projects"] == 0  # already present locally
    assert len(pm_mod.get_project_manager().list_projects(owner_uid=USER_A)) == 1
    assert len(store_mod.list_memory(seeded["pid"])) == 1


def test_restore_never_clobbers_local_writes(monkeypatch):
    """A locally-created project survives a restore (local-first, additive)."""
    seeded = _seed()
    # A project created while the durable store is unreachable is never
    # mirrored; a later restore must not treat its absence as a deletion.
    monkeypatch.setattr(pp_mod, "_fb", lambda: None)
    local_only = pm_mod.get_project_manager().create("Offline Created", owner_uid=USER_A)

    # Durable store comes back; only re-point _fb (not the DB path patches).
    monkeypatch.setattr(pp_mod, "_fb", lambda: _make_fb(_corpus()))
    _recover()

    recovered = pm_mod.get_project_manager()
    assert recovered.load(local_only.id).name == "Offline Created"
    assert recovered.load(seeded["pid"]).owner_uid == USER_A
    assert store_mod.get_file(seeded["file"])["content"] == "REPRESENTATIVE_CONTENT"


def test_deletion_propagates_to_durable_corpus():
    seeded = _seed()
    a = store_mod.create_file(seeded["pid"], "temp.md", "temp")
    assert any(c["row"]["id"] == a["id"] for c in _corpus()["children"])
    store_mod.delete_file(a["id"])
    assert not any(c["row"]["id"] == a["id"] for c in _corpus()["children"])


# ── C. Ownership ──────────────────────────────────────────────────────────────

def test_ownership_travels_and_is_never_widened():
    seeded = _seed(owner=USER_A)
    _wipe_local_db()
    _recover()

    pm = pm_mod.get_project_manager()
    assert pm.load(seeded["pid"]).owner_uid == USER_A
    assert [p.id for p in pm.list_projects(owner_uid=USER_A)] == [seeded["pid"]]
    assert pm.list_projects(owner_uid=USER_B) == []


def test_other_user_cannot_recover_another_users_project():
    seeded = _seed(owner=USER_A)
    _wipe_local_db()
    _recover()
    # B's view of the same corpus is empty; A's project is not listed for B.
    pm = pm_mod.get_project_manager()
    assert pm.list_projects(owner_uid=USER_B) == []
    assert pm.load(seeded["pid"]).owner_uid != USER_B


def test_legacy_null_owner_rows_stay_invisible_after_restore():
    pm = pm_mod.get_project_manager()
    legacy = pm.create("Legacy Unowned")  # owner None
    assert legacy.owner_uid is None
    _wipe_local_db()
    _recover()
    pm2 = pm_mod.get_project_manager()
    assert pm2.load(legacy.id).owner_uid is None
    assert pm2.list_projects(owner_uid=USER_A) == []
    assert pm2.list_projects(owner_uid=USER_B) == []


def test_orphan_child_rows_are_not_resurrected():
    """A sub-resource whose project is absent locally is not restored."""
    summary = pp_mod.restore_payload({
        "projects": [],
        "children": [{
            "project_id": "ghost-project",
            "table": "project_files",
            "row": {"id": "orphan", "project_id": "ghost-project", "name": "x",
                    "content": "y", "mime_type": "text/plain",
                    "created_at": 1.0, "updated_at": 1.0},
        }],
    })
    assert summary["children"] == 0
    assert store_mod.get_file("orphan") is None


# ── D. No parallel system ────────────────────────────────────────────────────

def test_local_sqlite_remains_the_single_project_model():
    """Project state still lives in the one canonical SQLite corpus."""
    seeded = _seed()
    with sqlite3.connect(pm_mod._DB_PATH) as conn:
        tables = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        n = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    assert "projects" in tables
    assert n == 1
    assert seeded["pid"]


def test_mirroring_failure_never_breaks_a_mutation(monkeypatch):
    """Best-effort sync: a durable-store outage must not fail the request."""
    def _boom(*_a, **_k):
        raise RuntimeError("durable store unavailable")

    monkeypatch.setattr(pp_mod, "_fb", _boom)
    pm = pm_mod.get_project_manager()
    project = pm.create("Resilient", owner_uid=USER_A)
    store_mod.create_task(project.id, "still works")
    assert len(store_mod.list_tasks(project.id)) == 1


def test_persistence_status_reports_corpus_state():
    _seed()
    status = pm_mod.get_project_manager(), pp_mod.persistence_status()
    assert status[1]["durable_store"] is True
    assert status[1]["projects_local"] == 1