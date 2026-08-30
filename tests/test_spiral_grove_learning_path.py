"""SG-03 Learning Path Engine nucleus contracts."""

import pytest

from spiral_grove.learning_path import (
    LearnerCapabilityMismatchError,
    LearningPathEngine,
)
from spiral_grove.models import LearnerCapabilityState
from spiral_grove.registry import build_ais_capability_catalog


def test_path_plans_from_learner_state_and_registry() -> None:
    registry = build_ais_capability_catalog()
    engine = LearningPathEngine(registry)
    state = LearnerCapabilityState(
        learner_id="learner-001",
        capability_id="cap-no-code-development",
    )

    plan = engine.plan(learner_state=state)

    assert plan.target_capability_id == "cap-no-code-development"
    assert plan.path.capability_ids == [
        "cap-digital-intelligence",
        "cap-no-code-development",
    ]
    assert plan.path.progression_rules["completion"] == "evidence_required"


def test_path_respects_demonstrated_prerequisite_capabilities() -> None:
    engine = LearningPathEngine(build_ais_capability_catalog())
    state = LearnerCapabilityState(
        learner_id="learner-001",
        capability_id="cap-no-code-development",
    )

    plan = engine.plan(
        learner_state=state,
        demonstrated_capability_ids={
            "cap-digital-intelligence",
            "cap-digital-operations",
        },
    )

    assert plan.path.capability_ids == ["cap-no-code-development"]


def test_demonstrated_target_state_does_not_create_a_new_prerequisite_loop() -> None:
    engine = LearningPathEngine(build_ais_capability_catalog())
    state = LearnerCapabilityState(
        learner_id="learner-001",
        capability_id="cap-digital-intelligence",
        demonstrated_level=1,
    )

    plan = engine.plan(learner_state=state)

    assert plan.path.capability_ids == ["cap-digital-intelligence"]


def test_target_must_match_learner_state() -> None:
    engine = LearningPathEngine(build_ais_capability_catalog())
    state = LearnerCapabilityState(
        learner_id="learner-001",
        capability_id="cap-digital-intelligence",
    )

    with pytest.raises(LearnerCapabilityMismatchError):
        engine.plan(
            learner_state=state,
            target_capability_id="cap-research-systems",
        )


def test_next_capability_is_deterministic() -> None:
    engine = LearningPathEngine(build_ais_capability_catalog())
    state = LearnerCapabilityState(
        learner_id="learner-001",
        capability_id="cap-no-code-development",
    )

    assert engine.next_capability(state) == "cap-digital-intelligence"
    assert engine.next_capability(state) == "cap-digital-intelligence"


def test_engine_does_not_generate_exercises_or_evidence() -> None:
    engine = LearningPathEngine(build_ais_capability_catalog())
    state = LearnerCapabilityState(
        learner_id="learner-001",
        capability_id="cap-ai-prompt-engineering",
    )

    path = engine.plan(learner_state=state).path

    assert path.exercise_ids == []
    assert path.challenge_ids == []
    assert path.project_template_ids == []
