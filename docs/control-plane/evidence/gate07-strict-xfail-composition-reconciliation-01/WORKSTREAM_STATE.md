# WORKSTREAM STATE — gate07/strict-xfail-composition-reconciliation-01

## Identity
- Gate: GATE-07 (router / attention composition)
- Branch: `gate07/strict-xfail-composition-reconciliation-01`
- Base: `main` @ `74e8ea53a30213db8783e6733679d2f11903de0b`
- Status: **IMPLEMENTED** (guard + decision record; companion change to #329 is sovereign-gated)
- Authority: verification + evidence only. No merge, no push to `main`, no subject-PR mutation.

## Current state
- The GATE-07 batch contains a **serialization constraint**: `#329` records the clean-stop
  defect as a `strict=True` xfail; `#342` is the repair that flips it. Merged together,
  `#329`'s node fails as a strict XPASS.
- Measured (worktree `/tmp/wt329`, `#342`'s `weaver/` patch applied): `1 failed, 5 passed`.
- Decision: `#329` must carry a companion change re-materializing the xfail as a strict
  positive quiet-stop assertion; then `#329` before `#342` (or one composed PR).

## Evidence
- `docs/control-plane/evidence/gate07-strict-xfail-composition-reconciliation-01/EVIDENCE.md`
- Guard: `tests/test_gate07_strict_xfail_composition_reconciliation.py` (6 checks,
  1 negative control, 2 positive controls, 1 literal self-check).
- Detector proven to fire on the composed tree and to stay silent on `main`.

## Regression boundary
Additive files only: one test file, one evidence file, this state file. No `weaver/**`,
no `api/**`, no workflow, no subject PR touched. Full-suite failing node-set is expected
unchanged; the guard adds one passing node.

## Next bounded task
1. Sovereign decision on the reconciliation rule (handoff; requires touching `#329`).
2. If authorized, materialize the `#329` companion change in that PR's own branch.

## Forbidden this workstream
- Merging any PR.
- Pushing to `main`.
- Editing `#329`, `#342`, or any subject PR.
- Promoting GATE-07 status or expanding scope.
