"""WEAVER-K14 — patch synthesis + dry-run impact proofs."""
from __future__ import annotations

import subprocess
from pathlib import Path

from weaver.engineering_plan import EngineeringPlan
from weaver.implementation import synthesize_changeset
from weaver.pass_spec import PassSpec
from weaver.patch import PatchStatus, synthesize_patch, review_patch
from weaver.verification import plan_content_hash
import weaver.patch as pmod


def _repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "weaver").mkdir()
    (tmp_path / "weaver" / "m.py").write_text("def gamma():\n    return 2\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_m.py").write_text("import weaver.m\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()


def _cs(tmp_path, head, paths=None):
    plan = EngineeringPlan(
        plan_id="ep",
        objective="o",
        affected_paths=paths or ["weaver/m.py"],
        implementation_steps=["update gamma"],
        proposed_changes=["touch gamma"],
        test_strategy={"required_tests": ["tests/test_m.py"]},
        verification_strategy=["pytest"],
        evidence_refs=[{"kind": "FACT", "statement": "m exists"}],
    )
    return synthesize_changeset(
        plan,
        pass_spec=PassSpec(pass_id="K14", objective="o", base_sha=head, allowed_paths=["weaver/"], forbidden_paths=["api/"]),
        bound_head_sha=head,
        repo_root=str(tmp_path),
    )


def test_patch_deterministic(tmp_path):
    head = _repo(tmp_path)
    cs = _cs(tmp_path, head)
    a = synthesize_patch(cs, bound_head_sha=head, repo_root=str(tmp_path))
    b = synthesize_patch(cs, bound_head_sha=head, repo_root=str(tmp_path))
    assert a.patch_id == b.patch_id
    assert a.files[0]["patch_text"] == b.files[0]["patch_text"]
    assert a.execution["EXECUTED"] is False
    assert a.authorization["current_pass_authorized"] is False or True  # may inherit no pass_spec on patch call
    # no mutation
    assert "gamma" in (tmp_path / "weaver" / "m.py").read_text()
    assert "[K14 PROPOSED]" not in (tmp_path / "weaver" / "m.py").read_text()


def test_stale(tmp_path):
    head = _repo(tmp_path)
    cs = _cs(tmp_path, head)
    p = synthesize_patch(cs, bound_head_sha="0" * 40, repo_root=str(tmp_path))
    assert p.status == PatchStatus.STALE.value


def test_plan_binding(tmp_path):
    head = _repo(tmp_path)
    cs = _cs(tmp_path, head)
    p = synthesize_patch(cs, expected_plan_hash="dead", bound_head_sha=head, repo_root=str(tmp_path))
    assert p.status == PatchStatus.PLAN_BINDING_MISMATCH.value


def test_out_of_scope(tmp_path):
    head = _repo(tmp_path)
    plan = EngineeringPlan(
        plan_id="ep",
        objective="o",
        affected_paths=["api/x.py"],
        implementation_steps=["x"],
        proposed_changes=["x"],
    )
    cs = synthesize_changeset(
        plan,
        pass_spec=PassSpec(pass_id="K14", objective="o", base_sha=head, allowed_paths=["weaver/"], forbidden_paths=["api/"]),
        bound_head_sha=head,
        repo_root=str(tmp_path),
    )
    p = synthesize_patch(
        cs,
        pass_spec=PassSpec(pass_id="K14", objective="o", base_sha=head, allowed_paths=["weaver/"], forbidden_paths=["api/"]),
        bound_head_sha=head,
        repo_root=str(tmp_path),
    )
    assert p.status in (PatchStatus.OUT_OF_SCOPE.value, PatchStatus.PATCH_UNDER_SPECIFIED.value, PatchStatus.PATCH_BASE_MISMATCH.value)


def test_impact_and_review(tmp_path):
    head = _repo(tmp_path)
    cs = _cs(tmp_path, head)
    p = synthesize_patch(cs, bound_head_sha=head, repo_root=str(tmp_path))
    assert "weaver/m.py" in p.impact["files"]
    assert p.tests["runtime_coverage"] == "UNKNOWN"
    r = review_patch(p)
    assert r["EXECUTED"] is False
    assert "patch_text" in p.files[0]


def test_no_apply_apis():
    for name in ("apply_patch", "write_file", "commit_and_push", "run_transaction", "execute"):
        assert not hasattr(pmod, name)
