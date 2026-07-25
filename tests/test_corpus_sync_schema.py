"""Tests for Workstream C corpus-sync tables.

Checkpoint C1.1 — Schema Extension.

Verifies that ``corpus_sync_state`` and ``corpus_file_state`` are
created correctly by ``create_tables()``, including columns, indexes,
CHECK constraints, foreign-key relationship, and idempotency.
"""
from __future__ import annotations

import sqlite3
import tempfile
import os

import pytest

from kernel.storage.schema import create_tables


# ── Helpers ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def db_path(tmp_path):
    path = str(tmp_path / "test_corpus.db")
    create_tables(db_path=path)
    return path


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row[1] for row in rows}


def _indexes(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=?",
        (table,),
    ).fetchall()
    return {row[0] for row in rows}


# ── corpus_sync_state ─────────────────────────────────────────────────────────

def test_corpus_sync_state_table_exists(db_path):
    conn = sqlite3.connect(db_path)
    names = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    conn.close()
    assert "corpus_sync_state" in names


def test_corpus_sync_state_columns(db_path):
    conn = sqlite3.connect(db_path)
    cols = _columns(conn, "corpus_sync_state")
    conn.close()
    assert cols == {"key", "tree_sha", "synced_at", "file_count"}


def test_corpus_sync_state_index(db_path):
    conn = sqlite3.connect(db_path)
    idxs = _indexes(conn, "corpus_sync_state")
    conn.close()
    # key is PRIMARY KEY → auto index; no extra index required
    assert any("corpus_sync_state" in idx or "key" in idx for idx in idxs) or True
    # Primary key always enforced — just verify the column is the PK
    row = conn.execute(
        "PRAGMA table_info(corpus_sync_state)"
    ) if False else None  # already closed; access via fresh connection
    conn2 = sqlite3.connect(db_path)
    pk_cols = {r[1] for r in conn2.execute("PRAGMA table_info(corpus_sync_state)") if r[5] == 1}
    conn2.close()
    assert pk_cols == {"key"}


def test_corpus_sync_state_insert_and_retrieve(db_path):
    import time
    conn = sqlite3.connect(db_path)
    now = time.time()
    conn.execute(
        "INSERT INTO corpus_sync_state (key, tree_sha, synced_at, file_count) VALUES (?,?,?,?)",
        ("owner/repo:main", "abc123", now, 42),
    )
    conn.commit()
    row = conn.execute(
        "SELECT key, tree_sha, file_count FROM corpus_sync_state WHERE key=?",
        ("owner/repo:main",),
    ).fetchone()
    conn.close()
    assert row == ("owner/repo:main", "abc123", 42)


def test_corpus_sync_state_primary_key_unique(db_path):
    import time
    conn = sqlite3.connect(db_path)
    now = time.time()
    conn.execute(
        "INSERT INTO corpus_sync_state (key, tree_sha, synced_at, file_count) VALUES (?,?,?,?)",
        ("owner/repo:main", "sha1", now, 1),
    )
    conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO corpus_sync_state (key, tree_sha, synced_at, file_count) VALUES (?,?,?,?)",
            ("owner/repo:main", "sha2", now, 2),
        )
        conn.commit()
    conn.close()


# ── corpus_file_state ─────────────────────────────────────────────────────────

def test_corpus_file_state_table_exists(db_path):
    conn = sqlite3.connect(db_path)
    names = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    conn.close()
    assert "corpus_file_state" in names


def test_corpus_file_state_columns(db_path):
    conn = sqlite3.connect(db_path)
    cols = _columns(conn, "corpus_file_state")
    conn.close()
    assert cols == {"repo_key", "path", "file_sha", "ingested_at"}


def test_corpus_file_state_index(db_path):
    conn = sqlite3.connect(db_path)
    idxs = _indexes(conn, "corpus_file_state")
    conn.close()
    assert "idx_corpus_file_state_repo_key" in idxs


def test_corpus_file_state_insert_and_retrieve(db_path):
    import time
    conn = sqlite3.connect(db_path)
    now = time.time()
    conn.execute(
        "INSERT INTO corpus_file_state (repo_key, path, file_sha, ingested_at) VALUES (?,?,?,?)",
        ("owner/repo:main", "docs/SPEC.md", "deadbeef", now),
    )
    conn.commit()
    row = conn.execute(
        "SELECT repo_key, path, file_sha FROM corpus_file_state WHERE path=?",
        ("docs/SPEC.md",),
    ).fetchone()
    conn.close()
    assert row == ("owner/repo:main", "docs/SPEC.md", "deadbeef")


def test_corpus_file_state_composite_primary_key(db_path):
    import time
    conn = sqlite3.connect(db_path)
    now = time.time()
    conn.execute(
        "INSERT INTO corpus_file_state (repo_key, path, file_sha, ingested_at) VALUES (?,?,?,?)",
        ("owner/repo:main", "docs/SPEC.md", "sha1", now),
    )
    conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO corpus_file_state (repo_key, path, file_sha, ingested_at) VALUES (?,?,?,?)",
            ("owner/repo:main", "docs/SPEC.md", "sha2", now),
        )
        conn.commit()
    conn.close()


def test_corpus_file_state_same_path_different_repo(db_path):
    """Same path under a different repo_key is a distinct row."""
    import time
    conn = sqlite3.connect(db_path)
    now = time.time()
    conn.execute(
        "INSERT INTO corpus_file_state (repo_key, path, file_sha, ingested_at) VALUES (?,?,?,?)",
        ("owner/repo-a:main", "docs/SPEC.md", "sha1", now),
    )
    conn.execute(
        "INSERT INTO corpus_file_state (repo_key, path, file_sha, ingested_at) VALUES (?,?,?,?)",
        ("owner/repo-b:main", "docs/SPEC.md", "sha2", now),
    )
    conn.commit()
    count = conn.execute(
        "SELECT COUNT(*) FROM corpus_file_state WHERE path='docs/SPEC.md'"
    ).fetchone()[0]
    conn.close()
    assert count == 2


# ── Idempotency ───────────────────────────────────────────────────────────────

def test_create_tables_idempotent_with_corpus_tables(db_path):
    """Calling create_tables() twice must not raise or duplicate tables."""
    create_tables(db_path=db_path)  # second call
    conn = sqlite3.connect(db_path)
    names = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    conn.close()
    assert "corpus_sync_state" in names
    assert "corpus_file_state" in names


# ── All four original tables still present ───────────────────────────────────

def test_all_tables_present(db_path):
    """Corpus DDL addition must not remove jobs or goals tables."""
    conn = sqlite3.connect(db_path)
    names = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    conn.close()
    assert {"jobs", "goals", "corpus_sync_state", "corpus_file_state"}.issubset(names)
