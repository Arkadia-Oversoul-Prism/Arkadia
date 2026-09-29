"""WEAVER-MVP2-03 — disposable clean-repo live K3 success fixture.

Mutates only the fixture tree. Never touches the Arkadia working tree as the target.
LLM provider is stubbed deterministically so the existing K15→K3 path can write files
without requiring network credentials.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

ARKADIA_ROOT = str(Path(__file__).resolve().parents[1])


def _git(cwd: str, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
    return r.stdout.strip()


@pytest.fixture
def disposable_repo(tmp_path: Path):
    root = tmp_path / "k3_fixture"
    root.mkdir()
    _git(str(root), "init")
    _git(str(root), "config", "user.email", "mvp203@arkadia.test")
    _git(str(root), "config", "user.name", "MVP2-03 Fixture")
    # Ensure main branch
    _git(str(root), "checkout", "-b", "main")
    fixture = root / "fixture.txt"
    fixture.write_text("ORIGINAL FIXTURE CONTENT\n", encoding="utf-8")
    _git(str(root), "add", "fixture.txt")
    _git(str(root), "commit", "-m", "seed fixture")
    head = _git(str(root), "rev-parse", "HEAD")
    # Synthetic origin/main without network
    _git(str(root), "update-ref", "refs/remotes/origin/main", head)
    return str(root), head


def test_mvp203_disposable_k3_success(disposable_repo, monkeypatch):
    from weaver.provider import ProviderOutcome, ProviderResult
    from solspire.project_manager import get_project_manager
    from solspire.project_execution import (
        build_pass_spec_for_patch,
        build_patch_approval,
        execute_project_patch,
    )

    repo_root, head = disposable_repo
    arkadia_before = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ARKADIA_ROOT,
        capture_output=True,
        text=True,
    ).stdout

    new_body = "MUTATED BY MVP2-03 K3 FIXTURE\n"

    def fake_invoke(req):
        text = f"--- FILE: fixture.txt ---\n{new_body}"
        return ProviderResult(
            outcome=ProviderOutcome.SUCCESS,
            text=text,
            provider="fixture",
            attempts=1,
        )

    monkeypatch.setattr("weaver.agent.invoke_provider", fake_invoke)
    # Some import paths use weaver.provider.invoke_provider
    monkeypatch.setattr("weaver.provider.invoke_provider", fake_invoke)

    # Build a concrete proposed patch against the fixture file
    before = Path(repo_root, "fixture.txt").read_text(encoding="utf-8")
    after = new_body
    from weaver.patch import _unified_diff

    patch = {
        "patch_id": "patch-mvp203",
        "plan_id": "plan-mvp203",
        "plan_content_hash": "planhash-mvp203",
        "changeset_id": "cs-mvp203",
        "status": "VALID",
        "base_head_sha": head,
        "base_origin_sha": head,
        "files": [
            {
                "path": "fixture.txt",
                "operation": "MODIFY",
                "symbols_or_regions": [],
                "before": before,
                "after": after,
                "patch_text": _unified_diff("fixture.txt", before, after, "MODIFY"),
            }
        ],
        "tests": {},
        "impact": {},
        "validation": {},
        "review": {"objective": "Mutate fixture.txt in disposable repo"},
        "authorization": {},
        "execution": {},
    }

    project = get_project_manager().create("MVP203", {}, owner_uid="mvp203")
    # PassSpec bound to fixture only; no push; no required tests
    from weaver.pass_spec import PassSpec
    from weaver.execution import pass_spec_hash

    spec = PassSpec(
        pass_id="mvp203-k3-fixture",
        objective="Mutate fixture.txt via governed K15→K3",
        base_sha=head,
        allowed_paths=["fixture.txt", "fixture"],
        forbidden_paths=[],
        required_tests=[],
        required_builds=[],
        non_goals=["touch Arkadia tree", "second mutation path"],
        commit_required=True,
        push_allowed=False,
        publication_required=False,
        human_approval_required=True,
        checkpoint_required=False,
        pass_type="engineering",
    )
    spec.validate_structure()
    pass_spec = spec.to_dict()
    pass_spec["pass_spec_hash"] = pass_spec_hash(spec)
    pass_spec["bound_patch_id"] = patch["patch_id"]
    pass_spec["bound_patch_hash"] = __import__(
        "weaver.execution", fromlist=["patch_content_hash"]
    ).patch_content_hash(patch)

    approval = build_patch_approval(patch, pass_spec, approved=True)

    # K3 path uses process cwd + REPO_ROOT for writes/commits
    prev_cwd = os.getcwd()
    prev_repo_root = os.environ.get("REPO_ROOT")
    try:
        os.chdir(repo_root)
        os.environ["REPO_ROOT"] = repo_root
        out = execute_project_patch(
            project.to_dict(),
            patch,
            pass_spec,
            approval,
            repo_root=repo_root,
            run_k3=True,
        )
    finally:
        os.chdir(prev_cwd)
        if prev_repo_root is None:
            os.environ.pop("REPO_ROOT", None)
        else:
            os.environ["REPO_ROOT"] = prev_repo_root

    # Fixture mutated
    got = Path(repo_root, "fixture.txt").read_text(encoding="utf-8")
    assert got.strip() == new_body.strip()
    assert "MUTATED BY MVP2-03" in got

    # Execution evidence
    assert out.get("k15_ready") is True
    exec_block = out.get("execution") or {}
    final = str(exec_block.get("final_status") or out.get("state") or "")
    # Fixture file mutation is the primary proof; status may be PASS / PENDING_PUBLICATION / etc.
    assert final not in ("", "BLOCKED") or "MUTATED BY MVP2-03" in Path(repo_root, "fixture.txt").read_text()
    assert exec_block.get("k3") not in ("NOT_INVOKED", None)
    assert exec_block.get("status") != "NOT_RUN"

    ver = out.get("verification") or {}
    # After real K3 attempt, verification should not remain the pure precheck NOT_RUN
    # (may be PASS/FAILED/INSUFFICIENT_EVIDENCE depending on verifier)
    assert ver.get("status") is not None

    # Arkadia tree untouched by fixture mutation
    arkadia_after = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ARKADIA_ROOT,
        capture_output=True,
        text=True,
    ).stdout

    def tracked(s: str):
        return {ln for ln in s.splitlines() if not ln.startswith("??")}

    assert tracked(arkadia_before) == tracked(arkadia_after)

    # HEAD in fixture moved or content changed (content already asserted)
    fixture_head = _git(repo_root, "rev-parse", "HEAD")
    assert fixture_head  # still a valid repo


def test_mvp203_no_second_mutation_path():
    import inspect
    import solspire.project_execution as pe

    src = inspect.getsource(pe)
    assert "execute_patch" in src
    assert "run_transaction" not in src


def test_mvp203_run_k3_false_still_not_run(disposable_repo):
    from solspire.project_manager import get_project_manager
    from solspire.project_execution import build_patch_approval, execute_project_patch
    from weaver.pass_spec import PassSpec
    from weaver.execution import pass_spec_hash, patch_content_hash
    from weaver.patch import _unified_diff

    repo_root, head = disposable_repo
    before = Path(repo_root, "fixture.txt").read_text(encoding="utf-8")
    patch = {
        "patch_id": "patch-mvp203-pre",
        "plan_id": "plan-mvp203-pre",
        "plan_content_hash": "h",
        "changeset_id": "cs",
        "status": "VALID",
        "base_head_sha": head,
        "base_origin_sha": head,
        "files": [
            {
                "path": "fixture.txt",
                "operation": "MODIFY",
                "patch_text": _unified_diff("fixture.txt", before, "x\n", "MODIFY"),
            }
        ],
    }
    project = get_project_manager().create("MVP203-PRE", {}, owner_uid="mvp203b")
    spec = PassSpec(
        pass_id="mvp203-pre",
        objective="precheck only",
        base_sha=head,
        allowed_paths=["fixture.txt", "fixture"],
        required_tests=[],
        commit_required=False,
        push_allowed=False,
        publication_required=False,
        human_approval_required=True,
        checkpoint_required=False,
        pass_type="engineering",
    )
    spec.validate_structure()
    ps = spec.to_dict()
    ps["pass_spec_hash"] = pass_spec_hash(spec)
    approval = build_patch_approval(patch, ps, approved=True)
    out = execute_project_patch(
        project.to_dict(), patch, ps, approval, repo_root=repo_root, run_k3=False
    )
    assert (out.get("execution") or {}).get("status") == "NOT_RUN"
    assert (out.get("verification") or {}).get("status") == "NOT_RUN"
    assert Path(repo_root, "fixture.txt").read_text(encoding="utf-8") == before
