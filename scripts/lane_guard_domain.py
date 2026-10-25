#!/usr/bin/env python3
"""The lane-guard domain — one derivation, two consumers.

The parallel-UI lane substrate (``scripts/lane_state.py``,
``scripts/lane_state_refresh.py``, ``scripts/lane_scope_probe.py`` and the
``lane-state.json`` snapshot) is judged by a set of guards. Two things must
agree on that set:

  * the CI gate, which has to **execute** it, and
  * the wiring judge (``tests/test_lane_currency_ci_wiring.py``), which has to
    **verify** it is executed.

When the gate carries a *fixed* inventory and the judge derives its own, the two
drift apart the moment a guard is added. Measured at ``76f6d87a``: the domain is
**4** guards, the gate executed **3** and filtered **3**. ``#567`` added
``tests/test_lane_guard_scope_boundary.py`` and no filter or step ever named it,
so the acceptance test for the scope repair was executed by nothing -- a guard
that is decoration, and exactly the shape ``#435``/``17988afd`` produced for the
console contract before it was derived.

This module is the single source of truth. The workflow runs

    python -m pytest -q $(python scripts/lane_guard_domain.py)

so its executed inventory is *derived* rather than restated, and the judge
imports :func:`derive_domain` from this same file. A guard added to the corpus is
therefore executed by the gate without editing it, and a guard *removed* from the
corpus drops out of both.

Read-only. Runs no tests, mutates nothing, never prints a token.

Usage:
    python scripts/lane_guard_domain.py            # one path per line
    python scripts/lane_guard_domain.py --json     # machine output

Exit status: 0 on success, 2 on a git/IO fault (fail closed: an empty domain must
never be mistaken for a satisfied contract).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# A guard belongs to the domain when it names the lane substrate. The joined
# spellings are included because guards build the snapshot path with ``Path``
# segments (``"parallel-ui" / "lane-state.json"``), which a slash-only substring
# scan misses.
DOMAIN_NEEDLES = (
    "lane_state",
    "lane_scope_probe",
    "lane-state.json",
)


def tracked_test_paths(repo_root: Path | None = None) -> list[str]:
    """Every tracked test module, repo-relative — the domain is derived from this."""
    root = repo_root or REPO_ROOT
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", "tests/"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise OSError(f"git ls-files failed: {result.stderr.strip()}")
    return sorted(p for p in result.stdout.split("\0") if p)


def read_guard_text(rel: str, repo_root: Path | None = None) -> str:
    """The guard's source, read for the domain needles."""
    root = repo_root or REPO_ROOT
    return (root / rel).read_text(encoding="utf-8", errors="ignore")


def derive_domain(repo_root: Path | None = None) -> list[str]:
    """The lane guards, derived from their content at call time.

    Restating the list anywhere would let it drift from the corpus it claims to
    cover: a new lane guard would be omitted from the gate while the judge stayed
    green.
    """
    domain = []
    for path in tracked_test_paths(repo_root):
        name = Path(path).name
        if not (name.startswith("test_") and name.endswith(".py")):
            continue
        text = read_guard_text(path, repo_root)
        if any(needle in text for needle in DOMAIN_NEEDLES):
            domain.append(path)
    return domain


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print the lane-guard domain (read-only)."
    )
    parser.add_argument("--repo", default=str(REPO_ROOT))
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    try:
        domain = derive_domain(Path(args.repo))
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not domain:
        print("ERROR: lane-guard domain is empty", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"domain": domain, "count": len(domain)}, indent=2))
    else:
        print("\n".join(domain))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
