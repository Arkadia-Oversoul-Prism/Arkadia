"""
Steward Filter — Decision Hygiene

Enforces sustainability, exit-validity, and action compression.
Blocks identity inflation and symbolic drift.
"""

from typing import Optional


def steward_filter(text: str, strict: bool = True) -> Optional[str]:
    """
    Apply steward filter to output.

    Returns:
    - text if passes filter
    - None if blocks output

    Rules:
    1. Block identity/belief escalation
    2. Block symbolism without action
    3. Block sustainability violations
    """
    if not text or not isinstance(text, str):
        return None

    text_lower = text.lower()

    # Rule 1: Block identity escalation
    forbidden_identity = [
        "divine", "chosen", "ascended", "eternal",
        "oversoul", "god", "transcendent", "immortal",
        "sacred authority", "holy mandate"
    ]
    if any(word in text_lower for word in forbidden_identity):
        return None

    # Rule 2: Block pure symbolism (no action)
    if text_lower.count("symbolism") > 2 and "do" not in text_lower and "act" not in text_lower:
        return None

    # Rule 3: Require action-oriented language for complex outputs
    if len(text) > 200:
        action_words = ["do", "act", "choose", "decide", "maintain", "quit", "release"]
        if not any(word in text_lower for word in action_words):
            return None

    # Rule 4: Check for mythic inflation (if strict mode)
    if strict:
        mythic_words = ["grid", "flame", "node", "resonance", "field"]
        mythic_count = sum(text_lower.count(word) for word in mythic_words)
        if mythic_count > len(text) / 100:  # More than 1% mythic language
            return None

    return text


def compress_to_choices(text: str) -> str:
    """
    Compress output to actionable choices.
    Distills meaning into decision points.
    """
    if not text:
        return ""

    # Keep only sentences with action verbs
    action_verbs = ["do", "choose", "quit", "maintain", "release", "adjust", "continue"]
    lines = text.split("\n")
    compressed = []

    for line in lines:
        if any(verb in line.lower() for verb in action_verbs):
            compressed.append(line)

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
