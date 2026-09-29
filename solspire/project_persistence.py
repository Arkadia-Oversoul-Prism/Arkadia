"""M01 — SolSpire workspace durability bridge.

The SolSpire project corpus is SQLite (``$SOLSPIRE_DATA_DIR/solspire_projects.db``).
A container filesystem is ephemeral, so that file is rebuilt from the image on
every backend redeploy and the corpus is lost. This module mirrors the corpus
into the durable store already used for jobs/goals and restores it when local
state is absent.

Boundaries:
  • SQLite remains the read/write path and the only project model.
  • No second database, filesystem, memory system, or identity system.
  • Ownership (``owner_uid``) travels verbatim and is never widened on restore;
    legacy NULL-owner rows stay invisible to everyone.
  • Mirroring is best-effort: a durable-store failure never breaks a request.
"""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger("solspire.project_persistence")

# Sub-resource tables mirrored alongside each project row. All key on
# ``project_id``; ``id`` is the child primary key.
CHILD_TABLES: tuple[str, ...] = (
    "project_conversations",
    "project_files",
    "project_repositories",
    "project_tasks",
    "project_memory",
    "project_events",
)


def _fb():
    """Resolve the durable store. Returns None when unavailable.

    Never raises: mirroring is best-effort and must not be able to fail a
    caller's mutation, so even an import/init error degrades to None.
    """
    try:
        from api.firebase_store import (
            fb_delete_project,
            fb_load_project_corpus,
            fb_sync_project,
            fb_sync_project_children,
            projects_available,
        )
        if not projects_available():
            return None
    except Exception:
        return None
    return {
        "sync_project": fb_sync_project,
        "sync_children": fb_sync_project_children,
        "delete_project": fb_delete_project,
        "load_corpus": fb_load_project_corpus,
    }


def _resolve():
    try:
        return _fb()
    except Exception:
        return None


def mirror_project(project_id: str) -> bool:
    """Push one project and its sub-resources into the durable corpus."""
    fb = _resolve()
    if fb is None or not project_id:
        return False
    try:
        from solspire.project_manager import get_project_manager

        try:
            project = get_project_manager().load(project_id)
        except KeyError:
            fb["delete_project"](project_id)
            return True

        fb["sync_project"](project.to_dict())

        from solspire.project_store import export_project_rows

        for table, rows in export_project_rows(project_id).items():
            fb["sync_children"](project_id, table, rows)
        return True
    except Exception as e:
        logger.warning(f"[M01] mirror failed for {project_id}: {e}")
        return False


def mirror_by_child(table: str, child_id: str) -> bool:
    """Mirror the project owning *child_id* (for id-keyed mutations)."""
    if table not in CHILD_TABLES or not child_id:
        return False
    try:
        from solspire.project_store import project_id_for_child

        pid = project_id_for_child(table, child_id)
    except Exception:
        return False
    return mirror_project(pid) if pid else False


def restore_project_corpus() -> dict[str, Any]:
    """Restore the corpus from the durable store into local SQLite."""
    fb = _resolve()
    if fb is None:
        return {"available": False, "projects": 0, "children": 0}
    summary = restore_payload(fb["load_corpus"]())
    summary["available"] = True
    return summary


def restore_payload(corpus: dict[str, Any]) -> dict[str, Any]:
    """Apply a durable-corpus payload to local SQLite.

    Idempotent and additive: a project already present locally is left
    untouched, so local writes are never clobbered and ownership fields are
    never rewritten.
    """
    summary: dict[str, Any] = {"available": False, "projects": 0, "children": 0}
    projects = (corpus or {}).get("projects") or []
    children = (corpus or {}).get("children") or []
    if not projects and not children:
        return summary

    try:
        from solspire.project_store import _db  # canonical connection lifecycle

        with _db() as conn:
            for row in projects:
                if not isinstance(row, dict) or not row.get("id"):
                    continue
                if _insert_row(conn, "projects", row):
                    summary["projects"] += 1
            for entry in children:
                if not isinstance(entry, dict):
                    continue
                table = str(entry.get("table") or "")
                row = entry.get("row")
                if table not in CHILD_TABLES or not isinstance(row, dict) or not row.get("id"):
                    continue
                # Never resurrect a child whose owning project is absent locally
                # (keeps project scoping intact).
                pid = row.get("project_id")
                if not pid or not _project_exists(conn, str(pid)):
                    continue
                if _insert_row(conn, table, row):
                    summary["children"] += 1
            conn.commit()
    except Exception as e:
        logger.warning(f"[M01] restore failed: {e}")
        return summary

    if summary["projects"] or summary["children"]:
        logger.info(
            "[M01] restored %d projects / %d sub-resource rows from durable corpus",
            summary["projects"], summary["children"],
        )
    return summary


def startup_restore() -> dict[str, Any]:
    """Startup hook: restore the corpus and log the outcome.

    Kept here so api/main.py only needs a one-line call — it is already over
    its decomposition budget and must not accrue business logic.
    """
    try:
        summary = restore_project_corpus()
        if summary.get("projects") or summary.get("children"):
            logger.info(
                "[M01] SolSpire corpus restored: %s project(s), %s sub-resource row(s)",
                summary.get("projects"), summary.get("children"),
            )
        return summary
    except Exception as e:
        logger.warning(f"[M01] SolSpire corpus restore skipped: {e}")
        return {"available": False, "projects": 0, "children": 0}


def persistence_status() -> dict[str, Any]:
    """Diagnostic view: is the durable corpus wired, and how much is local?"""
    status: dict[str, Any] = {"durable_store": _resolve() is not None}
    try:
        from solspire.project_store import _db

        with _db() as conn:
            status["projects_local"] = conn.execute(
                "SELECT COUNT(*) AS c FROM projects"
            ).fetchone()["c"]
    except Exception as e:
        status["projects_local"] = None
        status["error"] = str(e)
    return status


def _project_exists(conn, project_id: str) -> bool:
    row = conn.execute("SELECT 1 FROM projects WHERE id=?", (project_id,)).fetchone()
    return row is not None


def _coerce(value: Any) -> Any:
    """Normalise a durable-store value for a SQLite TEXT/REAL/None column.

    The durable store returns structured values (dict/list) where the local
    corpus stores JSON text, so containers are re-serialised on the way in.
    """
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    if isinstance(value, bool):
        return int(value)
    return value


def _insert_row(conn, table: str, row: dict[str, Any]) -> bool:
    """INSERT OR IGNORE a full row. Returns True when a new row was added."""
    cols = [c for c in row.keys() if c]
    if not cols:
        return False
    placeholders = ", ".join("?" for _ in cols)
    cur = conn.execute(
        f"INSERT OR IGNORE INTO {table} ({', '.join(cols)}) VALUES ({placeholders})",
        [_coerce(row[c]) for c in cols],
    )
    return cur.rowcount > 0


__all__ = [
    "CHILD_TABLES",
    "mirror_project",
    "mirror_by_child",
    "restore_project_corpus",
    "restore_payload",
    "startup_restore",
    "persistence_status",
]