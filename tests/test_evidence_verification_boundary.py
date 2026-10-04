"""Boundary Expansion Gate 04 — EVIDENCE ≠ VERIFICATION.

Investigation-first, starting from an actual persisted evidence record in the
ARK-WEAVER-01 enterprise chain (the same records the control-room projection
reads over HTTP).

Findings, measured not assumed:

1. Evidence is created only by ``EnterpriseOrchestrationStore.evidence()``.
2. Its durable identifier is ``ew_evidence.id`` (``ev-<uuid>``).
3. Creating evidence does **not** create a verification; verification is a
   separate, explicit call (``verify()``).
4. ``evidence -> verification`` is a *correlation*, not a foreign key:
   ``ew_verifications.evidence_refs`` is a JSON text list matched by substring
   in the projection, with no FOREIGN KEY and no reverse column on ``ew_evidence``.
5. A verification cannot be created without referencing an existing evidence
   record (write-time referential check) — but evidence can exist with no
   verification at all. The relationship is asymmetric.
6. Traversal is durable in both directions: ``reverse_walk(VERIFICATION)``
   resolves its evidence, and ``forward_walk(EVIDENCE)`` resolves its
   verification — but forward traversal fabricates nothing when no verification
   exists.
7. The Console authority bridge exposes authenticated first-class evidence and
   verification routes; the control-room projection remains a separate read
   surface, and enterprise lineage traversal is not exposed over HTTP.

No relationship is created or repaired to demonstrate the boundary. The
asymmetry (evidence without verification) is the finding.
"""
from __future__ import annotations

import inspect
import pathlib
import sqlite3

from weaver.enterprise_orchestration import EnterpriseOrchestrationStore

_ROUTE_SOURCES = [
    pathlib.Path("api/main.py"),
    *sorted(pathlib.Path("solspire").glob("*router*.py")),
    *sorted(pathlib.Path("api").glob("*route*.py")),
]


def _store(tmp_path, monkeypatch):
    import weaver.enterprise_orchestration as mod

    monkeypatch.setattr(mod, "_DB_PATH", str(tmp_path / "orchestration.db"))
    return mod.EnterpriseOrchestrationStore()


def _evidence(store, subject: str = "operator"):
    """Persist one real evidence record bound to a canonical source record."""
    canonical = store.canonical_record(
        subject=subject, source_channel="sensor", raw_payload={"reading": 42}, ingested_by="test"
    )
    evidence = store.evidence(
        subject=subject,
        evidence_type="capture",
        content_or_ref={"reading": 42},
        source_ref=canonical.id,
    )
    return canonical, evidence


def _count(store, table: str) -> int:
    import weaver.enterprise_orchestration as mod

    conn = sqlite3.connect(mod._DB_PATH)
    try:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    finally:
        conn.close()


def _schema(store, table: str) -> str:
    import weaver.enterprise_orchestration as mod

    conn = sqlite3.connect(mod._DB_PATH)
    try:
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        return (row[0] if row else "") or ""
    finally:
        conn.close()


def _kinds(walk: dict) -> set[tuple[str, str]]:
    return {(r["kind"], r["id"]) for r in walk["records"]}


