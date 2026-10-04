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

# pytest's trailing summary line, e.g.
#   `9 failed, 1417 passed, 20 skipped, 32 warnings, 1 error in 126.64s`
# This is ground truth for how many nodes pytest reported. It matters because the
# recommended invocation (`-rf`) omits ERROR summary lines: a collection error is then
# invisible to `extract`, and the fingerprint silently describes a *subset* of the debt.
#
# Anchored on the `in <n>s` duration pytest always appends (optionally followed by a
# `(H:MM:SS)` wall-clock suffix), so a synthetic fragment like `1 failed, 2 passed`
# (used to prove summary lines are not outcome lines) is not mistaken for a summary.
_SUMMARY_SHAPE_RE = re.compile(
    r"\bin \d+(?:\.\d+)?s\b(?:\s*\(\d+:\d+:\d+\))?\s*$"
)
_SUMMARY_FAILED_RE = re.compile(r"(\d+) failed")
_SUMMARY_ERROR_RE = re.compile(r"(\d+) errors?")


def summary_counts(text: str) -> tuple[int, int] | None:
    """Return (failed, errors) from pytest's trailing summary line, or None.

    The last line shaped like pytest's summary (a `in <n>s` duration, optionally
    followed by a wall-clock suffix) is the summary.
    """
    for line in reversed(text.splitlines()):
        line = line.rstrip()
        if not _SUMMARY_SHAPE_RE.search(line):
            continue
        failed = _SUMMARY_FAILED_RE.search(line)
        errors = _SUMMARY_ERROR_RE.search(line)
        return (int(failed.group(1)) if failed else 0, int(errors.group(1)) if errors else 0)
    return None


def extract(path: str) -> tuple[list[str], list[str]]:
    """Return (outcomes, ids) in sorted order from a pytest log file.

    Raises ``ValueError`` when pytest's summary line reports more failures or errors
    than the log carries `FAILED`/`ERROR` lines for. That is the signature of a run
    made with `-rf` instead of `-rEf`: pytest then omits ERROR summary lines, so a
    collection error is invisible and the fingerprint would describe a *subset* of the
    repository's debt while looking well-formed.
    """
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()

    outcomes: list[str] = []
    ids: list[str] = []
    for line in text.splitlines():
        m = OUTCOME_RE.match(line.rstrip("\n"))
        if not m:
            continue
        outcome, nodeid = m.group(1), m.group(2)
        outcomes.append(f"{outcome} {nodeid}")
        ids.append(nodeid)

    counts = summary_counts(text)
    if counts is not None:
        failed, errors = counts
        parsed_failed = sum(1 for o in outcomes if o.startswith("FAILED"))
        parsed_errors = sum(1 for o in outcomes if o.startswith("ERROR"))
        if parsed_failed < failed or parsed_errors < errors:
            raise ValueError(
                f"{path}: summary reports {failed} failed / {errors} error(s), but the "
                f"log carries {parsed_failed} FAILED / {parsed_errors} ERROR line(s). "
                "Re-run with `-rEf`; `-rf` alone suppresses ERROR summary lines and would "
                "fingerprint a subset of the debt."
            )

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
