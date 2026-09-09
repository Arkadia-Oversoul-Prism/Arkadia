from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class LabEntity(BaseModel):
    id: str
    type: str
    source: str
    confidence: float
    observed_at: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class Observation(LabEntity):
    value: Any = None
    provenance: dict[str, Any] = Field(default_factory=dict)
    collector_version: str = "lab-0.1"
    status: str = "observed"
    reason: str | None = None


class Relationship(BaseModel):
    id: str
    source_id: str
    relationship: str
    target_id: str
    source: str
    confidence: float
    observed_at: str
    provenance: dict[str, Any] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)
    method: str | None = None


class Pattern(LabEntity):
    pattern_id: str
    severity: str
    evidence: list[str] = Field(default_factory=list)
    affected_entities: list[str] = Field(default_factory=list)
    first_detected: str | None = None
    last_detected: str | None = None


def observed_now() -> str:
    return datetime.now(timezone.utc).isoformat()
