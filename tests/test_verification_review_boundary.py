"""Boundary Expansion Gate 05 — VERIFICATION != REVIEW (final downstream gate).

Investigation-first, starting from an actual persisted verification record
(``ew_verifications`` in the ARK-WEAVER-01 enterprise chain), not from the
assumption that REVIEW must exist because the grammar contains the word.

Measured result: **no distinct Review record exists.** The two verification
domains both terminate in a verification record and then wait for a *human
authorization* — there is no Review record, table, store, identifier, or HTTP
surface anywhere in the backend, and no verification -> review relationship to
be recorded, inferred, or left unexposed.

Where the word "review" appears, it names one of:
  * a read-only, non-persisted *bundle* attached to a verification
    (``VerificationReport.review_bundle`` via ``weaver/verification.py::_review``),
    whose own ``next_action`` is "awaiting human authorization";
  * a human-facing *stage label* in the in-memory weaver lifecycle
    (``weaver/workbench_view.py`` ``LIFECYCLE`` / ``pipeline``);
  * a ``REVIEWED`` *status string* on unrelated SolSpire pulse/synthesis records.

None of these is a Review record, and none is joined to a verification. The
absence is the measurement. No review mechanism was created or repaired to
demonstrate the boundary.

Domains measured:
  1. Enterprise chain  — ``weaver/enterprise_orchestration.py`` (``ew_verifications``).
  2. Weaver engineering — ``weaver/verification.py`` (``VerificationReport``,
     in-memory, never persisted).
"""
from __future__ import annotations

import inspect
import json
import pathlib
import re

import weaver.enterprise_orchestration as eo
import weaver.verification as ver
import weaver.workbench_view as wv

_BACKEND_ROOTS = ("weaver", "solspire", "api", "kernel", "knowledge", "governance")
_EXCLUDE = ("/.venv/", "/node_modules/", "/web/", "/tests/", "__pycache__")

# A route *path segment* equal to ``review``/``reviews`` — matched as a whole
# segment, never as a substring. Matching the substring ``review`` inside the
# raw decorator line flags unrelated paths such as ``/patches/preview``, which
# is not a Review surface; the segment match is the boundary that was intended.
_REVIEW_SEGMENTS = frozenset({"review", "reviews"})
_ROUTE_PATH = re.compile(r"""["'](/[^"']*)["']""")


def _review_path_segments(decorator_line: str) -> list[str]:
    """Return the review/reviews path segments a route decorator declares.

    The route path is read from the decorator's string literal and split on
    ``/``; only a segment *equal to* ``review`` or ``reviews`` counts. A word
    that merely contains the substring (``preview``) does not.
    """
    match = _ROUTE_PATH.search(decorator_line)
    if match is None:
        return []
    return [
        segment
        for segment in match.group(1).split("/")
        if segment.lower() in _REVIEW_SEGMENTS
    ]


def _enumerate_review_routes() -> tuple[int, list[str]]:
    """Enumerate backend route decorators and any that expose a review path.

    Returns ``(route_count, review_routes)``. Shared by the boundary assertion
    and its negative control so both exercise the same detector.
    """
    route_count = 0
    review_routes: list[str] = []
    for top in ("api", "solspire"):
        base = pathlib.Path(top)
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                stripped = line.strip()
                if not (stripped.startswith(("@router.", "@app.")) and "(" in stripped):
                    continue
                route_count += 1
                if _review_path_segments(stripped):
                    review_routes.append(f"{path}: {stripped}")
    return route_count, review_routes


def _all_backend_source() -> str:
    chunks: list[str] = []
    root = pathlib.Path(".")
    for top in _BACKEND_ROOTS:
        base = root / top
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(chunks)


# ---------------------------------------------------------------------------
# The enterprise verification domain
# ---------------------------------------------------------------------------

def test_enterprise_verification_has_a_durable_id_and_is_persisted(tmp_path, monkeypatch):
    monkeypatch.setattr(eo, "_DB_PATH", str(tmp_path / "orchestration.db"))
    store = eo.EnterpriseOrchestrationStore()
    canonical = store.canonical_record(
        subject="operator", source_channel="sensor", raw_payload={"reading": 42}, ingested_by="test"
    )
    evidence = store.evidence(
        subject="operator", evidence_type="capture", content_or_ref={"reading": 42},
        source_ref=canonical.id,
    )
    verification = store.verify(
        subject="operator", claim="reading is 42", evidence_refs=[evidence.id],
        verifier="test", verdict="VERIFIED",
    )

    # A durable, persisted verification record (Q1, Q2).
    assert verification.id.startswith("vr-")
    assert store._row("ew_verifications", verification.id) is not None


def test_enterprise_verification_creates_no_review_record(tmp_path, monkeypatch):
    monkeypatch.setattr(eo, "_DB_PATH", str(tmp_path / "orchestration.db"))
    store = eo.EnterpriseOrchestrationStore()
    canonical = store.canonical_record(
        subject="operator", source_channel="sensor", raw_payload={"x": 1}, ingested_by="test"
    )
    evidence = store.evidence(
        subject="operator", evidence_type="capture", content_or_ref={"x": 1}, source_ref=canonical.id
    )
    store.verify(
        subject="operator", claim="x", evidence_refs=[evidence.id], verifier="t", verdict="VERIFIED"
    )

    # Creating a verification creates, references and triggers no Review (Q3).
    import sqlite3

    conn = sqlite3.connect(eo._DB_PATH)
    try:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    finally:
        conn.close()
    assert not any("review" in t.lower() for t in tables), f"a review table exists: {tables}"


