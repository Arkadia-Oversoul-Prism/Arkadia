#!/usr/bin/env python3
"""Source-to-runtime revision reconciliation (ADR-016).

Compares the revision a running Arkadia deployment reports via
``GET /api/version`` against an intended source revision. It is a
**consistency check only**:

* a match is *necessary* evidence that the runtime corresponds to the source,
  but it is **not** proof the application is functioning correctly;
* a match is **not** deployment acceptance - that remains a human act;
* this tool cannot describe an already-running deployment that predates the
  ``/api/version`` endpoint.

Verdicts, and what each one means:

``MATCH``
    Both sides are valid Git revision identifiers and they agree.
``MISMATCH``
    Both sides are valid Git revision identifiers and they differ: genuine drift.
``UNKNOWN``
    Evidence is unavailable or unusable - missing, placeholder, or non-SHA
    metadata on either side, or an invalid value in a reported revision source.
    This is deliberately distinct from ``MISMATCH``: it must never be read as
    evidence of drift, and never as evidence of correspondence.
``CONFLICT``
    The deployment reports two valid revision sources that disagree with each
    other, so its own revision provenance is self-contradictory. Fail closed:
    this cannot be a match.
``BLOCKED``
    The endpoint could not be read as revision evidence (unreachable, non-200,
    or not the expected JSON object).

Absence and placeholder semantics live in ``kernel.revision_identity`` and are
shared with ``api/version_routes.py``, so the two cannot disagree about what
"absent" means.

Read-only. No mutation, no credential, and it never prints anything other than
the revision values it is given.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

# The script is executable directly (`python scripts/version_reconciliation.py`),
# so the repository root must be importable before `kernel` is resolved.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kernel.revision_identity import (  # noqa: E402
    CONFLICT_SOURCE_PAIR,
    INVALID,
    REVISION,
    classify,
    describe,
    normalize,
)

# Verdicts.
MATCH = "MATCH"
MISMATCH = "MISMATCH"
UNKNOWN = "UNKNOWN"
BLOCKED = "BLOCKED"
CONFLICT = "CONFLICT"

# Exit codes.
_EXIT = {MATCH: 0, MISMATCH: 1, UNKNOWN: 2, BLOCKED: 3, CONFLICT: 4}

_NOTE = "note: revision consistency is necessary evidence, not deployment acceptance."


def compare(expected: str | None, reported: str | None, *, conflict: bool = False) -> str:
    """Classify the relationship between an intended and a reported revision.

    Fail-closed: absent, placeholder, and invalid values yield ``UNKNOWN`` rather
    than a spurious ``MATCH``. Two identity-providing sources that disagree yield
    ``CONFLICT``, never ``MATCH``. Only two valid revision identifiers can produce
    ``MATCH`` or ``MISMATCH``.

    A non-revision value never produces ``MATCH`` even when both sides carry the
    identical placeholder - ``compare("UNKNOWN", "UNKNOWN")`` is ``UNKNOWN``, not
    ``MATCH``.
    """
    if conflict:
        return CONFLICT
    if classify(expected) != REVISION or classify(reported) != REVISION:
        return UNKNOWN
    return MATCH if normalize(expected) == normalize(reported) else MISMATCH


def explain(expected: str | None, reported: str | None, *, conflict: bool = False) -> str:
    """Return the operator-facing reason behind a verdict, without echoing raw values."""
    if conflict:
        return "conflicting valid revision sources reported by the deployment"
    expected_status = classify(expected)
    reported_status = classify(reported)
    if expected_status != REVISION and reported_status != REVISION:
        return f"unusable evidence on both sides (expected: {describe(expected)}; reported: {describe(reported)})"
    if expected_status != REVISION:
        return f"unusable expected revision ({describe(expected)})"
    if reported_status != REVISION:
        return f"unusable reported revision ({describe(reported)})"
    return "both sides are valid revision identifiers"


def git_head_revision() -> str | None:
    """Return the working tree's HEAD revision, or ``None`` if unavailable."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    value = out.stdout.strip()
    return value or None


