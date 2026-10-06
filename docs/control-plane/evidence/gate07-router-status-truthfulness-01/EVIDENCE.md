# EVIDENCE — gate07/router-status-truthfulness-01

Trajectory: `ARKADIA-CONSOLE-COMPLETION-01` (in progress)
Move class: bounded engineering guard (no gate promotion, no authority change)
PR: #322 · branch `gate07/router-status-truthfulness`
Base: `main` @ `451e41a30fcbff4a65326e897a84818cc623b769`
Head: `62d2bc50f0e0a4cb958e7c46b9eb3bd23b6cdfd5` (pre-evidence commit)

## Defect

`weaver/engineering_router.select_next_move()` dropped any move whose status was
outside its vocabulary with a silent `continue`, then fell through to
`no legal pending move (all complete or dependencies unresolved)`. That message is
false whenever a live frontier exists at an unrecognized status — the session cannot
name why it has no move.

Reproduced on the live console trajectory: moves `G12-A` and `G12-C` sit at
`merged_acceptance_pending`, which is absent from both the router vocabulary
(`in_progress, pending, revision_required` active; `accepted, completed, merged`
terminal) and the `main` trajectory schema enum
(`pending, revision_required, completed, accepted, blocked, failed, aborted`).

## Measured behaviour (old vs new, same input)

Command: load `main`'s router and the branch router side by side, feed the live
console trajectory in its post-PR-#319 shape (moves lifted to top level).

| Trajectory shape | Old router | New router |
|---|---|---|
| nested (current `main`) | `no legal pending move (…)` | `no legal pending move (…)` — unchanged |
| flat (post-#319) | `no legal pending move (…)` — **false** | names `G12-A`/`G12-C` at `merged_acceptance_pending` + expected vocabulary |

The nested shape is deliberately unchanged: the fallback message is emitted only
when no move was unrecognized. This is a truthfulness fix, not a routing change.

## Negative control

Against the pre-fix router, 3 guard assertions fail:

- `test_unrecognized_status_is_reported_not_silently_skipped`
- `test_unrecognized_status_is_not_misreported_as_all_complete`
- `test_every_unrecognized_status_is_named`

## CI liveness (the point of this move)

The guard was reachable by no workflow: `sg-02-fe-2-v.yml` is path-filtered and does
not list `weaver/engineering_router.py`. `.github/workflows/weaver-mvp2-validation.yml`
now selects the guard on both `push` and `pull_request` (identical filters) and names
it in a `run:` step. `test_guard_is_selected_and_executed_by_a_workflow` asserts
trigger **and** execution — a guard that is triggered but not executed is decoration.

Observed on PR #322 (run `37389820733`, job `112031977950`):

```
mvp2-validation success
  success | Weaver MVP2 and authority-boundary regressions
  success | Engineering-router status truthfulness guard
```

## Test results

| Suite | Result |
|---|---|
| `tests/test_engineering_router_status_truthfulness.py` | 8 passed, 1 skipped |
| `tests/test_engineering_scheduler_bootstrap.py` | passed |
| `tests/architecture` | 11 passed |
| CP10 mutation boundary judge (incl. new test path) | PASS |

The single skip is the live-trajectory probe: the trajectory does not load on this
revision (the structural slip PR #319 repairs). Unit behaviour is proven with
synthetic trajectories, including the negative control.

## Baseline comparison (node-set identity)

Full suite `-rEf --continue-on-collection-errors`, branch vs `main` @ `451e41a` in a
detached worktree:

- failing/error **node sets identical** — 79 nodes, `diff` empty
- 62 failed / 17 errors on **both** sides; passed 1326 vs 1318 (+8 = the new file)
- 62F/17E is pre-existing environment debt, not attributable to this change

## Independent pre-existing failures (not this change)

- `provider-routing` (run `37389821712`) fails at collection:
  `ImportError: cannot import name 'load_autonomy_config' from 'weaver.autonomy'` —
  the CE-01 module-vs-package collision, reserved to the sovereign.
- `Vercel – console` fails on `main` itself; not attributable to this PR.

## Authorization boundary

Review-gated. No merge, no deploy, no self-authorization. Human sovereign merges.
