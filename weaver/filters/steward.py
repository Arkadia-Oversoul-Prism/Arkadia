"""
Steward Filter — Decision Hygiene

Enforces sustainability, exit-validity, and action compression.
Blocks identity inflation and symbolic drift.
"""

import re
from typing import Optional

# Action-oriented vocabulary. Rule 2 admits mythic language when the passage is
# action-grounded, so these stems are matched on word boundaries rather than as
# bare substrings ("do" inside "words" is not an action).
_ACTION_STEMS = ("do", "act", "choose", "decide", "maintain", "quit", "release")
_ACTION_RE = re.compile(r"\b(?:" + "|".join(_ACTION_STEMS) + r")\w*\b")

# Identity escalation is a *claim*, not a topic. Each entry requires its subject
# ("you are divine") or a possessive ("divine authority"), so ordinary discussion
# of a mythic word no longer trips the filter.
_FORBIDDEN_IDENTITY = re.compile(
    r"\b(?:you|we|i)\s+(?:are|am)\s+(?:\w+\s+){0,2}?"
    r"(?:divine|chosen|ascended|eternal|transcendent|immortal|god)\b"
    r"|\b(?:divine|chosen|ascended|transcendent|immortal|oversoul|sacred|holy|god)\s+"
    r"(?:authority|mandate|right|being|one|self|status|nature|power)\b"
    r"|\b(?:you|we|i)\s+(?:have|has)\s+(?:transcended|ascended)\b",
    re.IGNORECASE,
)

# Symbolic drift, not mere recurrence. A single "grid"/"flame" mention is
# description; a *dominant density* of symbolic terms with no action is drift.
_MYTHIC_STEMS = ("grid", "flame", "resonance", "field", "symbolism")
_MYTHIC_RE = re.compile(r"\b(?:" + "|".join(_MYTHIC_STEMS) + r")\w*\b", re.IGNORECASE)
_WORD_RE = re.compile(r"[a-z']+")

_MYTHIC_DENSITY_LIMIT = 0.25
_MIN_WORDS_FOR_DENSITY = 4


def _has_action(text: str) -> bool:
    """True when the text is action-grounded."""
    return _ACTION_RE.search(text.lower()) is not None


def _mythic_density(text: str) -> float:
    """Share of words that are symbolic terms (0.0 for empty text)."""
    words = _WORD_RE.findall(text.lower())
    if not words:
        return 0.0
    return len(_MYTHIC_RE.findall(text)) / len(words)


def steward_filter(text: str, strict: bool = True) -> Optional[str]:
    """
    Apply steward filter to output.

    Returns:
    - text if passes filter
    - None if blocks output

    Rules:
    1. Block identity/belief escalation
    2. Block symbolism without action
    3. Require action-oriented language for complex outputs
    4. Block mythic inflation (dominant symbolic density) in strict mode
    """
    if not text or not isinstance(text, str):
        return None

    text_lower = text.lower()

    # Rule 1: Block identity escalation
    if _FORBIDDEN_IDENTITY.search(text):
        return None

    # Rule 2: Block pure symbolism (no action)
    if text_lower.count("symbolism") > 2 and not _has_action(text_lower):
        return None

    # Rule 3: Require action-oriented language for complex outputs
    if len(text) > 200 and not _has_action(text_lower):
        return None

    # Rule 4: Check for mythic inflation (if strict mode)
    if strict:
        words = _WORD_RE.findall(text_lower)
        if len(words) >= _MIN_WORDS_FOR_DENSITY and _mythic_density(text) > _MYTHIC_DENSITY_LIMIT:
            return None

    return text


def compress_to_choices(text: str) -> str:
    """
    Compress output to actionable choices.
    Distills meaning into decision points.
    """
    if not text:
        return ""

    # Split into sentences first: keeping whole lines would preserve non-action
    # sentences that merely share a line with a decision point.
    action_verbs = ["do", "choose", "quit", "maintain", "release", "adjust", "continue"]
    sentences = re.split(r"(?<=[.!?])\s+|\n", text)
    compressed = [
        sentence.strip()
        for sentence in sentences
        if sentence.strip() and any(verb in sentence.lower() for verb in action_verbs)
    ]

    return "\n".join(compressed[:5])  # Max 5 decision points


def check_sustainability(text: str) -> bool:
    """
    Check if output represents sustainable practice.
    Returns True if sustainable, False if unsustainable pattern.
    """
    unsustainable_patterns = [
        "must always", "never stop", "forever", "always",
        "infinite", "compulsive", "obsessive", "urgent immediately"
    ]

    text_lower = text.lower()
    return not any(pattern in text_lower for pattern in unsustainable_patterns)
