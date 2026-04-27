"""SolSpire Phase 3 — safety gate.

MANDATORY rule from the scroll:
    IF task includes money / deletion / irreversible action
    → REQUIRE USER CONFIRMATION

This module is the single source of truth for that decision so the
Task Engine never fires destructive operations on autopilot.
"""
from __future__ import annotations

import re
from typing import Any

# Word patterns that flip the safety gate. Tight on purpose — false negatives
# are a problem, but false positives kill autonomy. Add carefully.
_SENSITIVE_PATTERNS = [
    r"\bdelete\b", r"\bremove\b", r"\bpurge\b", r"\bwipe\b",
    r"\bdestroy\b", r"\bdrop\b",
    r"\bpay\b", r"\bcharge\b", r"\bwithdraw\b", r"\btransfer\b",
    r"\bbuy\b", r"\bpurchase\b", r"\brefund\b",
    r"\bsend\s+(?:money|funds|payment)\b",
    r"\bemail\s+everyone\b", r"\bnotify\s+all\b",
]
_SENSITIVE_RE = re.compile("|".join(_SENSITIVE_PATTERNS), re.IGNORECASE)


def detect_sensitive(*texts: str) -> list[str]:
    """Return the list of distinct trigger words that fired across `texts`."""
    found: list[str] = []
    seen: set[str] = set()
    for t in texts:
        if not isinstance(t, str):
            continue
        for m in _SENSITIVE_RE.finditer(t):
            tok = m.group(0).lower()
            if tok not in seen:
                seen.add(tok)
                found.append(tok)
    return found


def task_is_sensitive(task: dict[str, Any]) -> list[str]:
    """Inspect a single task envelope for sensitive triggers."""
    parts: list[str] = [str(task.get("step", "") or "")]
    params = task.get("input") or task.get("parameters") or {}
    if isinstance(params, dict):
        for v in params.values():
            if isinstance(v, str):
                parts.append(v)
    return detect_sensitive(*parts)


__all__ = ["detect_sensitive", "task_is_sensitive"]
