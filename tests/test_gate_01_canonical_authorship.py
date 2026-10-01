"""
GATE-01 — Canonical Authorship: SOURCE → CAPTURE → CANONICAL RECORD → AUTHORSHIP → PROVENANCE.

These tests exercise the real Knowledge OS code paths against an isolated
SQLite file and vault. No mocks.

They prove, per the GATE-01 success condition:
  - the capture boundary cannot be skipped (SOURCE → CAPTURE enforced)
  - raw capture is byte-identical and content-addressed
  - authorship is declared, never inferred from source/captor/content
  - UNKNOWN is preserved (never fabricated into a fact)
  - provenance names the canonical origin and is reconstructable
"""
from __future__ import annotations

import hashlib
import os
import tempfile

import pytest

_tmpdir = tempfile.mkdtemp(prefix="arkadia_gate01_")
os.environ["ARKADIA_DB_PATH"] = os.path.join(_tmpdir, "knowledge.db")

import knowledge.db as db
import knowledge.vault as vault
from knowledge import capture as cap
from knowledge import pipeline


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    """Fresh vault and clean Knowledge OS rows for every test.

    Follows the repository's established isolation pattern (environment path
    plus explicit row purge) rather than monkeypatching knowledge.db._DB_PATH:
    that module caches a per-thread connection and never re-checks its path,
    so rebinding the path leaks a stale connection into later test modules.
    """
    monkeypatch.setattr(vault, "VAULT_ROOT", tmp_path / "vault")
    db._local.conn = None
    for table in (
        "capture_records", "capture_sources", "graph_edges", "timeline",
        "chunks", "embeddings", "note_tags", "notes", "threads", "projects",
    ):
        try:
            db.execute(f"DELETE FROM {table}")
        except Exception:
            pass
    yield
    db._local.conn = None


# ── SOURCE ───────────────────────────────────────────────────────────────────

def test_source_registration_is_idempotent_by_origin():
    a = cap.register_source(source_kind="message", source_ref="wa:+234", title="Supplier chat")
    b = cap.register_source(source_kind="message", source_ref="wa:+234", title="Supplier chat")
    assert a["source_uuid"] == b["source_uuid"]
    assert a["fingerprint"] == b["fingerprint"]


def test_distinct_origins_are_distinct_sources():
    a = cap.register_source(source_kind="message", source_ref="wa:+234")
    b = cap.register_source(source_kind="message", source_ref="wa:+235")
    assert a["source_uuid"] != b["source_uuid"]


def test_unknown_source_kind_is_rejected():
    with pytest.raises(ValueError):
        cap.register_source(source_kind="telepathy", source_ref="x")


def test_source_ref_absent_remains_unknown():
    s = cap.register_source(source_kind="manual")
    assert s["source_ref"] is None
    assert s["title"] is None


# ── CAPTURE (SOURCE → CAPTURE enforced) ──────────────────────────────────────

def test_capture_requires_a_registered_source():
    with pytest.raises(LookupError):
        cap.capture(source_uuid="does-not-exist", raw_content="hello")


def test_capture_is_byte_identical_and_content_addressed():
    s = cap.register_source(source_kind="document", source_ref="doc-1")
    raw = "Price is ₦1,200 per crate.\nSecond line."
    c = cap.capture(source_uuid=s["source_uuid"], raw_content=raw, content_kind="document")
    assert c["raw_checksum"] == hashlib.sha256(raw.encode("utf-8")).hexdigest()


def test_capture_unknown_content_kind_is_rejected():
    s = cap.register_source(source_kind="document", source_ref="doc-2")
    with pytest.raises(ValueError):
        cap.capture(source_uuid=s["source_uuid"], raw_content="x", content_kind="rumour")


# ── AUTHORSHIP (declared, not inferred) ──────────────────────────────────────

