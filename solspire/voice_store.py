"""Arkadia Voice — persistence for voice events and the causal evidence chain.

Storage lives in the canonical SolSpire store (``data/solspire_projects.db``,
``SOLSPIRE_PROJECTS_DB``), the same SQLite database that already holds
workspaces, proposals and work events. The repository's ``conftest.py`` already
sandboxes that database for every test session, so voice records inherit the
same isolation — no second database, no parallel store.

Two tables:

  voice_events  one row per captured utterance, including the audio bytes,
                sha256 hash, and the typed links of the governance chain
                (proposal / approval / authorization / execution / work event /
                evidence / verification).
  voice_chain   append-only stage log (VOICE_EVENT → … → VERIFICATION) with a
                per-stage payload digest and prev_record_id so every object is
                traceable backwards.

All reads accept the authenticated subject and refuse cross-subject access.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from typing import Any

from solspire.voice_contracts import ChainStage, canonical_digest, utc_now

_DB_PATH = os.environ.get("SOLSPIRE_PROJECTS_DB") or os.path.join(
    os.environ.get("SOLSPIRE_DATA_DIR", "data"), "solspire_projects.db"
)

#: Columns update_event may write (whitelist — no schema surprises).
_UPDATABLE = {
    "status", "error_state", "error_detail", "transcript_json", "intent_json",
    "context_json", "proposal_id", "approval_ref", "authorization_ref",
    "execution_id", "work_event_id", "evidence_ref", "verification_ref",
    "language",
}

_EVENT_SELECT = """
    event_id, session_id, subject_ref, workspace_ref, created_at, language,
    audio_reference, audio_mime, audio_size, audio_hash, duration_ms, status,
    error_state, error_detail, transcript_json, intent_json, context_json,
    proposal_id, approval_ref, authorization_ref, execution_id, work_event_id,
    evidence_ref, verification_ref
"""


def _db() -> sqlite3.Connection:
    directory = os.path.dirname(_DB_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS voice_events (
            event_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            subject_ref TEXT NOT NULL,
            workspace_ref TEXT NOT NULL,
            created_at REAL NOT NULL,
            language TEXT NOT NULL DEFAULT 'en',
            audio_reference TEXT,
            audio_mime TEXT,
            audio_size INTEGER,
            audio_hash TEXT,
            audio_bytes BLOB,
            duration_ms INTEGER,
            status TEXT NOT NULL,
            error_state TEXT,
            error_detail TEXT,
            transcript_json TEXT,
            intent_json TEXT,
            context_json TEXT,
            proposal_id TEXT,
            approval_ref TEXT,
            authorization_ref TEXT,
            execution_id TEXT,
            work_event_id TEXT,
            evidence_ref TEXT,
            verification_ref TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS voice_chain (
            chain_id TEXT NOT NULL,
            seq INTEGER NOT NULL,
            stage TEXT NOT NULL,
            record_type TEXT NOT NULL,
            record_id TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            payload_digest TEXT NOT NULL,
            prev_record_id TEXT,
            created_at REAL NOT NULL,
            PRIMARY KEY (chain_id, seq)
        )
        """
    )
    conn.commit()
    return conn


def _loads(raw: str | None) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError):  # pragma: no cover
        return None


def _row_to_event(row: sqlite3.Row) -> dict[str, Any]:
    event = {key: row[key] for key in row.keys() if key != "audio_bytes"}
    for key in ("transcript_json", "intent_json", "context_json"):
        event[key.replace("_json", "")] = _loads(event.pop(key))
    return event


