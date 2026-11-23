"""K5 — static ingestion idempotency (checksum round-trip).

An ingested object must be checksum-stable across a persistence round-trip.
`pipeline.ingest` dedupes on `sha256(content)` while `vault.create_note`
persists `frontmatter + content`; if the two disagree by so much as a trailing
newline, re-reading the written file ingests a spurious second copy. These
tests pin the convergence that `_normalize_body` provides.

They are deliberately scoped to the *round-trip* invariant — the property that
failed in production — and run against a private tempdir so they never touch
the repository vault, the shared knowledge DB, or the oracle store.

The oracle store is part of that isolation, not an exception to it.
`static_ingestion._ORACLE_STORE_PATH` is snapshotted from `SOLSPIRE_DATA_DIR` at
*import* time, so any earlier module that sets that variable process-wide
redirects it for the rest of the session. Measured on `main` @ `bb19aabd`:
`tests/test_ao006_canvas_contract.py` sets `SOLSPIRE_DATA_DIR` to its own tempdir
at import and never restores it, so this module — imported later — read a
nonexistent `oracle_store.json`, `_oracle_open_loop_rows()` returned `[]`, and
`assert loops` failed. Both modules pass in isolation; together they failed. The
fixture therefore pins the oracle store to a deterministic file inside the same
sandbox instead of inheriting whatever the ambient environment happens to hold.
"""
from __future__ import annotations

import hashlib
import json

import tempfile
from pathlib import Path

import pytest

from knowledge import static_ingestion

#: Deterministic open-loop rows for the round-trip check. Deliberately carries
#: trailing newlines and padding so `_normalize_body` is exercised rather than
#: bypassed; the invariant is checksum stability, not the oracle's own contents.
_ORACLE_LOOPS = [
    {"id": "K5-1", "loop": "Reconcile the static ingestion pass\n", "status": "open"},
    {"id": "K5-2", "loop": "  Verify the checksum fixed point  ", "status": "open"},
]


@pytest.fixture()
def isolated_knowledge(monkeypatch):
    """Point the DB, vault and oracle store at a throwaway directory."""
    from knowledge import db as knowledge_db
    from knowledge import vault as knowledge_vault
    import knowledge as knowledge_pkg

    sandbox = Path(tempfile.mkdtemp(prefix="k5_idempotency_"))
    monkeypatch.setattr(knowledge_db, "_DB_PATH", sandbox / "knowledge.db")
    monkeypatch.setattr(knowledge_pkg, "_DB_PATH", sandbox / "knowledge.db")

    vault_root = sandbox / "vault"
    monkeypatch.setattr(knowledge_vault, "VAULT_ROOT", vault_root)
    monkeypatch.setattr(knowledge_pkg, "VAULT_ROOT", vault_root)

    oracle_store = sandbox / "oracle_store.json"
    oracle_store.write_text(json.dumps({"open_loops": _ORACLE_LOOPS}), encoding="utf-8")
    monkeypatch.setattr(static_ingestion, "_ORACLE_STORE_PATH", oracle_store)
    yield sandbox


def test_normalize_body_strips_trailing_whitespace():
    assert static_ingestion._normalize_body("body\n") == "body"
    assert static_ingestion._normalize_body("body\n\n  ") == "body"
    assert static_ingestion._normalize_body("  body  ") == "body"


def test_the_oracle_store_is_sandboxed(isolated_knowledge):
    """The fixture must own the oracle path, not inherit it from the environment.

    A fixture that isolates only the DB and vault leaves this module reading
    whatever `SOLSPIRE_DATA_DIR` an earlier test module happened to set. That is
    the exact defect this fixture repairs, so it is asserted rather than assumed:
    the path must resolve inside the sandbox the fixture created.
    """
    assert static_ingestion._ORACLE_STORE_PATH.parent == isolated_knowledge
    assert static_ingestion._ORACLE_STORE_PATH.exists()
    assert static_ingestion._oracle_open_loop_rows(), "fixture must supply rows"


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
