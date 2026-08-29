"""WEAVER-MVP1 — durable governed operator loop invariants."""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = str(Path(__file__).resolve().parents[1])


@pytest.fixture
def repo_root():
    return REPO_ROOT


@pytest.fixture
def project_a():
    from solspire.project_manager import get_project_manager

    return get_project_manager().create("MVP1-A", {}, owner_uid="mvp1-owner-a")


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
    patch.setdefault("plan_id", "plan-mvp1")
    patch.setdefault("plan_content_hash", "planhash-mvp1")
    patch.setdefault("changeset_id", "cs-mvp1")
    patch.setdefault("patch_id", "patch-mvp1")
    return patch


def test_mvp1_project_isolation():
    from solspire.project_manager import get_project_manager
    from solspire.project_store import add_memory, list_memory

    pm = get_project_manager()
    a = pm.create("MVP1-Iso-A", {}, owner_uid="iso-a")
    b = pm.create("MVP1-Iso-B", {}, owner_uid="iso-b")
    add_memory(a.id, "secret", "only A", tags=[])
    assert len(list_memory(a.id)) >= 1
    assert len(list_memory(b.id)) == 0
    ids_a = {p.id for p in pm.list_projects(owner_uid="iso-a")}
    ids_b = {p.id for p in pm.list_projects(owner_uid="iso-b")}
    assert a.id in ids_a and a.id not in ids_b
    assert b.id in ids_b and b.id not in ids_a


def test_mvp1_knowledge_to_weaver_context(project_a, repo_root):
    from solspire.project_store import add_memory
    from solspire.weaver_bridge import project_analyze

    add_memory(project_a.id, "note", "context only", tags=["t"])
    result = project_analyze(
        project_a.to_dict(),
        "Review PassSpec boundary",
        affected_paths=["weaver/pass_spec.py"],
        repo_root=repo_root,
    )
    assert result.get("executed") is False
    assert (result.get("authorization") or {}).get("Execution") == "LOCKED"


def test_mvp1_pipeline_no_redesign_region(sample_patch):
    assert sample_patch.get("files")
    pt = (sample_patch.get("files") or [{}])[0].get("patch_text") or ""
    assert "@@ redesign region @@" not in pt


def test_mvp1_pass_spec_approval_and_hash(project_a, sample_patch, repo_root):
    from solspire.project_execution import (
        build_pass_spec_for_patch,
        build_patch_approval,
        evaluate_execution_state,
    )

    assert evaluate_execution_state(patch=sample_patch, repo_root=repo_root)["state"] == "PASSSPEC_REQUIRED"
    spec = build_pass_spec_for_patch(project_a.to_dict(), sample_patch, repo_root=repo_root)
    assert evaluate_execution_state(patch=sample_patch, pass_spec=spec, repo_root=repo_root)["state"] == "PATCH_APPROVAL_REQUIRED"
    approval = build_patch_approval(sample_patch, spec, approved=True)
    ready = evaluate_execution_state(patch=sample_patch, pass_spec=spec, approval=approval, repo_root=repo_root)
    assert ready["k15_ready"] is True
    approval2 = dict(approval)
    approval2["patch_hash"] = "0" * 64
    bad = evaluate_execution_state(patch=sample_patch, pass_spec=spec, approval=approval2, repo_root=repo_root)
    assert bad["k15_ready"] is False and bad["state"] == "BLOCKED"


def test_mvp1_k15_only_no_direct_k3():
    import inspect
    import solspire.project_execution as pe

    src = inspect.getsource(pe)
    assert "execute_patch" in src
    assert "run_transaction" not in src


def test_mvp1_precheck_no_mutation(project_a, sample_patch, repo_root):
    import subprocess
    from solspire.project_execution import (
        build_pass_spec_for_patch,
        build_patch_approval,
        execute_project_patch,
    )

    before = subprocess.run(["git", "status", "--porcelain"], cwd=repo_root, capture_output=True, text=True).stdout
    spec = build_pass_spec_for_patch(project_a.to_dict(), sample_patch, repo_root=repo_root)
    approval = build_patch_approval(sample_patch, spec, approved=True)
    result = execute_project_patch(
        project_a.to_dict(), sample_patch, spec, approval, repo_root=repo_root, run_k3=False
    )
    after = subprocess.run(["git", "status", "--porcelain"], cwd=repo_root, capture_output=True, text=True).stdout
    assert result.get("k15_ready") is True
    assert (result.get("verification") or {}).get("status") == "NOT_RUN"

    def tracked(s: str):
        return {ln for ln in s.splitlines() if not ln.startswith("??")}

    assert tracked(before) == tracked(after)


def test_mvp1_embeddings_not_available(project_a):
    from solspire.project_knowledge import build_knowledge_summary

    s = build_knowledge_summary(project_a.id)
    assert (s.get("embeddings") or {}).get("status") == "NOT_AVAILABLE"
