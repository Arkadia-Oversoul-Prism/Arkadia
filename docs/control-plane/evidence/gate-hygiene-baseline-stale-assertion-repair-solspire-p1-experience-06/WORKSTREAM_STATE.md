# WORKSTREAM_STATE — `gate-hygiene` / SH-02 (baseline STALE_ASSERTION migration)

Reconstructed from live repository evidence, not memory. `main` @
`df7a99a067382401c00de5e7bbaaac0125ba2088`.

## Workstream

Repair baseline test failures whose failure fingerprint is a **stale source-level string
assertion** (`STALE_ASSERTION`) against a reworded-but-intact governance property. Scope is
test-only. It does **not** cover `DRIFT`, `SH-08` governance contradictions, or
product-decision nodes.

Classification source of truth:
`docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/BASELINE_TEST_DEBT_CLASSIFICATION.md`.

## Baseline fingerprint at `main` @ `df7a99a`

Measured this pass on a clean worktree at `main`, same interpreter and `PYTHONPATH`, with
`--continue-on-collection-errors`:

- full suite: **32 failed / 1025 passed / 13 skipped / 2 collection errors**
  (`test_autonomy.py`, `test_render_codex.py`)
- architecture: **11/11 passed** (the brief's "10/10" is stale; the suite has grown)
- `vite build`: environment-blocked (no npm registry access)

Node fingerprint: 32 sorted `FAILED`/`ERROR` node ids. A new failure is attributed to new
work only if its **node id** appears that was not present here.

> Measurement trap, recorded so it is not repeated: the two collection errors **abort** the
> session. Without `--continue-on-collection-errors` the run ends in ~1.5s reporting
> `0 failed / 1 skipped / 2 errors`, which is easily misread as a clean tree. Always pass the
> flag and compare by node name.

## Batch ledger

| Batch | Branch | Nodes | State |
| --- | --- | --- | --- |
| — | merged PR #124 | SCI / nexus 6-node | **merged** |
| — | merged PR #125 | Solariun consolidation 3-node | **merged** |
| — | merged PR #127 | `test_prism_pass_c_surface_ownership.py` 13-18 | **merged** |
| 3 | `gate-hygiene/baseline-stale-assertion-repair-identity-spine-03` | identity spine / `ais_profile` | open PR #130 |
| 4 | `gate-hygiene/baseline-stale-assertion-repair-future-skills-04` | `test_ais_w6_future_skills_challenge.py` | open PR #132 |
| d | `gate-hygiene/sh02d-prism-interior-shell` | `test_prism_interior_shell.py` (3 nodes) | open PR #135 |
| 5 | `gate-hygiene/baseline-stale-assertion-repair-spiral-grove-05` | `spiral_grove_{chambers,frontend_projection,learning_path_projection}` | open PR #131 |
| e | see PR #136 | `test_ais_capability_profile_onboarding.py`, `test_agent_run.py` | open PR #136 |
| **f** | **`gate-hygiene/sh02f-solspire-p1-experience-01-repair`** | **`test_solspire_p1_experience_01.py` (2 nodes)** | **this PR** |

Batch f repairs rows 22-23 (`test_p1_1_arkana_context_pack`, `test_p1_1_not_authorization`).
Full record, including the rewording commit (`eebf39c6`), the six negative controls, and the
before/after fingerprint deltas, is `BASELINE_TEST_DEBT_CLASSIFICATION.md` **§13**.

## Excluded clusters (recorded, not repaired)

- **SG-04** — `test_spiral_grove_activity_runtime.py` (4), `test_spiral_grove_registry.py`
  (2): merge **CONTRADICTION** per ledger §11.2. Re-confirmed this pass; the mount
  expectation needs a product decision.
- **SolSpire R-series** — `test_solspire_r{1,2,3}_*.py` (4 nodes): governance / mutation-path
  invariants. Reclassifying to `REAL_DEFECT` is the authority-model boundary owned by
  **SH-08**, not a test edit.

## CI applicability note (so a future pass does not misread this as missing evidence)

`SG-02-FE.2-V`'s `validate` job is **path-filtered** (see `.github/workflows/sg-02-fe-2-v.yml`).
Batch **f** touches `tests/test_solspire_p1_experience_01.py` plus docs; confirm whether that
path is inside the filter. If it is not, the absence of a `validate` run is expected
behaviour, not a missing check. `security-secret-scan` has an unfiltered `pull_request`
trigger, so it runs on every PR.

## Next bounded tasks (proposed, not authorized)

1. Continue any batch whose PR is still open — do **not** open a duplicate.
2. Remaining `STALE_ASSERTION` rows neither owned by an open PR nor an `SH-08` / `DRIFT`
   product decision. The `test_weaver_sci_*` / `test_weaver_mvp2_08` "nexus→novanet" family
   has been re-expressed in `App.tsx` and is a candidate — measure first.
3. Rows requiring a product/architectural decision stay with their owners (`SH-03` SG-04
   mount expectation; `SH-08` SolSpire governance reclassification).

Each requires a bounded scope, completion condition, evidence requirement, regression
boundary, and authority boundary before execution.

## Authority

Human sovereign merge only. Never merge, never push `main`, never force-push. A read-only
token is a hard stop, not a puzzle.
