"""Buyer Recon board contract — the two repaired defects and their migration.

This file binds the *repair* introduced under `SHARED-CONTRACTS.md` §1/§7.1 for
`solspire/buyer_recon.py`:

  * defect 1 — `create_entry` supplied 34 values to a 33-column table;
  * defect 2 — `buyer_recon_boards.subject_ref` was UNIQUE on the subject alone,
    so one subject could not hold both a workspace board and a project board.

The migration is measured against a **legacy-shaped** database built here from
the pre-fix DDL, not only against a fresh one, so "preserves existing data" is an
observation rather than a claim. Negative controls accompany each detector.
"""
from __future__ import annotations

import importlib
import sqlite3

import pytest

import solspire.buyer_recon as buyer_recon

# The pre-fix board DDL, verbatim: both `workspace_ref` and `subject_ref` UNIQUE.
LEGACY_BOARDS_DDL = """
CREATE TABLE buyer_recon_boards (
  id TEXT PRIMARY KEY,
  workspace_ref TEXT NOT NULL UNIQUE,
  subject_ref TEXT NOT NULL UNIQUE,
  board_type TEXT NOT NULL,
  display_name TEXT NOT NULL,
  lifecycle TEXT NOT NULL DEFAULT 'active',
  created_at REAL NOT NULL,
  updated_at REAL NOT NULL
)
"""

LEGACY_ENTRIES_DDL = """
CREATE TABLE buyer_recon_entries (
  id TEXT PRIMARY KEY,
  board_id TEXT NOT NULL,
  subject_ref TEXT NOT NULL,
  prospect TEXT NOT NULL,
  location TEXT NOT NULL DEFAULT '',
  buyer_type TEXT NOT NULL DEFAULT '',
  contact_route TEXT NOT NULL DEFAULT '',
  commodity TEXT NOT NULL DEFAULT '',
  estimated_demand TEXT NOT NULL DEFAULT 'UNKNOWN',
  procurement_frequency TEXT NOT NULL DEFAULT 'UNKNOWN',
  decision_maker TEXT NOT NULL DEFAULT 'UNKNOWN',
  current_price TEXT NOT NULL DEFAULT 'UNKNOWN',
  quantity TEXT NOT NULL DEFAULT 'UNKNOWN',
  specification TEXT NOT NULL DEFAULT 'UNKNOWN',
  delivery_point TEXT NOT NULL DEFAULT 'UNKNOWN',
  delivery_window TEXT NOT NULL DEFAULT 'UNKNOWN',
  payment_terms TEXT NOT NULL DEFAULT 'UNKNOWN',
  supplier TEXT NOT NULL DEFAULT 'UNKNOWN',
  source_price TEXT NOT NULL DEFAULT 'UNKNOWN',
  available_quantity TEXT NOT NULL DEFAULT 'UNKNOWN',
  logistics_quote TEXT NOT NULL DEFAULT 'UNKNOWN',
  packaging_qc_cost TEXT NOT NULL DEFAULT 'UNKNOWN',
  landed_cost TEXT NOT NULL DEFAULT 'UNKNOWN',
  buyer_price TEXT NOT NULL DEFAULT 'UNKNOWN',
  expected_gross_margin TEXT NOT NULL DEFAULT 'UNKNOWN',
  capital_required TEXT NOT NULL DEFAULT 'UNKNOWN',
  evidence_status TEXT NOT NULL DEFAULT 'NONE',
  evidence_json TEXT NOT NULL DEFAULT '[]',
  why_this_prospect TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'UNCONTACTED',
  notes TEXT NOT NULL DEFAULT '',
  created_at REAL NOT NULL,
  updated_at REAL NOT NULL,
  FOREIGN KEY(board_id) REFERENCES buyer_recon_boards(id)
)
"""

SUBJECT = "uid-legacy"
WORKSPACE = "ws-legacy"


