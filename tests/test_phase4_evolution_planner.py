"""Phase 4 — Evolution Planner golden fixtures (no execution)."""
from lab.evolution import plan_from_patterns, validate_proposal


GOLDEN_PATTERNS = [
    {
        "pattern_id": "pattern:parallel-execution-paths",
        "kind": "parallel_execution",
        "confidence": 0.72,
        "components": ["weaver/", "solspire/", "kernel/"],
        "evidence": ["weaver/execute.py", "solspire/project_execution.py"],
    }
]


def test_golden_proposal_schema_valid():
    prop = plan_from_patterns(GOLDEN_PATTERNS, proposal_id="EV-GOLDEN-001")
    assert prop.schema_errors == ()
    assert prop.data["approval_required"] is True
    assert prop.data["proposal_id"].startswith("EV-")
    assert "pattern:parallel-execution-paths" in prop.data["problem"]["evidence"]
    assert prop.council_consensus == "PASS"
    assert prop.valid is True
    d = prop.to_dict()
    assert d["phase4_execution"] is False


def test_schema_rejects_missing_approval_required():
    bad = plan_from_patterns(GOLDEN_PATTERNS).data.copy()
    bad["approval_required"] = False
    errs = validate_proposal(bad)
    assert any("approval_required" in e for e in errs)


def test_schema_rejects_execution_flag():
    bad = plan_from_patterns(GOLDEN_PATTERNS).data.copy()
    bad["execution"] = True
    errs = validate_proposal(bad)
    assert any("execution" in e for e in errs)


def test_empty_patterns_still_schema_valid():
    prop = plan_from_patterns([], proposal_id="EV-EMPTY-001")
    assert prop.schema_errors == ()
    assert prop.data["approval_required"] is True


def test_no_side_effects_planner_pure():
    """Planner must not mutate global state / files — pure function check via double call."""
    a = plan_from_patterns(GOLDEN_PATTERNS, proposal_id="EV-PURE-001")
    b = plan_from_patterns(GOLDEN_PATTERNS, proposal_id="EV-PURE-001")
    assert a.data == b.data
