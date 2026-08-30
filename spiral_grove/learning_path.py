"""SG-03 Learning Path Engine nucleus.

This module turns a capability + evidence-scoped learner state into a small,
deterministic learning path. It deliberately does not generate exercises,
score learners, mutate capability state, or replace Knowledge OS.
"""
from __future__ import annotations

from dataclasses import dataclass

from .models import LearningPath, LearnerCapabilityState
from .registry import CapabilityRegistry


class LearningPathEngineError(ValueError):
    """Base error for invalid learning-path planning requests."""


class LearnerCapabilityMismatchError(LearningPathEngineError):
    """Raised when learner state refers to a different capability."""


@dataclass(frozen=True)
class LearningPathPlan:
    """Planning result with an immutable path and explanatory reason."""

    path: LearningPath
    target_capability_id: str
    reason: str


class LearningPathEngine:
    """Deterministic SG-03 planner over the existing Capability Registry."""

    def __init__(self, registry: CapabilityRegistry) -> None:
        self._registry = registry

    def plan(
        self,
        *,
        learner_state: LearnerCapabilityState,
        target_capability_id: str | None = None,
        demonstrated_capability_ids: set[str] | None = None,
    ) -> LearningPathPlan:
        target_id = target_capability_id or learner_state.capability_id
        if learner_state.capability_id != target_id:
            raise LearnerCapabilityMismatchError(
                f"state targets {learner_state.capability_id}, not {target_id}"
            )

        target = self._registry.get(target_id)
        graph = self._registry.graph()
        demonstrated = set(demonstrated_capability_ids or set())
        if learner_state.demonstrated_level is not None:
            demonstrated.add(learner_state.capability_id)

        prerequisites = graph.prerequisites_for(target.id)
        missing = [item for item in prerequisites if item.id not in demonstrated]
        if missing:
            next_capability = missing[0]
            reason = f"Prerequisite first: {next_capability.name}."
            capability_ids = [next_capability.id, target.id]
        else:
            reason = f"Continue developing {target.name}."
            capability_ids = [target.id]

        path = LearningPath(
            id=f"path-{learner_state.learner_id}-{target.id}-v1",
            name=f"{target.name} progression",
            audience="learner",
            capability_ids=capability_ids,
            progression_rules={
                "entry": "learner_capability_state",
                "completion": "evidence_required",
                "next_step": "registry_prerequisite_or_target",
            },
            version=1,
        )
        return LearningPathPlan(path=path, target_capability_id=target.id, reason=reason)

    def next_capability(
        self,
        learner_state: LearnerCapabilityState,
        *,
        demonstrated_capability_ids: set[str] | None = None,
    ) -> str:
        """Return the next registry capability required by the learner state."""
        plan = self.plan(
            learner_state=learner_state,
            demonstrated_capability_ids=demonstrated_capability_ids,
        )
        return plan.path.capability_ids[0]
