"""R1 — SolSpire governance convergence tests.

These tests establish that SolSpire remains a project adapter while Weaver
owns PassSpec, PatchApproval, hashing, and K15 readiness semantics.
"""
from __future__ import annotations

import inspect
from pathlib import Path

REPO_ROOT = str(Path(__file__).resolve().parents[1])


def _patch(repo_root: str) -> dict:
    from weaver.pass_spec import current_head, current_origin_main

    return {
        "patch_id": "r1-patch",
        "plan_id": "r1-plan",
        "plan_content_hash": "r1-plan-hash",
        "base_head_sha": current_head(repo_root),
        "base_origin_sha": current_origin_main(repo_root),
        "status": "VALID",
        "files": [{
            "path": "weaver/pass_spec.py",
            "operation": "MODIFY",
            "patch_text": "--- a/weaver/pass_spec.py\n+++ b/weaver/pass_spec.py\n@@\n-x\n+y\n",
        }],
        "review": {"objective": "R1 governance convergence"},
    }


def test_r1_solspire_readiness_delegates_to_weaver(repo_root=REPO_ROOT):
    from solspire.project_execution import evaluate_execution_state
    from weaver.governance import evaluate_patch_readiness

    patch = _patch(repo_root)
    project_state = evaluate_execution_state(patch=patch, pass_spec=None, approval=None, repo_root=repo_root)
    weaver_state = evaluate_patch_readiness(patch=patch, pass_spec=None, approval=None, repo_root=repo_root)
    assert project_state == weaver_state


def test_r1_solspire_builders_delegate_to_weaver(repo_root=REPO_ROOT):
    from solspire.project_execution import build_pass_spec_for_patch, build_patch_approval
    from weaver.governance import build_patch_approval as weaver_build_approval
    from weaver.governance import build_pass_spec_for_patch as weaver_build_spec

    patch = _patch(repo_root)
    project = {"id": "r1-project", "name": "R1 Project"}
    sol_spec = build_pass_spec_for_patch(project, patch, repo_root=repo_root)
    canonical_spec = weaver_build_spec(
        patch,
        pass_id="mvp1-r1-patch",
        objective="R1 Project",
        repo_root=repo_root,
    ).to_dict()
    for key in canonical_spec:
        assert sol_spec[key] == canonical_spec[key]

    sol_approval = build_patch_approval(patch, sol_spec, approved=True)
    canonical_approval = weaver_build_approval(patch, sol_spec, approved=True).to_dict()
    for key in canonical_approval:
        assert sol_approval[key] == canonical_approval[key]


def test_r1_solspire_has_no_local_governance_constructors():
    import solspire.project_execution as project_execution

    source = inspect.getsource(project_execution)
    assert "PassSpec(" not in source
    assert "PatchApproval(" not in source
    assert "def pass_spec_hash" not in source
    assert "def patch_content_hash" not in source
    assert "path_in_allowlist" not in source


def test_r1_weaver_governance_is_canonical():
    import weaver.governance as governance

    source = inspect.getsource(governance)
    assert "def evaluate_patch_readiness" in source
    assert "def build_pass_spec_for_patch" in source
    assert "def build_patch_approval" in source
    assert "execute_patch" in source


def test_r1_project_execution_remains_k15_k3_adapter(repo_root=REPO_ROOT):
    from solspire.project_execution import build_pass_spec_for_patch, build_patch_approval, execute_project_patch

    patch = _patch(repo_root)
    project = {"id": "r1-project", "name": "R1 Project"}
    spec = build_pass_spec_for_patch(project, patch, repo_root=repo_root)
    approval = build_patch_approval(patch, spec, approved=True)
    result = execute_project_patch(project, patch, spec, approval, repo_root=repo_root, run_k3=False)
    assert result["k15_ready"] is True
    assert result["execution"]["status"] == "NOT_RUN"
    assert result["verification"]["status"] == "NOT_RUN"