def fetch_reported_evidence(base_url: str, timeout: float) -> dict:
    """Return the revision evidence reported by ``GET {base}/api/version``.

    The return value always carries a ``verdict_hint``:

    * ``BLOCKED`` - the endpoint could not be read as revision evidence at all
      (unreachable, non-200, non-JSON such as an HTML rewrite, or not a JSON
      object). ``revision`` is ``None`` and ``conflict`` is ``False``.
    * ``"OK"``    - a JSON object was read; the caller compares ``revision`` and
      honours ``conflict``.

    An HTML body is explicitly *not* accepted as revision evidence: a static host
    that rewrites unknown paths to ``index.html`` answers ``200`` with HTML, which
    must read as blocked rather than as an absent revision.
    """
    url = base_url.rstrip("/") + "/api/version"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310
            if response.status != 200:
                return {"verdict_hint": BLOCKED, "revision": None, "conflict": False, "sources": {}}
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError, UnicodeDecodeError):
        return {"verdict_hint": BLOCKED, "revision": None, "conflict": False, "sources": {}}
    if not isinstance(payload, dict):
        return {"verdict_hint": BLOCKED, "revision": None, "conflict": False, "sources": {}}
    revision = payload.get("source_revision")
    raw_sources = payload.get("revision_sources")
    sources = raw_sources if isinstance(raw_sources, dict) else {}
    return {
        "verdict_hint": "OK",
        "revision": revision if isinstance(revision, str) else None,
        "conflict": payload.get("revision_conflict") is True,
        "sources": sources,
    }


def invalid_reported_sources(sources: dict) -> list[str]:
    """Names of reported revision sources carrying an unusable (non-SHA, non-placeholder) value.

    A source holding a tag, a truncated SHA, or a mangled value means the
    deployment's revision channel is misconfigured, so its evidence is not
    trustworthy enough to report correspondence. Absent and placeholder values
    are *expected* (the build argument defaults to empty) and are not listed.
    """
    if not isinstance(sources, dict):
        return []
    bad: list[str] = []
    for name in CONFLICT_SOURCE_PAIR:
        entry = sources.get(name)
        if isinstance(entry, dict) and entry.get("status") == INVALID:
            bad.append(name)
    return bad


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="Deployment origin, e.g. https://host")
    parser.add_argument("--expected", default=None, help="Intended source revision (default: git HEAD)")
    parser.add_argument("--timeout", type=float, default=15.0, help="HTTP timeout in seconds")
    args = parser.parse_args(argv)

    expected = args.expected or git_head_revision()
    evidence = fetch_reported_evidence(args.base_url, args.timeout)
    reported = evidence["revision"]
    bad_sources = invalid_reported_sources(evidence["sources"])

    if evidence["verdict_hint"] == BLOCKED:
        verdict = BLOCKED
        reason = "endpoint could not be read as revision evidence"
    elif evidence["conflict"]:
        verdict = CONFLICT
        reason = explain(expected, reported, conflict=True)
    elif bad_sources:
        verdict = UNKNOWN
        reason = "reported metadata carries an invalid value in: " + ", ".join(bad_sources)
    else:
        verdict = compare(expected, reported)
        reason = explain(expected, reported)

    print(f"base_url:         {args.base_url}")
    print(f"expected revision: {expected if expected is not None else 'unknown'}")
    print(f"reported revision: {reported if reported is not None else 'unreachable'}")
    if evidence["sources"]:
        for name, entry in evidence["sources"].items():
            status = entry.get("status") if isinstance(entry, dict) else None
            print(f"  source {name}: {status}")
    print(f"revision_conflict: {bool(evidence['conflict'])}")
    print(f"reason:           {reason}")
    print(f"verdict:          {verdict}")
    print(_NOTE)
    return _EXIT.get(verdict, _EXIT[BLOCKED])


if __name__ == "__main__":
    sys.exit(main())
