# GATE-HYGIENE — CI gate trigger coverage, enforced-target pass (02)

## Status

IMPLEMENTED / VERIFIED (repository-source). Awaiting sovereign merge.
No production or deployment claim is made here.

## BASE

- BASE_MAIN: `f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8`
  ("Expose sovereign economic seam scan in canonical Opportunity Radar")
- Observed: 2026-10-10 (Weaver hourly pass)

## Defect (measured, not inferred)

`tests/test_ci_gate_trigger_coverage.py` (added by #300, `3f61cf2e`) states three
invariants but was executed by **no** workflow — `grep -rl
test_ci_gate_trigger_coverage .github/workflows/` returns 0. It was a guard no
gate runs: decoration, not a boundary.

The three invariants generalise the sibling `tests/test_m02a_ci_gate_integrity.py`
lesson only as far as "a workflow that runs `tests/architecture` must be selected
by `tests/architecture/**`". They do not cover the **named test files** a workflow
executes as a load-bearing step. Measured across PR-triggered workflows: **13**
named files are executed but absent from the trigger filter.

## Change

1. Extend `tests/test_ci_gate_trigger_coverage.py` with a fourth invariant,
   `test_executed_named_test_is_selected_by_its_file`, parametrised over every
   named test file a workflow executes as a load-bearing step. *Load-bearing* is
   defined as CP10 does: not `continue-on-error`, **or** `continue-on-error` with
   its `step.id` asserted via `${{ steps.<id>.outcome }}` — the CP10 backend step
   is judged by the enforce step, so it counts. File targets are read from the
   `pytest` command line, so `tests/` or `tests/architecture` (suite globs) name no
   file and contribute nothing.
   - Four controls added: an ordinary step contributes targets; a directory glob
     contributes none; an **unasserted** soft step contributes none (must not
     redden on advisory steps); an **asserted** soft step does.
2. Repair the two workflows whose filters omitted the files they execute:
   - `.github/workflows/prism-execution-workevent-governance.yml` +4
   - `.github/workflows/sg-02-fe-2-v.yml` +9
3. **Wire the guard.** `sg-02-fe-2-v.yml` runs the guard as an enforced step
   (`id: trigger_coverage`, `run: python -m pytest tests/test_ci_gate_trigger_coverage.py -q`,
   asserted in "Enforce CP10 executable gates") and the guard's own file is added
   to that workflow's filter. The step is **not** `continue-on-error`, so the
   assertion is real — unlike the pre-existing `${{ steps.<id>.outcome }}` lines in
   that enforce step, which are self-satisfying under `continue-on-error` and are a
   separate, documented class not repaired here.

### Measured violations, pre-repair (guard exited non-zero, 13 parametrisations)

`prism-execution-workevent-governance.yml` (4, run by the `if: always()`
regression step): `test_workevent_evidence_boundary`, `test_authority_boundary`,
`test_evidence_verification_boundary`, `test_authority_api_enterprise_boundary`.

`sg-02-fe-2-v.yml` (9, run by the enforced phase-gate + SolSpire runtime steps):
`test_phase7_calibration`, `test_phase8_possibility`, `test_phase9_decision_queue`,
`test_phase10_binding`, `test_engineering_lab_candidate_proposals`,
`test_solspire_project_execution_service`, `test_solspire_integration_health`,
`test_solspire_larder_graph_binding`, `test_solspire_template_health_contract`.

## Regression boundary (measured)

- Full suite `python -m pytest tests/ -q --continue-on-collection-errors -rEf`:
  base **16** failing/error nodes, branch **16** — sorted `FAILED`/`ERROR` node
  sets byte-identical, sha256
  `bfcfe5920c3789302e80c72618e1f280e3577a8395320c89f174147cd11ec733`. Zero
  node-set delta.
- The 13 affected files all pass (73 passed, 1 skipped) — being added to a filter
  imports no debt.
- Architecture suite: **11 passed**.
- Guard: **120 passed** post-repair; 13 failures pre-repair.
- Pre-existing, not attributable to this pass: 3 `test_m02a_ci_gate_integrity.py`
  `deploy/` allowlist failures (CP10 `LEGIT` omission, owned by PR #354).

## Authority boundary

Repository-source only: two workflow filters widened to select tests the workflows
already execute; one guard generalised and wired. No runtime, authority, or
mutation-path change. Merge is sovereign-only.

## Scope not widened

The `api/**` question from pass 01 stays open and untouched: `sg-02-fe-2-v.yml`
runs `pytest tests/ -q`, which carries pre-existing `main` failures, so widening to
`api/**` would redden every API PR with debt it did not introduce.

## CI execution (measured this pass, 2026-10-10)

- PR **#390**, head `462278f4c49a21b066e90299d80b63dffa2381e1`.
- `sg-02-fe-2-v.yml` run `38022403228` / job `114126018722`:
  - **Step 10 "CI gate trigger coverage" -> success.** The guard added to this
    workflow executes under CI and passes — the wiring is runtime-proven, not a
    source-level claim.
  - Step 33 "CP10 mutation boundary" -> success.
  - Step 36 "Enforce CP10 executable gates" -> failure, on `test 'failure' =
    success`: the **browser verification** step (30) failed with
    `firebase-config.js :: net::ERR_ABORTED` (empty `FIREBASE_WEB_API_KEY` in the
    job env).
- **Pre-existing, not attributable to this PR.** `main` at `f9ced6b6` run
  `37954341298` fails the **same** enforce step (`test 'failure' = success`) with
  the **same** `firebase-config.js :: net::ERR_ABORTED` browser failure. The
  earlier `main` runs at `27cc85d2` / `24a00f85` succeeded, so the browser step
  regressed on `main` between `27cc85d2` and `f9ced6b6` — before this branch.
- Other checks on the head: `Full-history secret scan` success, `governance`
  success, `native-arkadia-golden-workflow` success, `bundle-beta-evidence`
  success, `Vercel Preview Comments` success.

## Independent base measurement (this pass)

The full-suite node set was re-measured in a **detached worktree at `origin/main`**
(`git worktree add --detach /tmp/base_wt origin/main`), not read from a fixture:
base and branch both yield 16 failing/error nodes, outcomes sha256
`bfcfe5920c3789302e80c72618e1f280e3577a8395320c89f174147cd11ec733`, ids sha256
`ed5e4714df236078d6eb04cb43197c22403d2c244caa3e7bc7d71d45f6c0a833`. Zero delta,
measured on both trees.

## Self-correction: the `steps.<id>.outcome` overclaim (2026-10-10, pass 02)

The AGENTS.md paragraph appended by this PR originally asserted that the
`Enforce CP10 executable gates` step is "self-satisfying" because
`${{ steps.<id>.outcome }}` is a constant inside a `run:` block. **That claim is
false and this branch's own CI run refutes it.** The enforce step failed on this
PR's head with `test 'failure' = success` — the true `outcome` of the browser
step — which is only possible if the substitution *is* performed.

- The paragraph was corrected in place to state the measured behaviour
  (`continue-on-error` separates *outcome* `failure` from *conclusion* `success`;
  the enforce step reads `.outcome` and genuinely reddens the job).
- The independent fix and its controls — `test_enforcement_never_reads_step_conclusion`,
  the `.conclusion` negative control, and the "do not switch to `.conclusion`"
  guard — are owned by **PR #388** (`gate10/cp10-enforcement-step-truthfulness-01`),
  which is the correct home for that invariant. This branch does not duplicate it.
- The two PRs touch **different regions** of `AGENTS.md` (`#390` appends at the end;
  `#388` rewrites the "A green CI job can execute ZERO tests" section) and different
  files otherwise, so they compose without conflict. Merge order is immaterial.

## Composition with PR #388 (measured, 2026-10-10)

PR #388 (`gate10/cp10-enforcement-step-truthfulness-01`) is the independent
authority on the `.outcome` invariant. Composed onto this branch head
`c3f186e7` in a detached worktree (`git worktree add --detach /tmp/wt390 HEAD`;
`git apply --3way` of #388 AGENTS.md + tests/test_m02a_ci_gate_integrity.py
diff):

- Both files apply **cleanly** — #390 appends a new section at the end of
  `AGENTS.md`; #388 rewrites the "A green CI job can execute ZERO tests" section
  in the middle. Disjoint regions, no textual conflict, merge order immaterial.
- Composed tree: `cyrillic 0`, `AGENTS.md` 984 lines.
- `tests/test_m02a_ci_gate_integrity.py` + `test_agents_md_*` +
  `test_ci_gate_trigger_coverage.py` = **204 passed, 3 failed, 5 skipped**. The 3
  failures are the **same** pre-existing `deploy/` allowlist-omission nodes present
  on this branch alone — zero new failing nodes from composition.
- This branch therefore carries **no duplicate** of #388 guard
  (`test_enforcement_never_reads_step_conclusion`); it only *cites* it, so the two
  do not diverge.
