# WORKSTREAM STATE — gate-hygiene

Pass: `gate-hygiene/arcana-weaver-merge-loss-restore-01`
Reconstructed: 2026-10-06 · BASE_MAIN `451e41a30fcbff4a65326e897a84818cc623b769`

## Current state

| item | evidence |
|---|---|
| canonical clone | `main`, non-shallow (2142 commits), ancestry intact |
| BASE_MAIN | `451e41a` (#317, 2026-10-05 18:37:24 +0100) |
| active workstream | gate-hygiene independent verification → bounded repair |
| prior cluster #293–#296 | **all MERGED** (`c1dc419`, `554447b`, `7116eee`, `3e14865`) |
| #273 | **MERGED** (`6c8e7f4`) — headline fusion absent from `main`; repaired here |
| this pass | merge-loss restoration on `ProjectDashboard.tsx` + fusion-test repin + evidence |

## Reconciliation note

The previous pass's ledger recorded BASE_MAIN `4550531e` (#290) and the cluster
#293–#296 as OPEN. That was true then and is superseded now: `main` has advanced to
`451e41a`, `4550531e` is an ancestor, and every member of the cluster plus #273 is
merged. Per the contract, state is derived from live evidence, not inherited prose.

## Disposition (measured)

| PR | state | note |
|---|---|---|
| #273 | MERGED | fusion feature landed as test + component file but not as dashboard mount — merge-loss |
| #293 | MERGED | — |
| #294 | MERGED | — |
| #295 | MERGED | — |
| #296 | MERGED | `api/main.py` restored within budget; measured 2432 here |

## Open PRs observed (live `gh pr list`, none authored by this pass)

#306, #318, #319, #320, #321, #322, #323, #324, #325 — all `MERGEABLE` / `UNSTABLE`.
`gate07/*` (#322–#325) is a separate active workstream; #319–#321 are gate-hygiene
scheduler items. Not in scope for this pass; recorded, not executed.

## Test / baseline fingerprint at this pass

- full suite, both trees: `pytest tests/ -q -rEf --continue-on-collection-errors`
  - baseline `451e41a` clean: 11F / 1509P / 20S / 1E — nodes `2dafe6a8…` (12)
  - branch: 10F / 1510P / 20S / 1E — nodes `92d344d0…` (11)
  - delta: exactly `test_arcana_weaver_fusion.py::test_arcana_weaver_fuses_project_canvas_weaver_and_arkana_runtime` removed
- `python -m py_compile api/main.py` — OK; `api/main.py` = 2432 lines (≤ 2600)
- `corepack pnpm build` — exit 0
- `scripts/cp10_mutation_boundary_policy.py --judge` — PASS

## Next bounded task

Sovereign review of this PR. Candidate follow-on (proposed, not authorized, not
started): sweep the remaining two-of-three rename residue from the same
hand-resolution (`motion.div key="arcana-weaver"` on the `canvas` tab).
