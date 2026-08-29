"""WEAVER-K5 — proposal engine proofs."""
from __future__ import annotations

import pytest

from weaver.pass_spec import PassSpec
from weaver.proposal import (
    Proposal,
    ProposalError,
    ProposalStatus,
    approve_proposal,
    build_deterministic_proposal,
    candidate_pass_spec_from_proposal,
    execute_approved_proposal,
    normalize_paths,
    normalize_proposal,
    proposal_cannot_expand_spec,
    reject_proposal,
    validate_proposal_against_spec,
)
import weaver.proposal as proposal_mod


def _spec(**kw) -> PassSpec:
    base = dict(
        pass_id="WEAVER-K5-TEST",
        objective="proposal test",
        base_sha="abc1234",
        allowed_paths=["weaver/", "tests/test_weaver_k5.py"],
        forbidden_paths=["api/", ".git/"],
        required_tests=[],
        commit_required=False,
        push_allowed=False,
        publication_required=False,
    )
    base.update(kw)
    return PassSpec(**base)


def test_schema_accepts_valid():
    p = build_deterministic_proposal("do x", anchor="deadbeef", allowed_paths=["weaver/"])
    assert p.proposal_id.startswith("prop-")
    assert p.authorization_status == ProposalStatus.PROPOSED.value


def test_malformed_rejected():
    with pytest.raises(ProposalError):
        normalize_proposal({}, anchor="", objective="")


def test_scope_allow_and_forbid():
    s = _spec()
    ok = build_deterministic_proposal("x", anchor="a", allowed_paths=["weaver/agent.py"])
    validate_proposal_against_spec(ok, s)
    bad = build_deterministic_proposal("x", anchor="a", allowed_paths=["api/main.py"])
    with pytest.raises(ProposalError, match="out of scope|forbidden"):
        validate_proposal_against_spec(bad, s)


def test_cannot_expand_spec():
    s = _spec(allowed_paths=["weaver/pass_spec.py"])
    p = build_deterministic_proposal("x", anchor="a", allowed_paths=["weaver/pass_spec.py"])
    assert proposal_cannot_expand_spec(p, s) is s or proposal_cannot_expand_spec(p, s).allowed_paths == s.allowed_paths


def test_proposed_not_approved():
    p = build_deterministic_proposal("x", anchor="a")
    assert p.authorization_status == ProposalStatus.PROPOSED.value
    assert p.authorization_status != ProposalStatus.APPROVED.value


def test_rejected_cannot_execute(monkeypatch):
    s = _spec()
    p = reject_proposal(build_deterministic_proposal("x", anchor="a", allowed_paths=["weaver/"]))
    with pytest.raises(ProposalError, match="unapproved|rejected"):
        execute_approved_proposal(p, s)


def test_unapproved_cannot_execute():
    s = _spec()
    p = build_deterministic_proposal("x", anchor="a", allowed_paths=["weaver/"])
    with pytest.raises(ProposalError):
        execute_approved_proposal(p, s)


def test_path_normalization_deterministic():
    a = normalize_paths(["./weaver/a.py", "weaver/a.py", "weaver//b.py"])
    b = normalize_paths(["weaver/b.py", "weaver/a.py"])
    assert a == b == ["weaver/a.py", "weaver/b.py"]


def test_candidate_pass_spec_not_self_auth():
    s = _spec()
    p = build_deterministic_proposal("x", anchor="abc", allowed_paths=["weaver/"])
    cand = candidate_pass_spec_from_proposal(p, s)
    assert cand.human_approval_required is True
    assert cand.allowed_paths  # subset
    # candidate is not executed by creation
    assert p.authorization_status == ProposalStatus.PROPOSED.value


def test_approve_then_handoff(monkeypatch):
    s = _spec(base_sha="0" * 40)
    p = approve_proposal(build_deterministic_proposal("x", anchor="0" * 40, allowed_paths=["weaver/"]))
    assert p.authorization_status == ProposalStatus.APPROVED.value

    from weaver.session_kernel import SessionResult
    from weaver.transaction import TransactionResult

    monkeypatch.setattr(
        "weaver.transaction.run_transaction",
        lambda *a, **k: TransactionResult(ok=True, status="NO_CHANGE", stage="complete", message="ok"),
    )
    # execute_approved_proposal imports run_transaction inside function
    monkeypatch.setattr(
        "weaver.proposal.run_transaction",
        lambda *a, **k: TransactionResult(ok=True, status="NO_CHANGE", stage="complete", message="ok"),
        raising=False,
    )
    # patch where used
    import weaver.transaction as tx

    monkeypatch.setattr(
        tx,
        "run_transaction",
        lambda *a, **k: TransactionResult(ok=True, status="NO_CHANGE", stage="complete", message="ok"),
    )
    res = execute_approved_proposal(p, s)
    assert res.ok


def test_provider_module_untouched_by_proposal():
    assert not hasattr(proposal_mod, "write_file")
    assert not hasattr(proposal_mod, "commit_and_push")
