"""Auditable human decision records. No execution authority."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class DecisionKind(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    DEFER = "DEFER"


@dataclass(frozen=True)
class Decision:
    """A human decision bound to a Phase 8 opportunity.

    FORBIDDEN fields: auto_execute, auto_build, merge, deploy.
    """

    opportunity_title: str
    kind: DecisionKind
    rationale: str
    decided_by: str = "human"
    opportunity_provenance: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["kind"] = self.kind.value
        # Explicit non-authority markers
        d["execution_authorized"] = False
        d["auto_build"] = False
        d["auto_merge"] = False
        return d
