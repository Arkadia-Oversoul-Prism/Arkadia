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

## Second move in this pass — removing the residue this repair itself created

Mounting the fused canvas on the `canvas` tab displaced `ProjectAgenticCanvas` from
that tab. The component is **not lost** (`ArkanaWeaverCanvas.tsx:55` renders it
internally — the fused canvas is a strict superset), but the dashboard's import of it
became **unused**: `grep -n ProjectAgenticCanvas ProjectDashboard.tsx` → the import
line only. That is the same residue class this pass repairs (mount displaced, import
survives), so it was removed rather than left standing.

Pinned tests are unaffected: `test_solspire_project_instantiation_ui.py:58` pins
`ProjectAgenticCanvas.tsx` itself, `test_arcana_weaver_fusion.py:16` pins its presence
inside the canvas — neither pins the dashboard import. `pnpm build` exit 0; the
`arcana-weaver-canvas` marker still emits **2** occurrences in the built
`ProjectDashboard-*.js` chunk.

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
  - **independently re-measured this pass** with `scripts/baseline_fingerprint.py`
    (not inherited): both trees reproduced the recorded values, and the `main`
    baseline was re-run in a detached worktree rather than copied from prose.
    Both derivations are recorded, since they are deliberately different:
    `ids_fingerprint` — `main` `2dafe6a8b471…` / branch `92d344d0fbeb…`;
    `outcomes_fingerprint` — `main` `5e782bf9b1ec…` / branch `f3e7364703a0…`.
    The `diff` of the two sorted node lists is one line, a removal only.
- `python -m py_compile api/main.py` — OK; `api/main.py` = 2432 lines (≤ 2600)
- `corepack pnpm build` — exit 0
- `scripts/cp10_mutation_boundary_policy.py --judge` — PASS

## Next bounded task

Sovereign review of PR #326. Candidate follow-on (proposed, **not authorized, not
started**): sweep for *other* two-of-three rename residue from the same
hand-resolution that is live on `main`. Note: the `motion.div key="arcana-weaver"`
residue named in the prior ledger is **not** live on `main` — it exists only in the
discarded branch blob `51e21ce` (see EVIDENCE §2/§6); the repair's mount uses
`key="canvas"`. The remaining question is therefore unmeasured, not established.

## CI on head `c31daba` (PR #326)

| gate | result | note |
|---|---|---|
| SG-02-FE.2-V | success | CP10 mutation boundary + frontend; diff touches its trigger paths |
| Weaver MVP2 validation | success | — |
| Full-history secret scan | success | whole-history range |
| Vercel – arkadia-prism | success | preview build completed |
| Vercel Preview Comments | success | — |
| Vercel – console | **failure** | **pre-existing on `main`** — `commits/451e41a/status` → `failure` |
| engineering-scheduler | failure on `main` | pre-existing, not attributable |

CI is being re-established on the new head `53108b3`; the table above is the last
complete measurement and is not carried forward as a claim about the new head.

## Corrections applied in this pass

Two claims in the first draft of `EVIDENCE.md` were contradicted by measurement and
corrected in place (rather than left standing):

1. "the `weaver` tab label was already `Arkana Weaver` on `main` — unchanged" was
   **false**. Measured: `origin/main` has `label: 'Weaver'`; the rename is this
   branch's change.
2. "the branch's combined condition **replaces** the `weaver` tab's `WeaverPanel`" was
   asserted without measurement. Now measured on branch blob `51e21ce`: the combined
   line is the only canvas mount and `<WeaverPanel` is mounted **0** times while
   `function WeaverPanel` is defined **1** time — the claim holds, but it is now
   evidence-backed rather than assumed.
