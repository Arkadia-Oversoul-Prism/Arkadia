"""Governed content cadence for the Voice of Belonging series.

Thin operating layer over Arkadia's existing Growth OS / Knowledge OS /
automation spine. It owns no scheduler, provider, memory store, or publication
authority.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Any

STATES = ("SOURCE","CANDIDATE","DRAFT","READY","APPROVED","PUBLISHED","MEASURED","REPURPOSE","BLOCKED")
TRANSITIONS: dict[str, frozenset[str]] = {
    "SOURCE": frozenset({"CANDIDATE","BLOCKED"}),
    "CANDIDATE": frozenset({"DRAFT","BLOCKED"}),
    "DRAFT": frozenset({"READY","BLOCKED"}),
    "READY": frozenset({"APPROVED","DRAFT","BLOCKED"}),
    "APPROVED": frozenset({"PUBLISHED","BLOCKED"}),
    "PUBLISHED": frozenset({"MEASURED","BLOCKED"}),
    "MEASURED": frozenset({"REPURPOSE","BLOCKED"}),
    "REPURPOSE": frozenset({"DRAFT","BLOCKED"}),
    "BLOCKED": frozenset({"SOURCE","CANDIDATE","DRAFT"}),
}

@dataclass(frozen=True)
class ContentSource:
    source_id: str
    provenance_refs: tuple[str, ...]
    thesis: str
    audience: str = "people exhausted by performing significance"
    evidence_refs: tuple[str, ...] = ()

@dataclass
class ContentItem:
    content_id: str
    series: str
    source: ContentSource
    format: str
    state: str = "SOURCE"
    cadence_slot: str | None = None
    canonical_text: str | None = None
    visual_brief: str | None = None
    audio_brief: str | None = None
    delivery_targets: tuple[str, ...] = ()
    approval_ref: str | None = None
    publication_refs: tuple[str, ...] = ()
    measurement_refs: tuple[str, ...] = ()
    created_on: str = field(default_factory=lambda: date.today().isoformat())

    def __post_init__(self) -> None:
        if self.state not in STATES:
            raise ValueError(f"unknown content state: {self.state}")
        if not self.source.provenance_refs:
            raise ValueError("content requires provenance references")

    @property
    def human_approval_required(self) -> bool:
        return True

    @property
    def externally_publishable(self) -> bool:
        return self.state == "APPROVED" and bool(self.approval_ref)

    def transition(self, target: str, *, approval_ref: str | None = None) -> None:
        if target not in STATES:
            raise ValueError(f"unknown content state: {target}")
        if target not in TRANSITIONS[self.state]:
            raise ValueError(f"illegal content transition {self.state} -> {target}")
        if target == "APPROVED":
            if not approval_ref:
                raise ValueError("human approval reference required")
            self.approval_ref = approval_ref
        if target == "PUBLISHED" and not self.externally_publishable:
            raise ValueError("publication requires recorded human approval")
        self.state = target

    def to_dict(self) -> dict[str, Any]:
        return {
            "content_id": self.content_id, "series": self.series,
            "source_id": self.source.source_id,
            "provenance_refs": list(self.source.provenance_refs),
            "evidence_refs": list(self.source.evidence_refs),
            "thesis": self.source.thesis, "audience": self.source.audience,
            "format": self.format, "state": self.state,
            "cadence_slot": self.cadence_slot,
            "canonical_text": self.canonical_text,
            "visual_brief": self.visual_brief, "audio_brief": self.audio_brief,
            "delivery_targets": list(self.delivery_targets),
            "approval_ref": self.approval_ref,
            "publication_refs": list(self.publication_refs),
            "measurement_refs": list(self.measurement_refs),
            "human_approval_required": self.human_approval_required,
            "externally_publishable": self.externally_publishable,
            "created_on": self.created_on,
        }

@dataclass(frozen=True)
class CadenceSlot:
    key: str
    kind: str
    weekday: int
    objective: str

VOICE_OF_BELONGING_CADENCE = (
    CadenceSlot("MON_TRANSMISSION","transmission",0,"establish the week's emotional thesis"),
    CadenceSlot("WED_WHISPER","whisper",2,"compress the thesis into a memorable line"),
    CadenceSlot("FRI_TRANSMISSION","transmission",4,"deepen or challenge the week's thesis"),
    CadenceSlot("SAT_FIELD_NOTE","field_note",5,"ground belonging in ordinary human life"),
)

def due_slots(weekday: int) -> tuple[CadenceSlot, ...]:
    return tuple(slot for slot in VOICE_OF_BELONGING_CADENCE if slot.weekday == weekday)

def select_next_source(*, sources: list[ContentSource], existing: list[ContentItem]) -> ContentSource | None:
    used = {item.source.source_id for item in existing}
    for candidate in sources:
        if candidate.source_id not in used and candidate.provenance_refs:
            return candidate
    return None

def governance_view() -> dict[str, Any]:
    return {
        "series": "VOICE_OF_BELONGING",
        "cadence": [slot.__dict__ for slot in VOICE_OF_BELONGING_CADENCE],
        "scheduler": "existing_arkadia_scheduler",
        "ai_may": ["derive","draft","repurpose","score","prepare_delivery"],
        "human_gate": "required_before_publication",
        "autonomous_publication": False,
        "canonical_source": "arkadia_knowledge_os",
        "distribution_model": "content_object_then_adapter",
        "evidence_required": True,
    }