@pytest.fixture()
def legacy_db(tmp_path, monkeypatch):
    """A database in the exact pre-repair shape, with one board and one entry."""
    db = tmp_path / "solspire_projects.db"
    monkeypatch.setattr(buyer_recon, "_DB_PATH", str(db))
    conn = sqlite3.connect(db)
    conn.executescript(LEGACY_BOARDS_DDL)
    conn.executescript(LEGACY_ENTRIES_DDL)
    conn.execute(
        "INSERT INTO buyer_recon_boards VALUES (?,?,?,?,?,?,?,?)",
        ("legacy-b1", WORKSPACE, SUBJECT, "eden_buyer_recon", "Eden Buyer Recon", "active", 10.0, 11.0),
    )
    conn.execute(
        """INSERT INTO buyer_recon_entries
           (id, board_id, subject_ref, prospect, status, evidence_status, evidence_json, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        ("legacy-e1", "legacy-b1", SUBJECT, "Existing Buyer", "REQUIREMENT_CAPTURED",
         "NONE", '[{"note": "kept"}]', 10.0, 12.0),
    )
    conn.commit()
    conn.close()
    return db


@pytest.fixture()
def fresh_db(tmp_path, monkeypatch):
    db = tmp_path / "solspire_projects.db"
    monkeypatch.setattr(buyer_recon, "_DB_PATH", str(db))
    return db


def _unique_index_column_sets(db: str) -> list[set[str]]:
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    try:
        sets = []
        for row in conn.execute("PRAGMA index_list(buyer_recon_boards)").fetchall():
            if row["unique"]:
                sets.append({r[2] for r in conn.execute(f"PRAGMA index_info({row['name']!r})").fetchall()})
        return sets
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Defect 1 — create-entry arity
# ---------------------------------------------------------------------------


def test_create_entry_column_and_value_counts_match(fresh_db):
    """The named column list and the value tuple are the same length, always."""
    manager = buyer_recon.BuyerReconManager()
    board = manager.get_or_create(WORKSPACE, SUBJECT)
    entry = manager.create_entry(board, {"prospect": "Arity Buyer"})
    assert len(buyer_recon._ENTRY_COLUMNS) == 33
    with buyer_recon._db() as conn:
        columns = [r["name"] for r in conn.execute("PRAGMA table_info(buyer_recon_entries)")]
    assert set(buyer_recon._ENTRY_COLUMNS) == set(columns)
    assert entry.prospect == "Arity Buyer"


def test_create_entry_names_columns_so_arity_cannot_drift(fresh_db):
    """The insert names its columns and derives them from the dataclass."""
    from pathlib import Path

    source = Path(buyer_recon.__file__).read_text(encoding="utf-8")
    assert "INSERT INTO buyer_recon_entries ({columns})" in source
    assert "_ENTRY_COLUMNS" in source


def test_negative_control_the_legacy_bare_values_insert_would_still_mismatch(fresh_db):
    """Proves the arity detector is not vacuous: the old shape really does fail.

    Reproduces the pre-fix statement (34 placeholders, 33 columns) against the
    live table and asserts it raises — so a detector that reported "no mismatch"
    unconditionally would be caught.
    """
    buyer_recon._db()  # materialize the schema
    with buyer_recon._db() as conn:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute(
                "INSERT INTO buyer_recon_entries VALUES (" + ",".join("?" * 34) + ")",
                tuple(range(34)),
            )


# ---------------------------------------------------------------------------
# Defect 2 — one board per subject
# ---------------------------------------------------------------------------


def test_fresh_database_allows_workspace_and_project_boards(fresh_db):
    manager = buyer_recon.BuyerReconManager()
    workspace_board = manager.get_or_create(WORKSPACE, SUBJECT)
    project_board = manager.get_or_create(f"{WORKSPACE}:project:p1", SUBJECT)
    assert workspace_board.id != project_board.id
    with buyer_recon._db() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM buyer_recon_boards WHERE subject_ref=?", (SUBJECT,)
        ).fetchone()[0]
    assert count == 2


def test_unique_scope_is_the_composite_not_the_subject(fresh_db):
    buyer_recon._db()
    assert {"workspace_ref", "subject_ref"} in _unique_index_column_sets(fresh_db)
    # The legacy subject-only uniqueness must be gone.
    assert {"subject_ref"} not in _unique_index_column_sets(fresh_db)


def test_negative_control_a_duplicate_composite_scope_is_still_rejected(fresh_db):
    """The composite uniqueness keeps its teeth after the rebuild."""
    manager = buyer_recon.BuyerReconManager()
    manager.get_or_create(WORKSPACE, SUBJECT)
    with pytest.raises(sqlite3.IntegrityError):
        with buyer_recon._db() as conn:
            conn.execute(
                "INSERT INTO buyer_recon_boards VALUES (?,?,?,?,?,?,?,?)",
                ("dup", WORKSPACE, SUBJECT, "eden_buyer_recon", "Eden Buyer Recon", "active", 1.0, 1.0),
            )


# ---------------------------------------------------------------------------
# Migration — existing data is preserved
# ---------------------------------------------------------------------------


def test_migration_preserves_the_existing_board_and_entries(legacy_db):
    manager = buyer_recon.BuyerReconManager()
    board = manager.get_or_create(WORKSPACE, SUBJECT)
    assert board.id == "legacy-b1", "the pre-existing board must survive the migration byte-for-byte"
    entries = manager.list_entries(board.id, SUBJECT)
    assert [(e.id, e.prospect, e.status) for e in entries] == [
        ("legacy-e1", "Existing Buyer", "REQUIREMENT_CAPTURED")
    ]
    assert entries[0].evidence == [{"note": "kept"}], "evidence_json must be preserved"
    assert entries[0].buyer_price == "UNKNOWN", "unverified defaults must be preserved"


def test_migration_removes_the_subject_only_constraint(legacy_db):
    buyer_recon._db()  # the migration runs on first touch
    assert {"subject_ref"} not in _unique_index_column_sets(legacy_db)
    assert {"workspace_ref", "subject_ref"} in _unique_index_column_sets(legacy_db)


def test_migration_lets_a_legacy_subject_gain_a_project_board(legacy_db):
    manager = buyer_recon.BuyerReconManager()
    manager.get_or_create(WORKSPACE, SUBJECT)
    project_board = manager.get_or_create(f"{WORKSPACE}:project:p1", SUBJECT)
    assert project_board.workspace_ref == f"{WORKSPACE}:project:p1"
    with buyer_recon._db() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM buyer_recon_boards WHERE subject_ref=?", (SUBJECT,)
        ).fetchone()[0]
    assert count == 2


def test_migration_preserves_the_foreign_key_binding(legacy_db):
    """`buyer_recon_entries.board_id` must still reference the renamed table."""
    buyer_recon._db()
    conn = sqlite3.connect(legacy_db)
    try:
        sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE name='buyer_recon_entries'"
        ).fetchone()[0]
        assert "buyer_recon_boards(id)" in sql
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        conn.close()


def test_migration_is_idempotent_on_a_fresh_database(fresh_db):
    """Calling `_db()` repeatedly never rebuilds an already-migrated table."""
    buyer_recon._db()
    before = _unique_index_column_sets(fresh_db)
    for _ in range(3):
        buyer_recon._db()
    assert _unique_index_column_sets(fresh_db) == before


def test_migration_is_idempotent_on_a_legacy_database(legacy_db):
    buyer_recon._db()
    after_first = _unique_index_column_sets(legacy_db)
    for _ in range(3):
        buyer_recon._db()
    assert _unique_index_column_sets(legacy_db) == after_first
    with buyer_recon._db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM buyer_recon_entries").fetchone()[0] == 1


def test_migration_does_not_leave_legacy_alter_table_armed(legacy_db):
    """The pragma is restored, so it cannot leak into unrelated connections."""
    buyer_recon._db()
    conn = sqlite3.connect(legacy_db)
    try:
        assert conn.execute("PRAGMA legacy_alter_table").fetchone()[0] == 0
    finally:
        conn.close()


def test_negative_control_an_unmigrated_legacy_db_really_does_reject_a_second_board(legacy_db):
    """Proves the migration detector is not vacuous.

    Before any touch by the module, the legacy schema rejects a second board for
    the same subject — the exact defect the migration repairs.
    """
    conn = sqlite3.connect(legacy_db)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO buyer_recon_boards VALUES (?,?,?,?,?,?,?,?)",
                ("legacy-b2", f"{WORKSPACE}:project:p1", SUBJECT, "eden_buyer_recon",
                 "Eden Buyer Recon", "active", 1.0, 1.0),
            )
    finally:
        conn.close()
    # And after the module touches it, the same insert succeeds.
    buyer_recon._db()
    conn = sqlite3.connect(legacy_db)
    try:
        conn.execute(
            "INSERT INTO buyer_recon_boards VALUES (?,?,?,?,?,?,?,?)",
            ("legacy-b2", f"{WORKSPACE}:project:p1", SUBJECT, "eden_buyer_recon",
             "Eden Buyer Recon", "active", 1.0, 1.0),
        )
        conn.commit()
        assert conn.execute("SELECT COUNT(*) FROM buyer_recon_boards").fetchone()[0] == 2
    finally:
        conn.close()


def test_module_reimport_does_not_disturb_a_migrated_database(legacy_db):
    """A reload (fresh process semantics) re-runs the migration guard harmlessly."""
    buyer_recon._db()
    reloaded = importlib.reload(buyer_recon)
    reloaded._db()
    conn = sqlite3.connect(legacy_db)
    try:
        assert conn.execute("SELECT COUNT(*) FROM buyer_recon_boards").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM buyer_recon_entries").fetchone()[0] == 1
    finally:
        conn.close()
