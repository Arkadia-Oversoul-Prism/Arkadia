"""WEAVER-K15 — governed patch execution orchestration proofs."""
from __future__ import annotations

import subprocess

from weaver.engineering_plan import EngineeringPlan
from weaver.execution import (
    PatchApproval,
    execute_patch,
    patch_content_hash,
    pass_spec_hash,
)
from weaver.implementation import synthesize_changeset
from weaver.pass_spec import PassSpec
from weaver.patch import synthesize_patch
import weaver.execution as emod


def _repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "weaver").mkdir()
    (tmp_path / "weaver" / "x.py").write_text("def z():\n    return 0\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()


def _spec(head, **kw):
    base = dict(
        pass_id="K15",
        objective="exec",
        base_sha=head,
        allowed_paths=["weaver/", "data/weaver/", "docs/verification/"],
        forbidden_paths=["api/"],
        required_tests=[],
        publication_required=False,
    )
    base.update(kw)
    return PassSpec(**base)


def _patch(tmp_path, head):
    plan = EngineeringPlan(
        plan_id="ep",
        objective="o",
        affected_paths=["weaver/x.py"],
        implementation_steps=["touch"],
        proposed_changes=["touch"],
        test_strategy={"required_tests": []},
    )
    cs = synthesize_changeset(plan, pass_spec=_spec(head), bound_head_sha=head, repo_root=str(tmp_path))
    return synthesize_patch(cs, pass_spec=_spec(head), bound_head_sha=head, repo_root=str(tmp_path))


def _approval(patch, spec):
    return PatchApproval(
        patch_id=patch.patch_id,
        patch_hash=patch_content_hash(patch),
        plan_id=patch.plan_id,
        plan_hash=patch.plan_content_hash,
        base_head_sha=patch.base_head_sha,
        base_origin_sha=patch.base_origin_sha,
        pass_spec_hash=pass_spec_hash(spec),
        approved=True,
    )


def test_no_pass_spec_blocked(tmp_path):
    head = _repo(tmp_path)
    p = _patch(tmp_path, head)
    r = execute_patch(p, None, _approval(p, _spec(head)), repo_root=str(tmp_path), run_k3=False)
    assert r.final_status == "BLOCKED"
    assert "PassSpec" in r.message


def test_no_approval_blocked(tmp_path):
    head = _repo(tmp_path)
    p = _patch(tmp_path, head)
    r = execute_patch(p, _spec(head), None, repo_root=str(tmp_path), run_k3=False)
    assert r.final_status == "BLOCKED"


def test_approval_patch_mismatch(tmp_path):
    head = _repo(tmp_path)
    p = _patch(tmp_path, head)
    a = _approval(p, _spec(head))
    a.patch_hash = "deadbeef"
    r = execute_patch(p, _spec(head), a, repo_root=str(tmp_path), run_k3=False)
    assert r.final_status == "BLOCKED"
    assert "patch binding" in r.message


def test_head_drift(tmp_path):
    head = _repo(tmp_path)
    p = _patch(tmp_path, head)
    a = _approval(p, _spec(head))
    # mutate p base
    p.base_head_sha = "0" * 40
    a.base_head_sha = "0" * 40
    a.patch_hash = patch_content_hash(p)
    r = execute_patch(p, _spec(head), a, repo_root=str(tmp_path), run_k3=False)
    assert r.final_status == "BLOCKED"
    assert "HEAD drift" in r.message


def test_out_of_scope(tmp_path):
    head = _repo(tmp_path)
    plan = EngineeringPlan(
        plan_id="ep",
        objective="o",
        affected_paths=["api/x.py"],
        implementation_steps=["x"],
        proposed_changes=["x"],
    )
    from weaver.implementation import synthesize_changeset
    from weaver.patch import synthesize_patch

    cs = synthesize_changeset(
        plan,
        pass_spec=_spec(head, allowed_paths=["weaver/"], forbidden_paths=["api/"]),
        bound_head_sha=head,
        repo_root=str(tmp_path),
    )
    p = synthesize_patch(
        cs,
        pass_spec=_spec(head, allowed_paths=["weaver/"], forbidden_paths=["api/"]),
        bound_head_sha=head,
        repo_root=str(tmp_path),
    )
    # force a file path out of scope for execute gate
    if not p.files:
        p.files = [{"path": "api/x.py", "operation": "MODIFY", "patch_text": ""}]
    a = _approval(p, _spec(head, allowed_paths=["weaver/"], forbidden_paths=["api/"]))
    r = execute_patch(p, _spec(head, allowed_paths=["weaver/"], forbidden_paths=["api/"]), a, repo_root=str(tmp_path), run_k3=False)
    assert r.final_status == "BLOCKED"


def test_preflight_ok_no_k3(tmp_path):
    head = _repo(tmp_path)
    p = _patch(tmp_path, head)
    a = _approval(p, _spec(head))
    r = execute_patch(p, _spec(head), a, repo_root=str(tmp_path), run_k3=False)
    assert r.preflight["authorization"] is True
    assert r.preflight["scope"] is True
    assert r.preflight["binding"] is True
    assert r.mutation["attempted"] is False
    assert r.authorization["current_pass_authorized"] is False


def test_no_second_mutation_api():
    for name in ("write_file", "commit_and_push", "apply_patch"):
        assert not hasattr(emod, name)
    assert hasattr(emod, "execute_patch")
