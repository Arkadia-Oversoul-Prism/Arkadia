#!/usr/bin/env python3
"""The Stellar Cartography guard domain — one derivation, two consumers.

``kernel/stellar.py`` computes the readout served at ``GET /api/stellar-cartography``
and rendered as the console's star-date header. It is also a *second* implementation
of the Ark Date: ``api/main.py::_ark_date`` computes the same coordinate for the rest
of the API, and ``kernel/stellar.py`` states the invariant explicitly

    Mirrors api.main._ark_date exactly; duplicated here to avoid a circular
    import through api.main's heavy dependency tree.

Measured on ``main`` @ ``cb284195`` that claim was enforced nowhere: the only test
that named it (``tests/test_stellar_cartography.py::test_ark_date_in_stellar_matches_
canonical_shape``) asserts the *shape* of the stellar copy, never its equality with
the canonical one, and **no workflow selected** ``kernel/stellar.py`` at all
(``grep -rn "kernel" .github/workflows/`` names only ``kernel/jobs.py`` and
``kernel/worker.py``). A divergence between the two copies would therefore be silent
and user-visible: the header would state one Ark Day while the rest of the API stated
another.

Two things must agree on the guard set that catches that:

  * the CI gate, which has to **execute** it, and
  * the wiring judge (``tests/test_stellar_contract_ci_wiring.py``), which has to
    **verify** it is executed.

A fixed list on either side drifts the moment a guard is added — the failure this
repository has already recorded for the console contract and the economic-seam
engine. This module is the single source of truth: the workflow runs

    python -m pytest -q $(python scripts/stellar_contract_domain.py)

so its executed inventory is *derived* rather than restated, and the judge imports
:func:`derive_domain` from this same file.

Read-only. Runs no tests, mutates nothing, never prints a token.

Usage:
    python scripts/stellar_contract_domain.py            # one path per line
    python scripts/stellar_contract_domain.py --json     # machine output

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

# A guard belongs to the domain when it names the stellar engine. The import
# spellings are matched separately because ``from kernel import stellar`` never
# contains the dotted form.
DOMAIN_NEEDLES = (
    "kernel.stellar",
    "kernel import stellar",
    '"stellar"',
    "'stellar'",
)

# The engine, the canonical half of the parity invariant, and this derivation.
# A gate must be selected by all of them.
SURFACES = (
    "kernel/stellar.py",
    "api/main.py",
    "scripts/stellar_contract_domain.py",
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
    """The stellar-contract guards, derived from their content at call time.

    Restating the list anywhere would let it drift from the corpus it claims to
    cover: a new guard would be omitted from the gate while the judge stayed green.
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
        description="Print the Stellar Cartography guard domain (read-only)."
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
        print("ERROR: stellar-contract domain is empty", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"domain": domain, "count": len(domain)}, indent=2))
    else:
        print("\n".join(domain))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
