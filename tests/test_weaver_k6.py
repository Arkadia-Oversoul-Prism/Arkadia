"""WEAVER-K6 — session conductor lifecycle proofs."""
from __future__ import annotations

from weaver.pass_spec import PassSpec
from weaver.session import (
    SessionState,
    WeaverSession,
    approve,
    create_session,
    execute,
    propose,
    reject,
    review_bundle,
    run_recon,
    proposal_content_hash,
)
from weaver.proposal import Proposal, normalize_proposal, approve_proposal
from weaver.transaction import TransactionResult


def _spec(**kw) -> PassSpec:
    base = dict(
        pass_id="WEAVER-K6-TEST",
        objective="session test",
        base_sha="0" * 40,
        allowed_paths=["weaver/", "tests/test_weaver_k6.py"],
        forbidden_paths=["api/"],
        commit_required=False,
        push_allowed=False,
        publication_required=False,
    )
    base.update(kw)
    return PassSpec(**base)


def test_create_and_recon(tmp_path, monkeypatch):
    import subprocess, os
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "README").write_text("x")
    subprocess.run(["git", "add", "README"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    s = create_session("improve docs", repo_root=str(tmp_path))
    assert s.state == SessionState.CREATED.value
    run_recon(s, repo_root=str(tmp_path))
    assert s.state == SessionState.RECONSTRUCTED.value
    assert s.recon.get("head_sha")


def test_stops_at_awaiting_approval(tmp_path):
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "README").write_text("x")
    subprocess.run(["git", "add", "README"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    s = create_session("obj", repo_root=str(tmp_path))
    propose(s, allowed_paths=["weaver/"], repo_root=str(tmp_path))
    assert s.state == SessionState.AWAITING_APPROVAL.value
    # must not auto-execute
    assert s.execution_result is None


def test_reject_terminates(tmp_path):
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "README").write_text("x")
    subprocess.run(["git", "add", "README"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    s = create_session("obj", repo_root=str(tmp_path))
    propose(s, allowed_paths=["weaver/"], repo_root=str(tmp_path))
    reject(s)
    assert s.state == SessionState.REJECTED.value
    assert s.terminal_status == SessionState.REJECTED.value


def test_approval_binding_blocks_mutation(tmp_path):
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "README").write_text("x")
    subprocess.run(["git", "add", "README"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    s = create_session("obj", repo_root=str(tmp_path))
    propose(s, allowed_paths=["weaver/"], repo_root=str(tmp_path))
    approve(s, head_sha=head, repo_root=str(tmp_path))
    assert s.state == SessionState.APPROVED.value
    # mutate proposal after approval
    s.proposal["affected_paths"] = ["api/secret.py"]
    s.proposal["proposed_changes"] = ["evil"]
    res = execute(s, _spec(base_sha=head), repo_root=str(tmp_path))
    assert res.state in (SessionState.BLOCKED.value, SessionState.FAILED.value)


def test_no_pass_spec_no_execute_without_approve(tmp_path):
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "README").write_text("x")
    subprocess.run(["git", "add", "README"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    s = create_session("obj", repo_root=str(tmp_path))
    propose(s, allowed_paths=["weaver/"], repo_root=str(tmp_path))
    # execute without approve
    execute(s, _spec(), repo_root=str(tmp_path))
    assert s.state == SessionState.BLOCKED.value


def test_review_bundle_has_fields(tmp_path):
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "README").write_text("x")
    subprocess.run(["git", "add", "README"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    s = create_session("obj", repo_root=str(tmp_path))
    propose(s, allowed_paths=["weaver/"], repo_root=str(tmp_path))
    b = review_bundle(s)
    assert b["objective"] == "obj"
    assert "affected_paths" in b
    assert "AUTHORIZATION" in b["authorization_note"].upper() or "authorization" in b["authorization_note"].lower()


def test_execute_approved_handoff(monkeypatch, tmp_path):
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "README").write_text("x")
    subprocess.run(["git", "add", "README"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    s = create_session("obj", repo_root=str(tmp_path))
    propose(s, allowed_paths=["weaver/"], repo_root=str(tmp_path))
    approve(s, head_sha=head, repo_root=str(tmp_path))

    monkeypatch.setattr(
        "weaver.session.execute_approved_proposal",
        lambda *a, **k: TransactionResult(ok=True, status="NO_CHANGE", stage="complete", message="ok"),
    )
    execute(s, _spec(base_sha=head, allowed_paths=["weaver/"]), repo_root=str(tmp_path))
    assert s.terminal_status in (SessionState.NO_CHANGE.value, SessionState.COMPLETED.value, "NO_CHANGE")


def test_session_has_no_write_api():
    import weaver.session as mod
    assert not hasattr(mod, "write_file")
    assert not hasattr(mod, "commit_and_push")
