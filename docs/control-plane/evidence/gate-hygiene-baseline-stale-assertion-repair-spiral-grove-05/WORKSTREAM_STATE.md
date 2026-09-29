# WORKSTREAM_STATE — `gate-hygiene` / SH-02 (baseline STALE_ASSERTION migration)

Reconstructed from live repository evidence, not memory. `main` @
`4164573586860b9c7e04e1815bca4957559046a2`.

## Workstream

Repair baseline test failures whose failure fingerprint is a **stale source-level string
assertion** (`STALE_ASSERTION`) against a reworded-but-intact governance property. Scope
is test-only. It does **not** cover `DRIFT`, `SH-08` governance contradictions, or
product-decision nodes.

Classification source of truth:
`docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/BASELINE_TEST_DEBT_CLASSIFICATION.md`.

## Baseline fingerprint at `main` @ `41645735`

Baseline captured on a clean worktree at `main`, same interpreter and `PYTHONPATH`,
ignoring the two documented collection-error modules (`test_autonomy.py`,
`test_render_codex.py`):

- full suite: **39 failed / 1018 passed / 13 skipped**
- architecture: **11/11 passed** (the brief's "10/10" is stale; the suite has grown)
- `vite build`: environment-blocked

Node fingerprint: `/tmp/baseline_nodes_main.txt` derivation — 39 sorted `FAILED`/`ERROR`
node ids. A new failure is attributed to new work only if its **node id** appears that was
not present here.

## Batch ledger

| Batch | Branch | Nodes | State |
| --- | --- | --- | --- |
| — | merged PR #124 | SCI / nexus 6-node | **merged** |
| — | merged PR #125 | Solariun consolidation 3-node | **merged** |
| — | merged PR #127 | `test_prism_pass_c_surface_ownership.py` 13-18 | **merged** |
| 3 | `gate-hygiene/baseline-stale-assertion-repair-identity-spine-03` | identity spine / `ais_profile` | **open PR #130**, green |
| 4 | `gate-hygiene/baseline-stale-assertion-repair-future-skills-04` | `test_ais_w6_future_skills_challenge.py` (node 9) | **open PR #132** @ `cefb2f5`, green |
| d | `gate-hygiene/sh02d-prism-interior-shell` | `test_prism_interior_shell.py` (nodes 10-12) | branch @ `8d1c386`, **no PR** — blocked, see below |
| 5 | `gate-hygiene/baseline-stale-assertion-repair-spiral-grove-05` | `spiral_grove_{chambers,frontend_projection,learning_path_projection}` (nodes 24-26) | **this PR** (#131) |

### Batch d is blocked on a rebase decision (not acted on)

`gate-hygiene/sh02d-prism-interior-shell` (`8d1c386`) edits three files, one of which is
`docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/BASELINE_TEST_DEBT_CLASSIFICATION.md`.
**PR #129 rewrites that same file by 321 lines** (`+321/-75` on a 137-line doc). Publishing
batch d as-is would create a textual conflict with an open, green, sovereign-pending PR.
This is a rebase/sequencing decision, not a test-hygiene edit, so it is **recorded and left
unresolved** — publishing it is a separate bounded action that should follow #129's merge
(or be rebased onto it).

Adjacent open work, not part of SH-02:

- PR #129 `gate-hygiene/baseline-ledger-correction-sg04-01` — ledger correction + drift
  reconciliation; awaiting sovereign merge.

## Next bounded tasks (proposed, not authorized)

1. Batch d (`gate-hygiene/sh02d-prism-interior-shell`, nodes 10-12) — publish **after**
   PR #129 merges, or rebase it onto #129's ledger rewrite first. Blocked on that
   sequencing decision; do not publish as-is.
2. The un-rendered version-string assertions noted in the batch-5 evidence "Remaining
   uncertainty" section (candidate SH-02 batch 6).
3. Remaining `STALE_ASSERTION` clusters that are not owned by open work and are not
   `SH-08` / `DRIFT` product decisions.

Each requires a bounded scope, completion condition, evidence requirement, regression
boundary, and authority boundary before execution.

## CI applicability note (so a future pass does not misread this as missing evidence)

`SG-02-FE.2-V`'s `validate` job is **path-filtered** (`push` + `pull_request` paths in
`.github/workflows/sg-02-fe-2-v.yml`: `web/public_prism/**`, `spiral_grove/**`, `lab/**`,
and specific test files). So:

- PR #131 (this PR) touches `tests/test_spiral_grove_frontend_projection.py` and
  `tests/test_spiral_grove_chambers.py`, which **are** in the filter → `validate` runs and
  is green.
- PR #132 (batch 4) touches only `tests/test_ais_w6_future_skills_challenge.py` plus docs,
  which are **not** in the filter → no `validate` run is created. That absence is expected
  behaviour, not a missing check.

`security-secret-scan` has an unfiltered `pull_request` trigger, so it runs on every PR.


## Authority

Human sovereign merge only. Never merge, never push `main`, never force-push.
