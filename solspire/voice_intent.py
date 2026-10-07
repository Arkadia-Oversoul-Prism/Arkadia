"""Arkadia Voice — bounded, deterministic transcript → intent layer (Phase 5).

A small vocabulary, parsed by rules, never guessed:

    ASK · SEARCH · CREATE · MODIFY · EXECUTE · UNKNOWN

Unknown or ambiguous requests stay UNKNOWN. Confidence here is *rule-match
coverage* (1.0 = complete grammar match, 0.6 = action matched but a required
entity is missing, None = no match) — explicitly not a model probability; the
``parser`` field records that provenance.

Human-only operations (merge / deploy — the Engineering Lab's canonical
``HUMAN_ONLY`` set) are refused at this boundary exactly like
``lab/engineering_lab/voice.py`` refuses them: voice is never an authority.

The canonical ``IntentType`` (SolSpire's 7-type router) is resolved through the
existing ``solspire.intent_router.IntentRouter`` and carried alongside the
voice action; nothing is re-implemented here.
"""
from __future__ import annotations

import re

from lab.engineering_lab.contracts import HUMAN_ONLY  # canonical human-only ops
from solspire.intent_router import IntentRouter  # canonical intent typing
from solspire.voice_contracts import Intent, VoiceAction, new_id

#: Phrases mapping onto the canonical human-only set. Mirrors the keyword
#: vocabulary of lab/engineering_lab/voice.py (`merge` / `deploy`).
_HUMAN_ONLY_PHRASES = (re.compile(r"\bmerge\b", re.I), re.compile(r"\bdeploy\b", re.I))

_CREATE = re.compile(
    r"\b(create|make|spin up|start|open)\b.*\b(project|note|task|document|file|report)\b",
    re.I,
)
_MODIFY = re.compile(r"\b(rename|update|change|modify|move|archive|delete)\b", re.I)
_EXECUTE = re.compile(r"\b(run|execute|launch|perform|send|share|email|deliver|forward)\b", re.I)
_SEARCH = re.compile(
    r"\b(find|search(?:\s+for)?|look\s+for|look\s+up|query|locate|where(?:'|\s+i)s)\b",
    re.I,
)
_ASK_START = re.compile(
    r"^(what|who|when|where|why|how|is|are|was|were|do|does|did|can|could|should|"
    r"would|will|tell me|explain|describe|show me)\b",
    re.I,
)

_NOUN_TO_ENTITY = {
    "project": "PROJECT",
    "note": "NOTE",
    "task": "TASK",
    "document": "DOCUMENT",
    "report": "DOCUMENT",
    "file": "FILE",
}

_REQUESTED_EFFECT = {
    VoiceAction.ASK: "ANSWER_QUESTION",
    VoiceAction.SEARCH: "SEARCH_KNOWLEDGE",
    VoiceAction.CREATE: "CREATE_ENTITY",
    VoiceAction.MODIFY: "MODIFY_ENTITY",
    VoiceAction.EXECUTE: "EXECUTE_OPERATION",
    VoiceAction.UNKNOWN: "NONE",
}

#: Documented confidence semantics — rule-match coverage, never a model score.
CONFIDENCE_FULL_MATCH = 1.0
CONFIDENCE_MISSING_ENTITY = 0.6


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip()).rstrip("?.! ")


def _extract_called_name(text: str) -> str | None:
    """'… called Eden Pilot' / '… named Eden Pilot' → 'Eden Pilot'."""
    match = re.search(r"\b(?:called|named)\s+(.+)$", text, re.I)
    return _clean(match.group(1)) if match else None


def _trailing_after_noun(text: str, noun: str) -> str | None:
    match = re.search(rf"\b{re.escape(noun)}\s+(?:called\s+|named\s+)?(.+)$", text, re.I)
    if not match:
        return None
    value = _clean(match.group(1))
    return value or None


def _human_only(transcript: str) -> bool:
    return any(pattern.search(transcript or "") for pattern in _HUMAN_ONLY_PHRASES)


