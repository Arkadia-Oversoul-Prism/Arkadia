"""
Arkadia Knowledge OS — Capture Boundary (GATE-01)
=================================================
The canonical information boundary:

    SOURCE → CAPTURE → CANONICAL RECORD → AUTHORSHIP → PROVENANCE

Rules enforced here:

- A capture cannot exist without a registered source. The `source_id`
  column is NOT NULL, so SOURCE → CAPTURE is an enforced edge, not a
  convention.
- Raw content is stored byte-identical. Interpretation happens later and
  never mutates the captured artifact; the artifact's identity is a hash of
  its content, so any change is a different artifact.
- Authorship is declared explicitly or remains UNKNOWN. It is never inferred
  from the source, the captor, or the content. Capture ≠ authorship.
- Provenance is derived and read-only. It reports UNKNOWN rather than
  guessing, and it always names the canonical origin.

This module does not classify, extract, summarize, or judge. Those are later
transitions and must be independently inspectable when they exist.
"""

from __future__ import annotations

import hashlib
import json
import uuid as _uuid
from datetime import datetime, timezone
from typing import Optional

from knowledge.db import execute, execute_one, last_insert_id
from knowledge import timeline as tl

SOURCE_KINDS = frozenset(
    {"message", "document", "url", "api", "manual", "system"}
)
CONTENT_KINDS = frozenset(
    {"message", "document", "transcript", "manual", "system", "unknown"}
)
ACTOR_KINDS = frozenset({"human", "system", "unknown"})

# UNKNOWN is represented as SQL NULL — never an empty string or a placeholder.
UNKNOWN = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _validate(value: str, allowed: frozenset, field: str) -> None:
    if value not in allowed:
        raise ValueError(f"unknown {field}: {value!r} (allowed: {sorted(allowed)})")


def _normalize_actor(actor: Optional[str], kind: str) -> tuple[Optional[str], str]:
    _validate(kind, ACTOR_KINDS, "actor kind")
    uid = (actor or "").strip() or None
    if uid is None:
        # No declared actor is UNKNOWN, whatever the declared kind claimed.
        return None, "unknown"
    if kind == "unknown":
        # An actor was declared but its nature was not — keep the actor,
        # record the nature as UNKNOWN rather than assuming 'human'.
        return uid, "unknown"
    return uid, kind


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE — canonical origin identity
# ─────────────────────────────────────────────────────────────────────────────

def register_source(
    *,
    source_kind: str,
    source_ref: Optional[str] = None,
    title: Optional[str] = None,
    origin_meta: Optional[dict] = None,
) -> dict:
    """Register a canonical source. Idempotent per origin fingerprint.

    Identity is (source_kind, source_ref, title) — not content, so the same
    origin is the same source across many captures. A caller that needs a
    distinct source per item must supply a distinct `source_ref`.
    """
    _validate(source_kind, SOURCE_KINDS, "source kind")
    ref = (source_ref or "").strip() or None
    clean_title = (title or "").strip() or None
    fingerprint = _sha256(
        json.dumps(
            {"kind": source_kind, "ref": ref, "title": clean_title},
            sort_keys=True,
            separators=(",", ":"),
        )
    )

    existing = execute_one(
        "SELECT * FROM capture_sources WHERE fingerprint = ?", (fingerprint,)
    )
    if existing:
        return existing

    source_uuid = str(_uuid.uuid4())
    execute(
        """
        INSERT INTO capture_sources
            (source_uuid, source_kind, source_ref, title, origin_meta, fingerprint, created_at)
        VALUES (?,?,?,?,?,?,?)
        """,
        (
            source_uuid, source_kind, ref, clean_title,
            json.dumps(origin_meta or {}), fingerprint, _now(),
        ),
    )
    source_id = last_insert_id()
    tl.record(
        "source_registered",
        {"source_id": source_id, "source_uuid": source_uuid,
         "source_kind": source_kind, "source_ref": ref},
    )
    return execute_one("SELECT * FROM capture_sources WHERE id = ?", (source_id,))


