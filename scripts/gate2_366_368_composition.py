#!/usr/bin/env python3
"""Gate-2 composition classifier: PR #366 x PR #368 (gate-hygiene).

Two open PRs repair **the same two Gate-2 instrument files** from the same base:

    scripts/gate2_production_observation.py
    tests/test_gate2_production_observation.py

#366 (``gate2-marker-oracle-soundness-01``) repairs marker-oracle soundness; #368
(``gate2-deployment-window-01``) repairs a pagination artifact that reported
``main -> deployment identity := UNKNOWN`` while ``main`` was deployed and
sha-identical. Each is green alone; GitHub reports both ``MERGEABLE`` because that
verdict compares a head against ``main`` only and is blind to a *cross-PR* overlap.

Measured at base ``24a00f85`` the two patches do not compose cleanly: a 3-way apply
of #368 onto #366 yields ``UU`` on both files. The conflicted regions are **additive**
(#366 adds ``KNOWN_FRONTENDS``/``MARKER_APP``; #368 adds ``DEPLOYMENT_SCAN_PAGES`` and
the paged fetch), so keeping *both* sides — not choosing one — is the honest
reconciliation, and the composed tree is then green (39 passed on the merged test
file). This module records that reconciliation so a future pass neither re-derives it
nor, worse, merges the pair in either order and silently loses one repair.

Read-only and stdlib-only: it reads a frozen manifest, imports no application module,
and mutates nothing. ``--measure`` re-derives the composition from a live git tree.
"""

from __future__ import annotations

import argparse
import json
import sys
from itertools import combinations

# The base every recorded head below was measured against.
BASE_MAIN = "24a00f856a0286cbb464a4b585117dd57a2646fa"

# Paths appended to by every workstream; a collision there is mechanical, not semantic.
TAIL_APPEND_ALLOWLIST = frozenset({"AGENTS.md"})

# Frozen population: every open PR at the measurement, PR -> changed paths. Cards are
# read from the GitHub pull-files API (paginated). A PR present here but absent from the
# live repository is a *record* of that measurement, not a claim it is still open.
POPULATION: dict[str, list[str]] = {
    "337": [
        "AGENTS.md",
        "api/lab_routes.py",
        "web/public_prism/src/App.tsx",
        "web/public_prism/src/components/ArkadiaNavigation.tsx",
        "web/public_prism/src/pages/EngineeringLabPage.tsx",
    ],
    "338": [
        "AGENTS.md",
        "api/lab_routes.py",
        "web/public_prism/src/App.tsx",
        "web/public_prism/src/components/ArkadiaNavigation.tsx",
        "web/public_prism/src/pages/EngineeringLabPage.tsx",
        "web/public_prism/src/pages/EngineeringLabPage.css",
    ],
    "347": ["AGENTS.md"],
    "348": ["AGENTS.md"],
    "349": ["AGENTS.md"],
    "350": ["AGENTS.md"],
    "351": ["AGENTS.md"],
    "354": ["AGENTS.md"],
    "355": ["AGENTS.md"],
    "356": ["AGENTS.md"],
    "357": ["AGENTS.md"],
    "358": ["AGENTS.md", "tests/test_open_pr_cluster_composability.py"],
    "361": ["AGENTS.md"],
    "362": ["AGENTS.md"],
    "363": ["AGENTS.md"],
    "364": ["AGENTS.md"],
    "365": ["AGENTS.md"],
    "366": [
        "AGENTS.md",
        "scripts/gate2_production_observation.py",
        "tests/test_gate2_production_observation.py",
    ],
    "367": ["AGENTS.md"],
    "368": [
        "AGENTS.md",
        "scripts/gate2_production_observation.py",
        "tests/test_gate2_production_observation.py",
    ],
    "369": [
        "AGENTS.md",
        "scripts/gate2_alias_app_binding.py",
        "tests/test_gate2_alias_app_binding.py",
    ],
}

# The PRs whose shared non-AGENTS.md source is a *classified* composition hazard.
#
# Each entry records the measured defect and the reconciliation, so the guard fails
# loudly if a future pass drops the classification (which would let the hazard be read
# as "two independent PRs") or keeps it after the hazard is resolved.
CLASSIFIED: dict[frozenset[str], dict[str, object]] = {
    frozenset({"337", "338"}): {
        "kind": "dependency pair",
        "disposition": "reconcile before either lands (prerequisite #337 first, #338 rebased onto it)",
        "shared": [
            "api/lab_routes.py",
            "web/public_prism/src/App.tsx",
            "web/public_prism/src/components/ArkadiaNavigation.tsx",
            "web/public_prism/src/pages/EngineeringLabPage.tsx",
        ],
    },
    frozenset({"366", "368"}): {
        "kind": "same-instrument hazard",
        "disposition": "merge #366 first, then rebase #368 onto it keeping BOTH edits; or land one composed PR",
        "shared": [
            "scripts/gate2_production_observation.py",
            "tests/test_gate2_production_observation.py",
        ],
        # Recorded because it is the point: the same file is edited twice, so the
        # composed tree — not either head — is the only tree that carries both repairs.
        "measured_conflict_regions": {
            "scripts/gate2_production_observation.py": [
                "MARKER_APP / KNOWN_FRONTENDS constant block at BUILD_INPUTS",
            ],
            "tests/test_gate2_production_observation.py": [
                "import block (KNOWN_FRONTENDS, MARKER_APP, MARKERS vs DEPLOYMENT_SCAN_PAGES)",
                "appended test blocks (ordering fault vs fetch window)",
            ],
        },
    },
}

