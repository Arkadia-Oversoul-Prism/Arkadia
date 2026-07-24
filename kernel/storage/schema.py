"""Arkadia runtime database — SQLite schema and creation.

Single responsibility: define DDL and expose ``create_tables()``.
Nothing in this module touches kernel/jobs.py, kernel/goals.py, or
the API layer. Those integrations belong to B1.2 and B1.3.

Usage::

    from kernel.storage.schema import create_tables
    create_tables()                          # uses default path
    create_tables(db_path="data/test.db")    # explicit path (tests)
"""
from __future__ import annotations

import os
import sqlite3

# ── Database path ────────────────────────────────────────────────────────────
# Separate from knowledge/arkadia.db — runtime state must not couple to
# knowledge state (different backup, retention, and migration schedules).
# Override with ARKADIA_DB_PATH env var for tests or alternative deployments.
_DEFAULT_DB_PATH = os.path.join(
    os.environ.get("SOLSPIRE_DATA_DIR", "data"),
    "runtime.db",
)


# ── DDL ──────────────────────────────────────────────────────────────────────

_PRAGMAS = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
"""

_JOBS_DDL = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id      TEXT PRIMARY KEY,
    status      TEXT NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    intent      TEXT NOT NULL DEFAULT '{}',
    result      TEXT,
    error       TEXT,
    trace       TEXT,
    retries     INTEGER NOT NULL DEFAULT 0,
    source      TEXT NOT NULL DEFAULT 'api',
    created_at  REAL NOT NULL,
    updated_at  REAL NOT NULL,
    started_at  REAL,
    ended_at    REAL
);

CREATE INDEX IF NOT EXISTS idx_jobs_status     ON jobs (status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_source     ON jobs (source);
"""

_GOALS_DDL = """
CREATE TABLE IF NOT EXISTS goals (
    goal_id           TEXT PRIMARY KEY,
    description       TEXT NOT NULL,
    status            TEXT NOT NULL DEFAULT 'active'
                           CHECK (status IN ('active', 'paused', 'completed')),
    cadence_seconds   REAL NOT NULL DEFAULT 300.0,
    max_runs_per_hour INTEGER NOT NULL DEFAULT 6,
    next_run          REAL,
    last_run          REAL,
    run_count         INTEGER NOT NULL DEFAULT 0,
    history           TEXT NOT NULL DEFAULT '[]',
    created_at        REAL NOT NULL,
    updated_at        REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_goals_status   ON goals (status);
CREATE INDEX IF NOT EXISTS idx_goals_next_run ON goals (next_run);
"""


# ── Public API ───────────────────────────────────────────────────────────────

def create_tables(db_path: str | None = None) -> str:
    """Create all runtime tables in the SQLite database at *db_path*.

    Idempotent — safe to call on every startup (``CREATE TABLE IF NOT EXISTS``).
    WAL mode is set so that concurrent readers never block on a write.

    Parameters
    ----------
    db_path:
        Path to the SQLite file.  Created (with parent directories) if absent.
        Defaults to ``data/runtime.db`` (or ``$SOLSPIRE_DATA_DIR/runtime.db``).

    Returns
    -------
    str
        The resolved database path (useful for callers that need it).
    """
    resolved = db_path or os.environ.get("ARKADIA_DB_PATH", _DEFAULT_DB_PATH)
    os.makedirs(os.path.dirname(os.path.abspath(resolved)), exist_ok=True)

    conn = sqlite3.connect(resolved)
    try:
        conn.executescript(_PRAGMAS)
        conn.executescript(_JOBS_DDL)
        conn.executescript(_GOALS_DDL)
        conn.commit()
    finally:
        conn.close()

    return resolved


__all__ = ["create_tables"]
