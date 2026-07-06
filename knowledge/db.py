"""
Arkadia Knowledge OS — SQLite Database Layer
============================================
Thread-safe per-thread connection pool via threading.local().
Each OS thread gets its own SQLite connection — no shared-state race conditions.
LAW I: One capability. One implementation. One canonical home.
"""

import sqlite3
import threading
import os
from pathlib import Path

_DB_PATH = Path(os.environ.get("ARKADIA_DB_PATH", "knowledge/arkadia.db"))
_SCHEMA_PATH = Path(__file__).parent / "schema.sql"

# Per-thread connection storage — each thread gets its own connection
_local = threading.local()


def get_connection() -> sqlite3.Connection:
    """
    Return the per-thread SQLite connection.
    Creates and initialises it on first access by this thread.
    Thread-safe: each thread owns its own connection.
    """
    if not hasattr(_local, "conn") or _local.conn is None:
        _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(_DB_PATH), check_same_thread=True)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _apply_schema(conn)
        _local.conn = conn
    return _local.conn


def _apply_schema(conn: sqlite3.Connection) -> None:
    schema = _SCHEMA_PATH.read_text()
    statements = [s.strip() for s in schema.split(";") if s.strip()]
    for stmt in statements:
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError:
            pass  # e.g. duplicate INSERT OR IGNORE on re-initialise
    conn.commit()


def execute(sql: str, params: tuple = ()) -> list[dict]:
    """
    Execute a query on this thread's connection and return rows as dicts.
    Commits automatically for DML statements (INSERT/UPDATE/DELETE).
    """
    conn = get_connection()
    cur = conn.execute(sql, params)
    # Only commit for write operations
    sql_upper = sql.strip().upper()
    if any(sql_upper.startswith(kw) for kw in ("INSERT", "UPDATE", "DELETE", "REPLACE")):
        conn.commit()
    if cur.description:
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    return []


def execute_one(sql: str, params: tuple = ()) -> dict | None:
    rows = execute(sql, params)
    return rows[0] if rows else None


def last_insert_id() -> int:
    """
    Return the last rowid inserted by THIS thread's connection.
    Safe because each thread owns its own connection.
    """
    conn = get_connection()
    cur = conn.execute("SELECT last_insert_rowid()")
    return cur.fetchone()[0]
