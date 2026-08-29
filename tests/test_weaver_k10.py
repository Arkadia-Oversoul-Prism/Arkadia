"""WEAVER-K10 — evidence + traceability proofs."""
from __future__ import annotations

import subprocess
from pathlib import Path

from weaver.evidence import (
    ContinuityLike,
    EvidenceKind,
    collect_evidence,
    evidence_staleness,
    query_evidence,
    evidence_for_analysis,
)
import weaver.evidence as ev_mod


def _repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "weaver").mkdir()
    (tmp_path / "weaver" / "a.py").write_text("from weaver import b\n\ndef foo():\n    return 1\n")
    (tmp_path / "weaver" / "b.py").write_text("X = 1\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text("import weaver.a\nfrom weaver.a import foo\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()


def test_collect_deterministic(tmp_path):
    head = _repo(tmp_path)
    a = collect_evidence(str(tmp_path), roots=["weaver", "tests"])
    b = collect_evidence(str(tmp_path), roots=["weaver", "tests"])
    assert a.bound_head_sha == head == b.bound_head_sha
    assert len(a.records) == len(b.records)
    assert any(r.kind == EvidenceKind.FACT.value for r in a.records)


def test_import_relation(tmp_path):
    _repo(tmp_path)
    idx = collect_evidence(str(tmp_path), roots=["weaver", "tests"])
    imports = [r for r in idx.relations if r.relation == "IMPORTS"]
    assert any("weaver.a" in r.source or r.source.endswith("a") for r in imports)


def test_query_and_tests(tmp_path):
    _repo(tmp_path)
    idx = collect_evidence(str(tmp_path), roots=["weaver", "tests"])
    q = query_evidence(idx, "weaver/a.py")
    assert q["authorization"]["current_pass_authorized"] is False
    assert q["test_map_kind"] in (
        "DIRECT_TEST_REFERENCE",
        "LIKELY_TEST_COVERAGE",
        "NO_DISCOVERABLE_TEST",
        "UNKNOWN",
    )


def test_staleness(tmp_path):
    _repo(tmp_path)
    idx = collect_evidence(str(tmp_path), roots=["weaver", "tests"])
    assert evidence_staleness(idx, str(tmp_path)) == ContinuityLike.CURRENT
    (tmp_path / "README").write_text("z")
    subprocess.run(["git", "add", "README"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "advance"], cwd=tmp_path, check=True)
    assert evidence_staleness(idx, str(tmp_path)) == ContinuityLike.STALE


def test_evidence_not_authorization():
    for name in ("write_file", "commit_and_push", "run_transaction", "approve"):
        assert not hasattr(ev_mod, name)


def test_evidence_for_analysis(tmp_path):
    _repo(tmp_path)
    payload = evidence_for_analysis(str(tmp_path), subject_hints=["weaver/a.py"])
    assert payload["authorization"]["current_pass_authorized"] is False
    assert "index_summary" in payload
