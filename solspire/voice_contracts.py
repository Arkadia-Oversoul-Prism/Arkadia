"""Arkadia Voice — canonical, provider-independent voice contracts (Phase 2).

These contracts are the *only* shapes the Voice pipeline exchanges. Every
object carries the linkage needed to trace the chain backwards:

    VoiceEvent ──▶ Transcript ──▶ Intent ──▶ Context ──▶ Authority
        └──────────── proposal ── approval ── authorization ── execution
                        └── work_event ── evidence ── verification

Nothing here creates authority, identity, or an execution path. Speech is an
input modality; it is never authorization. Governance objects referenced by
these contracts (Proposal, Authorization, ExecutionAttempt, WorkEvent,
Evidence, Verification) are the canonical substrate records — see
docs/voice/ARCHITECTURE_DISCOVERY.md.

Stage order below follows the *implemented* canonical chain (the repository's
governance requires a proposal to be ACCEPTED before authorization can exist).
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


# ── Stage vocabulary (the evidence timeline shown by the UI) ─────────────────

class VoiceStage(str, Enum):
    VOICE_EVENT = "VOICE_EVENT"
    TRANSCRIPT = "TRANSCRIPT"
    INTENT = "INTENT"
    CONTEXT = "CONTEXT"
    AUTHORITY = "AUTHORITY"
    PROPOSAL = "PROPOSAL"
    APPROVAL = "APPROVAL"
    AUTHORIZATION = "AUTHORIZATION"
    EXECUTION = "EXECUTION"
    RESULT = "RESULT"
    WORK_EVENT = "WORK_EVENT"
    EVIDENCE = "EVIDENCE"
    VERIFICATION = "VERIFICATION"
    ERROR = "ERROR"
    CLARIFICATION = "CLARIFICATION"


#: Canonical, ordered causal chain. Informational (observation-only) requests
#: legitimately skip PROPOSAL → AUTHORIZATION; that skip is recorded, not hidden.
STAGE_ORDER: tuple[VoiceStage, ...] = (
    VoiceStage.VOICE_EVENT,
    VoiceStage.TRANSCRIPT,
    VoiceStage.INTENT,
    VoiceStage.CONTEXT,
    VoiceStage.AUTHORITY,
    VoiceStage.PROPOSAL,
    VoiceStage.APPROVAL,
    VoiceStage.AUTHORIZATION,
    VoiceStage.EXECUTION,
    VoiceStage.RESULT,
    VoiceStage.WORK_EVENT,
    VoiceStage.EVIDENCE,
    VoiceStage.VERIFICATION,
)


# ── Bounded action vocabulary (Phase 5) ──────────────────────────────────────

class VoiceAction(str, Enum):
    ASK = "ASK"
    SEARCH = "SEARCH"
    CREATE = "CREATE"
    MODIFY = "MODIFY"
    EXECUTE = "EXECUTE"
    UNKNOWN = "UNKNOWN"


#: Risk policy. INFORMATIONAL = observation-only (no proposal, no approval —
#: mirrors lab/engineering_lab/voice.py `_READ_INTENTS` disposition READ).
#: Everything else is consequential and must pass the full governance chain.
RISK_LEVELS: dict[VoiceAction, str] = {
    VoiceAction.ASK: "INFORMATIONAL",
    VoiceAction.SEARCH: "INFORMATIONAL",
    VoiceAction.EXECUTE: "MEDIUM",
    VoiceAction.CREATE: "MEDIUM",
    VoiceAction.MODIFY: "HIGH",
    VoiceAction.UNKNOWN: "UNKNOWN",
}


def requires_approval(action: VoiceAction | str) -> bool:
    """True iff a request is consequential and needs an explicit human decision."""
    risk = RISK_LEVELS.get(VoiceAction(action), "UNKNOWN")
    return risk != "INFORMATIONAL"


# ── Resolution / authority states ────────────────────────────────────────────

class ResolutionStatus(str, Enum):
    KNOWN = "KNOWN"
    AMBIGUOUS = "AMBIGUOUS"
    UNKNOWN = "UNKNOWN"
    UNAUTHORIZED = "UNAUTHORIZED"


class ProviderState(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    MISCONFIGURED = "MISCONFIGURED"
    FAILED = "FAILED"


#: Explicit error states (Phase 12) with a useful recovery action. The UI
#: renders these verbatim; nothing hangs without a next step.
VOICE_ERROR_STATES: dict[str, dict[str, str]] = {
    "MICROPHONE_DENIED": {
        "recovery": "Allow microphone access in the browser, then press RECORD again.",
        "stage": "VOICE_EVENT",
    },
    "AUDIO_CAPTURE_FAILED": {
        "recovery": "Check the input device and retry the recording.",
        "stage": "VOICE_EVENT",
    },
    "AUDIO_EMPTY": {
        "recovery": "Record a longer clip (audio must be non-empty and ≤ 5 MiB).",
        "stage": "VOICE_EVENT",
    },
    "ASR_UNAVAILABLE": {
        "recovery": "Choose an available provider (GET /solspire/voice/providers) "
                    "or configure official provider credentials.",
        "stage": "TRANSCRIPT",
    },
    "ASR_FAILED": {
        "recovery": "Retry the transcription, or select a different ASR provider.",
        "stage": "TRANSCRIPT",
    },
    "TRANSCRIPT_EMPTY": {
        "recovery": "Re-record and speak clearly; empty transcripts are never guessed.",
        "stage": "TRANSCRIPT",
    },
    "INTENT_UNKNOWN": {
        "recovery": "Rephrase using the bounded vocabulary (ASK / SEARCH / CREATE / "
                    "MODIFY / EXECUTE) and submit again.",
        "stage": "INTENT",
    },
    "CONTEXT_AMBIGUOUS": {
        "recovery": "Choose which candidate the request refers to (CLARIFY), then retry.",
        "stage": "CONTEXT",
    },
    "CONTEXT_UNKNOWN": {
        "recovery": "Name the target explicitly (for example: the project called …).",
        "stage": "CONTEXT",
    },
    "AUTHORITY_MISSING": {
        "recovery": "This request needs a principal with the Govern authority "
                    "(Flamekeeper or access_level ≥ 3).",
        "stage": "AUTHORITY",
    },
    "AUTHORIZATION_DENIED": {
        "recovery": "Authorization was refused. Ask a governing principal to "
                    "authorize, or reduce the scope of the request.",
        "stage": "AUTHORIZATION",
    },
    "AUTHORIZATION_REQUIRED": {
        "recovery": "The proposal is ACCEPTED but not yet authorized. Press "
                    "AUTHORIZE (govern authority) before execution.",
        "stage": "AUTHORIZATION",
    },
    "APPROVAL_REQUIRED": {
        "recovery": "Open the proposal and press APPROVE (human decision) before "
                    "execution can proceed.",
        "stage": "APPROVAL",
    },
    "PROPOSAL_REQUIRED": {
        "recovery": "Generate the explicit proposal for this consequential request first.",
        "stage": "PROPOSAL",
    },
    "EXECUTION_FAILED": {
        "recovery": "Inspect the execution result in the evidence chain; correct the "
                    "request and propose again. Evidence of the failure is preserved.",
        "stage": "EXECUTION",
    },
    "VERIFICATION_PENDING": {
        "recovery": "Execution succeeded but is NOT verified. Record a verification "
                    "verdict against the evidence.",
        "stage": "VERIFICATION",
    },
    "VERIFICATION_FAILED": {
        "recovery": "The verification verdict was REJECTED/INCONCLUSIVE — inspect the "
                    "evidence chain and re-execute or re-verify.",
        "stage": "VERIFICATION",
    },
}


def new_id(prefix: str) -> str:
    """Deterministic-format identifier: PREFIX-<uuid4hex>."""
    return f"{prefix}-{uuid.uuid4().hex}"


def utc_now() -> float:
    return time.time()


def canonical_digest(payload: Any) -> str:
    """Stable sha256 over a JSON-normalised payload (evidence linkage)."""
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def hash_audio(audio: bytes) -> str:
    """sha256 of the captured audio bytes — recorded before any provider runs."""
    return hashlib.sha256(audio).hexdigest()


# ── Contracts ────────────────────────────────────────────────────────────────

@dataclass
class VoiceEvent:
    """A captured human speech utterance entering the Arkadia pipeline."""

    event_id: str
    session_id: str
    subject: str
    audio_reference: str
    audio_hash: str
    timestamp: float
    language: str
    asr_provenance: dict[str, Any]
    transcript: str = ""
    workspace_ref: str | None = None
    audio_mime: str = ""
    audio_size: int = 0
    duration_ms: int | None = None
    status: str = "RECEIVED"
    error_state: str | None = None
    error_detail: str | None = None

    @staticmethod
    def create(
        *,
        subject: str,
        workspace_ref: str,
        audio_hash: str,
        audio_reference: str,
        language: str = "en",
        session_id: str | None = None,
        audio_mime: str = "",
        audio_size: int = 0,
        duration_ms: int | None = None,
    ) -> "VoiceEvent":
        event_id = new_id("VE")
        return VoiceEvent(
            event_id=event_id,
            session_id=session_id or workspace_ref,
            subject=subject,
            audio_reference=audio_reference,
            audio_hash=audio_hash,
            timestamp=utc_now(),
            language=language,
            asr_provenance={"state": "PENDING"},
            workspace_ref=workspace_ref,
            audio_mime=audio_mime,
            audio_size=audio_size,
            duration_ms=duration_ms,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Transcript:
    """Canonical provider-independent transcript.

    ``confidence`` is ``None`` when the provider cannot honestly supply one —
    it is never invented. ``provenance`` records exactly how the text was
    produced (provider, model, engine, and whether text was supplied rather
    than recognized).
    """

    text: str
    language: str
    confidence: float | None
    provider: str
    model: str
    timestamp: float
    audio_hash: str
    provenance: dict[str, Any]

    @staticmethod
    def normalize(text: str) -> str:
        """Whitespace-normalised transcript. Empty/stripped input stays empty."""
        return " ".join((text or "").split())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Intent:
    """Structured intent derived from a transcript by the bounded parser."""

    intent_id: str
    action: str
    entities: dict[str, Any]
    requested_effect: str
    confidence: float | None
    source_event_id: str
    canonical_intent_type: str = ""
    parser: str = "rule_based"
    transcript: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Context:
    """Resolved context for an intent. Uncertainty is preserved, never converted
    into confidence: KNOWN / AMBIGUOUS / UNKNOWN / UNAUTHORIZED."""

    context_id: str
    resolved_entities: dict[str, Any]
    candidate_entities: dict[str, list[dict[str, Any]]]
    ambiguities: list[dict[str, Any]]
    resolution_status: str
    source_event_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VoiceProposal:
    """Voice view of the canonical SolSpire proposal + its governance posture."""

    proposal_id: str
    intent_id: str
    context_id: str
    requested_action: str
    risk_level: str
    authority_status: str
    authorization_status: str
    required_approval: bool
    status: str
    executor: str = ""
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VoiceExecution:
    """Execution view. EXECUTION ≠ VERIFICATION: a successful executor response
    is not verified real-world completion."""

    execution_id: str
    proposal_id: str | None
    approval_id: str | None
    executor: str
    work_event_id: str | None
    result: dict[str, Any]
    status: str
    verification_state: str = "PENDING"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ChainStage:
    """One inspectable stage of the causal evidence chain."""

    stage: str
    seq: int
    record_type: str
    record_id: str
    payload: dict[str, Any]
    created_at: float
    prev_record_id: str | None = None
    payload_digest: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def chain_digest(stages: list[ChainStage]) -> str:
    """Digest over the ordered chain — every stage is traceable backwards via
    seq order + prev_record_id; this binds them into one evidence claim."""
    return canonical_digest(
        [[s.seq, s.stage, s.record_id, s.payload_digest] for s in stages]
    )


__all__ = [
    "VoiceStage",
    "STAGE_ORDER",
    "VoiceAction",
    "RISK_LEVELS",
    "requires_approval",
    "ResolutionStatus",
    "ProviderState",
    "VOICE_ERROR_STATES",
    "new_id",
    "utc_now",
    "canonical_digest",
    "hash_audio",
    "VoiceEvent",
    "Transcript",
    "Intent",
    "Context",
    "VoiceProposal",
    "VoiceExecution",
    "ChainStage",
    "chain_digest",
]
