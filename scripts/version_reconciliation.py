#!/usr/bin/env python3
"""Source-to-runtime revision reconciliation (ADR-016).

Compares the revision a running Arkadia deployment reports via
``GET /api/version`` against an intended source revision. It is a
**consistency check only**:

* a match is *necessary* evidence that the runtime corresponds to the source,
  but it is **not** proof the application is functioning correctly;
* a match is **not** deployment acceptance — that remains a human act;
* this tool cannot describe an already-running deployment that predates the
  ``/api/version`` endpoint.

Read-only. Standard library only. No mutation, no credential, and it never
prints anything other than the revision values it is given.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request

# Verdicts.
MATCH = "MATCH"
MISMATCH = "MISMATCH"
UNKNOWN = "UNKNOWN"
BLOCKED = "BLOCKED"

# Exit codes.
_EXIT = {MATCH: 0, MISMATCH: 1, UNKNOWN: 2, BLOCKED: 3}

_ABSENT = {"", "unknown", "none", None}


def compare(expected: str | None, reported: str | None) -> str:
    """Classify the relationship between an intended and a reported revision.

    Fail-closed: any missing or placeholder value yields ``UNKNOWN`` rather than
    a spurious ``MATCH``.
    """
    if expected in _ABSENT or reported in _ABSENT:
        return UNKNOWN
    return MATCH if str(expected).strip() == str(reported).strip() else MISMATCH


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


def fetch_reported_revision(base_url: str, timeout: float) -> tuple[str, str | None]:
    """Return ``(verdict_hint, revision)`` for ``GET {base}/api/version``.

    ``verdict_hint`` is ``BLOCKED`` when the endpoint cannot be read, otherwise
    the caller compares the returned revision.
    """
    url = base_url.rstrip("/") + "/api/version"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310
            if response.status != 200:
                return BLOCKED, None
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError, UnicodeDecodeError):
        return BLOCKED, None
    if not isinstance(payload, dict):
        return BLOCKED, None
    revision = payload.get("source_revision")
    return "OK", revision if isinstance(revision, str) else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="Deployment origin, e.g. https://host")
    parser.add_argument("--expected", default=None, help="Intended source revision (default: git HEAD)")
    parser.add_argument("--timeout", type=float, default=15.0, help="HTTP timeout in seconds")
    args = parser.parse_args(argv)

    expected = args.expected or git_head_revision()
    hint, reported = fetch_reported_revision(args.base_url, args.timeout)

    if hint == BLOCKED:
        verdict = BLOCKED
    else:
        verdict = compare(expected, reported)

    print(f"base_url:         {args.base_url}")
    print(f"expected revision: {expected or 'unknown'}")
    print(f"reported revision: {reported if reported is not None else 'unreachable'}")
    print(f"verdict:          {verdict}")
    print("note: revision consistency is necessary evidence, not deployment acceptance.")
    return _EXIT.get(verdict, _EXIT[BLOCKED])


if __name__ == "__main__":
    sys.exit(main())