def test_evidence_is_persisted_with_a_durable_id_and_creates_no_verification(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    _, evidence = _evidence(store)

    # A durable identifier, persisted (Q1, Q2).
    assert evidence.id.startswith("ev-")
    assert store._row("ew_evidence", evidence.id) is not None
    # Creating evidence does not create a verification (Q3).
    assert _count(store, "ew_verifications") == 0


def test_verification_is_created_separately_and_requires_evidence(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    _, evidence = _evidence(store)

    # No evidence references -> no verification (Q3).
    try:
        store.verify(
            subject="operator", claim="x", evidence_refs=[], verifier="v", verdict="VERIFIED"
        )
    except ValueError as exc:
        assert "requires evidence references" in str(exc)
    else:
        raise AssertionError("a verification with no evidence must be rejected")

    # Explicit, separate creation with its own durable identifier (Q2, Q3).
    verification = store.verify(
        subject="operator", claim="x", evidence_refs=[evidence.id], verifier="v", verdict="VERIFIED"
    )
    assert verification.id.startswith("vr-")
    assert verification.id != evidence.id
    assert _count(store, "ew_verifications") == 1


def test_evidence_to_verification_is_a_correlation_not_a_foreign_key(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    _evidence(store)

    ev_sql = _schema(store, "ew_evidence").lower()
    vr_sql = _schema(store, "ew_verifications").lower()

    # The verification points at evidence only through a JSON text list.
    assert "evidence_refs" in vr_sql
    assert "evidence_refs text" in vr_sql
    # ...which is not a foreign key, and has no FK clause at all.
    assert "foreign key" not in vr_sql
    assert "references" not in vr_sql
    # ...and evidence carries no reverse pointer to a verification.
    assert "verification" not in ev_sql
    assert "evidence_refs" not in ev_sql


def test_verification_cannot_reference_evidence_that_does_not_exist(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    _evidence(store)

    try:
        store.verify(
            subject="operator",
            claim="x",
            evidence_refs=["ev-does-not-exist"],
            verifier="v",
            verdict="VERIFIED",
        )
    except ValueError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("a verification referencing absent evidence must be rejected")
    assert _count(store, "ew_verifications") == 0


def test_evidence_can_exist_without_any_verification(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    _, evidence = _evidence(store)

    # The asymmetry is the finding: evidence stands alone, unverified.
    assert store._row("ew_evidence", evidence.id) is not None
    assert _count(store, "ew_verifications") == 0
    # And forward traversal does not fabricate a verification for it (Q6).
    forward = store.forward_walk(subject="operator", kind="EVIDENCE", record_id=evidence.id)
    assert not any(kind == "VERIFICATION" for kind, _ in _kinds(forward))


def test_reverse_traversal_from_verification_resolves_its_evidence(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    _, evidence = _evidence(store)
    verification = store.verify(
        subject="operator", claim="x", evidence_refs=[evidence.id], verifier="v", verdict="VERIFIED"
    )

    reverse = store.reverse_walk(
        subject="operator", kind="VERIFICATION", record_id=verification.id
    )
    assert ("VERIFICATION", verification.id) in _kinds(reverse)
    assert ("EVIDENCE", evidence.id) in _kinds(reverse)


def test_forward_traversal_from_evidence_resolves_its_verification(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    _, evidence = _evidence(store)
    verification = store.verify(
        subject="operator", claim="x", evidence_refs=[evidence.id], verifier="v", verdict="VERIFIED"
    )

    forward = store.forward_walk(subject="operator", kind="EVIDENCE", record_id=evidence.id)
    assert ("EVIDENCE", evidence.id) in _kinds(forward)
    assert ("VERIFICATION", verification.id) in _kinds(forward)


def test_evidence_and_verification_records_are_append_only():
    import weaver.enterprise_orchestration as mod

    src = inspect.getsource(mod)
    for table in ("ew_evidence", "ew_verifications"):
        assert f"UPDATE {table}" not in src, f"{table} must not be mutated in place"
        assert f"DELETE FROM {table}" not in src, f"{table} must not be deleted"


def test_console_authority_routes_expose_evidence_and_verification_separately():
    # Sovereign Option A: these are intended first-class Console authority routes.
    authority_path = pathlib.Path("solspire/console_authority_router.py")
    authority = authority_path.read_text(encoding="utf-8")
    assert '@router.post("/executions/{execution_id}/evidence")' in authority
    assert '@router.post("/verification")' in authority
    assert "user: dict[str, Any] = Depends(require_auth)" in authority
    # Verification identity is server-derived from Firebase, not the request label.
    assert 'verifier=f"firebase:{user[\'uid\']}"' in authority
    assert "store.evidence(" in authority
    assert "store.verify(" in authority


def test_evidence_and_verification_are_http_readable_through_console_and_projection():
    # The control-room projection joins evidence to verification and the execution chain.
    eden = pathlib.Path("solspire/eden_ops_02.py").read_text(encoding="utf-8")
    assert "ew_evidence" in eden and "ew_verifications" in eden
    assert "JOIN ew_execution_attempts" in eden
    assert "instr(v.evidence_refs, e.id)" in eden

    # The projection remains a distinct read surface; lineage walk is not exposed.
    routes = pathlib.Path("solspire/eden_ops_02_routes.py").read_text(encoding="utf-8")
    assert "control-room" in routes
    assert "@router.get(\"/evidence" not in routes
    assert "@router.get(\"/verif" not in routes