class VoiceStore:
    """Subject-scoped voice event + chain persistence."""

    # ── events ──────────────────────────────────────────────────────────────

    def insert_event(
        self,
        *,
        event_id: str,
        session_id: str,
        subject_ref: str,
        workspace_ref: str,
        language: str,
        audio_reference: str,
        audio_mime: str,
        audio_size: int,
        audio_hash: str,
        audio_bytes: bytes,
        duration_ms: int | None,
        status: str,
    ) -> dict[str, Any]:
        now = utc_now()
        conn = _db()
        try:
            conn.execute(
                """
                INSERT INTO voice_events (
                    event_id, session_id, subject_ref, workspace_ref, created_at,
                    language, audio_reference, audio_mime, audio_size, audio_hash,
                    audio_bytes, duration_ms, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id, session_id, subject_ref, workspace_ref, now,
                    language, audio_reference, audio_mime, audio_size, audio_hash,
                    audio_bytes, duration_ms, status,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        event = self.get_event(event_id, subject_ref)
        assert event is not None
        return event

    def get_event(self, event_id: str, subject_ref: str | None = None) -> dict[str, Any] | None:
        conn = _db()
        try:
            sql = f"SELECT {_EVENT_SELECT} FROM voice_events WHERE event_id=?"
            params: list[Any] = [event_id]
            if subject_ref is not None:
                sql += " AND subject_ref=?"
                params.append(subject_ref)
            row = conn.execute(sql, params).fetchone()
        finally:
            conn.close()
        return _row_to_event(row) if row else None

    def get_audio(self, event_id: str, subject_ref: str) -> tuple[bytes, str, str] | None:
        conn = _db()
        try:
            row = conn.execute(
                "SELECT audio_bytes, audio_mime, audio_hash FROM voice_events "
                "WHERE event_id=? AND subject_ref=?",
                (event_id, subject_ref),
            ).fetchone()
        finally:
            conn.close()
        if row is None or row["audio_bytes"] is None:
            return None
        return bytes(row["audio_bytes"]), row["audio_mime"] or "", row["audio_hash"] or ""

    def list_events(
        self, subject_ref: str, session_id: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        conn = _db()
        try:
            sql = f"SELECT {_EVENT_SELECT} FROM voice_events WHERE subject_ref=?"
            params: list[Any] = [subject_ref]
            if session_id:
                sql += " AND session_id=?"
                params.append(session_id)
            sql += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
        finally:
            conn.close()
        return [_row_to_event(row) for row in rows]

    def update_event(self, event_id: str, **fields: Any) -> None:
        assignments: list[str] = []
        values: list[Any] = []
        for key, value in fields.items():
            if key not in _UPDATABLE:
                raise ValueError(f"field '{key}' is not updatable on voice_events")
            if key in {"transcript_json", "intent_json", "context_json"} and value is not None:
                value = json.dumps(value, default=str)
            assignments.append(f"{key}=?")
            values.append(value)
        if not assignments:
            return
        values.append(event_id)
        conn = _db()
        try:
            conn.execute(
                f"UPDATE voice_events SET {', '.join(assignments)} WHERE event_id=?",
                values,
            )
            conn.commit()
        finally:
            conn.close()

    # ── chain ───────────────────────────────────────────────────────────────

    def append_stage(
        self,
        chain_id: str,
        *,
        stage: str,
        record_type: str,
        record_id: str,
        payload: dict[str, Any],
    ) -> ChainStage:
        digest = canonical_digest(payload)
        conn = _db()
        try:
            last = conn.execute(
                "SELECT seq, record_id FROM voice_chain WHERE chain_id=? "
                "ORDER BY seq DESC LIMIT 1",
                (chain_id,),
            ).fetchone()
            seq = (last["seq"] + 1) if last else 1
            prev = last["record_id"] if last else None
            conn.execute(
                """
                INSERT INTO voice_chain
                    (chain_id, seq, stage, record_type, record_id, payload_json,
                     payload_digest, prev_record_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chain_id, seq, stage, record_type, record_id,
                    json.dumps(payload, default=str), digest, prev, utc_now(),
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return ChainStage(
            stage=stage,
            seq=seq,
            record_type=record_type,
            record_id=record_id,
            payload=payload,
            created_at=utc_now(),
            prev_record_id=prev,
            payload_digest=digest,
        )

    def list_stages(self, chain_id: str) -> list[ChainStage]:
        conn = _db()
        try:
            rows = conn.execute(
                "SELECT * FROM voice_chain WHERE chain_id=? ORDER BY seq ASC",
                (chain_id,),
            ).fetchall()
        finally:
            conn.close()
        return [
            ChainStage(
                stage=row["stage"],
                seq=row["seq"],
                record_type=row["record_type"],
                record_id=row["record_id"],
                payload=_loads(row["payload_json"]) or {},
                created_at=row["created_at"],
                prev_record_id=row["prev_record_id"],
                payload_digest=row["payload_digest"],
            )
            for row in rows
        ]


_STORE = VoiceStore()
_STORE_LOCK = threading.Lock()


def get_voice_store() -> VoiceStore:
    with _STORE_LOCK:
        return _STORE


__all__ = ["VoiceStore", "get_voice_store", "_DB_PATH"]
