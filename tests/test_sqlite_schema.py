"""B1.1 — SQLite schema verification tests.

Verifies that ``create_tables()`` produces the correct tables,
columns, and indexes in a temporary database. Does not touch
``data/runtime.db`` — every test uses a fresh ``tmp_path`` fixture.
"""
from __future__ import annotations

import sqlite3
import os
import pytest

from kernel.storage.schema import create_tables


# ── helpers ──────────────────────────────────────────────────────────────────

def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row[1] for row in rows}  # row[1] is column name


def _indexes(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA index_list({table})").fetchall()
    return {row[1] for row in rows}  # row[1] is index name


def _tables(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    return {row[0] for row in rows}


# ── fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def db_path(tmp_path):
    return str(tmp_path / "test_runtime.db")


@pytest.fixture()
def conn(db_path):
    create_tables(db_path=db_path)
    c = sqlite3.connect(db_path)
    yield c
    c.close()


# ── table existence ───────────────────────────────────────────────────────────

def test_jobs_table_exists(conn):
    assert "jobs" in _tables(conn)


def test_goals_table_exists(conn):
    assert "goals" in _tables(conn)


# ── jobs columns ─────────────────────────────────────────────────────────────

_EXPECTED_JOB_COLUMNS = {
    "job_id", "status", "intent", "result", "error", "trace",
    "retries", "source", "created_at", "updated_at", "started_at", "ended_at",
}

def test_jobs_columns(conn):
    assert _EXPECTED_JOB_COLUMNS == _columns(conn, "jobs")


# ── goals columns ─────────────────────────────────────────────────────────────

_EXPECTED_GOAL_COLUMNS = {
    "goal_id", "description", "status", "cadence_seconds",
    "max_runs_per_hour", "next_run", "last_run", "run_count",
    "history", "created_at", "updated_at",
}

def test_goals_columns(conn):
    assert _EXPECTED_GOAL_COLUMNS == _columns(conn, "goals")


# ── indexes ───────────────────────────────────────────────────────────────────

def test_jobs_indexes(conn):
    idx = _indexes(conn, "jobs")
    assert "idx_jobs_status"     in idx
    assert "idx_jobs_created_at" in idx
    assert "idx_jobs_source"     in idx


def test_goals_indexes(conn):
    idx = _indexes(conn, "goals")
    assert "idx_goals_status"   in idx
    assert "idx_goals_next_run" in idx


# ── WAL mode ──────────────────────────────────────────────────────────────────

def test_wal_mode(db_path):
    create_tables(db_path=db_path)
    conn = sqlite3.connect(db_path)
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    conn.close()
    assert mode == "wal"


# ── idempotency ───────────────────────────────────────────────────────────────

def test_create_tables_is_idempotent(db_path):
    """Calling create_tables() twice must not raise or duplicate anything."""
    create_tables(db_path=db_path)
    create_tables(db_path=db_path)  # second call — should be silent
    conn = sqlite3.connect(db_path)
    assert "jobs"  in _tables(conn)
    assert "goals" in _tables(conn)
    conn.close()


# ── jobs CHECK constraint ─────────────────────────────────────────────────────

def test_jobs_status_constraint(db_path):
    """Invalid status must be rejected by the CHECK constraint."""
    create_tables(db_path=db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    import time
    now = time.time()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO jobs (job_id, status, intent, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("j_bad", "invalid_status", "{}", now, now),
        )
        conn.commit()
    conn.close()


# ── goals CHECK constraint ────────────────────────────────────────────────────

def test_goals_status_constraint(db_path):
    """Invalid goal status must be rejected."""
    create_tables(db_path=db_path)
    conn = sqlite3.connect(db_path)
    import time
    now = time.time()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO goals "
            "(goal_id, description, status, cadence_seconds, max_runs_per_hour, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("g_bad", "test goal", "invalid_status", 300.0, 6, now, now),
        )
        conn.commit()
    conn.close()


# ── return value ──────────────────────────────────────────────────────────────

def test_create_tables_returns_path(tmp_path):
    p = str(tmp_path / "sub" / "runtime.db")
    result = create_tables(db_path=p)
    assert result == p
    assert os.path.exists(p)
