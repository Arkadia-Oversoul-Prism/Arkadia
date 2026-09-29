"""M02A — CP10 mutation-boundary policy (testable without git).

Legitimate surfaces may change. Constitutional dual-shell V3 and active V2
implementations are forbidden. Unknown top-level paths are rejected.
"""
from __future__ import annotations

import re

# The allowlist must be a complete inventory of legitimate surfaces: it runs on
# every main push, so ANY surface omitted here turns the canonical branch red.
# Each omission below was proven by merged history, not speculation.
#
# Root-level narrative docs (`AGENTS.md`, `ROADMAP.md`, ...) are first-class
# product surfaces: AGENTS.md is the repository's persistent agent memory and is
# committed by ordinary work. Omitting them rejected the EL-01..10 substrate PR
# (#97) and the Solariun thread-navigation PR (#104). `[^/]+[.]md$` admits only
# top-level markdown. `conftest.py` is the test-session root fixture and is
# committed by ordinary work; omitting it rejected a bootstrap commit. Both are
# deliberately top-level-only literals — they do not open nested paths.
LEGIT = re.compile(
    r"^(\.github/|web/|api/|solspire/|kernel/|weaver/|lab/|tests/|docs/|scripts/|"
    r"enterprises/|android/|render|package|pnpm-|requirements|pyproject|README|LICENSE|"
    r"\.gitignore|\.npmrc|\.editorconfig|Makefile|Dockerfile|conftest\.py|"
    r"knowledge/|spiral_grove/|[^/]+\.md$)"
)

# Content surfaces. A top-level directory only counts as "touched" when a real
# artifact inside it changed — directory-prefix-only paths (`knowledge/`) are
# not artifacts.
CONTENT_DIRS = frozenset({"knowledge", "spiral_grove"})
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
