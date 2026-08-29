"""Canonical typed models for the Spiral Grove Wave 01 learning nucleus.

These models are domain contracts only. They do not grant authorization, execute
providers/tools, or create a parallel Knowledge OS authority.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GroveModel(BaseModel):
    """Shared strict-ish configuration for Grove domain objects."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class CapabilityStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


class Difficulty(str, Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class ResourceType(str, Enum):
    ARTICLE = "ARTICLE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    LESSON = "LESSON"
    DATASET = "DATASET"
    DOCUMENT = "DOCUMENT"
    EXTERNAL = "EXTERNAL"


class ExerciseEvaluationMode(str, Enum):
    SELF = "SELF"
    FACILITATOR = "FACILITATOR"
    RUBRIC = "RUBRIC"
    AUTOMATED_ASSIST = "AUTOMATED_ASSIST"


class EvidenceType(str, Enum):
    ARTIFACT = "ARTIFACT"
    SUBMISSION = "SUBMISSION"
    OBSERVATION = "OBSERVATION"
    ASSESSMENT = "ASSESSMENT"
    REFLECTION = "REFLECTION"


class LearnerCapabilityStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    EXPLORING = "EXPLORING"
    PRACTICING = "PRACTICING"
    DEMONSTRATED = "DEMONSTRATED"
    MASTERED = "MASTERED"


class Capability(GroveModel):
    """A reusable unit of human capability development."""

    id: str = Field(min_length=1, max_length=128)
    slug: str = Field(min_length=1, max_length=128, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=4000)
    domain: str = Field(min_length=1, max_length=100)
    level: int = Field(ge=1, le=12)
    prerequisites: list[str] = Field(default_factory=list, max_length=50)
    outcomes: list[str] = Field(default_factory=list, max_length=50)
    status: CapabilityStatus = CapabilityStatus.DRAFT
    version: int = Field(default=1, ge=1)

    @field_validator("prerequisites", "outcomes")
    @classmethod
    def unique_non_empty(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("list values must not be empty")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("list values must be unique")
        return cleaned


class LearningResource(GroveModel):
    """Learning material referenced by a path or exercise."""

    id: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=300)
    resource_type: ResourceType
    source_ref: str = Field(min_length=1, max_length=500)
    capability_ids: list[str] = Field(default_factory=list, max_length=50)
    difficulty: Difficulty = Difficulty.BEGINNER
    estimated_minutes: int = Field(ge=1, le=10080)
    provenance: str = Field(min_length=1, max_length=2000)
    status: Literal["DRAFT", "ACTIVE", "RETIRED"] = "DRAFT"


class Exercise(GroveModel):
    """A bounded practice activity for one capability."""

    id: str = Field(min_length=1, max_length=128)
    capability_id: str = Field(min_length=1, max_length=128)
    prompt: str = Field(min_length=1, max_length=8000)
    expected_output: str = Field(min_length=1, max_length=4000)
    evaluation_mode: ExerciseEvaluationMode = ExerciseEvaluationMode.FACILITATOR
    difficulty: Difficulty = Difficulty.BEGINNER
    timebox_minutes: int = Field(ge=1, le=1440)


class LearningPath(GroveModel):
    """A versioned sequence composing reusable learning primitives."""

    id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=300)
    audience: str = Field(min_length=1, max_length=200)
    capability_ids: list[str] = Field(default_factory=list, max_length=100)
    resource_ids: list[str] = Field(default_factory=list, max_length=200)
    exercise_ids: list[str] = Field(default_factory=list, max_length=200)
    challenge_ids: list[str] = Field(default_factory=list, max_length=200)
    project_template_ids: list[str] = Field(default_factory=list, max_length=100)
    progression_rules: dict[str, str] = Field(default_factory=dict)
    version: int = Field(default=1, ge=1)

    @field_validator(
        "capability_ids",
        "resource_ids",
        "exercise_ids",
        "challenge_ids",
        "project_template_ids",
    )
    @classmethod
    def unique_ids(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("IDs must not be empty")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("IDs must be unique within a path")
        return cleaned


class Evidence(GroveModel):
    """Traceable learner evidence; source-backed and explicitly scoped."""

    id: str = Field(min_length=1, max_length=128)
    learner_id: str = Field(min_length=1, max_length=128)
    capability_id: str = Field(min_length=1, max_length=128)
    evidence_type: EvidenceType
    source_ref: str = Field(min_length=1, max_length=500)
    provenance: str = Field(min_length=1, max_length=2000)
    created_at: datetime
    consent_scope: str = Field(min_length=1, max_length=200)
    visibility: Literal["PRIVATE", "LEARNER", "COHORT", "FACILITATOR"] = "LEARNER"


class LearnerCapabilityState(GroveModel):
    """Progress state for a learner against one capability.

    ``demonstrated_level`` is evidence-scoped. It is not a judgment of the
    learner's intrinsic intelligence, worth, or overall ability.
    """

    learner_id: str = Field(min_length=1, max_length=128)
    capability_id: str = Field(min_length=1, max_length=128)
    status: LearnerCapabilityStatus = LearnerCapabilityStatus.NOT_STARTED
    demonstrated_level: int | None = Field(default=None, ge=1, le=12)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list, max_length=200)
    last_assessed_at: datetime | None = None
    next_recommended_action: str | None = Field(default=None, max_length=1000)

    @field_validator("evidence_refs")
    @classmethod
    def unique_evidence_refs(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("evidence references must not be empty")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("evidence references must be unique")
        return cleaned

    @field_validator("demonstrated_level")
    @classmethod
    def level_requires_evidence(cls, value: int | None) -> int | None:
        return value