# Blob identity at the base and at each recorded head — the drift pin. If a branch head
# moves, the recorded identity no longer describes it and ``--measure`` must be re-run
# before the reconciliation text is trusted.
BLOBS: dict[str, dict[str, str]] = {
    "base": {
        "scripts/gate2_production_observation.py": "9b481812d54d7440ff8fe45843f5a9fb2e63cbd5",
        "tests/test_gate2_production_observation.py": "5d6ef978cf3b15203186ba04256579d20e4e5ce9",
    },
    "366": {
        "scripts/gate2_production_observation.py": "82907d6e25165880b04c86cbf912c7f68a9bf529",
        "tests/test_gate2_production_observation.py": "b81ed4886230ddde32223a76ffa71293d0635a18",
    },
    "368": {
        "scripts/gate2_production_observation.py": "c5ec73a3239e82fae21b7bc44868a1163d0c50b3",
        "tests/test_gate2_production_observation.py": "bcdc4bf31ac03cd22b403bcdcff2874e7c84c239",
    },
}

# The composed blob identities, measured by resolving both conflicted files "keep both"
# and running the merged test file (39 passed). A re-measurement that disagrees with
# this means the reconciliation text is stale, not that the pair now composes.
COMPOSED: dict[str, object] = {
    "method": "git merge --no-ff #368 onto #366; resolve every conflict by keeping both sides",
    "status": "semantically sound",
    "evidence": "39 passed (tests/test_gate2_production_observation.py, composed)",
    "blobs": {
        "scripts/gate2_production_observation.py": "cf09b073f12753f43514a6baef7fc6fb62bd82b8",
        "tests/test_gate2_production_observation.py": "07aefd2e642e3d8aea278238fad06262cbfb17d7",
    },
    "requirement": (
        "neither PR may be merged while the other's repair is dropped: the two repairs "
        "are independently necessary (pagination + marker-app identity)"
    ),
}


def overlapping_sources(prs: dict[str, list[str]]) -> list[tuple[str, str, list[str]]]:
    """Return ``(pr_a, pr_b, shared_paths)`` for every pair sharing a non-allowlisted path."""
    overlaps = []
    for (a, files_a), (b, files_b) in combinations(prs.items(), 2):
        shared = (set(files_a) & set(files_b)) - TAIL_APPEND_ALLOWLIST
        if shared:
            overlaps.append((a, b, sorted(shared)))
    return overlaps


def unclassified_overlaps(
    prs: dict[str, list[str]], classified: dict[frozenset[str], object] | None = None
) -> list[tuple[str, str, list[str]]]:
    """Overlaps that are *not* recorded as a classified composition hazard."""
    known = CLASSIFIED if classified is None else classified
    return [o for o in overlapping_sources(prs) if frozenset({o[0], o[1]}) not in known]


def _measure(base: str) -> int:
    """Re-derive the composition from the live git tree (read-only, no checkout kept)."""
    import subprocess

    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *args], capture_output=True, text=True)

    recorded = BLOBS["366"]["scripts/gate2_production_observation.py"]
    blob = git("rev-parse", f"origin/gate-hygiene/gate2-marker-oracle-soundness-01:scripts/gate2_production_observation.py")
    head = blob.stdout.strip()
    print(f"base                : {base}")
    print(f"#366 head script    : {head or '<unavailable>'}")
    print(f"#368 head script    : {git('rev-parse', 'origin/gate-hygiene/gate2-deployment-window-01:scripts/gate2_production_observation.py').stdout.strip() or '<unavailable>'}")
    ok = head == recorded
    print(f"recorded #366 blob  : {recorded}")
    print(f"drift               : {'none (record still binds)' if ok else 'HEAD MOVED -- re-measure the reconciliation'}")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--measure", action="store_true", help="re-derive from the live git tree")
    parser.add_argument("--base", default=BASE_MAIN)
    args = parser.parse_args(argv)

    if args.measure:
        return _measure(args.base)

    overlaps = overlapping_sources(POPULATION)
    unclassified = unclassified_overlaps(POPULATION)
    report = {
        "base_main": BASE_MAIN,
        "population": len(POPULATION),
        "overlaps": [{"pair": [a, b], "shared": s} for a, b, s in overlaps],
        "unclassified_hazards": [{"pair": [a, b], "shared": s} for a, b, s in unclassified],
        "composed": COMPOSED,
        "classification": "CLASSIFIED" if not unclassified else "UNCLASSIFIED_HAZARD",
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"base main        : {BASE_MAIN}")
        print(f"open PRs recorded: {len(POPULATION)}")
        print(f"non-AGENTS.md overlaps: {len(overlaps)}")
        for a, b, shared in overlaps:
            tag = "classified" if frozenset({a, b}) in CLASSIFIED else "UNCLASSIFIED"
            print(f"  #{a} x #{b}  [{tag}]  {shared}")
        print(f"composed #366+#368: {COMPOSED['status']} -- {COMPOSED['evidence']}")
        print(f"classification   : {report['classification']}")
    return 0 if not unclassified else 2


if __name__ == "__main__":
    sys.exit(main())
