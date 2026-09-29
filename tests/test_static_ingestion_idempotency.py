"""K5 — static ingestion idempotency (checksum round-trip).

An ingested object must be checksum-stable across a persistence round-trip.
`pipeline.ingest` dedupes on `sha256(content)` while `vault.create_note`
persists `frontmatter + content`; if the two disagree by so much as a trailing
newline, re-reading the written file ingests a spurious second copy. These
tests pin the convergence that `_normalize_body` provides.

They are deliberately scoped to the *round-trip* invariant — the property that
failed in production — and run against a private tempdir so they never touch
the repository vault or the shared knowledge DB.
"""
from __future__ import annotations

import hashlib

import tempfile
from pathlib import Path

import pytest

from knowledge import static_ingestion


@pytest.fixture()
def isolated_knowledge(monkeypatch):
    """Point the DB and vault at a throwaway directory for this test only."""
    from knowledge import db as knowledge_db
    from knowledge import vault as knowledge_vault
    import knowledge as knowledge_pkg

    sandbox = Path(tempfile.mkdtemp(prefix="k5_idempotency_"))
    monkeypatch.setattr(knowledge_db, "_DB_PATH", sandbox / "knowledge.db")
    monkeypatch.setattr(knowledge_pkg, "_DB_PATH", sandbox / "knowledge.db")

    vault_root = sandbox / "vault"
    monkeypatch.setattr(knowledge_vault, "VAULT_ROOT", vault_root)
    monkeypatch.setattr(knowledge_pkg, "VAULT_ROOT", vault_root)
    yield sandbox


def test_normalize_body_strips_trailing_whitespace():
    assert static_ingestion._normalize_body("body\n") == "body"
    assert static_ingestion._normalize_body("body\n\n  ") == "body"
    assert static_ingestion._normalize_body("  body  ") == "body"


def test_open_loop_content_is_checksum_stable_through_a_vault_round_trip(
    isolated_knowledge,
):
    """The production failure: write -> re-read -> checksum must be identical."""
    from knowledge import vault as knowledge_vault

    loops = static_ingestion._oracle_open_loop_rows()
    assert loops, "oracle store has no open-loop records to verify"

    for loop in loops[:3]:
        text = str(loop.get("loop") or "unidentified")
        content = static_ingestion._normalize_body(
            f"Open loop\n"
            f"ID: {loop.get('id') or 'unidentified'}\n"
            f"Loop: {text}"
        )
        note = knowledge_vault.create_note(
            title=f"Open loop: {text}",
            content=content,
            note_type="task",
            source_provider="static:oracle_open_loops",
        )

        note_path = knowledge_vault.VAULT_ROOT / note["vault_path"]
        file_text = note_path.read_text(encoding="utf-8")

        _, body = static_ingestion._strip_frontmatter(file_text)
        reread = static_ingestion._normalize_body(body or file_text)

        assert hashlib.sha256(reread.encode()).hexdigest() == note["checksum"], (
            f"checksum drifted for {text!r}: the projection is not a fixed point "
            "of the ingest checksum"
        )
