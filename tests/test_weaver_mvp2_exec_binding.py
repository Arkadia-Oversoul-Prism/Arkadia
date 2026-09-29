"""WEAVER-MVP2 execution-binding matrix — new lineage event."""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = str(Path(__file__).resolve().parents[1])
FRONTEND = Path(REPO_ROOT) / "web/public_prism/src/pages/ProjectDashboard.tsx"


@pytest.fixture
def repo_root():
    return REPO_ROOT


@pytest.fixture
def project_a():
    from solspire.project_manager import get_project_manager
    return get_project_manager().create("MVP2EB-A", {}, owner_uid="mvp2eb-a")


@pytest.fixture
def sample_patch(repo_root):
    from weaver.pass_spec import current_head, current_origin_main
    from weaver.workbench_view import run_read_only_pipeline

    result = run_read_only_pipeline(
        "Clarify module docstring on weaver/pass_spec.py.",
        repo_root=repo_root,
        affected_paths=["weaver/pass_spec.py"],
    )
    patch = dict(result.get("patch") or {})
    if not patch.get("base_head_sha"):
        patch["base_head_sha"] = current_head(repo_root)
    if "base_origin_sha" not in patch:
        patch["base_origin_sha"] = current_origin_main(repo_root)
    patch.setdefault("plan_id", "plan-mvp2eb")
    patch.setdefault("plan_content_hash", "planhash-mvp2eb")
    patch.setdefault("patch_id", "patch-mvp2eb")
    patch.setdefault("status", "VALID")
    return patch


def test_eb_owner_reaches_k15_ready(project_a, sample_patch, repo_root):
    from solspire.project_execution import (
        build_pass_spec_for_patch, build_patch_approval, evaluate_execution_state,
    )
    spec = build_pass_spec_for_patch(project_a.to_dict(), sample_patch, repo_root=repo_root)
    approval = build_patch_approval(sample_patch, spec, approved=True)
    st = evaluate_execution_state(patch=sample_patch, pass_spec=spec, approval=approval, repo_root=repo_root)
    assert st["k15_ready"] is True and st["state"] == "K15_READY"


def test_eb_missing_pass_spec_locked(sample_patch, repo_root):
    from solspire.project_execution import evaluate_execution_state
    st = evaluate_execution_state(patch=sample_patch, pass_spec=None, approval=None, repo_root=repo_root)
    assert st["k15_ready"] is False and st["state"] == "PASSSPEC_REQUIRED"


def test_eb_missing_approval_locked(project_a, sample_patch, repo_root):
    from solspire.project_execution import build_pass_spec_for_patch, evaluate_execution_state
    spec = build_pass_spec_for_patch(project_a.to_dict(), sample_patch, repo_root=repo_root)
    st = evaluate_execution_state(patch=sample_patch, pass_spec=spec, approval=None, repo_root=repo_root)
    assert st["k15_ready"] is False and st["state"] == "PATCH_APPROVAL_REQUIRED"


def test_eb_patch_hash_mismatch_locked(project_a, sample_patch, repo_root):
    from solspire.project_execution import (
        build_pass_spec_for_patch, build_patch_approval, evaluate_execution_state,
    )
    spec = build_pass_spec_for_patch(project_a.to_dict(), sample_patch, repo_root=repo_root)
    approval = build_patch_approval(sample_patch, spec, approved=True)
    approval["patch_hash"] = "0" * 64
    st = evaluate_execution_state(patch=sample_patch, pass_spec=spec, approval=approval, repo_root=repo_root)
    assert st["k15_ready"] is False and st["state"] == "BLOCKED"


def test_eb_pass_spec_hash_mismatch_locked(project_a, sample_patch, repo_root):
    from solspire.project_execution import (
        build_pass_spec_for_patch, build_patch_approval, evaluate_execution_state,
    )
    spec = build_pass_spec_for_patch(project_a.to_dict(), sample_patch, repo_root=repo_root)
    approval = build_patch_approval(sample_patch, spec, approved=True)
    approval["pass_spec_hash"] = "0" * 64
    st = evaluate_execution_state(patch=sample_patch, pass_spec=spec, approval=approval, repo_root=repo_root)
    assert st["k15_ready"] is False and st["state"] == "BLOCKED"


