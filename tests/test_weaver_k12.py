"""WEAVER-K12 — verification / proof reconciliation proofs."""
from __future__ import annotations

import subprocess

from weaver.engineering_plan import build_engineering_plan, EngineeringPlan
from weaver.pass_spec import PassSpec
from weaver.verification import (
    VerificationVerdict,
    PublicationStatus,
    plan_content_hash,
    verify_implementation,
    verify_transaction_result,
)
import weaver.verification as vmod


def _repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "weaver").mkdir()
    (tmp_path / "weaver" / "a.py").write_text("x=1\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()


def _plan(paths, tests=None):
    return EngineeringPlan(
        plan_id="p1",
        objective="t",
        affected_paths=list(paths),
        implementation_steps=["s1"],
        proposed_changes=["c1"],
        test_strategy={"required_tests": list(tests or [])},
    )


def test_match_verified(tmp_path):
    head = _repo(tmp_path)
    p = _plan(["weaver/a.py"])
    r = verify_implementation(
        p,
        actual_paths=["weaver/a.py"],
        test_results={"executed": [], "passed": [], "failed": []},
        publication_required=False,
        bound_head_sha=head,
        bound_origin_sha=None,
        repo_root=str(tmp_path),
    )
    assert r.verdict["status"] in (
        VerificationVerdict.VERIFIED.value,
        VerificationVerdict.INSUFFICIENT_EVIDENCE.value,
        VerificationVerdict.PARTIALLY_VERIFIED.value,
    )
    assert r.authorization["current_pass_authorized"] is False


def test_missing_and_unexpected(tmp_path):
    head = _repo(tmp_path)
    p = _plan(["weaver/a.py"])
    r = verify_implementation(
        p,
        actual_paths=["weaver/other.py"],
        bound_head_sha=head,
        repo_root=str(tmp_path),
    )
    assert "weaver/a.py" in r.scope["missing_paths"]
    assert "weaver/other.py" in r.scope["unexpected_paths"]


def test_failed_tests(tmp_path):
    head = _repo(tmp_path)
    p = _plan(["weaver/a.py"], tests=["tests/test_a.py"])
    r = verify_implementation(
        p,
        actual_paths=["weaver/a.py"],
        test_results={
            "executed": ["tests/test_a.py"],
            "passed": [],
            "failed": ["tests/test_a.py"],
        },
        bound_head_sha=head,
        repo_root=str(tmp_path),
    )
    assert r.verdict["status"] == VerificationVerdict.FAILED.value


def test_insufficient_tests(tmp_path):
    head = _repo(tmp_path)
    p = _plan(["weaver/a.py"], tests=["tests/test_a.py"])
    r = verify_implementation(
        p,
        actual_paths=["weaver/a.py"],
        test_results={"executed": [], "passed": [], "failed": []},
        bound_head_sha=head,
        repo_root=str(tmp_path),
    )
    assert r.verdict["status"] == VerificationVerdict.INSUFFICIENT_EVIDENCE.value


def test_stale(tmp_path):
    head = _repo(tmp_path)
    p = _plan(["weaver/a.py"])
    r = verify_implementation(
        p,
        actual_paths=["weaver/a.py"],
        bound_head_sha="0" * 40,
        bound_origin_sha=None,
        repo_root=str(tmp_path),
    )
    assert r.verdict["status"] == VerificationVerdict.STALE.value


def test_plan_binding_mismatch(tmp_path):
    head = _repo(tmp_path)
    p = _plan(["weaver/a.py"])
    r = verify_implementation(
        p,
        actual_paths=["weaver/a.py"],
        expected_plan_hash="deadbeef",
        bound_head_sha=head,
        repo_root=str(tmp_path),
    )
    assert r.plan["binding"] == "PLAN_BINDING_MISMATCH"
    assert r.verdict["status"] == VerificationVerdict.FAILED.value


def test_publication_published(tmp_path):
    head = _repo(tmp_path)
    p = _plan(["weaver/a.py"])
    r = verify_implementation(
        p,
        actual_paths=["weaver/a.py"],
        result_sha=head,
        remote_sha=head,
        publication_required=True,
        bound_head_sha=head,
        bound_origin_sha=head,
        repo_root=str(tmp_path),
    )
    assert r.publication["status"] == PublicationStatus.PUBLISHED.value


def test_no_execute():
    for name in ("write_file", "commit_and_push", "run_transaction", "execute", "approve"):
        assert not hasattr(vmod, name)


def test_hash_stable():
    p = _plan(["b", "a"])
    assert plan_content_hash(p) == plan_content_hash(p)


def test_transaction_adapter(tmp_path):
    head = _repo(tmp_path)
    p = _plan(["weaver/a.py"])
    r = verify_transaction_result(
        plan=p,
        changed_paths=["weaver/a.py"],
        result_sha=head,
        remote_sha=head,
        publication_required=False,
        repo_root=str(tmp_path),
    )
    assert r.proof_matrix
    assert r.review_bundle["next_action"] == "awaiting human authorization"
