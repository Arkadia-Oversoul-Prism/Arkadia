"""WEAVER-K7 — workbench composition proofs."""
from __future__ import annotations

import subprocess

from weaver.pass_spec import PassSpec
from weaver.workbench import Workbench
from weaver.session import SessionState
from weaver.transaction import TransactionResult


def _git_repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "README").write_text("x")
    subprocess.run(["git", "add", "README"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()


def _spec(head, **kw) -> PassSpec:
    base = dict(
        pass_id="WEAVER-K7-TEST",
        objective="wb",
        base_sha=head,
        allowed_paths=["weaver/"],
        forbidden_paths=["api/"],
        commit_required=False,
        push_allowed=False,
        publication_required=False,
    )
    base.update(kw)
    return PassSpec(**base)


def test_start_recon_propose_stops_at_approval(tmp_path):
    _git_repo(tmp_path)
    wb = Workbench(str(tmp_path))
    assert wb.start("fix docs").ok
    assert wb.recon().ok
    r = wb.propose(allowed_paths=["weaver/"])
    assert r.state == SessionState.AWAITING_APPROVAL.value
    assert r.review.get("next_action") == "awaiting human approval"


def test_cannot_execute_before_approval(tmp_path):
    head = _git_repo(tmp_path)
    wb = Workbench(str(tmp_path))
    wb.start("x")
    wb.propose(allowed_paths=["weaver/"])
    r = wb.execute(_spec(head))
    assert r.state == SessionState.BLOCKED.value


def test_workbench_no_write_api():
    import weaver.workbench as m
    assert not hasattr(m, "write_file")
    assert not hasattr(m.Workbench, "write_file")
    assert not hasattr(m, "commit_and_push")


def test_approve_execute_handoff(monkeypatch, tmp_path):
    head = _git_repo(tmp_path)
    wb = Workbench(str(tmp_path))
    wb.start("x")
    wb.propose(allowed_paths=["weaver/"])
    ar = wb.approve()
    assert ar.state == SessionState.APPROVED.value
    monkeypatch.setattr(
        "weaver.session.execute_approved_proposal",
        lambda *a, **k: TransactionResult(ok=True, status="NO_CHANGE", stage="complete", message="ok"),
    )
    r = wb.execute(_spec(head))
    assert r.session.get("terminal_status") in (
        SessionState.NO_CHANGE.value,
        SessionState.COMPLETED.value,
        "NO_CHANGE",
    )


def test_reject(tmp_path):
    _git_repo(tmp_path)
    wb = Workbench(str(tmp_path))
    wb.start("x")
    wb.propose(allowed_paths=["weaver/"])
    r = wb.reject()
    assert r.state == SessionState.REJECTED.value


def test_review_bundle_fields(tmp_path):
    _git_repo(tmp_path)
    wb = Workbench(str(tmp_path))
    wb.start("objective text")
    wb.propose(allowed_paths=["weaver/"])
    b = wb.review_bundle()
    for key in ("session_id", "objective", "affected_paths", "authorization_state", "publication_policy"):
        assert key in b
    assert "AUTHORIZATION" in b.get("context_note", "").upper() or "authorization" in b.get("authorization_state", "").lower()


def test_pass_spec_required_type(tmp_path):
    _git_repo(tmp_path)
    wb = Workbench(str(tmp_path))
    wb.start("x")
    wb.propose(allowed_paths=["weaver/"])
    wb.approve()
    r = wb.execute("not-a-spec")  # type: ignore
    assert r.state == "BLOCKED"
