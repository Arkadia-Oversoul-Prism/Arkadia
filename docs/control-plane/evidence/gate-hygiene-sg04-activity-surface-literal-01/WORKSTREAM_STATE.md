# WORKSTREAM_STATE — `gate-hygiene` / SG-04 activity-surface literal pin

Reconstructed from live repository evidence, not memory. Base `main` @
`3d4df9ec890c8b8f6d087c5c1577450cfacf1360`. Observed 2026-10-02 (UTC).

## Workstream

Repair the last remaining SG-04 baseline failure whose fingerprint is a **stale/expanded
source-level string assertion** (`STALE_ASSERTION` form) against an intact governance
property. Scope is **test-only**. It does not cover `DRIFT` nodes, `SH-08` governance
contradictions, or product-decision nodes.

Classification lineage: `BASELINE_TEST_DEBT_CLASSIFICATION.md` §11.2 proposed
`REAL_DEFECT` from the `4164573` measurement; three later measured records
(`gate02-capability-chamber-merge-loss-repair-01`, `gate02-capability-chamber-union-repair-02`
§8, `gate01-relational-lineage-canonical-provenance-01`) reclassify it as **test-side** and
reserve it for its own bounded workstream. This pass is that workstream. See
`EVIDENCE.md` §3.

## Baseline fingerprint at base `3d4df9e`

Captured on a clean worktree, deps installed, with
`pytest tests/ -q --continue-on-collection-errors`:

- full suite: **20 failed / 1236 passed / 17 skipped / 1 error** (21 nodes)
- node-id sha256: `c2f31d8caab562fa92fa693ee6bcda3caa8a95da7e26ae8d5255e94657f3c7e5`
- architecture: **11/11**
- `api/main.py`: 2571 / 2600 lines
- `vite build`: environment-blocked (not claimed)

A new failure is attributed to new work only if its **node id** was not present here.
Counts alone are not used (`AGENTS.md` → "Test-suite fingerprint is UNSTABLE on main").

## Result of this pass

- **19 failed / 1237 passed / 17 skipped / 1 error** (20 nodes)
- node-id sha256: `66a69c500d9c1be2f807af77334480869673bda8896e50c5089318cdba199393`
- delta: **1 resolved, 0 new** — exactly
  `test_spiral_grove_activity_runtime.py::test_runtime_dispatches_all_eight_kinds_to_deterministic_renderers`

## Batch ledger (SH-02 / SG-04 line)

| Batch | Branch | Nodes | State |
| --- | --- | --- | --- |
| 5 | `gate-hygiene/baseline-stale-assertion-repair-spiral-grove-05` | spiral-grove projection nodes | merged (PR #131) |
| — | `gate02/capability-chamber-merge-loss-repair-01` | chamber merge-loss | merged |
| — | `gate02/capability-chamber-union-repair-02` | chamber union + canonical header | merged |
| 6 | `gate-hygiene/sg04-activity-surface-literal-01` | `activity_runtime` dispatch node (1) | **this PR**, green |

## Next bounded tasks (proposed, NOT authorized)

1. `test_spiral_grove_registry.py` (2 nodes) — `::test_ais_catalog_supports_progressive_creative_workflow`,
   `::test_registry_rejects_prerequisite_cycle`. Not yet classified; needs its own
   classification pass before any repair.
2. `test_steward_filter.py` (3 nodes) — `SH-06` ("decide whether `steward_filter` should
   stem-match `transcend*`"). Carries a **product judgement** dependency; a prior provenance
   workstream (`gate-hygiene-f02-steward-filter-provenance-01`) exists. Do not repair
   without resolving that judgement.
3. `test_upstream_causal_continuity_01.py` (1 node) — `::test_api_approval_does_not_create_enterprise_authorization`.
4. Remaining `REAL_DEFECT` clusters (`solspire_r1/r2/r3`, `m02_reasomate_truth` `SH-07`) —
   these are **not** test hygiene; they need architectural/product decisions.

Each requires a bounded scope, completion condition, evidence requirement, regression
boundary, and authority boundary before execution.

## CI applicability note (so a future pass does not misread this as missing evidence)

`SG-02-FE.2-V`'s `validate` job is **path-filtered** (`push` + `pull_request` paths in
`.github/workflows/sg-02-fe-2-v.yml`). This change touches only
`tests/test_spiral_grove_activity_runtime.py` plus this evidence directory; the test file is
**not** in the filter, so `validate` is not created by this path alone. That absence is
expected behaviour, not a missing check. The boundary is still exercised directly
(`cp10_mutation_boundary_policy.py --judge` → PASS) and by
`tests/test_m02a_ci_gate_integrity.py` (51 passed).

`security-secret-scan` has an unfiltered `pull_request` trigger and runs on every PR.
`provider-routing` triggers on `weaver/**` only — untouched here.

## Deterministic next-action block

- **Current state:** repair implemented, verified, evidence committed on the branch; PR open.
- **Evidence:** `EVIDENCE.md` (fingerprint table, negative controls, classification lineage).
- **Blockers:** none for this bounded task. `vite build` remains environment-blocked.
- **Authorized action:** none pending — open PR, request sovereign review.
- **Forbidden:** merge, force-push, push to `main`, scope expansion into the next-tasks list
  above, or touching the three sibling SG-04 nodes that are already green.
- **Completion condition:** this PR merges, then the node is re-measured absent on the new
  `main`.

## Authority

Human sovereign merge only. Never merge, never push `main`, never force-push.
