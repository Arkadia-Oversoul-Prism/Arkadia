# WORKSTREAM STATE — gate-hygiene-sh05-retirement-boundary-hold-01

**Pass:** hourly bounded execution, 2026-10-03
**BASE_MAIN:** `162f574b05dd839540d803aadda7608342618a84`
**Branch tip:** `e3b25b0` (`gate-hygiene/stale-gate-fixture-retirement-01`)
**PR:** #220 (draft / HOLD)
**Classification:** `BLOCKED` — sovereign `SH-05` disposition required

## Current state

The retirement branch is a coherent, well-evidenced proposal for `SH-05a`. It is **not**
executable without the gating `SH-05` product ruling (retire / relocate / restore). The
pass therefore stops at the authority boundary; nothing about the Gate UI's fate is decided.

## Evidence (measured this pass)

| check | result |
|---|---|
| `main @ 162f574` suite | 20 failed / 1305 passed / 18 skipped / 1 error → **21 nodes** |
| branch `e3b25b0` suite | 18 failed / 1306 passed / 18 skipped / 1 error → **19 nodes** |
| delta | **2 nodes removed (the gate pair) / 0 new** |
| `tests/test_baseline_fingerprint.py` (branch) | **19 passed** |
| `main:tests/fixtures/baseline_node_set.txt` vs branch `superseded_…` | **byte-identical** |
| composed tree `/tmp/compose @ 0d8ba22` | 0 conflict markers; fingerprint test 19 passed |
| open PRs #215–#219 | all `MERGEABLE`/`UNSTABLE`; secret-scan `success` on every head |

## Blockers

1. **`SH-05` disposition never recorded** — PR #142 merged evidence-only; no sovereign
   comment. Every workstream doc names this as a sovereign call.
2. **Gate-2 production parity** — unchanged; deployment-specific URL behind Vercel SSO
   (provider auth), not a repository defect.

## Authorized action (next pass)

- Do **not** execute `SH-05a` on this branch. It stays draft/HOLD until a disposition lands.
- Safe unrelated work only on a **separate** bounded branch.
- Reconstruct state from live evidence; the five open PRs (#215–#219) remain the only
  merge-ready queue and need a sovereign merge decision.

## Forbidden actions

- Merge (any PR), push to `main`, force-push.
- Executing the retirement (deleting the two tests) without a recorded `SH-05` ruling.
- Re-opening SH-05 provenance work (marked EXHAUSTED by the queue pass).

## Completion condition

A sovereign `SH-05` disposition is recorded → this branch either proceeds as `SH-05a`,
is superseded by a relocation PR, or is closed.
