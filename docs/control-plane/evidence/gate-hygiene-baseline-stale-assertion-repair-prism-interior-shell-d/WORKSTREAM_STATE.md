# WORKSTREAM_STATE — `gate-hygiene` / SH-02 (baseline STALE_ASSERTION migration)

Reconstructed from live repository evidence, not memory.
`BASE_MAIN := df7a99a067382401c00de5e7bbaaac0125ba2088` (PR #131 merged).

## Workstream

Repair baseline test failures whose failure fingerprint is a **stale source-level string
assertion** (`STALE_ASSERTION`) against a reworded-but-intact governance property. Scope is
test-only. It does **not** cover `DRIFT`, `SH-08` governance contradictions, or
product-decision nodes.

Classification source of truth:
`docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/BASELINE_TEST_DEBT_CLASSIFICATION.md`.

## Baseline fingerprint at `BASE_MAIN` @ `df7a99a`

Clean worktree at `main`, same interpreter and `PYTHONPATH`, ignoring the two documented
collection-error modules (`tests/test_autonomy.py`, `tests/test_render_codex.py`):

- full suite: **32 failed / 1025 passed / 13 skipped**
- architecture: **11/11 passed**
- `api/main.py`: 2519 / 2600 lines, `py_compile` pass
- `vite build`: environment-blocked

Node fingerprint derivation: 32 sorted `FAILED`/`ERROR` node ids. A new failure is
attributed to new work **only if its node id appears that was not present here**.

The contract's `main := 6038989` / `804 passed` / `architecture 9/10` and the batch-5
ledger's `39F / 1018P @ 4164573` are **both stale** — they predate `#130`–`#133`.

## Batch ledger

| Batch | Branch | Nodes | State |
| --- | --- | --- | --- |
| — | merged PR #124 | SCI / nexus 6-node | **merged** |
| — | merged PR #125 | Solariun consolidation 3-node | **merged** |
| — | merged PR #127 | `test_prism_pass_c_surface_ownership.py` 13-18 | **merged** |
| 3 | merged PR #130 | identity spine / `ais_profile` | **merged** |
| 4 | merged PR #132 | `test_ais_w6_future_skills_challenge.py` (node 9) | **merged** |
| 5 | merged PR #131 | `spiral_grove_{chambers,frontend_projection,learning_path_projection}` (nodes 24-26) | **merged** |
| 6 | `gate-w2/living-gate-grove-handoff` | `test_ais_w2_living_gate_grove_handoff.py` (nodes 3-8) | **open PR #133** @ `b8e6afc`, green, sovereign-pending |
| d | `gate01/sh02d-prism-interior-shell` | `test_prism_interior_shell.py` (nodes 10-12) | **this PR** — reconstructed off `df7a99a` |

### Batch d: unblocked and reconstructed (resolved this pass)

The original batch-d branch `gate-hygiene/sh02d-prism-interior-shell` @ `8d1c386` was based
on `4164573` and was **never published** — the batch-5 ledger records it as blocked because
it edited `BASELINE_TEST_DEBT_CLASSIFICATION.md`, which PR #129 rewrote by 321 lines.

Both conditions have cleared: **PR #129 merged** at `2026-09-29T15:00:46Z`, and `8d1c386` is
now an **orphan** (its parent `4164573` is an ancestor of `main`; the branch itself predates
`df7a99a`). This PR is a **fresh reconstruction off `df7a99a`** carrying the test repair
only — the ledger edit is dropped, because re-applying pre-#129 text to a doc #129 rewrote
would regress a merged artifact.

Note for future passes: the clone arrives **shallow**. Before `git fetch --unshallow`,
`git merge-base --is-ancestor 4164573 origin/main` returns false, which reads as "orphaned
branch" — a false negative. Always unshallow before reasoning about ancestry.

## CI applicability note (so a future pass does not misread this as missing evidence)

`SG-02-FE.2-V`'s `validate` job is **path-filtered** (`push` + `pull_request` paths in
`.github/workflows/sg-02-fe-2-v.yml`: `web/public_prism/**`, `spiral_grove/**`, `lab/**`,
`api/lab_routes.py`, and specific named test files). Consequences:

- This PR touches `tests/test_prism_interior_shell.py` + `docs/**` only. Whether `validate`
  runs depends on whether that test file is in the filter — a `validate` **absence** here is
  expected behaviour, not a missing check.
- `security-secret-scan` has an unfiltered `pull_request` trigger and runs on every PR.

## Next bounded tasks (proposed, not authorized)

1. The structural drift recorded in this batch's evidence §2: the shell carries no
   `prism-primary-rail` / `prism-secondary-toggle` / `prism-secondary-lenses` testids, and
   the rail keys `sci` / `knowledge-os` are gone. Re-pinning them in product code is a
   **product change**, not test hygiene — needs sovereign direction.
2. Remaining `STALE_ASSERTION` clusters not owned by open work and not `SH-08` / `DRIFT`
   product decisions: `test_spiral_grove_activity_runtime.py` (4 nodes),
   `test_spiral_grove_registry.py` (2), `test_steward_filter.py` (3),
   `test_engineering_scheduler_bootstrap.py` (2).
3. F-01 `test_no_firebase_persistence_in_gate` — a persistence-boundary governance
   decision, deliberately left red (see PR #133).

Each requires a bounded scope, completion condition, evidence requirement, regression
boundary, and authority boundary before execution.

## Authority

Human sovereign merge only. Never merge, never push `main`, never force-push.
