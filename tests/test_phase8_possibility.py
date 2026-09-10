from lab.possibility.engine import generate_opportunities
from lab.possibility.schema import Opportunity


GOLDEN_INPUT = {
    "capabilities": ["engineering-observatory"],
    "patterns": ["repeated verification demand"],
    "trajectory": ["external observability need"],
    "unused_infrastructure": ["existing Lab verification spine"],
    "recurring_needs": ["inspectable engineering evidence"],
}


def test_golden_opportunity_is_deterministic_and_provenanced():
    first = generate_opportunities(**GOLDEN_INPUT)
    second = generate_opportunities(**GOLDEN_INPUT)

    assert first == second
    assert len(first) == 1
    opportunity = first[0]
    assert isinstance(opportunity, Opportunity)
    assert opportunity.title == "Extend engineering-observatory into a governed opportunity path"
    assert opportunity.provenance["capability"] == ["engineering-observatory"]
    assert opportunity.provenance["pattern"] == ["repeated verification demand"]
    assert opportunity.provenance["trajectory"] == ["external observability need"]


def test_opportunity_schema_contains_no_auto_build_field():
    record = generate_opportunities(**GOLDEN_INPUT)[0].to_dict()
    assert set(record) == {
        "title",
        "provenance",
        "value",
        "evidence",
        "cost",
        "risk",
        "alignment",
    }
    assert "auto_build" not in record
    assert "execute" not in record
    assert "deploy" not in record


def test_engine_only_proposes_and_does_not_apply():
    result = generate_opportunities(**GOLDEN_INPUT)
    assert result
    assert all(isinstance(item, Opportunity) for item in result)


def test_missing_evidence_produces_no_opportunity():
    assert generate_opportunities(
        capabilities=["engineering-observatory"],
        patterns=[],
        trajectory=["external observability need"],
        unused_infrastructure=[],
        recurring_needs=[],
    ) == []
