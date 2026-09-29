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
# entry in `git ls-files` (75 entries, 1398 paths) is enumerated here or admitted
# by the generic rules, and test_allowlist_covers_every_tracked_surface asserts
# exactly that against the live tree. An allowlist that omits a surface the repository
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
    # opportunity_radar/ carries the SAPZ capture MVP persisted state
    # (opportunity_radar/SAPZ_CAPTURE_STATE.md), merged via PR #110. It landed
    # before this allowlist was completed, so CP10 was red on the #110 merge and
    # green on the next one: the gate diffed only the tip commit's first parent,
    # and a merge commit whose first parent already contains the path reports no
    # change, so the offender never reappeared to fail. That masking is closed
    # separately by resolve_range_endpoint(), which judges base..HEAD; the surface
    # still has to be enumerated, not inherited.
    r"|opportunity_radar/"
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


def resolve_range_endpoint(
    event: dict, *, ref_exists: bool = True
) -> tuple[str | None, str]:
    """Return ``(base_ref, reason)`` for the commit range a CP10 run must judge.

    The gate historically diffed ``HEAD^ HEAD``. A pull-request run executes on the
    PR's head commit, so that range judges only the *last* commit of the PR: a path
    the allowlist does not admit that was added in an earlier PR commit reports no
    change and never fails (PR #110 would have landed
    ``opportunity_radar/SAPZ_CAPTURE_STATE.md`` this way on an allowlist that
    rejected it). Diffing ``base..HEAD`` judges the whole pull-request range, so a
    masked offender cannot pass.

    ``(None, reason)`` means "no range could be determined"; callers must treat
    that as a gate failure rather than silently passing, because a boundary that
    cannot see the change set cannot bound it.
    """
    event = event or {}
    base = ((event.get("pull_request") or {}).get("base") or {}).get("sha")
    if base:
        return base, "pull_request.base.sha (full PR range)"
    before = event.get("before")
    if before and set(before) != {"0"}:
        return before, "push.before (full push range)"
    if ref_exists:
        # No event range (e.g. workflow_dispatch, replay): fall back to this
        # commit's parent, which is the pre-existing single-commit behaviour.
        return "HEAD^", "fallback HEAD^ (no event range supplied)"
    return None, "cannot determine a base commit for the mutation-boundary range"


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
    import json
    import os
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--resolve-range":
        # Emitted for the CP10 workflow shell. Two lines, so the shell can read
        # them without a JSON parser:
        #   <base-ref>   (empty when undeterminable)
        #   <reason>
        path = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("GITHUB_EVENT_PATH") or ""
        if path and os.path.exists(path):
            with open(path, encoding="utf-8") as handle:
                event = json.load(handle)
        else:
            event = {}
        base, reason = resolve_range_endpoint(event, ref_exists=True)
        print(base or "")
        print(reason)
        raise SystemExit(0)

    ok, msg = evaluate_changed_paths(sys.argv[1:])
    print(msg)
    raise SystemExit(0 if ok else 1)
