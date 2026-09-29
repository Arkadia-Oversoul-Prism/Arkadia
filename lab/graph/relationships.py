from __future__ import annotations

from typing import Iterable
from ..model import Relationship, observed_now


def relates(source_id: str, relationship: str, target_id: str, *, source: str = "derived", confidence: float = 1.0, evidence: Iterable[str] = (), provenance: dict | None = None, method: str | None = None) -> Relationship:
    evidence_list=sorted(set(str(x) for x in evidence))
    rid=f"rel:{source_id}:{relationship}:{target_id}"
    return Relationship(id=rid,source_id=source_id,relationship=relationship,target_id=target_id,source=source,confidence=confidence,observed_at=observed_now(),provenance=provenance or {},evidence=evidence_list,method=method)
