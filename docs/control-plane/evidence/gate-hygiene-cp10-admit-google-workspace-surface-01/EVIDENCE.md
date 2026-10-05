# EVIDENCE — gate-hygiene: admit `google_workspace/` to the CP10 mutation boundary

Pass: WEAVER hourly bounded execution · GATE-10 (governed execution) hygiene
Branch: `gate-hygiene/cp10-admit-google-workspace-surface-01`
Synchronized base: `0d7c090bfceb1949a4ff164db612749d5882bfa8` (current `main` after PR #308)
Companion target: PR **#311** (`feat/weaver-attention-bus-google-workspace`)

Authority: read/measure/implement/test/PR only. No merge, no push to `main`. Merge remains with the human sovereign.

## 1. Defect

PR #311 introduces the tracked top-level tree `google_workspace/` with `Code.gs` and `appsscript.json`. The CP10 legitimate-surface inventory did not enumerate that tree, so the gate rejects the change set.

## 2. Bounded change

This synchronized branch adds one explicit `google_workspace/` alternation to `scripts/cp10_mutation_boundary_policy.py`, plus four bounded fitness tests covering admission and prefix-lookalike rejection.

No production runtime or authorization behavior is changed.

## 3. Verification boundary

Verification must be run against this branch after synchronization. Required checks:
- `pytest tests/test_m02a_ci_gate_integrity.py -q`
- CP10 `--judge` against the branch tree
- negative controls for `google_workspace_evil/`, `google_workspace2/`, unknown roots, and constitutional V3
- architecture suite and full-suite regression comparison against synchronized `main`

## 4. Composition target

This PR is an admission dependency for PR #311. It must merge first so the composed Weaver attention-bus tree is inside the CP10 mutation boundary.

Human authority required for both merges.
