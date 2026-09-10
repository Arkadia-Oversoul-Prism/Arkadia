"""Auditable Phase 8 opportunity record schema."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Opportunity:
    """A recognition-only opportunity; deliberately contains no execution field."""

    title: str
    provenance: dict[str, list[str]]
    value: str
    evidence: list[str]
    cost: str
    risk: str
    alignment: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
