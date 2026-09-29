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
#
# The true allowlist is the set of tracked repository surfaces: every top-level
# entry in `git ls-tree -r HEAD` (74 entries, 1393 paths) is enumerated here or
# admitted by the generic rules. An allowlist that omits a surface the repository
# tracks does not tighten the boundary — it reddens CI on the next unrelated merge
# (this bug class recurred across EDEN-OPS-02, EL-01..10 #97, Solariun #104).
# Constitutional limits live in the FORBID_V3/V2 stage and the unknown-root
# rejection, not in the breadth of this admit-list. Kept in sync with the workflow
# mirror by tests/test_m02a_ci_gate_integrity.py.
LEGIT = re.compile(
    r"^("
    # engines, product and runtime surfaces
    r"\.github/|web/|api/|solspire/|kernel/|weaver/|lab/|tests/|docs/|scripts/"
    r"|enterprises/|knowledge/|spiral_grove/|android/|arkadia-android/|sonata-android/"
    r"|app/|architecture/|arkana_rasa/|arkana_space/|bot/|codex/|collective/"
    r"|corpus/|forge/|governance/|openclaw/|orchestration/|providers/|sanctum/|static/"
    # runtime state, archive and asset trees the repository tracks
    r"|data/|archive/|artifacts/|attached_assets/|\"?attached_assets/"
    # vault/ tracks only its scaffold; generated notes stay outside the boundary
    r"|vault/(Index/|Templates/|[A-Za-z]+/[.]gitkeep$)"
    # agent/operator scaffolding
    r"|\.agents/|\.bootstrap/|\.replit_integration_files/"
    # root-level files (exact where a prefix would over-admit)
    r"|conftest\.py$|entrypoint\.sh$|firestore\.rules$|github_corpus\.py$"
    r"|railway\.json$|vercel\.json$|\.replit$|\.env\.example$"
    r"|render|package|pnpm-|requirements|pyproject|README|LICENSE"
    r"|\.gitignore|\.npmrc|\.editorconfig|Makefile|Dockerfile$"
    # root-level markdown only ([^/] forbids nested paths)
    r"|[^/]+\.md$"
    r")"
)
FORBID_V3 = re.compile(r"SolSpireExperienceV3\.tsx$")
FORBID_V2 = re.compile(r"SolSpireExperienceV2\.tsx$")


def evaluate_changed_paths(paths: list[str], *, v2_diff_adds_function: bool = False) -> tuple[bool, str]:
    """Return (ok, message)."""
    paths = [p for p in paths if p and p.strip()]
    for p in paths:
        if p.startswith("vault/") and not LEGIT.search(p):
            # Vault is the private Knowledge OS runtime output: only its tracked
            # scaffold is legitimate. Guarded first so the reason is unambiguous
            # even if a future edit widens the generic rules.
            return False, f"Personal vault surface outside the tracked scaffold: {p}"
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
