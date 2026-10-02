#!/usr/bin/env python3
"""Baseline test-debt fingerprint (gate-hygiene).

Turns a full-suite pytest run into a *reproducible* regression fingerprint.

The value this exists to fix: a fingerprint is only usable if an independent
operator can re-derive it. `pytest -q` prints each outcome as

    FAILED tests/x.py::test_y - AssertionError: assert 'a' == 'b'

and truncates that reason to the terminal width. Hashing the printed line
therefore bakes the terminal width into the fingerprint: the same node set
yields a different hash in a 120-column CI job than in an 80-column shell.

Two derivations are supported, and they are deliberately different so a
regression can never be confused with a convention change:

  outcomes (canonical)  "FAILED <nodeid>" / "ERROR <nodeid>", one per line,
                        sorted, trailing newline. Invocation-independent.
  ids (node set only)   "<nodeid>", one per line, sorted, trailing newline.
                        Identical for the same failing *nodes* regardless of
                        whether a node failed or errored.

Read-only. Parses a pytest log; runs no tests and mutates nothing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys

# `FAILED <nodeid> - <truncated reason>` / `ERROR <nodeid>` at line start.
# The nodeid is the first whitespace-delimited token, so everything from the
# reason separator onward is dropped before hashing.
OUTCOME_RE = re.compile(r"^(FAILED|ERROR)\s+(\S+)")


def extract(path: str) -> tuple[list[str], list[str]]:
    """Return (outcomes, ids) in sorted order from a pytest log file."""
    outcomes: list[str] = []
    ids: list[str] = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = OUTCOME_RE.match(line.rstrip("\n"))
            if not m:
                continue
            outcome, nodeid = m.group(1), m.group(2)
            outcomes.append(f"{outcome} {nodeid}")
            ids.append(nodeid)
    return sorted(outcomes), sorted(ids)


def fingerprint(entries: list[str]) -> str:
    return hashlib.sha256(("\n".join(entries) + "\n").encode()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("log", help="pytest log to parse (e.g. the full-suite output)")
    ap.add_argument(
        "--json", action="store_true", help="emit machine-readable output"
    )
    args = ap.parse_args(argv)

    outcomes, ids = extract(args.log)
    result = {
        "log": args.log,
        "nodes": len(ids),
        "failed": sum(1 for o in outcomes if o.startswith("FAILED")),
        "errors": sum(1 for o in outcomes if o.startswith("ERROR")),
        "outcomes_fingerprint": fingerprint(outcomes),
        "ids_fingerprint": fingerprint(ids),
    }

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print("BASELINE TEST-DEBT FINGERPRINT")
    print(f"  log                 : {result['log']}")
    print(f"  failing/error nodes : {result['nodes']} "
          f"({result['failed']} failed, {result['errors']} error)")
    print("  outcomes fingerprint: " + result["outcomes_fingerprint"])
    print("  ids fingerprint     : " + result["ids_fingerprint"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
