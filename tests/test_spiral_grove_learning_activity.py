from spiral_grove.learning_activity import LearningActivity, project_learning_activity


def test_path_projects_explicit_activity_slot() -> None:
    projection = project_learning_activity("path-demo", "cap-demo")
    assert projection.path_id == "path-demo"
    assert projection.capability_id == "cap-demo"
    assert len(projection.activities) == 1
    assert isinstance(projection.activities[0], LearningActivity)
    assert projection.activities[0].capability_id == "cap-demo"


def test_activity_does_not_adjudicate_evidence() -> None:
    activity = project_learning_activity("path-demo", "cap-demo").activities[0]
    assert activity.evidence_required is True
    assert not hasattr(activity, "evidence_refs")
    assert not hasattr(activity, "assessment_result")


def test_activity_contract_is_not_an_autonomous_generator() -> None:
    projection = project_learning_activity("path-demo", "cap-demo")
    assert projection.activities[0].kind == "orientation"
    assert "generate" not in projection.activities[0].instruction.lower()
