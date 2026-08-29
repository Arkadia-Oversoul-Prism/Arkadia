"""Wave 01 domain tests for the Spiral Grove learning nucleus."""
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from spiral_grove.models import (
    Capability,
    CapabilityStatus,
    Evidence,
    EvidenceType,
    Exercise,
    ExerciseEvaluationMode,
    LearningPath,
    LearnerCapabilityState,
    LearnerCapabilityStatus,
)


def test_capability_accepts_valid_domain_record() -> None:
    capability = Capability(
        id="cap-ai-literacy",
        slug="ai-literacy",
        name="AI Literacy",
        description="Understand core AI concepts and use AI critically.",
        domain="digital_intelligence",
        level=2,
        prerequisites=["cap-digital-basics"],
        outcomes=["evaluate-ai-output", "write-bounded-prompts"],
        status=CapabilityStatus.ACTIVE,
    )

    assert capability.slug == "ai-literacy"
    assert capability.level == 2
    assert capability.model_dump()["status"] == "ACTIVE"


def test_capability_rejects_duplicate_prerequisites() -> None:
    with pytest.raises(ValidationError):
        Capability(
            id="cap-1",
            slug="cap-1",
            name="Example",
            description="Example capability.",
            domain="systems",
            level=1,
            prerequisites=["cap-0", "cap-0"],
        )


def test_learning_path_composes_reusable_ids() -> None:
    path = LearningPath(
        id="path-future-builder-01",
        name="Future Builder Foundations",
        audience="young_adults",
        capability_ids=["cap-ai-literacy", "cap-research-systems"],
        resource_ids=["resource-ai-01"],
        exercise_ids=["exercise-source-check"],
        challenge_ids=["challenge-research-sprint"],
        project_template_ids=["project-market-brief"],
        progression_rules={"completion": "evidence_required"},
    )

    assert path.capability_ids == ["cap-ai-literacy", "cap-research-systems"]
    assert path.progression_rules["completion"] == "evidence_required"


def test_learning_path_rejects_duplicate_activity_ids() -> None:
    with pytest.raises(ValidationError):
        LearningPath(
            id="path-1",
            name="Broken Path",
            audience="students",
            exercise_ids=["exercise-1", "exercise-1"],
        )


def test_exercise_is_bounded_and_typed() -> None:
    exercise = Exercise(
        id="exercise-prompt-01",
        capability_id="cap-prompt-engineering",
        prompt="Improve this prompt and explain why.",
        expected_output="A revised prompt plus a short rationale.",
        evaluation_mode=ExerciseEvaluationMode.FACILITATOR,
        timebox_minutes=30,
    )

    assert exercise.capability_id == "cap-prompt-engineering"
    assert exercise.timebox_minutes == 30


def test_exercise_rejects_unbounded_timebox() -> None:
    with pytest.raises(ValidationError):
        Exercise(
            id="exercise-1",
            capability_id="cap-1",
            prompt="Do something.",
            expected_output="Something.",
            timebox_minutes=0,
        )


def test_evidence_requires_traceability_and_consent_scope() -> None:
    evidence = Evidence(
        id="evidence-001",
        learner_id="learner-001",
        capability_id="cap-research-systems",
        evidence_type=EvidenceType.SUBMISSION,
        source_ref="artifact://submission/001",
        provenance="Learner submission from research sprint.",
        created_at=datetime.now(timezone.utc),
        consent_scope="learning_delivery",
        visibility="LEARNER",
    )

    assert evidence.source_ref.startswith("artifact://")
    assert evidence.consent_scope == "learning_delivery"


def test_evidence_rejects_missing_source_reference() -> None:
    with pytest.raises(ValidationError):
        Evidence(
            id="evidence-001",
            learner_id="learner-001",
            capability_id="cap-1",
            evidence_type=EvidenceType.OBSERVATION,
            source_ref="",
            provenance="Facilitator observation.",
            created_at=datetime.now(timezone.utc),
            consent_scope="learning_delivery",
        )


def test_learner_state_is_evidence_scoped() -> None:
    state = LearnerCapabilityState(
        learner_id="learner-001",
        capability_id="cap-research-systems",
        status=LearnerCapabilityStatus.DEMONSTRATED,
        demonstrated_level=3,
        confidence=0.8,
        evidence_refs=["evidence-001"],
        last_assessed_at=datetime.now(timezone.utc),
        next_recommended_action="Practice evidence synthesis.",
    )

    assert state.status == LearnerCapabilityStatus.DEMONSTRATED
    assert state.demonstrated_level == 3
    assert state.evidence_refs == ["evidence-001"]


def test_learner_state_rejects_confidence_outside_range() -> None:
    with pytest.raises(ValidationError):
        LearnerCapabilityState(
            learner_id="learner-001",
            capability_id="cap-1",
            confidence=1.5,
        )


def test_learner_state_rejects_duplicate_evidence_refs() -> None:
    with pytest.raises(ValidationError):
        LearnerCapabilityState(
            learner_id="learner-001",
            capability_id="cap-1",
            evidence_refs=["evidence-1", "evidence-1"],
        )


def test_models_forbid_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        Capability(
            id="cap-1",
            slug="cap-1",
            name="Example",
            description="Example capability.",
            domain="systems",
            level=1,
            unauthorized_authority=True,
        )
