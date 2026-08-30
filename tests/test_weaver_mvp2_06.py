"""MVP2-06 — proposal-only orchestration invariants."""
from weaver.orchestration import build_proposal


def test_orchestration_is_proposal_only():
    result = build_proposal(
        "Clarify the module documentation",
        plan={"id": "p1"},
        changeset={"id": "c1"},
        patch={"id": "x1"},
    )
    assert result["status"] == "PROPOSAL_ONLY"
    assert result["autonomy"]["enabled"] is False
    assert result["autonomy"]["status"] == "DISABLED_PROPOSAL_ONLY"
    assert result["execution"]["performed"] is False
    assert result["mutation"]["performed"] is False
    assert result["mutation"]["commit"] is False
    assert result["mutation"]["push"] is False
    assert result["operator_action_required"] is True


def test_no_authorization_model_is_invented():
    result = build_proposal("Review a change")
    assert result["autonomy"]["authorization_model"] == "UNDEFINED"
    assert "independently defined authorization model" in result["autonomy"]["reason"]


def test_missing_artifacts_are_not_fabricated():
    result = build_proposal("Investigate")
    assert result["steps"] == []
