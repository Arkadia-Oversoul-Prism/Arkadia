"""Phase 7 — deterministic calibration gate; proposals only, no side effects."""

from lab.calibration import build_repair_proposal, classify
from lab.evolution.schema import validate_proposal_dict


def test_simulated_regression_proposes_repair_without_application():
    expected_state = {"routes": 3, "tests": 8, "patterns": 0}
    actual_state = {"routes": 3, "tests": 7, "patterns": 1}

    result = classify(expected_state, actual_state)
    assert result.status == "REGRESSION"
    assert result.mismatches == ("patterns", "tests")

    proposal = build_repair_proposal(
        expected_state,
        actual_state,
        calibration_status=result.status,
        proposal_id="EV-CAL-REGRESSION-001",
    )
    assert validate_proposal_dict(proposal) == []
    assert proposal["approval_required"] is True
    assert proposal["execution"] is False
    assert proposal["auto_apply"] is False

    # Gate invariant: calibration creates data only; it does not create a branch,
    # PR, merge, deployment, or mutation of the supplied states.
    assert expected_state == {"routes": 3, "tests": 8, "patterns": 0}
    assert actual_state == {"routes": 3, "tests": 7, "patterns": 1}


def test_success_closes_loop_without_repair():
    state = {"routes": 3, "tests": 8, "patterns": 0}
    result = classify(state, state)
    assert result.status == "SUCCESS"
    assert result.mismatches == ()
