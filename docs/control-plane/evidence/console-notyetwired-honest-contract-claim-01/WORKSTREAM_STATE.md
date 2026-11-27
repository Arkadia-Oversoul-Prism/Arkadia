# Workstream state — console `NotYetWired` honest contract claim

**Observation time:** 2026-11-22T10:xx Z (this cycle)
**Base:** `main` @ `034d8879d68ecf8ed4c291eb0ab07432657a06a1` (live `main`, confirmed via
`git/ref/heads/main`)
**Branch:** `fix/console-notyetwired-honest-contract-claim-01`

## Reconciled state at the start of the cycle

| boundary | state | evidence |
|---|---|---|
| current main | `034d8879d68ecf8ed4c291eb0ab07432657a06a1` | `git/ref/heads/main` |
| working tree | clean, full clone (`is-shallow-repository` = false) | `git status` |
| main CI | green | check-runs on `034d8879`: `Full-history secret scan`, `boot-syntax`, `console-contract`, `lane-doc-currency`, `posture-currency`, `test`, `weaver_evolution` all `success` |
| lane doc currency | `--check` exit 0 | `python scripts/lane_state.py --check` |
| production identity | **VERIFIED** | `GET /api/version` -> `source_revision == 034d8879…`, `revision_source: RENDER_GIT_COMMIT`, `revision_conflict: false` |
| production reachability | 200 after one cold start | first probe `503` / timeout, then three consecutive `200`; Render cold start, not an outage |
| active console build | green | `corepack pnpm install --frozen-lockfile` + `pnpm build` (`tsc --noEmit` + vite, 170 modules) |

Nine open PRs, all draft and `CLEAN`: #675, #677, #678, #679, #680, #681, #682, #683, #684.
Their changed paths are largely disjoint (`scripts/lane_state.py` vs
`scripts/lane_state_refresh.py`, one evidence doc + one test each), so no textual conflict was
found. Merge execution is human-only (GOV-03); nothing here merges them.

## This change

See `EVIDENCE.md`. One shared component's copy plus one guard.

## Regression — failing/error node set, same environment

Both trees run with `-q -rEf --continue-on-collection-errors`.

```
branch  : 19 failed, 4235 passed, 35 skipped, 1 error   (20 nodes, sha256 642021cb240a30e2…)
main    : 29 failed, 4224 passed, 35 skipped, 1 error   (30 nodes, sha256 fd29a5ae00e288df…)
```

`comm -13` (nodes only on the branch) is **empty**: the branch introduces zero new failures.
The branch's node set is a strict subset of `main`'s.

The 10-node difference is **entirely** `tests/test_mission_lifecycle_adapter_contract.py`, and
it is a worktree artifact, not repository debt: the `main` baseline was measured in a detached
worktree at `/tmp/wt-main`, which has no `web/arkadia_console/node_modules`, and the guard
asserts the repository TypeScript compiler exists:

```
AssertionError: the repository TypeScript compiler is missing at
/tmp/wt-main/web/arkadia_console/node_modules/typescript/lib/typescript.js
```

The same file on the branch tree (which has `node_modules`): `10 passed`.

**Consequence:** the environment-independent claim is *no new failing/error nodes*. The
absolute counts are not comparable across the two directories — passed counts move with the
installed dependency set and the presence of `node_modules`, exactly as the repo's baseline
guidance records. Attribute by node identity, never by totals.

## Observations recorded, not repaired (separate proposed work)

1. **`data/engineering_lab/agent_events.jsonl` is stageable.** A full-suite run creates it and
   no `.gitignore` rule covers it (`git check-ignore` exit 1). `.gitignore` already carries
   per-store families (`data/solspire_projects.db*`, `data/economic_seams.db*`), so this is the
   same class one store over. A `git add -A` would sweep a runtime artifact into a commit.
   Bounded repair: one ignore rule + a pin in `tests/test_repo_hygiene_gitignore.py`. **Not
   performed here** — unrelated to this PR's subject.
2. **The two `NotYetWired` states are still not visually distinct.** The copy no longer makes a
   false claim, but "contract absent" and "interface absent" render identically. Distinguishing
   them needs an explicit `state` prop and a page-owned change in lanes 1–4.
3. **PR #684's snapshot records live lane threads.** Its own "known limitation" says a merge of
   any recorded PR (#677–#680) makes the snapshot stale. If #684 merges first, re-derive before
   merging those. Merge order and execution remain human decisions.

## Next permitted action

Human review of the draft PR. No merge, deployment, or production acceptance is claimed or
authorized.