def test_authorship_is_not_inferred_from_source_or_captor():
    s = cap.register_source(source_kind="message", source_ref="wa:+234")
    c = cap.capture(
        source_uuid=s["source_uuid"],
        raw_content="We confirm 40 crates.",
        captured_by="user-captor",
        captured_by_kind="human",
        # authorship not declared
    )
    assert c["authored_by"] is None
    assert c["authored_by_kind"] == "unknown"


def test_authorship_human_is_recorded_when_declared():
    s = cap.register_source(source_kind="message", source_ref="wa:+234")
    c = cap.capture(
        source_uuid=s["source_uuid"],
        raw_content="We confirm 40 crates.",
        authored_by="user-author",
        authored_by_kind="human",
    )
    assert c["authored_by"] == "user-author"
    assert c["authored_by_kind"] == "human"


def test_declared_actor_with_unknown_nature_keeps_actor_but_unknown_kind():
    s = cap.register_source(source_kind="api", source_ref="erp")
    c = cap.capture(source_uuid=s["source_uuid"], raw_content="{}", authored_by="svc-1")
    assert c["authored_by"] == "svc-1"
    assert c["authored_by_kind"] == "unknown"


def test_actor_kind_requires_declared_actor():
    s = cap.register_source(source_kind="api", source_ref="erp-2")
    c = cap.capture(source_uuid=s["source_uuid"], raw_content="{}", captured_by_kind="human")
    assert c["captured_by"] is None
    assert c["captured_by_kind"] == "unknown"


# ── CANONICAL RECORD + PROVENANCE ────────────────────────────────────────────

def test_capture_binds_to_canonical_note_and_provenance_names_origin():
    s = cap.register_source(source_kind="document", source_ref="invoice-7", title="Invoice 7")
    c = cap.capture(
        source_uuid=s["source_uuid"],
        raw_content="Total: ₦500,000",
        content_kind="document",
        authored_by="user-author",
        authored_by_kind="human",
    )
    note = vault.create_note(title="Invoice 7", content="Total: ₦500,000")
    cap.bind_capture_to_note(capture_uuid=c["capture_uuid"], note_id=note["id"])

    prov = cap.provenance_for_note(note["id"])
    assert prov["source"]["source_uuid"] == s["source_uuid"]
    assert prov["source"]["source_ref"] == "invoice-7"
    assert prov["authorship"]["authored_by"] == "user-author"
    assert prov["authorship"]["declared"] is True
    assert prov["canonical_origin"]["source_uuid"] == s["source_uuid"]


def test_provenance_preserves_unknown_author():
    s = cap.register_source(source_kind="message", source_ref="wa:+999")
    c = cap.capture(source_uuid=s["source_uuid"], raw_content="unattributed")
    note = vault.create_note(title="Unattributed", content="unattributed")
    cap.bind_capture_to_note(capture_uuid=c["capture_uuid"], note_id=note["id"])
    prov = cap.provenance_for_note(note["id"])
    assert prov["authorship"]["authored_by"] is None
    assert prov["authorship"]["declared"] is False


def test_note_without_capture_has_unknown_provenance():
    note = vault.create_note(title="Legacy", content="no capture")
    prov = cap.provenance_for_note(note["id"])
    assert prov["state"] == "UNKNOWN"
    assert prov["unknown"] is True
    assert prov["source"] is None


def test_provenance_for_missing_capture_is_unknown():
    prov = cap.provenance_for_capture("no-such-capture")
    assert prov["state"] == "UNKNOWN"
    assert prov["unknown"] is True


# ── END-TO-END ───────────────────────────────────────────────────────────────

