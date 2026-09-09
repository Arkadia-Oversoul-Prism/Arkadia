from __future__ import annotations

from typing import Any
from ..model import LabEntity, Relationship, observed_now

ENTITY_TYPES = ["System","Project","Canon","Principle","Vision","Goal","Feature","Architecture","Component","Module","Route","API","Database","Repository","Branch","Commit","PR","Deployment","Runtime","Decision","Task","Experiment","Failure","Pattern","Observation","Checkpoint","Proposal","Approval","Opportunity","Provider","Model","Capability"]


def entity(entity_type: str, entity_id: str, source: str, confidence: float = 1.0, **metadata: Any) -> LabEntity:
    return LabEntity(id=entity_id,type=entity_type,source=source,confidence=confidence,observed_at=observed_now(),metadata=metadata)
