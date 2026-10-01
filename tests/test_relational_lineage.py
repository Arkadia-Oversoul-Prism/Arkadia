"""Canonical relational lineage projection tests."""
from __future__ import annotations

import hashlib
import os
import tempfile

_tmpdir = tempfile.mkdtemp(prefix="arkadia_lineage_")
os.environ["ARKADIA_DB_PATH"] = os.path.join(_tmpdir, "test.db")

from knowledge import capture as cap
from knowledge.graph import full_graph_export, traverse
from knowledge.vault import create_note
from knowledge.db import get_connection


def _reset() -> None:
    conn = get_connection()
    for table in (
        "capture_records", "capture_sources", "graph_edges", "timeline",
        "chunks", "embeddings", "note_tags", "notes", "threads", "projects",
    ):
        try:
            conn.execute(f"DELETE FROM {table}")
        except Exception:
            pass
    conn.commit()


def test_graph_node_exposes_canonical_capture_provenance():
    _reset()
    note = create_note(
        title="Lineage node",
        content="raw lineage content",
        note_type="document",
        user_id=None,
    )
    source = cap.register_source(
        source_kind="document", source_ref="test:lineage", title="Lineage source"
    )
    capture = cap.capture(
        source_uuid=source["source_uuid"],
        raw_content="raw lineage content",
        content_kind="document",
        captured_by="system:test",
        captured_by_kind="system",
        authored_by=None,
        authored_by_kind="unknown",
    )
    cap.bind_capture_to_note(
        capture_uuid=capture["capture_uuid"], note_id=note["id"]
    )

    exported = full_graph_export(user_id=None)
    node = next(n for n in exported["nodes"] if n["id"] == note["id"])

    assert node["provenance"]["capture_uuid"] == capture["capture_uuid"]
    assert node["provenance"]["raw_checksum"] == hashlib.sha256(
        b"raw lineage content"
    ).hexdigest()
    assert node["provenance"]["authorship"]["authored_by"] is None
    assert node["provenance"]["source"]["source_ref"] == "test:lineage"


def test_graph_node_without_capture_remains_explicitly_unknown():
    _reset()
    note = create_note(
        title="Unknown lineage",
        content="legacy note",
        note_type="note",
        user_id=None,
    )
    exported = full_graph_export(user_id=None)
    node = next(n for n in exported["nodes"] if n["id"] == note["id"])
    assert node["provenance"] == {"state": "UNKNOWN"}


def test_traversal_preserves_provenance_projection():
    _reset()
    note = create_note(
        title="Traversed lineage",
        content="captured",
        note_type="document",
        user_id=None,
    )
    source = cap.register_source(
        source_kind="document", source_ref="test:traverse", title="Traverse source"
    )
    capture = cap.capture(
        source_uuid=source["source_uuid"],
        raw_content="captured",
        content_kind="document",
        captured_by="system:test",
        captured_by_kind="system",
    )
    cap.bind_capture_to_note(
        capture_uuid=capture["capture_uuid"], note_id=note["id"]
    )

    traversed = traverse(note["id"], max_depth=1, user_id=None)
    node = next(n for n in traversed["nodes"] if n["id"] == note["id"])
    assert node["provenance"]["capture_uuid"] == capture["capture_uuid"]
