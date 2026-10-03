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
# entry in `git ls-files` (83 entries, 1645 paths at 886759f) is enumerated here or
# admitted by the generic rules, and test_allowlist_covers_every_tracked_surface
# asserts exactly that against the live tree. An allowlist that omits a surface the repository
# tracks does not tighten the boundary — it reddens CI on the next unrelated merge
# (this bug class recurred across EDEN-OPS-02, EL-01..10 #97, Solariun #104).
# Constitutional limits live in the FORBID_V3/V2 stage and the unknown-root
# rejection, not in the breadth of this admit-list.
#
# This module is the SINGLE source of the boundary decision: the CP10 workflow
# executes `--judge` (and `--resolve-range`) instead of carrying its own copy of
# the regex. A second hand-maintained copy was a composability defect — the gate
# and the tests that prove it could disagree with the code that actually ran.
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
    # reconciliation/ carries the upstream causal-continuity forensic record
    # (reconciliation/UPSTREAM-CAUSAL-CONTINUITY-01.md), merged via PR #180. It is a
    # first-class control-plane artifact, not a scratch surface, so it is enumerated
    # rather than left to the generic rules. Omitting it rejected the very PR that
    # merged it and left three fitness tests red on main
    # (test_allowlist_admits_every_tracked_top_level_prefix,
    # test_allowlist_covers_every_tracked_surface,
    # test_delegated_verdict_admits_every_tracked_surface).
    r"|reconciliation/"
    # economic_seams/ is the provider-neutral economic seam engine (__init__,
    # engine, correlation, market_data, nocopo), merged to main. It was tracked
    # while this allowlist still omitted it, so three fitness tests were red on
    # main and the CP10 gate rejected the merge that introduced it
    # (39cd05e "fix: repair correlation source registry syntax" touches only
    # economic_seams/correlation.py and is judged FAIL by --judge). A later
    # non-merge commit touching the tree reddens the gate for the same reason.
    r"|economic_seams/"
    # musical-intention-engine/ is the MIE control-plane corpus (constitution,
    # field recon, interaction canvas, musical-object spec, prototype loop,
    # decisions, experiments, research) that issue #209's MVP build reads from.
    # Same omission class: tracked, omitted, three fitness tests red on main.
    r"|musical-intention-engine/"
    # runtime state, archive and asset trees the repository tracks
    r"|data/|archive/|artifacts/|attached_assets/|\"?attached_assets/"
    # vault/ tracks only its scaffold; generated notes stay outside the boundary
    r"|vault/(Index/|Templates/|[A-Za-z]+/[.]gitkeep$)"
    # agent/operator scaffolding
    r"|\.agents/|\.bootstrap/|\.replit_integration_files/"
    # root-level files (exact where a prefix would over-admit)
    r"|conftest\.py$|pytest\.ini$|entrypoint\.sh$|firestore\.rules$|github_corpus\.py$"
    r"|railway\.json$|vercel\.json$|\.replit$|\.env\.example$"
    r"|render|package|pnpm-|requirements|pyproject|README|LICENSE"
    r"|\.gitignore|\.npmrc|\.editorconfig|Makefile|Dockerfile$"
    # gitleaks config read by the full-history secret-scan gate (root-level)
    r"|\.gitleaks\.toml$"
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


def judge_paths(paths: list[str], *, v2_diff_adds_function: bool = False) -> int:
    """Print the boundary verdict for ``paths``; return a process exit status.

    Emitted for the CP10 workflow shell so the CI decision is made by exactly the
    code `tests/test_m02a_ci_gate_integrity.py` proves, rather than by a regex
    copy the shell maintains beside it (they had drifted before: a surface was
    admitted in one and not the other).
    """
    ok, msg = evaluate_changed_paths(paths, v2_diff_adds_function=v2_diff_adds_function)
    if ok:
        print("Mutation boundary PASS (M02A legitimate-surface + constitutional denylist)")
        return 0
    print("Unexpected path outside legitimate repository surfaces:")
    print(msg)
    return 1


def main(argv: list[str] | None = None) -> int:
    import json
    import os
    import sys

    argv = list(sys.argv[1:] if argv is None else argv)

    if argv and argv[0] == "--judge":
        # Paths arrive on stdin, one per line (the workflow pipes `git diff
        # --name-only`). No paths is a pass: an empty change set is bounded trivially.
        return judge_paths([line.strip() for line in sys.stdin if line.strip()])

    if argv and argv[0] == "--resolve-range":
        # Emitted for the CP10 workflow shell. Two lines, so the shell can read
        # them without a JSON parser:
        #   <base-ref>   (empty when undeterminable)
        #   <reason>
        path = argv[1] if len(argv) > 1 else os.environ.get("GITHUB_EVENT_PATH") or ""
        if path and os.path.exists(path):
            with open(path, encoding="utf-8") as handle:
                event = json.load(handle)
        else:
            event = {}
        base, reason = resolve_range_endpoint(event, ref_exists=True)
        print(base or "")
        print(reason)
        return 0

    ok, msg = evaluate_changed_paths(argv)
    print(msg)
    return 0 if ok else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
