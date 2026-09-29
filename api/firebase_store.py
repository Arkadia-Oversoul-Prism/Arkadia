"""Arkadia Firebase Persistence Layer.

Provides an optional Firestore-backed sync for the kernel's JobStore and
GoalStore. When FIREBASE_SERVICE_ACCOUNT_JSON is set in the environment,
all writes go to both local JSON (for the in-process queue) and Firestore
(for cross-restart durability). When Firebase is not configured, the
module no-ops cleanly — the JSON-backed stores continue as normal.

Collections:
  • jobs  — mirrors kernel/jobs.py JobStore
  • goals — mirrors kernel/goals.py GoalStore

Usage (called from kernel/jobs.py and kernel/goals.py _persist methods):
    from api.firebase_store import fb_sync_jobs, fb_sync_goals
    from api.firebase_store import fb_load_jobs, fb_load_goals
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger("arkadia.firebase_store")

_db = None
_available = False


def _init() -> None:
    global _db, _available
    sa_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    if not sa_json:
        logger.debug("[FB-STORE] FIREBASE_SERVICE_ACCOUNT_JSON not set — Firebase sync disabled")
        return
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore as fs

        if not firebase_admin._apps:
            cred_data = json.loads(sa_json) if sa_json.startswith("{") else sa_json
            cred = credentials.Certificate(cred_data)
            firebase_admin.initialize_app(cred)

        _db = fs.client()
        _available = True
        logger.info("[FB-STORE] Firestore persistence layer active")
    except Exception as e:
        logger.warning(f"[FB-STORE] Firestore init failed — JSON fallback only: {e}")


_init()


def is_available() -> bool:
    return _available


# ── Jobs ─────────────────────────────────────────────────────────────────────

def fb_sync_jobs(jobs: dict[str, Any]) -> None:
    """Write all jobs to Firestore. Called after every local _persist()."""
    if not _available or _db is None:
        return
    try:
        batch = _db.batch()
        col = _db.collection("jobs")
        for job_id, job in jobs.items():
            batch.set(col.document(job_id), _serialise(job))
        batch.commit()
    except Exception as e:
        logger.warning(f"[FB-STORE] jobs sync failed: {e}")


def fb_load_jobs() -> dict[str, Any]:
    """Load all jobs from Firestore. Used as fallback when local JSON is empty."""
    if not _available or _db is None:
        return {}
    try:
        docs = _db.collection("jobs").stream()
        return {doc.id: doc.to_dict() for doc in docs}
    except Exception as e:
        logger.warning(f"[FB-STORE] jobs load failed: {e}")
        return {}


def fb_upsert_job(job_id: str, job: dict[str, Any]) -> None:
    """Upsert a single job document. Faster than syncing the full store."""
    if not _available or _db is None:
        return
    try:
        _db.collection("jobs").document(job_id).set(_serialise(job))
    except Exception as e:
        logger.debug(f"[FB-STORE] job upsert failed: {e}")


# ── Goals ────────────────────────────────────────────────────────────────────

def fb_sync_goals(goals: dict[str, Any]) -> None:
    """Write all goals to Firestore. Called after every local _persist()."""
    if not _available or _db is None:
        return
    try:
        batch = _db.batch()
        col = _db.collection("goals")
        for goal_id, goal in goals.items():
            batch.set(col.document(goal_id), _serialise(goal))
        batch.commit()
    except Exception as e:
        logger.warning(f"[FB-STORE] goals sync failed: {e}")


def fb_load_goals() -> dict[str, Any]:
    """Load all goals from Firestore. Used as fallback when local JSON is empty."""
    if not _available or _db is None:
        return {}
    try:
        docs = _db.collection("goals").stream()
        return {doc.id: doc.to_dict() for doc in docs}
    except Exception as e:
        logger.warning(f"[FB-STORE] goals load failed: {e}")
        return {}


def fb_upsert_goal(goal_id: str, goal: dict[str, Any]) -> None:
    """Upsert a single goal document."""
    if not _available or _db is None:
        return
    try:
        _db.collection("goals").document(goal_id).set(_serialise(goal))
    except Exception as e:
        logger.debug(f"[FB-STORE] goal upsert failed: {e}")


def fb_delete_goal(goal_id: str) -> None:
    """Delete a goal from Firestore."""
    if not _available or _db is None:
        return
    try:
        _db.collection("goals").document(goal_id).delete()
    except Exception as e:
        logger.debug(f"[FB-STORE] goal delete failed: {e}")


# ── SolSpire project corpus (M01 persistence) ────────────────────────────────
#
# The SolSpire project corpus lives in SQLite (data/solspire_projects.db).
# A container filesystem is ephemeral, so that file is rebuilt from the image
# on every backend redeploy and project state is lost. This mirrors the corpus
# into the SAME durable store already used for jobs/goals — no second database,
# no parallel project model. Ownership fields travel verbatim and are never
# widened on restore; local SQLite stays the read/write path.

_PROJECTS_COLLECTION = "solspire_projects"
_PROJECT_CHILDREN_COLLECTION = "solspire_project_children"

_BATCH_LIMIT = 400


def _chunks(items: list[Any], size: int = _BATCH_LIMIT):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def projects_available() -> bool:
    return _available and _db is not None


def fb_sync_project(project: dict[str, Any]) -> None:
    """Upsert one project row into the durable corpus."""
    if not projects_available():
        return
    pid = str(project.get("id") or "")
    if not pid:
        return
    try:
        _db.collection(_PROJECTS_COLLECTION).document(pid).set(_serialise(project))
    except Exception as e:
        logger.warning(f"[FB-STORE] project upsert failed: {e}")


def fb_sync_project_children(project_id: str, table: str, rows: list[dict[str, Any]]) -> None:
    """Mirror the current child rows for one project/table.

    Children are keyed ``{table}:{row_id}`` so a re-sync is idempotent and
    deletions are reconciled by removing documents absent from ``rows``.
    """
    if not projects_available():
        return
    pid = str(project_id or "")
    if not pid:
        return
    try:
        col = _db.collection(_PROJECT_CHILDREN_COLLECTION)
        desired = {f"{table}:{r.get('id')}" for r in rows if r.get("id")}
        existing = {
            doc.id
            for doc in col.where("project_id", "==", pid).where("table", "==", table).stream()
        }
        for doc_id in existing - desired:
            col.document(doc_id).delete()
        for chunk in _chunks(list(rows)):
            batch = _db.batch()
            for row in chunk:
                rid = row.get("id")
                if not rid:
                    continue
                batch.set(
                    col.document(f"{table}:{rid}"),
                    _serialise({"project_id": pid, "table": table, "row": row}),
                )
            batch.commit()
    except Exception as e:
        logger.warning(f"[FB-STORE] project children sync failed ({table}): {e}")


def fb_delete_project(project_id: str) -> None:
    """Remove a project and all of its mirrored children."""
    if not projects_available():
        return
    pid = str(project_id or "")
    if not pid:
        return
    try:
        _db.collection(_PROJECTS_COLLECTION).document(pid).delete()
        col = _db.collection(_PROJECT_CHILDREN_COLLECTION)
        for doc in col.where("project_id", "==", pid).stream():
            doc.reference.delete()
    except Exception as e:
        logger.warning(f"[FB-STORE] project delete failed: {e}")


def fb_load_project_corpus() -> dict[str, Any]:
    """Load the mirrored project corpus: ``{"projects": [...], "children": [...]}``."""
    if not projects_available():
        return {"projects": [], "children": []}
    try:
        projects = [doc.to_dict() for doc in _db.collection(_PROJECTS_COLLECTION).stream()]
        children = [doc.to_dict() for doc in _db.collection(_PROJECT_CHILDREN_COLLECTION).stream()]
        return {"projects": projects, "children": children}
    except Exception as e:
        logger.warning(f"[FB-STORE] project corpus load failed: {e}")
        return {"projects": [], "children": []}


# ── Utilities ─────────────────────────────────────────────────────────────────

def _serialise(obj: Any) -> Any:
    """Recursively convert non-serialisable types for Firestore."""
    if isinstance(obj, dict):
        return {k: _serialise(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialise(i) for i in obj]
    if isinstance(obj, float) and (obj != obj):
        return None
    return obj


__all__ = [
    "is_available",
    "fb_sync_jobs", "fb_load_jobs", "fb_upsert_job",
    "fb_sync_goals", "fb_load_goals", "fb_upsert_goal", "fb_delete_goal",
    "projects_available",
    "fb_sync_project", "fb_sync_project_children", "fb_delete_project",
    "fb_load_project_corpus",
]
