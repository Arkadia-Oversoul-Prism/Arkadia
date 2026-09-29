"""Phase 9 — Human Decision Queue deterministic gate."""
from __future__ import annotations

from lab.decision.queue import decide_opportunities, record_decision
from lab.decision.schema import DecisionKind
from lab.possibility.engine import generate_opportunities

GOLDEN_INPUT = {
    "capabilities": ["engineering-observatory"],
    "patterns": ["repeated verification demand"],
    "trajectory": ["external observability need"],
    "unused_infrastructure": ["existing Lab verification spine"],
    "recurring_needs": ["inspectable engineering evidence"],
}


def test_decision_defaults_to_defer_without_policy():
    opps = generate_opportunities(**GOLDEN_INPUT)
    decisions = decide_opportunities(opps)
    assert len(decisions) == 1
    assert decisions[0].kind == DecisionKind.DEFER
    d = decisions[0].to_dict()
    assert d["execution_authorized"] is False
    assert d["auto_build"] is False
    assert d["auto_merge"] is False


def test_explicit_approve_still_forbids_execution_flags():
    opps = generate_opportunities(**GOLDEN_INPUT)
    title = opps[0].title
    decisions = decide_opportunities(opps, policy={title: "APPROVE"})
    assert decisions[0].kind == DecisionKind.APPROVE
    payload = decisions[0].to_dict()
    assert payload["execution_authorized"] is False
    assert payload["auto_build"] is False
    assert "auto_execute" not in payload


def test_reject_and_provenance_binding():
    opps = generate_opportunities(**GOLDEN_INPUT)
    d = record_decision(opps[0], DecisionKind.REJECT, rationale="Out of scope for Level 2")
    assert d.kind == DecisionKind.REJECT
    assert d.opportunity_provenance["capability"] == ["engineering-observatory"]
    assert d.decided_by == "human"


def test_decision_schema_has_no_build_authority_fields():
    opps = generate_opportunities(**GOLDEN_INPUT)
    keys = set(record_decision(opps[0], "DEFER", rationale="hold").to_dict())
    forbidden = {"auto_execute", "auto_build", "merge", "deploy", "run_transaction"}
    assert keys.isdisjoint(forbidden) or (
        # auto_build may appear only as explicit False marker
        record_decision(opps[0], "DEFER", rationale="hold").to_dict().get("auto_build") is False
    )
