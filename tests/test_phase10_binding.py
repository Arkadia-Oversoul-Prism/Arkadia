"""Phase 10 — Governed binding deterministic gate."""
from __future__ import annotations

from lab.binding.binder import bind_approved_decision
from lab.decision.queue import decide_opportunities, record_decision
from lab.decision.schema import DecisionKind
from lab.possibility.engine import generate_opportunities

GOLDEN = {
    "capabilities": ["engineering-observatory"],
    "patterns": ["repeated verification demand"],
    "trajectory": ["external observability need"],
    "unused_infrastructure": ["existing Lab verification spine"],
    "recurring_needs": ["inspectable engineering evidence"],
}


def test_approve_binds_to_dry_run_without_merge():
    opps = generate_opportunities(**GOLDEN)
    title = opps[0].title
    decisions = decide_opportunities(opps, policy={title: "APPROVE"})
    br = bind_approved_decision(decisions[0], mode="dry_run")
    assert br.bound is True
    payload = br.to_dict()
    assert payload["merge"] is False
    assert payload["deploy"] is False
    assert payload["auto_execute"] is False
    assert payload["execution"]["merge"] is False
    assert payload["execution"]["mode"] == "dry_run"


def test_reject_and_defer_do_not_bind():
    opps = generate_opportunities(**GOLDEN)
    reject = record_decision(opps[0], DecisionKind.REJECT, rationale="no")
    defer = record_decision(opps[0], DecisionKind.DEFER, rationale="later")
    assert bind_approved_decision(reject).bound is False
    assert bind_approved_decision(defer).bound is False


def test_smuggled_execution_authorized_true_is_refused():
    opps = generate_opportunities(**GOLDEN)
    d = record_decision(opps[0], "APPROVE", rationale="yes").to_dict()
    d["execution_authorized"] = True
    br = bind_approved_decision(d)
    assert br.bound is False
    assert "execution_authorized" in br.reason


def test_end_to_end_possibility_to_dry_run():
    opps = generate_opportunities(**GOLDEN)
    decisions = decide_opportunities(opps, policy={opps[0].title: "APPROVE"})
    br = bind_approved_decision(decisions[0])
    assert br.bound is True
    assert any(e.get("event") == "dry_run.completed" for e in br.events)
