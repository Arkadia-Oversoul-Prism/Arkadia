# Workstream state — gate-hygiene / CI gate trigger coverage (GATE-10)

Bounded objective: add CI trigger coverage for the executable gate guard and pin
the truth about the CP10 `Enforce CP10 executable gates` step (no gate promotion,
no authority change).

## Current state (2026-10-10)

- **Main:** `f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8` (untouched).
- **Branch:** `gate-hygiene/ci-gate-trigger-coverage-02`, PR **#390**, head
  `0a19032aa806ee11e5d4c1d0debef47dc006c6c7`. State OPEN,
  `MERGEABLE/UNSTABLE`.
- **Sibling:** PR #388 `gate10/cp10-enforcement-step-truthfulness-01` owns the
  `steps.<id>.outcome` invariant + its guard; this branch only cites it.

## Pinned measurements

- `.github/workflows/sg-02-fe-2-v.yml` `Enforce CP10 executable gates` carries
  **16** `test '…' = success` assertion lines on `main`; the pre-existing failing
  node `steps.browser.outcome` is **#14 of 16**.
- This branch adds `steps.trigger_coverage` at #2 and is green on it; the same
  failing node moves to **#15 of 17**. Per revision: `main` `f9ced6b6` #14 · this
  branch #15 · PR #354 `ebb4077b` #14 · PR #388 `63b3ce9b7c` #14. Zero branch
  regression.
- Citation convention: PR #388's evidence calls the same node "the 15th
  assertion" by counting the `##[group]Run` group-echo line as #1. Both docs name
  the identical node. Recorded, not reconciled (their doc is not modified here).

## Baseline debt (recorded, not repaired)

- `tests/test_m02a_ci_gate_integrity.py` carries **3** pre-existing failures, all
  the `deploy/n-atlas-server/` allowlist omission owned by PR #354. Unchanged by
  this branch (181 passed, 3 failed).
- `main`'s `SG-02-FE.2-V` browser gate has been red since `d466e1378`
  (firebase-web-config deferral); the node is identical to this branch's. A
  separate bounded workstream, not repaired here.

## AGENTS.md

- `scripts/agents_md_encoding_audit.py` → `alterations=0`, `reproduced=True`,
  `Cyrillic 0`, exit 1 (clean, oracle-corroborated). This branch appends past the
  oracle, insertions-only.

## Next bounded task

Sovereign review of #390. The `.outcome` guard belongs to #388; merge order
between #390 and #388 is immaterial (disjoint `AGENTS.md` regions).

## Authority boundary

Evidence/verification only. No merge, no gate promotion, no authority change.
Human sovereign retains merge authority.
