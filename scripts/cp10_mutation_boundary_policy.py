"""M02A — CP10 mutation-boundary policy (testable without git).

Legitimate surfaces may change. Constitutional dual-shell V3 and active V2
implementations are forbidden. Unknown top-level paths are rejected.
"""
from __future__ import annotations

import re

LEGIT = re.compile(
    r"^(\.github/|web/|api/|solspire/|kernel/|weaver/|lab/|tests/|docs/|scripts/|"
    r"android/|render|package|pnpm-|requirements|pyproject|README|LICENSE|"
    r"\.gitignore|\.npmrc|\.editorconfig|Makefile|Dockerfile)"
)
FORBID_V3 = re.compile(r"SolSpireExperienceV3\.tsx$")
FORBID_V2 = re.compile(r"SolSpireExperienceV2\.tsx$")


def evaluate_changed_paths(paths: list[str], *, v2_diff_adds_function: bool = False) -> tuple[bool, str]:
    """Return (ok, message)."""
    paths = [p for p in paths if p and p.strip()]
    for p in paths:
        if not LEGIT.search(p):
            return False, f"Unexpected path outside legitimate surfaces: {p}"
        if FORBID_V3.search(p):
            return False, f"Forbidden V3 dual shell: {p}"
        if FORBID_V2.search(p) and v2_diff_adds_function:
            return False, f"Forbidden active V2 implementation: {p}"
    return True, "PASS"


if __name__ == "__main__":
    import sys

    ok, msg = evaluate_changed_paths(sys.argv[1:])
    print(msg)
    raise SystemExit(0 if ok else 1)