def test_eb_head_drift_locked(project_a, sample_patch, repo_root):
    from solspire.project_execution import (
        build_pass_spec_for_patch, build_patch_approval, evaluate_execution_state,
    )
    drifted = dict(sample_patch)
    drifted["base_head_sha"] = "deadbeef" * 5
    spec = build_pass_spec_for_patch(project_a.to_dict(), drifted, repo_root=repo_root)
    approval = build_patch_approval(drifted, spec, approved=True)
    st = evaluate_execution_state(patch=drifted, pass_spec=spec, approval=approval, repo_root=repo_root)
    assert st["k15_ready"] is False and st["state"] == "BLOCKED"
    assert any("drift" in r.lower() for r in st.get("lock_reasons") or [])


def test_eb_out_of_scope_locked(project_a, sample_patch, repo_root):
    from solspire.project_execution import (
        build_pass_spec_for_patch, build_patch_approval, evaluate_execution_state,
    )
    oos = dict(sample_patch)
    oos["files"] = [{
        "path": "secrets/not-allowed.py",
        "operation": "MODIFY",
        "patch_text": "--- a/secrets/not-allowed.py\n+++ b/secrets/not-allowed.py\n+x\n",
    }]
    spec = build_pass_spec_for_patch(
        project_a.to_dict(), oos, allowed_paths=["weaver/"], repo_root=repo_root
    )
    approval = build_patch_approval(oos, spec, approved=True)
    st = evaluate_execution_state(patch=oos, pass_spec=spec, approval=approval, repo_root=repo_root)
    assert st["k15_ready"] is False and st["state"] == "BLOCKED"
    assert any("OUT_OF_SCOPE" in r for r in st.get("lock_reasons") or [])


def test_eb_forbidden_path_locked(project_a, sample_patch, repo_root):
    from solspire.project_execution import (
        build_pass_spec_for_patch, build_patch_approval, evaluate_execution_state,
    )
    from weaver.execution import pass_spec_hash
    from weaver.pass_spec import PassSpec

    patch = dict(sample_patch)
    spec = build_pass_spec_for_patch(
        project_a.to_dict(), patch, allowed_paths=["weaver/"], repo_root=repo_root
    )
    spec["forbidden_paths"] = ["weaver/pass_spec.py"]
    psh = pass_spec_hash(PassSpec.from_dict(spec))
    spec["pass_spec_hash"] = psh
    approval = build_patch_approval(patch, spec, approved=True)
    st = evaluate_execution_state(patch=patch, pass_spec=spec, approval=approval, repo_root=repo_root)
    assert st["k15_ready"] is False and st["state"] == "BLOCKED"
    assert any("forbidden" in r.lower() for r in st.get("lock_reasons") or [])


def test_eb_unauthorized_project_denied():
    from solspire.project_manager import get_project_manager
    a = get_project_manager().create("MVP2EB-Own", {}, owner_uid="owner-a")
    assert (a.owner_uid or "").strip() == "owner-a"
    assert (a.owner_uid or "").strip() != "intruder"


def test_eb_precheck_no_mutation(project_a, sample_patch, repo_root):
    from solspire.project_execution import (
        build_pass_spec_for_patch, build_patch_approval, execute_project_patch,
    )
    spec = build_pass_spec_for_patch(project_a.to_dict(), sample_patch, repo_root=repo_root)
    approval = build_patch_approval(sample_patch, spec, approved=True)
    out = execute_project_patch(
        project_a.to_dict(), sample_patch, spec, approval, repo_root=repo_root, run_k3=False
    )
    assert out.get("k15_ready") is True
    assert (out.get("execution") or {}).get("status") == "NOT_RUN"
    assert (out.get("verification") or {}).get("status") == "NOT_RUN"


def test_eb_frontend_no_direct_k3():
    text = FRONTEND.read_text(encoding="utf-8")
    assert "run_transaction" not in text
    assert "execute_patch" not in text
    assert "weaver/execution" in text


def test_eb_no_second_mutation_path():
    import inspect
    import solspire.project_execution as pe
    import solspire.weaver_bridge as wb
    assert "run_transaction" not in inspect.getsource(pe)
    assert "execute_patch" in inspect.getsource(pe)
    assert "run_transaction" not in inspect.getsource(wb)


def test_eb_valid_reaches_k15_seam(project_a, sample_patch, repo_root):
    from solspire.weaver_bridge import project_execute_governed
    from solspire.project_execution import build_pass_spec_for_patch, build_patch_approval
    spec = build_pass_spec_for_patch(project_a.to_dict(), sample_patch, repo_root=repo_root)
    approval = build_patch_approval(sample_patch, spec, approved=True)
    out = project_execute_governed(
        project_a.to_dict(), sample_patch, spec, approval, run_k3=False, repo_root=repo_root
    )
    assert out.get("k15_ready") is True
    assert (out.get("execution") or {}).get("status") == "NOT_RUN"
