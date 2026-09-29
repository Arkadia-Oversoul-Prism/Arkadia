"""EL-07 — provider-neutral voice command boundary.

Voice resolves into explicit Arkadia intents. It is a *provider-neutral*
boundary: no assistant (Google Assistant, etc.) is a hidden authority layer.

Canonical flow (directive section 10):

  VOICE -> INTENT -> IDENTITY -> WORKSPACE -> AUTHORIZATION CHECK
        -> AGENT/ACTION -> EVIDENCE

The recognizer is pluggable. If no recognizer is configured the boundary reports
``UNCONFIGURED`` and returns no intent — it never invents one.

Voice cannot bypass human authorization. An intent that maps to a human-only
operation is rejected here, before any agent or action is reached.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from .contracts import HUMAN_ONLY, utc_now

#: Canonical Engineering Lab intents voice may resolve to.
VOICE_INTENTS: tuple[str, ...] = (
    "OPEN_ENGINEERING_LAB",
    "SHOW_ACTIVE_RUNS",
    "INSPECT_SESSION",
    "INSPECT_ARTIFACTS",
    "INSPECT_EVIDENCE",
    "INSPECT_PR_STATE",
    "REQUEST_REVIEW",
    "PAUSE_RUN",
    "MERGE_PR",  # human-only; never dispatched by voice
    "DEPLOY_PRODUCTION",  # human-only; never dispatched by voice
    "UNKNOWN",
)

#: Intents that are observation-only.
_READ_INTENTS = frozenset(
    {
        "OPEN_ENGINEERING_LAB",
        "SHOW_ACTIVE_RUNS",
        "INSPECT_SESSION",
        "INSPECT_ARTIFACTS",
        "INSPECT_EVIDENCE",
        "INSPECT_PR_STATE",
    }
)

#: Intents that require an existing human authorization to act.
_ACTION_INTENTS = frozenset({"REQUEST_REVIEW", "PAUSE_RUN"})

#: Human-only intents. Voice is *never* an authority boundary for these.
_HUMAN_ONLY_INTENTS = frozenset({"MERGE_PR", "DEPLOY_PRODUCTION"})

#: Keyword -> intent map. A deterministic resolver, not an authority.
_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("engineering lab", "OPEN_ENGINEERING_LAB"),
    ("open lab", "OPEN_ENGINEERING_LAB"),
    ("active runs", "SHOW_ACTIVE_RUNS"),
    ("what is running", "SHOW_ACTIVE_RUNS"),
    ("inspect session", "INSPECT_SESSION"),
    ("artifacts", "INSPECT_ARTIFACTS"),
    ("evidence", "INSPECT_EVIDENCE"),
    ("pull request", "INSPECT_PR_STATE"),
    ("pr state", "INSPECT_PR_STATE"),
    ("request review", "REQUEST_REVIEW"),
    ("pause", "PAUSE_RUN"),
    ("merge", "MERGE_PR"),
    ("deploy", "DEPLOY_PRODUCTION"),
)


class VoiceRecognizer(Protocol):
    def transcribe(self, audio_ref: str) -> str: ...


@dataclass
class VoiceResolution:
    """The result of resolving a voice command into an explicit intent."""

    transcript: str
    intent: str
    requires_authorization: bool
    human_only: bool
    disposition: str  # READ | AUTHORIZATION_REQUIRED | HUMAN_ONLY_REFUSED | UNKNOWN
    detail: str = ""
    resolved_at: str = utc_now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "transcript": self.transcript,
            "intent": self.intent,
            "requires_authorization": self.requires_authorization,
            "human_only": self.human_only,
            "disposition": self.disposition,
            "detail": self.detail,
            "resolved_at": self.resolved_at,
        }


def classify_intent(transcript: str) -> str:
    """Deterministically classify a transcript into a canonical intent.

    Human-only keywords (merge/deploy) are matched first so a phrase like
    "merge the pull request" cannot be downgraded to an observation intent.
    """
    text = (transcript or "").strip().lower()
    if not text:
        return "UNKNOWN"
    for keyword, intent in _KEYWORDS:
        if intent in _HUMAN_ONLY_INTENTS and keyword in text:
            return intent
    for keyword, intent in _KEYWORDS:
        if intent not in _HUMAN_ONLY_INTENTS and keyword in text:
            return intent
    return "UNKNOWN"


def resolve_voice_command(
    transcript: str,
    *,
    identity_present: bool = False,
    workspace_present: bool = False,
    authorization_present: bool = False,
) -> VoiceResolution:
    """Resolve a transcript through the full boundary.

    Human-only intents (merge/deploy) are refused at the boundary regardless of
    any other flag — voice is never an authority layer.
    """
    intent = classify_intent(transcript)

    if intent in _HUMAN_ONLY_INTENTS:
        return VoiceResolution(
            transcript=transcript,
            intent=intent,
            requires_authorization=True,
            human_only=True,
            disposition="HUMAN_ONLY_REFUSED",
            detail="this operation is human-only and is never dispatched by voice",
        )

    if intent == "UNKNOWN":
        return VoiceResolution(
            transcript=transcript,
            intent=intent,
            requires_authorization=False,
            human_only=False,
            disposition="UNKNOWN",
            detail="no canonical intent matched the transcript",
        )

    if intent in _READ_INTENTS:
        return VoiceResolution(
            transcript=transcript,
            intent=intent,
            requires_authorization=False,
            human_only=False,
            disposition="READ",
            detail="observation-only intent",
        )

    # Action intent: require identity, workspace, and authorization.
    if not identity_present:
        disposition, detail = "UNKNOWN", "identity required before an action intent"
        requires = True
    elif not workspace_present:
        disposition, detail = "UNKNOWN", "workspace required before an action intent"
        requires = True
    elif not authorization_present:
        disposition, detail = "AUTHORIZATION_REQUIRED", "human authorization required"
        requires = True
    else:
        disposition, detail = "AUTHORIZATION_REQUIRED", "authorized; action may be initiated"
        requires = True

    _ = _ACTION_INTENTS  # membership documented above
    return VoiceResolution(
        transcript=transcript,
        intent=intent,
        requires_authorization=True,
        human_only=False,
        disposition=disposition if intent in _ACTION_INTENTS else "UNKNOWN",
        detail=detail,
    )


def voice_boundary_report() -> dict[str, Any]:
    """Truthful status of the voice boundary (no recognizer is configured here)."""
    return {
        "surface": "voice_adapter",
        "provider_neutral": True,
        "recognizer_configured": False,
        "recognizer_state": "UNCONFIGURED",
        "detail": "no speech recognizer wired; boundary accepts transcripts only",
        "intents": list(VOICE_INTENTS),
        "human_only_intents": sorted(_HUMAN_ONLY_INTENTS),
        "human_authority_preserved": True,
        "assistant_is_hidden_authority": False,
        "non_collapse": sorted(HUMAN_ONLY) and "VOICE != AUTHORIZATION",
    }
