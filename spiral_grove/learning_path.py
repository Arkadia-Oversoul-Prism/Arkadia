"""SG-03 Learning Path Engine nucleus.

This module turns a capability + evidence-scoped learner state into a small,
deterministic learning path. It deliberately does not generate exercises,
score learners, mutate capability state, or replace Knowledge OS.
"""
from __future__ import annotations

from dataclasses import dataclass

from .models import LearningPath, LearnerCapabilityState, LearnerCapabilityStatus
from .registry import CapabilityRegistry, UnknownCapabilityError


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
    ) -> LearningPathPlan:
        target_id = target_capability_id or learner_state.capability_id
        if learner_state.capability_id != target_id:
            raise LearnerCapabilityMismatchError(
                f"state targets {learner_state.capability_id}, not {target_id}"
            )

        target = self._registry.get(target_id)
        graph = self._registry.graph()
        demonstrated = set(learner_state.evidence_refs) if learner_state.status in {
            LearnerCapabilityStatus.DEMONSTRATED,
            LearnerCapabilityStatus.MASTERED,
        } else set()

        prerequisites = graph.prerequisites_for(target.id)
        prerequisite_ids = [item.id for item in prerequisites]

        missing = [item for item in prerequisite_ids if item not in demonstrated]
        if missing:
            next_capability_id = missing[0]
            next_capability = self._registry.get(next_capability_id)
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

    def next_capability(self, learner_state: LearnerCapabilityState) -> str:
        """Return the next registry capability required by the learner state."""
        plan = self.plan(learner_state=learner_state)
        return plan.path.capability_ids[0]
