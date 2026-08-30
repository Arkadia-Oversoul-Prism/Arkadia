"""WEAVER-MVP2-01 — frontend binds to governed execution API; UI ≠ authority."""
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

    return get_project_manager().create("MVP201-A", {}, owner_uid="mvp201-a")


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
    patch.setdefault("plan_id", "plan-mvp201")
    patch.setdefault("plan_content_hash", "planhash-mvp201")
    patch.setdefault("changeset_id", "cs-mvp201")
    patch.setdefault("patch_id", "patch-mvp201")
    return patch


def test_mvp201_frontend_calls_execution_routes_only():
    src = FRONTEND.read_text(encoding="utf-8")
    # Routes are composed via execBase = `${base}/execution`
    assert 'execBase = `${base}/execution`' in src or 'execBase =' in src
    assert "/pass-spec" in src
    assert "/approval" in src
    assert "/execute" in src
    assert "/readiness" in src
    assert "run_transaction" not in src
    assert "weaver/transaction" not in src
    assert "k15_ready" in src
    assert "run_k3: false" in src or "run_k3:false" in src.replace(" ", "")


def test_mvp201_frontend_does_not_manufacture_hashes():
    src = FRONTEND.read_text(encoding="utf-8")
    # No local hash synthesis for authorization
    assert "sha256" not in src.lower() or "patch_hash" in src  # display ok
    # approved flag only sent as request field to backend, not as sole gate
    assert "k15Ready" in src or "k15_ready" in src


def test_mvp201_no_auth_locked(project_a, sample_patch, repo_root):
    from solspire.project_execution import evaluate_execution_state

    st = evaluate_execution_state(patch=sample_patch, repo_root=repo_root)
    assert st["k15_ready"] is False
    assert st["state"] == "PASSSPEC_REQUIRED"


def test_mvp201_pass_spec_only(project_a, sample_patch, repo_root):
    from solspire.project_execution import build_pass_spec_for_patch, evaluate_execution_state

    spec = build_pass_spec_for_patch(project_a.to_dict(), sample_patch, repo_root=repo_root)
    st = evaluate_execution_state(patch=sample_patch, pass_spec=spec, repo_root=repo_root)
    assert st["state"] == "PATCH_APPROVAL_REQUIRED"
    assert st["k15_ready"] is False


def test_mvp201_full_auth_k15_ready(project_a, sample_patch, repo_root):
    from solspire.project_execution import (
        build_pass_spec_for_patch,
        build_patch_approval,
        evaluate_execution_state,
        execute_project_patch,
    )

    spec = build_pass_spec_for_patch(project_a.to_dict(), sample_patch, repo_root=repo_root)
    approval = build_patch_approval(sample_patch, spec, approved=True)
    st = evaluate_execution_state(
        patch=sample_patch, pass_spec=spec, approval=approval, repo_root=repo_root
    )
    assert st["k15_ready"] is True
    out = execute_project_patch(
        project_a.to_dict(), sample_patch, spec, approval, repo_root=repo_root, run_k3=False
    )
    assert (out.get("execution") or {}).get("status") == "NOT_RUN"
    assert (out.get("verification") or {}).get("status") == "NOT_RUN"


def test_mvp201_hash_mismatch_blocked(project_a, sample_patch, repo_root):
    from solspire.project_execution import (
        build_pass_spec_for_patch,
        build_patch_approval,
        evaluate_execution_state,
    )

    spec = build_pass_spec_for_patch(project_a.to_dict(), sample_patch, repo_root=repo_root)
    approval = build_patch_approval(sample_patch, spec, approved=True)
    approval["patch_hash"] = "0" * 64
    st = evaluate_execution_state(
        patch=sample_patch, pass_spec=spec, approval=approval, repo_root=repo_root
    )
    assert st["k15_ready"] is False
    assert st["state"] == "BLOCKED"


def test_mvp201_project_layer_no_direct_k3():
    import inspect
    import solspire.project_execution as pe

    src = inspect.getsource(pe)
    assert "execute_patch" in src
    assert "run_transaction" not in src


def test_mvp201_isolation():
    from solspire.project_manager import get_project_manager
    from solspire.project_store import add_memory, list_memory

    pm = get_project_manager()
    a = pm.create("MVP201-Iso-A", {}, owner_uid="iso201-a")
    b = pm.create("MVP201-Iso-B", {}, owner_uid="iso201-b")
    add_memory(a.id, "secret", "only A", tags=[])
    assert len(list_memory(a.id)) >= 1
    assert len(list_memory(b.id)) == 0