def get_source(source_uuid: Optional[str] = None, source_id: Optional[int] = None) -> Optional[dict]:
    if source_uuid is not None:
        return execute_one("SELECT * FROM capture_sources WHERE source_uuid = ?", (source_uuid,))
    if source_id is not None:
        return execute_one("SELECT * FROM capture_sources WHERE id = ?", (source_id,))
    return None


# ─────────────────────────────────────────────────────────────────────────────
# CAPTURE — immutable artifact tied to a source
# ─────────────────────────────────────────────────────────────────────────────

def capture(
    *,
    source_uuid: str,
    raw_content: str,
    content_kind: str = "unknown",
    captured_by: Optional[str] = None,
    captured_by_kind: str = "unknown",
    authored_by: Optional[str] = None,
    authored_by_kind: str = "unknown",
    captured_at: Optional[str] = None,
) -> dict:
    """Capture raw content from a registered source.

    Fails if the source is unknown: SOURCE → CAPTURE cannot be skipped.
    Authorship is stored exactly as declared, or as UNKNOWN.
    """
    _validate(content_kind, CONTENT_KINDS, "content kind")
    source = get_source(source_uuid=source_uuid)
    if source is None:
        raise LookupError(f"unknown source: {source_uuid!r}")

    cap_uid, cap_kind = _normalize_actor(captured_by, captured_by_kind)
    auth_uid, auth_kind = _normalize_actor(authored_by, authored_by_kind)

    capture_uuid = str(_uuid.uuid4())
    raw_checksum = _sha256(raw_content)
    when = captured_at or _now()
    execute(
        """
        INSERT INTO capture_records
            (capture_uuid, source_id, content_kind, raw_checksum, captured_by,
             captured_by_kind, authored_by, authored_by_kind, capture_status,
             captured_at, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            capture_uuid, source["id"], content_kind, raw_checksum, cap_uid,
            cap_kind, auth_uid, auth_kind, "CAPTURED", when, _now(),
        ),
    )
    capture_id = last_insert_id()
    tl.record(
        "capture_recorded",
        {"capture_id": capture_id, "capture_uuid": capture_uuid,
         "source_id": source["id"], "raw_checksum": raw_checksum},
    )
    return execute_one("SELECT * FROM capture_records WHERE id = ?", (capture_id,))


def get_capture(capture_uuid: str) -> Optional[dict]:
    return execute_one("SELECT * FROM capture_records WHERE capture_uuid = ?", (capture_uuid,))


def bind_capture_to_note(*, capture_uuid: str, note_id: int) -> dict:
    """Bind a capture to the canonical record (note) it produced."""
    cap = get_capture(capture_uuid)
    if cap is None:
        raise LookupError(f"unknown capture: {capture_uuid!r}")
    execute(
        "UPDATE capture_records SET note_id = ?, capture_status = 'BOUND' WHERE id = ?",
        (note_id, cap["id"]),
    )
    tl.record(
        "capture_bound",
        {"capture_id": cap["id"], "note_id": note_id},
        note_id=note_id,
    )
    return execute_one("SELECT * FROM capture_records WHERE id = ?", (cap["id"],))


# ─────────────────────────────────────────────────────────────────────────────
# PROVENANCE — derived, read-only, UNKNOWN-preserving
# ─────────────────────────────────────────────────────────────────────────────

def _provenance_from_capture_row(cap: dict) -> dict:
    source = get_source(source_id=cap["source_id"])
    authored = cap.get("authored_by")
    return {
        "capture_uuid": cap["capture_uuid"],
        "state": cap["capture_status"],
        "note_id": cap.get("note_id"),
        "source": {
            "source_uuid": source["source_uuid"] if source else None,
            "source_kind": source["source_kind"] if source else None,
            "source_ref": source["source_ref"] if source else None,
            "title": source["title"] if source else None,
        },
        "authorship": {
            # Declared authorship only. UNKNOWN stays UNKNOWN.
            "authored_by": authored,
            "authored_by_kind": cap.get("authored_by_kind", "unknown"),
            "declared": authored is not None,
        },
        "captured_by": {
            "captured_by": cap.get("captured_by"),
            "captured_by_kind": cap.get("captured_by_kind", "unknown"),
            "declared": cap.get("captured_by") is not None,
        },
        "canonical_origin": {
            "source_uuid": source["source_uuid"] if source else None,
            "source_ref": source["source_ref"] if source else None,
        },
        "raw_checksum": cap["raw_checksum"],
        "captured_at": cap["captured_at"],
    }


def provenance_for_capture(capture_uuid: str) -> dict:
    cap = get_capture(capture_uuid)
    if cap is None:
        return {
            "capture_uuid": capture_uuid,
            "state": "UNKNOWN",
            "unknown": True,
            "source": None,
            "authorship": {"authored_by": None, "authored_by_kind": "unknown", "declared": False},
        }
    return _provenance_from_capture_row(cap)


def provenance_for_note(note_id: int) -> dict:
    """Return the canonical origin and authorship of a note.

    A note with no capture record has UNKNOWN provenance — it did not come
    through the capture boundary, and this function does not invent one.
    """
    row = execute_one(
        "SELECT * FROM capture_records WHERE note_id = ? ORDER BY id DESC LIMIT 1",
        (note_id,),
    )
    if row is None:
        return {
            "note_id": note_id,
            "state": "UNKNOWN",
            "unknown": True,
            "source": None,
            "authorship": {"authored_by": None, "authored_by_kind": "unknown", "declared": False},
        }
    return _provenance_from_capture_row(row)


# ─────────────────────────────────────────────────────────────────────────────
# END-TO-END — CAPTURE → CANONICAL RECORD
# ─────────────────────────────────────────────────────────────────────────────

def capture_and_ingest(
    *,
    source_kind: str,
    raw_content: str,
    title: str,
    source_ref: Optional[str] = None,
    source_title: Optional[str] = None,
    content_kind: str = "unknown",
    note_type: str = "note",
    captured_by: Optional[str] = None,
    captured_by_kind: str = "unknown",
    authored_by: Optional[str] = None,
    authored_by_kind: str = "unknown",
    project_id: Optional[int] = None,
    thread_id: Optional[int] = None,
    user_id: Optional[str] = None,
    auto_tag: bool = False,
    auto_embed: bool = False,
    auto_link: bool = False,
) -> dict:
    """Register source, capture, ingest to a canonical note, and bind them.

    The note is created through the existing pipeline — this function does not
    introduce a second write path. Returns the source, capture, note, and the
    resulting provenance view.
    """
    source = register_source(
        source_kind=source_kind, source_ref=source_ref, title=source_title
    )
    cap = capture(
        source_uuid=source["source_uuid"],
        raw_content=raw_content,
        content_kind=content_kind,
        captured_by=captured_by,
        captured_by_kind=captured_by_kind,
        authored_by=authored_by,
        authored_by_kind=authored_by_kind,
    )

    # Imported lazily: pipeline imports vault/timeline/graph, and capture is a
    # lower-level boundary that must not create an import cycle.
    from knowledge import pipeline

    result = pipeline.ingest(
        title=title,
        content=raw_content,
        note_type=note_type,
        project_id=project_id,
        thread_id=thread_id,
        source_provider=f"capture:{source_kind}",
        user_id=user_id,
        auto_tag=auto_tag,
        auto_embed=auto_embed,
        auto_link=auto_link,
    )

    note_id = None
    if result.get("duplicate"):
        existing = result.get("existing") or {}
        note_id = existing.get("id")
    else:
        note_id = result.get("id")

    if note_id is not None:
        cap = bind_capture_to_note(capture_uuid=cap["capture_uuid"], note_id=note_id)

    return {
        "source": source,
        "capture": cap,
        "note_id": note_id,
        "ingest": result,
        "provenance": provenance_for_capture(cap["capture_uuid"]),
    }