def test_capture_and_ingest_traces_source_to_canonical_record():
    result = cap.capture_and_ingest(
        source_kind="message",
        source_ref="wa:+234",
        source_title="Supplier chat",
        raw_content="Confirmed 40 crates at ₦1,200.",
        title="Supplier confirmation",
        content_kind="message",
        authored_by="user-author",
        authored_by_kind="human",
    )
    assert result["note_id"] is not None
    prov = result["provenance"]
    assert prov["source"]["source_ref"] == "wa:+234"
    assert prov["authorship"]["authored_by"] == "user-author"
    assert prov["state"] == "BOUND"

    # Reconstructed independently from durable records, not from the return value.
    again = cap.provenance_for_note(result["note_id"])
    assert again["source"]["source_uuid"] == result["source"]["source_uuid"]
    assert again["raw_checksum"] == result["capture"]["raw_checksum"]


def test_capture_and_ingest_is_idempotent_for_duplicate_content():
    first = cap.capture_and_ingest(
        source_kind="message", source_ref="wa:+234",
        raw_content="Same body text.", title="First",
    )
    second = cap.capture_and_ingest(
        source_kind="message", source_ref="wa:+234",
        raw_content="Same body text.", title="Second",
    )
    assert first["note_id"] == second["note_id"]


def test_capture_boundary_transitions_are_recorded():
    s = cap.register_source(source_kind="document", source_ref="log-1")
    c = cap.capture(source_uuid=s["source_uuid"], raw_content="entry")
    note = vault.create_note(title="Log", content="entry")
    cap.bind_capture_to_note(capture_uuid=c["capture_uuid"], note_id=note["id"])
    # Read the immutable log directly: recording is durable regardless of
    # whether an anonymous viewer is permitted to see the rows.
    rows = db.execute("SELECT event_type FROM timeline")
    types = {r["event_type"] for r in rows}
    assert {"source_registered", "capture_recorded", "capture_bound"} <= types


# ── SHARED INGRESS BOUNDARY ──────────────────────────────────────────────────

def test_pipeline_ingest_crosses_capture_before_canonical_note_creation():
    result = pipeline.ingest(
        title="Ingress proof",
        content="The capture boundary precedes canonicalization.",
        note_type="document",
        source_provider="test:shared-ingress",
        auto_tag=False,
        auto_embed=False,
        auto_link=False,
    )
    assert result["id"] is not None
    assert result["capture"]["source"]["source_ref"] == "test:shared-ingress"
    assert result["capture"]["state"] == "BOUND"
    assert result["capture"]["authorship"]["declared"] is False

    rows = db.execute(
        "SELECT event_type FROM timeline ORDER BY id"
    )
    types = [row["event_type"] for row in rows]
    assert types.index("capture_recorded") < types.index("knowledge_created")


def test_pipeline_ingest_preserves_explicit_authorship_without_inference():
    result = pipeline.ingest(
        title="Declared author",
        content="This author was explicitly declared.",
        note_type="document",
        source_provider="test:author",
        authored_by="human-author-1",
        authored_by_kind="human",
        auto_tag=False,
        auto_embed=False,
        auto_link=False,
    )
    assert result["capture"]["authorship"]["authored_by"] == "human-author-1"
    assert result["capture"]["authorship"]["declared"] is True


def test_pipeline_duplicate_still_binds_a_new_capture_to_existing_note():
    first = pipeline.ingest(
        title="Duplicate boundary",
        content="Same canonical content.",
        note_type="document",
        source_provider="test:duplicate",
        auto_tag=False,
        auto_embed=False,
        auto_link=False,
    )
    second = pipeline.ingest(
        title="Different title",
        content="Same canonical content.",
        note_type="document",
        source_provider="test:duplicate",
        auto_tag=False,
        auto_embed=False,
        auto_link=False,
    )
    assert second["duplicate"] is True
    assert second["existing"]["id"] == first["id"]
    assert second["capture"]["state"] == "BOUND"
    bound = db.execute(
        "SELECT note_id FROM capture_records WHERE raw_checksum = ?",
        (hashlib.sha256("Same canonical content.".encode()).hexdigest(),),
    )
    assert len(bound) == 2
    assert all(row["note_id"] == first["id"] for row in bound)