def test_enterprise_chain_has_no_review_concept():
    # The enterprise store source contains no review vocabulary at all (Q4, Q10).
    src = inspect.getsource(eo)
    assert "review" not in src.lower()

    # The traversal's record kinds include VERIFICATION and exclude REVIEW.
    kinds = set(__import__("re").findall(r'"([A-Z_]+)": "ew_[a-z_]+"', src))
    assert "VERIFICATION" in kinds
    assert "REVIEW" not in kinds


# ---------------------------------------------------------------------------
# The weaver verification domain
# ---------------------------------------------------------------------------

def test_weaver_verification_is_in_memory_and_not_persisted():
    # VerificationReport is a dataclass with to_dict(); nothing persists it (Q1, Q2).
    report = ver.VerificationReport()
    assert hasattr(report, "to_dict")
    assert report.verification_id == ""

    src = inspect.getsource(ver)
    assert "sqlite" not in src.lower()
    assert "CREATE TABLE" not in src
    assert "INSERT INTO" not in src


def test_weaver_review_is_a_non_persisted_bundle_attached_to_a_verification():
    # The only "review" attached to a verification is a dict field whose own
    # next_action is a human authorization — a bundle, not a Review record (Q3, Q5).
    report = ver.VerificationReport()
    assert "review_bundle" in {f for f in report.to_dict()}

    review = ver._review(report, "objective")
    assert isinstance(review, dict)
    assert review["next_action"] == "awaiting human authorization"
    # It is not a record: no identifier, no type, no store.
    assert "id" not in review
    assert "review_id" not in review
    assert "record_type" not in review


def test_weaver_review_is_a_stage_label_not_a_record():
    # REVIEW is a label in the lifecycle/pipeline, with no record behind it (Q4, Q10).
    assert "REVIEW" in wv.LIFECYCLE
    assert "VERIFICATION" in wv.LIFECYCLE

    src = inspect.getsource(wv)
    assert '"REVIEW": {"status": "AWAITING REVIEW"}' in src
    # A stage label is not a persisted record type.
    assert "class Review" not in src


# ---------------------------------------------------------------------------
# The absence, globally
# ---------------------------------------------------------------------------

def test_no_review_record_type_or_table_exists_anywhere_in_the_backend():
    # Q4, Q5, Q6: there is no Review record, so no durable verification -> review
    # relationship can exist, and no Review can exist without a verification.
    src = _all_backend_source()
    lowered = src.lower()
    assert "class review" not in lowered
    assert "ew_review" not in lowered
    assert "review_id" not in lowered
    assert "reviewrecord" not in lowered
    # No SQL table named review.
    assert "create table" not in lowered or "review" not in lowered.split("create table", 1)[1][:200]


def test_verification_exists_without_any_review(tmp_path, monkeypatch):
    # Q7: verification can exist with no review — in fact, that is the only case.
    monkeypatch.setattr(eo, "_DB_PATH", str(tmp_path / "orchestration.db"))
    store = eo.EnterpriseOrchestrationStore()
    canonical = store.canonical_record(
        subject="operator", source_channel="sensor", raw_payload={"x": 1}, ingested_by="test"
    )
    evidence = store.evidence(
        subject="operator", evidence_type="capture", content_or_ref={"x": 1}, source_ref=canonical.id
    )
    verification = store.verify(
        subject="operator", claim="x", evidence_refs=[evidence.id], verifier="t", verdict="VERIFIED"
    )

    # A verification stands alone; the forward walk reaches no review (Q6).
    forward = store.forward_walk(
        subject="operator", kind="VERIFICATION", record_id=verification.id
    )
    assert all(r["kind"] != "REVIEW" for r in forward["records"])
    assert "REVIEW" not in json.dumps(forward)

    # And no review row was created alongside the verification (Q6).
    import sqlite3

    conn = sqlite3.connect(eo._DB_PATH)
    try:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    finally:
        conn.close()
    assert not any("review" in t.lower() for t in tables)


def test_no_http_surface_exposes_review_as_a_first_class_record():
    # Q9: no HTTP route exposes review as a first-class record. Enumerated from
    # the route-decorator sources, matching the Gate 04 route check — but the
    # route path is matched by whole segment, not by the substring ``review``
    # (which flags ``/patches/preview``).
    route_count, review_routes = _enumerate_review_routes()
    assert route_count > 0, "expected route decorators"
    assert not review_routes, f"review route exists: {review_routes}"


def test_review_route_detector_matches_the_resource_not_a_substring():
    # Negative control for the boundary above: the detector must catch a real
    # review route and must NOT flag a path that merely contains the substring.
    # Without this, a detector that never matches anything would make the
    # boundary assertion vacuously green.
    assert _review_path_segments('@router.post("/review")') == ["review"]
    assert _review_path_segments('@router.get("/projects/{id}/reviews")') == ["reviews"]
    assert _review_path_segments('@router.post("/reviews/{review_id}/decide")') == ["reviews"]
    assert _review_path_segments('@router.post("/projects/{project_id}/patches/preview")') == []
    assert _review_path_segments('@router.post("/authorizations/{authorization_id}/execute")') == []
