"""SQLite connection lock-wait configuration regression test."""
from __future__ import annotations

from pathlib import Path

from knowledge import db


def test_connection_waits_for_concurrent_sqlite_writers(tmp_path, monkeypatch):
    # Each test gets an independent database and connection in this thread.
    monkeypatch.setattr(db, "_DB_PATH", Path(tmp_path) / "knowledge.db")
    old_conn = getattr(db._local, "conn", None)
    if old_conn is not None:
        old_conn.close()
    monkeypatch.setattr(db._local, "conn", None, raising=False)

    conn = db.get_connection()
    assert conn.execute("PRAGMA busy_timeout").fetchone()[0] == 30_000
    assert conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    conn.close()
    monkeypatch.setattr(db._local, "conn", None, raising=False)
