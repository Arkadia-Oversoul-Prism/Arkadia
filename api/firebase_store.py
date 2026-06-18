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
]
