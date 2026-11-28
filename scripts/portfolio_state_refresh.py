#!/usr/bin/env python3
"""Derive the portfolio ledger from live GitHub state.

``portfolio-state.json`` must be measured, never typed. This is the only thing
allowed to write it, so a row can always be traced to the request that produced
it -- the failure mode ``scripts/lane_state_refresh.py`` exists to prevent, in
the portfolio's shape.

Two properties are load-bearing and each has a test:

1. **The default branch is read, not assumed.** Measured 2026-11-26:
   ``Arkadia-Oversoul-Prism/sonata`` has ``default_branch ==
   "feature/sonata-tts-app"``, and ``GET /repos/.../commits/main`` answers
   ``422 No commit found for SHA: main``. A portfolio tool that hardcodes
   ``main`` therefore records no head for Sonata -- a repository silently
   dropped from the ledger while the tool reports success.
2. **A failed observation is recorded, not omitted.** The directive requires
   that a permission or access failure never cause a repository to disappear
   from the ledger. A row that could not be measured is written with
   ``observation: "UNKNOWN"`` and a ``detail``, and ``select_next`` refuses to
   choose it.

Read-only: ``GET`` only, no mutation, and the token is never printed or
included in any output field. Writes exactly one file, and only with
``--write``; the default invocation is a dry run.

Cross-repository access needs a token that can read all three repositories. A
repository-scoped ``GITHUB_TOKEN`` in CI cannot, so CI runs the offline guard
(``scripts/portfolio_state.py --check``) and this refresh stays an operator
command. That limitation is recorded rather than papered over with a gate that
would be permanently red.

Usage:
    python scripts/portfolio_state_refresh.py            # dry run
    python scripts/portfolio_state_refresh.py --write    # rewrite the ledger
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from portfolio_state import (
    CANONICAL_REPOS,
    CURSOR_PATH,
    REPO as REPO_ROOT,
    STATE_PATH,
    STATE_SCHEMA,
    last_progress_at,
    select_next,
)

API = "https://api.github.com"


def _token() -> str | None:
    return os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")


def _get(url: str, token: str | None, timeout: float = 30.0):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "arkadia-portfolio-state",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def observe(repository: str, get=_get, token: str | None = None) -> dict:
    """Measure one repository, or record why it could not be measured."""
    row = {
        "repository": repository,
        "default_branch": None,
        "head_sha": None,
        "head_committed_at": None,
        "pushed_at": None,
        "open_pulls": 0,
        "open_issues": 0,
        "latest_open_pull": None,
        "last_progress_at": None,
        "observation": "UNKNOWN",
        "detail": "",
    }
    try:
        meta = get(f"{API}/repos/{repository}", token)
        branch = meta["default_branch"]
        row["default_branch"] = branch
        # The fairness clock. Push-bearing only -- see last_progress_at().
        row["pushed_at"] = meta.get("pushed_at")
        commit = get(f"{API}/repos/{repository}/commits/{urllib.parse.quote(branch)}", token)
        row["head_sha"] = commit["sha"]
        row["head_committed_at"] = commit["commit"]["committer"]["date"]

        pulls = get(f"{API}/repos/{repository}/pulls?state=open&per_page=100", token)
        row["open_pulls"] = len(pulls)
        if pulls:
            # Descriptive only. `updated_at` advances on a comment, so it is
            # recorded for review but is not a progress input.
            newest = max(pulls, key=lambda pull: pull["updated_at"])
            row["latest_open_pull"] = {
                "number": newest["number"],
                "updated_at": newest["updated_at"],
            }
        # One page of 100. A repository with more open issues than that would be
        # undercounted silently, so the truncation is recorded instead.
        issues = get(f"{API}/repos/{repository}/issues?state=open&per_page=100", token)
        row["open_issues"] = sum(1 for issue in issues if "pull_request" not in issue)
        if len(issues) == 100:
            row["detail"] = "open issues truncated at the first 100"
        row["observation"] = "VERIFIED"
    except (urllib.error.HTTPError, urllib.error.URLError, OSError, KeyError, ValueError) as exc:
        # The status, not the body: a response body can echo request context.
        status = getattr(exc, "code", None)
        row["detail"] = f"{type(exc).__name__}" + (f" (HTTP {status})" if status else "")
    row["last_progress_at"] = last_progress_at(row)
    return row


def build(rows: list[dict], cursor: dict, now: datetime.datetime | None = None) -> dict:
    stamp = (now or datetime.datetime.now(datetime.timezone.utc)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    state = {
        "schema": STATE_SCHEMA,
        "derived_at": stamp,
        "authority": (
            "read-only observation; GET only. Not a merge, deployment or acceptance record."
        ),
        "repositories": rows,
    }
    state["selection"] = select_next(state, cursor)
    return state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="rewrite the ledger")
    parser.add_argument("--state", type=Path, default=STATE_PATH)
    parser.add_argument("--cursor", type=Path, default=CURSOR_PATH)
    args = parser.parse_args(argv)

    token = _token()
    if not token:
        print("NO TOKEN: set GH_TOKEN or GITHUB_TOKEN", file=sys.stderr)
        return 2
    try:
        cursor = json.loads(args.cursor.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"UNREADABLE cursor: {exc}", file=sys.stderr)
        return 2

    rows = [observe(name, token=token) for name in CANONICAL_REPOS]
    state = build(rows, cursor)

    for row in rows:
        print(
            f"{row['repository']}: {row['observation']} "
            f"branch={row['default_branch']} head={(row['head_sha'] or '')[:12]} "
            f"pulls={row['open_pulls']} issues={row['open_issues']} "
            f"progress={row['last_progress_at']}"
            + (f" detail={row['detail']}" if row["detail"] else "")
        )
    print(f"next: {state['selection']['repository']} -- {state['selection']['reason']}")

    if not args.write:
        return 0
    args.state.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    try:
        shown = args.state.resolve().relative_to(REPO_ROOT)
    except ValueError:
        shown = args.state
    print(f"wrote {shown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
