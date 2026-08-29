"""WEAVER-K3 — plan contract and transaction governance."""
from __future__ import annotations

from weaver.pass_spec import PassSpec
from weaver.plan import (
    Plan,
    PlanError,
    approve_plan,
    build_plan_from_spec,
    plan_cannot_expand_spec,
    validate_plan_against_spec,
)
from weaver.transaction import run_transaction
from weaver.provider import invoke_provider, ProviderRequest
import weaver.provider as prov


def _spec(**kw) -> PassSpec:
    base = dict(
        pass_id="WEAVER-K3-TEST",
        objective="test transaction",
        base_sha="abc1234",
        allowed_paths=["weaver/", "tests/test_weaver_k3.py", "data/weaver/"],
        forbidden_paths=["api/", ".git/"],
        required_tests=[],
        commit_required=False,
        push_allowed=False,
        publication_required=False,
    )
    base.update(kw)
    return PassSpec(**base)


def test_build_plan_from_spec():
    s = _spec()
    p = build_plan_from_spec(s, rationale="unit")
    assert p.pass_id == s.pass_id
    assert p.objective == s.objective
    assert p.approved is False


def test_plan_out_of_scope_rejected():
    s = _spec(allowed_paths=["weaver/"])
    p = Plan(pass_id=s.pass_id, objective="x", proposed_files=["api/main.py"])
    try:
        validate_plan_against_spec(p, s)
        assert False, "expected PlanError"
    except PlanError as e:
        assert "PLAN_OUT_OF_SCOPE" in str(e)


def test_plan_cannot_expand_spec():
    s = _spec(allowed_paths=["weaver/pass_spec.py"])
    p = build_plan_from_spec(s)
    out = plan_cannot_expand_spec(p, s)
    assert out.allowed_paths == s.allowed_paths
    assert out is s or out.allowed_paths == ["weaver/pass_spec.py"]


def test_unapproved_external_plan_blocked(monkeypatch):
    s = _spec(base_sha="0" * 40)
    p = Plan(pass_id=s.pass_id, objective="x", proposed_files=["weaver/"], approved=False)
    monkeypatch.setattr("weaver.transaction.preflight", lambda *a, **k: "0" * 40)
    res = run_transaction(s, plan=p, require_plan_approval=True, auto_approve_if_spec_is_authorization=False)
    assert res.status == "BLOCKED"
    assert res.stage == "plan_approval"


def test_derived_plan_auto_approves_when_spec_is_auth(monkeypatch):
    s = _spec(base_sha="0" * 40)
    monkeypatch.setattr("weaver.transaction.preflight", lambda *a, **k: "0" * 40)

    from weaver.session_kernel import SessionResult

    monkeypatch.setattr(
        "weaver.transaction.run_authorized",
        lambda *a, **k: SessionResult(
            ok=True,
            pass_id=s.pass_id,
            stage="complete",
            status="NO_CHANGE",
            message="noop",
        ),
    )
    res = run_transaction(s, require_plan_approval=True, auto_approve_if_spec_is_authorization=True)
    assert res.ok
    assert res.plan.get("approved") is True


def test_provider_still_cannot_write():
    for name in ("write_file", "commit_and_push", "push_current"):
        assert not hasattr(prov, name)


def test_approve_plan_sets_flag():
    p = Plan(pass_id="p", objective="o", proposed_files=["weaver/"])
    assert approve_plan(p).approved is True
