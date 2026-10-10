"""Canonical revision-metadata semantics for Arkadia's deployment identity (ADR-016).

There is exactly ONE definition of what counts as an absent, placeholder,
invalid, or genuine revision identifier. It is shared by both halves of the
runtime-revision probe:

* ``api/version_routes.py``     - the read-only ``GET /api/version`` surface
* ``scripts/version_reconciliation.py`` - the source-to-runtime comparison

Before this module the two carried independent absence vocabularies, so they
disagreed: the endpoint treated only a lowercase ``unknown`` as absent while the
reconciliation utility also accepted ``none``/``""``/``None``. A placeholder such
as ``N/A`` was therefore reported as present metadata and then escalated to
``MISMATCH``, i.e. presented as deployment drift when the truth was "revision
metadata was never configured". One policy removes that disagreement.

Pure stdlib, no fastapi/httpx import, so it loads standalone and in tests (the
same discipline as ``kernel/stellar.py``). Layer 2 runtime core: ``api`` (layer 1)
may import it; it must never import the api layer.
"""

from __future__ import annotations

import re
from typing import Any

# Candidate environment variables that may carry a source revision, in
# precedence order. The first entry yielding a *valid* revision wins.
REVISION_ENV_VARS: tuple[str, ...] = (
    "ARKADIA_SOURCE_REVISION",
    "RENDER_GIT_COMMIT",
    "GIT_COMMIT",
    "GIT_SHA",
    "SOURCE_VERSION",
)

# The two sources whose disagreement is a diagnosable conflict, rather than a
# simple precedence decision. A baked build argument and a provider-injected
# commit describe the same build; if both are valid and differ, one of them is
# describing a revision that was not built.
CONFLICT_SOURCE_PAIR: tuple[str, ...] = (
    "ARKADIA_SOURCE_REVISION",
    "RENDER_GIT_COMMIT",
)

# The single canonical "no usable revision metadata" value. Reported verbatim by
# the endpoint and accepted by the reconciliation utility.
ABSENT_REVISION = "unknown"

# Values that mean "no revision recorded", regardless of case or surrounding
# whitespace. Deliberately explicit and documented: this set is the definition
# of absence, so widening it is a contract change, not a convenience.
PLACEHOLDER_TOKENS: frozenset[str] = frozenset(
    {
        "",
        "unknown",
        "none",
        "null",
        "nil",
        "n/a",
        "na",
        "not available",
        "notavailable",
        "unset",
        "undefined",
        "-",
        "--",
        "?",
        "tbd",
        "placeholder",
    }
)

# Git abbreviations are 7..40 hexadecimal characters; a full object name is 40.
_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")

# Classification results.
REVISION = "revision"
PLACEHOLDER = "placeholder"
INVALID = "invalid"
ABSENT = "absent"

REVISION_FORMAT = "7-40 hexadecimal characters (a Git object name or abbreviation)"


def normalize(value: Any) -> str:
    """Return the canonical comparison form of ``value``.

    Leading/trailing whitespace is trimmed, internal whitespace runs collapse to
    a single space, and case is folded. A SHA has no internal whitespace and
    case-insensitive hex digits, so a tag, a padded value, and an upper-case SHA
    all normalize predictably. Non-string values normalize to ``""``.
    """
    if not isinstance(value, str):
        return ""
    return " ".join(value.split()).casefold()


def is_placeholder(value: Any) -> bool:
    """True when ``value`` denotes absent metadata rather than a revision."""
    return normalize(value) in PLACEHOLDER_TOKENS


def is_revision(value: Any) -> bool:
    """True only for a genuine Git revision identifier (7-40 hex characters)."""
    return bool(_SHA_RE.match(normalize(value)))


def classify(value: Any) -> str:
    """Classify a raw revision candidate.

    Returns one of ``REVISION`` (a usable Git identifier), ``ABSENT`` (nothing
    supplied), ``PLACEHOLDER`` (an explicitly documented "no value" token), or
    ``INVALID`` (something was supplied but it is not a Git identifier, e.g. a
    branch or tag name, or a truncated SHA).

    ``ABSENT``/``PLACEHOLDER``/``INVALID`` are all *unavailable evidence* and
    must never be treated as a match; only two ``REVISION`` values that differ
    are evidence of genuine drift.
    """
    token = normalize(value)
    if token in PLACEHOLDER_TOKENS:
        return ABSENT if token == "" else PLACEHOLDER
    return REVISION if _SHA_RE.match(token) else INVALID


def describe(value: Any) -> str:
    """Human-readable reason a value is not usable, for operator diagnostics.

    Never echoes the raw value: an unusable value may be a misconfiguration and
    only its shape is needed to diagnose it.
    """
    status = classify(value)
    if status == REVISION:
        return "valid revision identifier"
    if status == ABSENT:
        return "absent (no value supplied)"
    if status == PLACEHOLDER:
        return "placeholder (explicitly no revision recorded)"
    return "invalid (not 7-40 hexadecimal characters)"