def _canonical_intent_type(transcript: str) -> str:
    """Resolve the canonical SolSpire IntentType through the existing router."""
    try:
        return IntentRouter().classify(transcript).value
    except Exception:  # pragma: no cover — the router already swallows failures
        return ""


def _intent(action: VoiceAction, entities: dict, confidence: float | None,
            source_event_id: str, transcript: str) -> Intent:
    return Intent(
        intent_id=new_id("IN"),
        action=action.value,
        entities=entities,
        requested_effect=_REQUESTED_EFFECT[action],
        confidence=confidence,
        source_event_id=source_event_id,
        canonical_intent_type=_canonical_intent_type(transcript),
        parser="rule_based",
        transcript=transcript,
    )


def parse_intent(transcript: str, source_event_id: str) -> Intent:
    """Deterministically parse a canonical transcript into a structured intent.

    Never guesses: unmatched input returns action=UNKNOWN with confidence=None.
    """
    raw = (transcript or "").strip()
    text = _clean(transcript)

    if not text:
        return _intent(VoiceAction.UNKNOWN, {}, None, source_event_id, text)

    # Human-only operations are refused before any other classification.
    if _human_only(text):
        intent = _intent(
            VoiceAction.UNKNOWN,
            {"human_only": True, "operation": text},
            CONFIDENCE_FULL_MATCH,
            source_event_id,
            text,
        )
        intent.requested_effect = "REFUSED_HUMAN_ONLY"
        return intent

    # ── CREATE ──────────────────────────────────────────────────────────────
    match = _CREATE.search(text)
    if match:
        noun = match.group(2).lower()
        entity = _NOUN_TO_ENTITY.get(noun, noun.upper())
        # 'called/named X' wins; otherwise the phrase after the noun.
        name = _extract_called_name(text) or _trailing_after_noun(text, noun)
        entities = {"entity": entity, "noun": noun}
        if name:
            entities["name"] = name
            confidence = CONFIDENCE_FULL_MATCH
        else:
            confidence = CONFIDENCE_MISSING_ENTITY
        return _intent(VoiceAction.CREATE, entities, confidence, source_event_id, text)

    # ── MODIFY ──────────────────────────────────────────────────────────────
    match = _MODIFY.search(text)
    if match:
        verb = match.group(1).lower()
        entities: dict = {"verb": verb}
        confidence = CONFIDENCE_FULL_MATCH
        if verb == "rename":
            rename = re.search(
                r"rename\s+(?:the\s+)?(?:(?P<noun>project|note|task|document|file|report)\s+)?"
                r"(?P<target>.+?)\s+to\s+(?P<new>.+)$",
                text, re.I,
            )
            if rename:
                noun = (rename.group("noun") or "project").lower()
                entities["entity"] = _NOUN_TO_ENTITY.get(noun, noun.upper())
                entities["target"] = _clean(rename.group("target"))
                entities["new_value"] = _clean(rename.group("new"))
                entities["field"] = "name"
            else:
                confidence = CONFIDENCE_MISSING_ENTITY
                entities["entity"] = "PROJECT"
        elif verb == "archive":
            archive = re.search(
                r"archive\s+(?:the\s+)?(?P<noun>project|note|task|document|file|report)?\s*"
                r"(?P<target>.+)?$",
                text, re.I,
            )
            noun = (archive.group("noun") if archive else None) or "project"
            target = _clean(archive.group("target")) if archive else ""
            target = _clean(re.sub(r"^(?:called|named)\s+", "", target, flags=re.I))
            entities["entity"] = _NOUN_TO_ENTITY.get(noun.lower(), "PROJECT")
            entities["field"] = "status"
            entities["new_value"] = "archived"
            if target:
                entities["target"] = target
            else:
                confidence = CONFIDENCE_MISSING_ENTITY
        else:
            # Generic update/change/modify/move/delete: bounded to PROJECT
            # with an explicit target phrase.
            target = _clean(re.sub(
                r"^(?:update|change|modify|move|delete)\s+(?:the\s+)?"
                r"(?:project|note|task|document|file|report)?\s*",
                "", text, flags=re.I,
            ))
            entities["entity"] = "PROJECT"
            if target:
                entities["target"] = target
                entities["field"] = "description"
                entities["new_value"] = target
            else:
                confidence = CONFIDENCE_MISSING_ENTITY
        return _intent(VoiceAction.MODIFY, entities, confidence, source_event_id, text)

    # ── EXECUTE ─────────────────────────────────────────────────────────────
    match = _EXECUTE.search(text)
    if match:
        verb = match.group(1).lower()
        if verb in {"send", "share", "email", "deliver", "forward"}:
            # Transfer requests name a payload and (usually) a recipient.
            recipient_match = re.search(r"\bto\s+(?P<rcpt>.+)$", text, re.I)
            recipient = _clean(recipient_match.group("rcpt")) if recipient_match else None
            payload = text if not recipient_match else _clean(
                re.sub(r"\s+to\s+.+$", "", text, flags=re.I)
            )
            payload = _clean(re.sub(
                r"^(?:send|share|email|deliver|forward)\s+(?:the\s+|an?\s+)?",
                "", payload, flags=re.I,
            ))
            noun_match = re.search(
                r"\b(report|document|file|note|attachment)s?\b", text, re.I
            )
            entities = {"entity": "DOCUMENT", "operation": "transfer"}
            if payload:
                entities["target"] = payload
                confidence = CONFIDENCE_FULL_MATCH
            elif noun_match:
                entities["target"] = noun_match.group(1)
                confidence = CONFIDENCE_MISSING_ENTITY
            else:
                confidence = CONFIDENCE_MISSING_ENTITY
            if recipient:
                entities["recipient"] = recipient
            else:
                confidence = CONFIDENCE_MISSING_ENTITY
            return _intent(VoiceAction.EXECUTE, entities, confidence,
                           source_event_id, text)
        rest = _clean(re.sub(
            r"^(?:run|execute|launch|perform)\s+(?:the\s+|an?\s+)?", "", text, flags=re.I
        ))
        path = rest or "."
        if path.strip().lower() in {"listing", "list", "directory listing", "dir listing"}:
            path = "."
        # "run the listing for vault" → path "vault"
        for_prep = re.search(r"\bfor\s+(.+)$", path, re.I)
        if for_prep:
            path = _clean(for_prep.group(1))
        entities = {"entity": "PATH", "path": path, "operation": "fs_list"}
        return _intent(VoiceAction.EXECUTE, entities, CONFIDENCE_FULL_MATCH,
                       source_event_id, text)

    # ── SEARCH ──────────────────────────────────────────────────────────────
    match = _SEARCH.search(text)
    if match:
        rest = _clean(re.sub(
            r"^(?:find|search(?:\s+for)?|look\s+for|look\s+up|query|locate|"
            r"where(?:'|\s+i)s)\s+",
            "", text, flags=re.I,
        ))
        query = rest or text
        entities = {"entity": "QUERY", "query": query}
        return _intent(VoiceAction.SEARCH, entities, CONFIDENCE_FULL_MATCH,
                       source_event_id, text)

    # ── ASK ─────────────────────────────────────────────────────────────────
    if raw.endswith("?") or _ASK_START.match(text):
        entities = {"entity": "QUERY", "query": text}
        return _intent(VoiceAction.ASK, entities, CONFIDENCE_FULL_MATCH,
                       source_event_id, text)

    # ── UNKNOWN — never guessed ─────────────────────────────────────────────
    return _intent(VoiceAction.UNKNOWN, {}, None, source_event_id, text)


__all__ = ["parse_intent", "HUMAN_ONLY", "CONFIDENCE_FULL_MATCH",
           "CONFIDENCE_MISSING_ENTITY"]
