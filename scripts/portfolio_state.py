#!/usr/bin/env python3
"""Decide which repository the hourly portfolio worker acts on next.

`docs/control-plane/openhands/hourly-weaver/2026-11-21-weekly-closure-directive.md`
turns the Hourly Weaver into a three-repository portfolio worker and requires
two artefacts that did not exist: a durable per-repository ledger, and a
deterministic fairness rule ("select the repository with the oldest verified
`last_progress_at` among repositories that have a legal, unblocked task; break
ties Sonata -> FSN -> Arkadia").

Fairness cannot be reconstructed from session memory, so it has to be derived
from something durable. This module is the offline half: it validates the two
committed artefacts and recomputes the selection from them, so a hand edit, a
dropped repository, or an abbreviated SHA fails in CI instead of silently
changing which repository the worker visits.

Two files, deliberately separate:

* ``portfolio-state.json`` is **derived** -- every field is measured from
  GitHub by ``scripts/portfolio_state_refresh.py``. Nothing in it is typed by
  hand, so it cannot drift from the authority that produced it.
* ``portfolio-cursor.json`` is **authored** -- phase, active item, blockers and
  the next legal task are judgements, not measurements.

Mixing the two is what makes a ledger drift: a derived field that a human may
edit has no oracle. Keeping them apart lets ``findings()`` check the derived
file against its own arithmetic (`last_progress_at` must equal the maximum of
the observed activity timestamps) without needing the network.

`last_progress_at` is derived from *repository activity* only, never from
"the worker ran a pulse". A pulse that produced nothing did not progress, and
letting a no-op pulse reset the clock is how a stalled repository is starved
forever -- the exact failure this fairness rule exists to prevent.

"Repository activity" has to mean *push-bearing* activity, which is why the
clock reads `pushed_at` and not a pull request's `updated_at`. GitHub moves
`updated_at` on a comment, a label or a title edit, so a pulse that merely talks
about a repository would reset the very clock the fairness rule reads. Measured
2026-11-27 at `main` `8f746f9e`: PR #741 carried `updated_at`
`2026-11-26T08:37:43Z` against a head commit of `2026-11-25T22:13:53Z` -- 10h24m
of apparent progress whose only cause was the `commented` timeline event at that
exact second (#747: 1h13m, same cause). `pushed_at` cannot be moved that way, so
it is the clock; `latest_open_pull.updated_at` is recorded for a reviewer and is
deliberately not an input.

Usage:
    python scripts/portfolio_state.py --check      # validate, exit 1 on findings
    python scripts/portfolio_state.py --select     # print the next repository

Exit codes: 0 clean, 1 findings, 2 the artefacts are unreadable.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOURLY_DIR = REPO / "docs" / "control-plane" / "openhands" / "hourly-weaver"
STATE_PATH = HOURLY_DIR / "portfolio-state.json"
CURSOR_PATH = HOURLY_DIR / "portfolio-cursor.json"

STATE_SCHEMA = "arkadia.portfolio-state/1.1"
CURSOR_SCHEMA = "arkadia.portfolio-cursor/1.0"

# The authorized repository set, in the directive's tie-break order
# (Sonata -> FSN -> Arkadia). Order is load-bearing: it is the tie-break, so it
# is data rather than a set.
CANONICAL_REPOS: tuple[str, ...] = (
    "Arkadia-Oversoul-Prism/sonata",
    "Arkadia-Oversoul-Prism/family-safety-network",
    "Arkadia-Oversoul-Prism/Arkadia",
)

# An observation is the worker's confidence that the row describes live state.
OBSERVATIONS = ("VERIFIED", "UNKNOWN", "BLOCKED")

_SHA = re.compile(r"^[0-9a-f]{40}$")
_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


def parse_iso(value: str) -> datetime.datetime:
    """Parse a GitHub UTC timestamp, with or without fractional seconds."""
    parsed = datetime.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=datetime.timezone.utc)


def last_progress_at(row: dict) -> str | None:
    """The verified progress timestamp: the latest *push-bearing* activity.

    Only measured activity counts. A cursor's ``last_pulse_at`` is deliberately
    excluded -- see the module docstring.

    ``latest_open_pull.updated_at`` is excluded as well, and that exclusion is
    the point: GitHub advances it on a comment, so including it lets a
    conversation reset a repository's fairness clock (measured on #741 and
    #747 -- see the module docstring). ``pushed_at`` is the widest push-bearing
    signal available without one request per open pull.
    """
    candidates = []
    if row.get("head_committed_at"):
        candidates.append(row["head_committed_at"])
    if row.get("pushed_at"):
        candidates.append(row["pushed_at"])
    if not candidates:
        return None
    return max(candidates, key=parse_iso)


def cursor_rows(cursor: dict) -> dict[str, dict]:
    return {
        row["repository"]: row
        for row in cursor.get("repositories", [])
        if isinstance(row, dict) and isinstance(row.get("repository"), str)
    }


def select_next(state: dict, cursor: dict) -> dict:
    """The deterministic next repository, or an explicit refusal.

    A row is a candidate only when it was VERIFIED and the cursor does not
    declare it blocked with a legal task outstanding. Everything else is
    reported by name, so a refusal is auditable rather than silent.
    """
    rows = {row["repository"]: row for row in state.get("repositories", [])}
    authored = cursor_rows(cursor)
    eligible: list[tuple[datetime.datetime, int, str]] = []
    skipped: list[str] = []

    for index, name in enumerate(CANONICAL_REPOS):
        row = rows.get(name)
        if row is None:
            skipped.append(f"{name}: absent from the ledger")
            continue
        if row.get("observation") != "VERIFIED":
            skipped.append(f"{name}: observation is {row.get('observation')}")
            continue
        entry = authored.get(name)
        if entry is None:
            skipped.append(f"{name}: no cursor row")
            continue
        if entry.get("blocked"):
            skipped.append(f"{name}: blocked by the cursor")
            continue
        if not (entry.get("next_legal_task") or "").strip():
            skipped.append(f"{name}: no legal task recorded")
            continue
        progress = row.get("last_progress_at")
        if not progress:
            skipped.append(f"{name}: no verified progress timestamp")
            continue
        eligible.append((parse_iso(progress), index, name))

    if not eligible:
        return {
            "repository": None,
            "reason": "no eligible repository: " + "; ".join(skipped),
            "skipped": skipped,
        }

    eligible.sort()
    stamp, _, name = eligible[0]
    return {
        "repository": name,
        "reason": (
            f"oldest verified last_progress_at among unblocked repositories "
            f"({stamp.strftime('%Y-%m-%dT%H:%M:%SZ')}); tie-break order "
            f"Sonata -> FSN -> Arkadia"
        ),
        "skipped": skipped,
    }


def _check_row(row: dict) -> list[str]:
    problems: list[str] = []
    name = row.get("repository", "<unnamed>")
    for field, kind in (
        ("default_branch", str),
        ("head_sha", (str, type(None))),
        ("head_committed_at", (str, type(None))),
        ("pushed_at", (str, type(None))),
        ("open_pulls", int),
        ("open_issues", int),
        ("latest_open_pull", (dict, type(None))),
        ("last_progress_at", (str, type(None))),
        ("observation", str),
        ("detail", str),
    ):
        if not isinstance(row.get(field), kind):
            problems.append(f"{name}: field {field!r} missing or wrong type")
    if row.get("observation") not in OBSERVATIONS:
        problems.append(
            f"{name}: observation {row.get('observation')!r} not in {OBSERVATIONS}"
        )
    sha = row.get("head_sha")
    if sha is not None and not (isinstance(sha, str) and _SHA.match(sha)):
        problems.append(
            f"{name}: head_sha must be a full 40-character sha, got {sha!r}"
        )
    for field in ("head_committed_at", "pushed_at", "last_progress_at"):
        value = row.get(field)
        if value is not None and not (isinstance(value, str) and _ISO.match(value)):
            problems.append(f"{name}: {field} must be UTC ISO-8601 ending in Z")
    latest = row.get("latest_open_pull")
    if isinstance(latest, dict):
        if not isinstance(latest.get("number"), int):
            problems.append(f"{name}: latest_open_pull.number must be an int")
        # Descriptive only: recorded so a reviewer can see which pull was
        # touched, never an input to the fairness clock (see last_progress_at).
        updated = latest.get("updated_at")
        if not (isinstance(updated, str) and _ISO.match(updated)):
            problems.append(f"{name}: latest_open_pull.updated_at must be UTC ISO-8601")
    if row.get("observation") == "VERIFIED":
        # A "verified" row with no head is the shape a hardcoded `main` produces
        # for a repository whose default branch is something else. `pushed_at`
        # belongs in this list because it is the fairness clock's only input.
        for field in ("default_branch", "head_sha", "head_committed_at", "pushed_at"):
            if not row.get(field):
                problems.append(
                    f"{name}: observation is VERIFIED but {field} is empty"
                )
    for field in ("open_pulls", "open_issues"):
        value = row.get(field)
        if isinstance(value, int) and value < 0:
            problems.append(f"{name}: {field} cannot be negative")
    # The fairness input must be the arithmetic result, not a typed value.
    expected = last_progress_at(row)
    if row.get("last_progress_at") != expected:
        problems.append(
            f"{name}: last_progress_at {row.get('last_progress_at')!r} is not the "
            f"maximum observed activity {expected!r}"
        )
    return problems


def findings(state: dict, cursor: dict) -> list[str]:
    """Every reason the committed artefacts do not support the selection."""
    problems: list[str] = []

    if state.get("schema") != STATE_SCHEMA:
        problems.append(f"state schema is {state.get('schema')!r}, expected {STATE_SCHEMA!r}")
    if not (isinstance(state.get("derived_at"), str) and _ISO.match(state["derived_at"])):
        problems.append("state derived_at must be UTC ISO-8601 ending in Z")

    rows = state.get("repositories")
    if not isinstance(rows, list):
        problems.append("state repositories must be a list")
        return problems
    names = [row.get("repository") for row in rows if isinstance(row, dict)]
    for name in CANONICAL_REPOS:
        if name not in names:
            problems.append(f"state is missing the canonical repository {name}")
    for name in names:
        if name not in CANONICAL_REPOS:
            problems.append(f"state carries a non-canonical repository {name!r}")
    if len(names) != len(set(names)):
        problems.append("state repeats a repository")
    for row in rows:
        if isinstance(row, dict):
            problems.extend(_check_row(row))

    if cursor.get("schema") != CURSOR_SCHEMA:
        problems.append(
            f"cursor schema is {cursor.get('schema')!r}, expected {CURSOR_SCHEMA!r}"
        )
    authored = cursor.get("repositories")
    if not isinstance(authored, list):
        problems.append("cursor repositories must be a list")
        return problems
    seen = set()
    for entry in authored:
        if not isinstance(entry, dict):
            problems.append("cursor carries a non-object row")
            continue
        name = entry.get("repository")
        if name not in CANONICAL_REPOS:
            problems.append(f"cursor names a non-canonical repository {name!r}")
            continue
        if name in seen:
            problems.append(f"cursor repeats {name}")
        seen.add(name)
        for field in ("phase", "next_legal_task"):
            if not isinstance(entry.get(field), str):
                problems.append(f"cursor {name}: field {field!r} must be a string")
        if not isinstance(entry.get("blocked"), bool):
            problems.append(f"cursor {name}: field 'blocked' must be a bool")
        if not isinstance(entry.get("blockers"), list):
            problems.append(f"cursor {name}: field 'blockers' must be a list")
        pulse = entry.get("last_pulse_at")
        if pulse is not None and not (isinstance(pulse, str) and _ISO.match(pulse)):
            problems.append(f"cursor {name}: last_pulse_at must be UTC ISO-8601")
    for name in CANONICAL_REPOS:
        if name not in seen:
            problems.append(f"cursor is missing the canonical repository {name}")

    recorded = state.get("selection") or {}
    recomputed = select_next(state, cursor)
    if recorded.get("repository") != recomputed["repository"]:
        problems.append(
            f"recorded selection {recorded.get('repository')!r} is not the "
            f"recomputed selection {recomputed['repository']!r}"
        )
    return problems


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate the artefacts")
    parser.add_argument("--select", action="store_true", help="print the next repository")
    parser.add_argument("--state", type=Path, default=STATE_PATH)
    parser.add_argument("--cursor", type=Path, default=CURSOR_PATH)
    args = parser.parse_args(argv)

    try:
        state = load(args.state)
        cursor = load(args.cursor)
    except (OSError, ValueError) as exc:
        print(f"UNREADABLE: {exc}", file=sys.stderr)
        return 2

    selection = select_next(state, cursor)
    if args.select or not args.check:
        print(json.dumps(selection, indent=2))
    if args.check:
        problems = findings(state, cursor)
        if problems:
            for problem in problems:
                print(f"FINDING {problem}")
            return 1
        print(
            "portfolio state PASS "
            f"({len(state['repositories'])} repositories, next: {selection['repository']})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
