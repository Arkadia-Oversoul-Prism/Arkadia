"""Regression guard: the shared Knowledge OS connection survives the session.

`knowledge.db` keeps one SQLite connection per thread in `_local.conn`, shared by
every test in the session. A test that closes it must leave the slot as `None` —
`get_connection()` treats `None` as "create one", but a closed
`sqlite3.Connection` is returned as-is, so every later query in the session raises
`ProgrammingError: Cannot operate on a closed database`.

This guard runs the busy-timeout test for real and then proves the shared slot is
still usable. It is a negative control: it fails against a revision that restores
a closed connection at teardown.
"""
from __future__ import annotations

import pytest

from knowledge import db
from test_sqlite_busy_timeout import (
    test_connection_waits_for_concurrent_sqlite_writers,
)


def test_busy_timeout_test_leaves_the_shared_connection_usable(tmp_path):
    # Prime a live session connection, exactly as the full suite would have.
    db._local.conn = None
    prime = db.get_connection()
    prime.execute("SELECT 1").fetchone()

    mp = pytest.MonkeyPatch()
    try:
        test_connection_waits_for_concurrent_sqlite_writers(tmp_path, mp)
    finally:
        mp.undo()

    # Raises ProgrammingError if the test left a closed connection behind.
    conn = db.get_connection()
    assert conn.execute("SELECT 1").fetchone()[0] == 1
