"""Boundary Expansion Gate 03 — WORK EVENT ≠ EVIDENCE.

Investigation-first, starting from an actual WorkEvent: what evidence does it
produce, where is that evidence persisted, and is there a durable
WorkEvent -> Evidence join?

The result is an ABSENCE, recorded not repaired. A WorkEvent carries only opaque
reference fields; runtime evidence binds to an *execution attempt* in the
ARK-WEAVER-01 enterprise chain (a different spine from the SolSpire WorkEvent
spine); and no field or table on either side joins the two. No HTTP route
exposes evidence or verification as first-class records.
"""
from __future__ import annotations

import dataclasses
import pathlib
import sqlite3

from solspire.workevent_manager import WorkEventManager
from weaver.enterprise_orchestration import EnterpriseOrchestrationStore

# Files that can mount a FastAPI route in this substrate.
_ROUTE_SOURCES = [
    pathlib.Path("api/main.py"),
    *sorted(pathlib.Path("solspire").glob("*router*.py")),
    *sorted(pathlib.Path("api").glob("*route*.py")),
]


def _both(tmp_path, monkeypatch):
    """Point the WorkEvent spine and the enterprise chain at one database file.

    The two stores are separate databases in production. Sharing one file is the
    strongest possible chance for a join to exist if one does — so a missing join
    here proves the absence is structural (no field, no table), not merely a
    matter of file location.
    """
    db = str(tmp_path / "substrate.db")
    import solspire.workevent_manager as wem
    import weaver.enterprise_orchestration as ew

    monkeypatch.setattr(wem, "_DB_PATH", db)
    monkeypatch.setattr(ew, "_DB_PATH", db)
    return WorkEventManager(), EnterpriseOrchestrationStore()


def _workevent(manager):
    return manager.create(
        subject_ref="operator",
        workspace_ref="ws-1",
        event_type="WORK_RECORDED",
        occurred_at=1.0,
        artifact_refs=["artifact://a"],
        decision_ref="decision://d",
        witness_ref="witness://w",
    )


def _table_sql(db: str) -> list[tuple[str, str]]:
    conn = sqlite3.connect(db)
    try:
        rows = conn.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table'"
        ).fetchall()
    finally:
        conn.close()
    return [(r[0], r[1] or "") for r in rows]


def _count(db: str, table: str) -> int:
    conn = sqlite3.connect(db)
    try:
        try:
            return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        except sqlite3.OperationalError:
            return 0
    finally:
        conn.close()


def test_a_workevent_carries_only_opaque_reference_fields(tmp_path, monkeypatch):
    manager, _ = _both(tmp_path, monkeypatch)
    event = _workevent(manager)

    assert event.artifact_refs == ["artifact://a"]
    assert event.decision_ref == "decision://d"
    assert event.witness_ref == "witness://w"

    names = {f.name for f in dataclasses.fields(event)}
    # No field on a WorkEvent can hold or point at an evidence record.
    assert not any("evidence" in n for n in names)
    assert "execution_ref" not in names
    assert "verification_ref" not in names


def test_creating_a_workevent_produces_no_evidence_or_verification(tmp_path, monkeypatch):
    manager, _ = _both(tmp_path, monkeypatch)
    _workevent(manager)

    import solspire.workevent_manager as wem

    assert _count(wem._DB_PATH, "ew_evidence") == 0
    assert _count(wem._DB_PATH, "ew_verifications") == 0


def test_no_table_joins_a_workevent_to_evidence_or_verification(tmp_path, monkeypatch):
    manager, store = _both(tmp_path, monkeypatch)
    _workevent(manager)
    # Materialise the enterprise schema too, so every table is present.
    store.canonical_record(
        subject="operator", source_channel="test", raw_payload={}, ingested_by="t"
    )

    import solspire.workevent_manager as wem

    for name, sql in _table_sql(wem._DB_PATH):
        lowered = sql.lower()
        if "work_event" in lowered:
            # The WorkEvent table itself references no evidence or verification.
            assert "evidence" not in lowered
            assert "verification" not in lowered
        if "evidence" in lowered or "verification" in lowered:
            # Conversely, no evidence/verification table references a WorkEvent.
            assert "work_event" not in lowered


def test_workevent_and_evidence_are_created_by_disjoint_modules(tmp_path, monkeypatch):
    manager, store = _both(tmp_path, monkeypatch)

    # The WorkEvent manager has no evidence/verification capability at all.
    assert not any("evidence" in m for m in dir(WorkEventManager))
    assert not any("verif" in m for m in dir(WorkEventManager))
    # The enterprise store has no WorkEvent capability at all.
    assert not any("work_event" in m for m in dir(EnterpriseOrchestrationStore))

    # Sanity: both real code paths work and are independent.
    assert _workevent(manager).work_event_id
    rec = store.canonical_record(
        subject="operator", source_channel="test", raw_payload={}, ingested_by="t"
    )
    assert rec.id


def test_evidence_binds_to_an_execution_attempt_not_a_workevent(tmp_path, monkeypatch):
    manager, store = _both(tmp_path, monkeypatch)
    event = _workevent(manager)

    evidence = store.evidence(
        subject="operator",
        evidence_type="capture",
        content_or_ref={"k": "v"},
        source_ref="src://1",
    )
    fields = {f.name for f in dataclasses.fields(evidence)}
    assert "execution_attempt_id" in fields
    assert "work_event_id" not in fields and "work_ref" not in fields

    # There is no parameter by which an evidence record could name a WorkEvent.
    try:
        store.evidence(
            subject="operator",
            evidence_type="capture",
            content_or_ref={},
            source_ref="src://2",
            work_event_id=event.work_event_id,
        )
    except TypeError:
        pass
    else:
        raise AssertionError("evidence() must not accept a WorkEvent reference")


def test_verification_references_evidence_not_a_workevent(tmp_path, monkeypatch):
    manager, store = _both(tmp_path, monkeypatch)
    event = _workevent(manager)
    evidence = store.evidence(
        subject="operator",
        evidence_type="capture",
        content_or_ref={"k": "v"},
        source_ref="src://1",
    )

    verification = store.verify(
        subject="operator",
        claim="the act happened",
        evidence_refs=[evidence.id],
        verifier="reviewer",
        verdict="VERIFIED",
    )
    assert verification.evidence_refs == [evidence.id]
    fields = {f.name for f in dataclasses.fields(verification)}
    assert "work_event_id" not in fields and "work_ref" not in fields
    assert event.work_event_id not in verification.evidence_refs

    try:
        store.verify(
            subject="operator",
            claim="x",
            evidence_refs=[evidence.id],
            verifier="reviewer",
            verdict="VERIFIED",
            work_event_id=event.work_event_id,
        )
    except TypeError:
        pass
    else:
        raise AssertionError("verify() must not accept a WorkEvent reference")


def test_console_exposes_evidence_verification_but_not_enterprise_walk():
    # Option A recognizes the two first-class Console routes.
    authority = pathlib.Path("solspire/console_authority_router.py").read_text(encoding="utf-8")
    assert '@router.post("/executions/{execution_id}/evidence")' in authority
    assert '@router.post("/verification")' in authority

    # The richer graph traversal remains intentionally unexposed over HTTP.
    for src in _ROUTE_SOURCES:
        source = src.read_text(encoding="utf-8")
        assert "forward_walk" not in source
        assert "reverse_walk" not in source
