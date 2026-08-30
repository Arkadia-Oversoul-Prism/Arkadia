"""Small SG-03 contract for activities consumed by the Grove.

Activities describe learner work. They are not generated here, and this module
contains no evidence adjudication or learner-state mutation.
"""

from dataclasses import dataclass
from typing import Literal

ActivityKind = Literal["orientation", "practice", "reflection", "project"]
ActivityStatus = Literal["available", "completed"]


@dataclass(frozen=True)
class LearningActivity:
    id: str
    path_id: str
    capability_id: str
    title: str
    instruction: str
    kind: ActivityKind
    status: ActivityStatus = "available"
    evidence_required: bool = True


@dataclass(frozen=True)
class LearningPathActivityProjection:
    path_id: str
    capability_id: str
    activities: tuple[LearningActivity, ...]


def project_learning_activity(path_id: str, capability_id: str) -> LearningPathActivityProjection:
    """Return a deterministic activity slot for an existing path.

    This is an explicit contract seam, not an autonomous activity generator.
    """
    activity = LearningActivity(
        id=f"activity-{path_id}-{capability_id}-01",
        path_id=path_id,
        capability_id=capability_id,
        title="Capability orientation",
        instruction="Review the capability context and identify one concrete application.",
        kind="orientation",
    )
    return LearningPathActivityProjection(path_id, capability_id, (activity,))
