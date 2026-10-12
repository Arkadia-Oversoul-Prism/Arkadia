#!/usr/bin/env python3
"""The console-contract guard domain — one derivation, two consumers.

The active console (``web/arkadia_console``) and the serving path that fronts it
(``api/frontend_routes.py``) are judged by a set of contract guards. Two things
must agree on that set:

  * the CI gate, which has to **execute** it, and
  * the wiring judge (``tests/test_prism_console_ci_wiring.py``), which has to
    **verify** it is executed.

When the gate carries a *fixed* inventory and the judge derives its own, the two
drift apart the moment a guard is added. Measured on ``main`` @ ``17988afd``:
after PR #435 merged, three new console guards arrived
(``tests/test_knowledge_projects_boundary.py``,
``tests/test_knowledge_timeline_boundary.py``,
``tests/test_prism_opportunity_entry_flow.py``); the gate still ran the twelve it
was written with, so the judge derived a **16**-guard domain, the gate executed
**13**, and ``_complete_gates()`` returned ``[]`` -- the whole console contract
had no complete gate again, silently.

This module is the single source of truth. The workflow runs

    python -m pytest -q $(python scripts/console_contract_domain.py)

so its executed inventory is *derived* rather than restated, and the judge
imports :func:`derive_domain` from this same file. A guard added to the corpus is
therefore executed by the gate without editing it, and a guard *removed* from the
corpus drops out of both.

Read-only. Runs no tests, mutates nothing, never prints a token.

Usage:
    python scripts/console_contract_domain.py            # one path per line
    python scripts/console_contract_domain.py --json     # machine output

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

# A guard belongs to the domain when it names the active console or the serving
# path that fronts it. The joined spellings are included because several guards
# build the path with ``Path`` segments (``"web" / "arkadia_console"``), which a
# slash-only substring scan misses -- measured: it hid 6 of 12 guards.
DOMAIN_NEEDLES = (
    "web/arkadia_console",
    "api/frontend_routes",
    '"arkadia_console"',
    "'arkadia_console'",
    '"frontend_routes"',
    "'frontend_routes'",
)

# The surfaces the guard domain judges; a gate must be selected by these.
SURFACES = ("web/arkadia_console/**", "api/frontend_routes.py")


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
    """The console-contract guards, derived from their content at call time.

    Restating the list anywhere would let it drift from the corpus it claims to
    cover: a new console guard would be omitted from the gate while the judge
    stayed green.
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
        description="Print the console-contract guard domain (read-only)."
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
        print("ERROR: console-contract domain is empty", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"domain": domain, "count": len(domain)}, indent=2))
    else:
        print("\n".join(domain))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
