# EVIDENCE — gate-hygiene / test-session DB intermittency attribution

> Attribution only. **No source, test, config, or `.gitignore` change in this pass.**
> The one-line fix already exists on PR #144. This pass supplies the mechanism that
> explains the intermittency PR #143 observed but could not attribute.

## 1. Bounded objective

Attribute the intermittent full-suite node
`tests/test_engineering_lab_agent_loop.py::test_agent_loop_does_not_mutate_repository`
(observed by PR #143 as `20, 21, 20, 21` failures across 4 full-suite runs on one SHA),
and classify it as pre-existing vs. blocker for the open-PR queue.

Completion condition: an experiment that reproduces the flip and names the exact
mechanism. Regression boundary: none (documentation-only). Authority boundary: none
required — no merge, no push to `main`.

## 2. What was already established (not re-derived)

- **PR #143 §2** correctly reports the node as intermittent, passing **8/8 in isolation**,
  and correctly reads the guard at `tests/test_engineering_lab_agent_loop.py:313-338`:
  it snapshots **global** `git status --porcelain` on `REPO_ROOT` before and after
  `execute_agent_loop` and asserts equality, so it is sensitive to repository writes made
  by *any other test in the same process*. PR #143 stops there: "test cross-contamination,
  not a boundary violation", **cause not identified**, proposed as its own workstream.
- **PR #144** (`gate-hygiene/test-session-db-isolation-01`, head `09521d2`) adds
  `.gitignore:25 data/solspire_projects.db*` and `_sandbox_solspire_store()`
  (`tests/conftest.py:70`) to stop the full suite materializing the canonical SolSpire store.

## 3. Root cause — the canonical store's SQLite sidecars

The two findings are one finding. On `main`, `.gitignore` ignores the store's **main file
only**:

```
data/solspire_projects.db        <- ignored
data/solspire_projects.db-wal    <- NOT ignored
data/solspire_projects.db-shm    <- NOT ignored
```

`git status --porcelain` is therefore **blind to the main file but reports the sidecars**.
Whenever any test in the session opens the canonical store, SQLite materializes
`-wal`/`-shm`, which appear as untracked paths. If that materialization lands **between**
the guard's `before` and `after` snapshots, the equality assertion flips — a 21-failure run.
If it lands outside that window, the run reports 20.

That is precisely the observed signature: the delta is exactly one node, and the node is
the only one whose subject is `git status`.

### Mechanism proof (reproduced, same machine, minutes apart)

```
### ON main (002b189)
$ touch data/solspire_projects.db-wal data/solspire_projects.db-shm
$ git status --porcelain
?? data/solspire_projects.db-shm
?? data/solspire_projects.db-wal
$ git check-ignore -v data/solspire_projects.db-wal
  NOT IGNORED -> pollutes status

### ON PR #144 (09521d2)
$ touch data/solspire_projects.db-wal data/solspire_projects.db-shm
$ git status --porcelain
  (empty — invisible to the guard)
$ git check-ignore -v data/solspire_projects.db-wal
.gitignore:25:data/solspire_projects.db*        data/solspire_projects.db-wal
```

On `main` the sidecars are visible to the guard; on PR #144 they are not. PR #144's
one-line change removes the guard's exposure **regardless of test ordering**, which is
why it is the correct remedy and not a reordering patch.

### Positive control — the store is genuinely created by the suite

```
$ python -m pytest tests/test_eden_solspire_01_instantiation.py tests/test_enterprise_onboarding.py -q
4 passed in 0.66s
$ ls data/solspire_projects.db*
data/solspire_projects.db          <- created
```

Both named modules pass in isolation; the store is created as a side effect. This is why
the pollution is order-dependent rather than deterministic.

## 4. Measurements this pass (not remembered)

| Run | Tree | Result |
|---|---|---|
| full suite ×2, clean tree | `main` `002b189` | `20 failed / 1041 passed / 11 skipped / 2 errors` (both runs identical) |
| full suite, pre-existing canonical store | `main` `002b189` | `20 failed / 1047 passed / 11 skipped / 2 errors` — **+6 passes, 0 new failures** |
| full suite, clean tree | PR #144 `09521d2` | `20 failed / 1047 passed / 11 skipped / 2 errors`; **canonical store NOT created** |
| `tests/architecture` | `main` `002b189` | **11 passed** |
| `python -m py_compile api/main.py` | `main` `002b189` | OK, 2519 lines (within the 2600 budget) |

The 20 failures are **identical in name and count** across all four full-suite runs; the
delta between the first two rows is a *pass-count* delta from ambient store state, not a
failure delta. No run this pass reproduced 21 — the flip is order-dependent by nature; the
mechanism is proven by the sidecar visibility experiment above, which does not depend on
catching the race.

## 5. Classification

| Item | Class | Note |
|---|---|---|
| Intermittent `test_agent_loop_does_not_mutate_repository` | **PRE-EXISTING, explained** | Cause identified: un-ignored SQLite sidecars of the canonical store. Not a boundary violation — the agent loop's own allowlist is `("git",)`. |
| 20 full-suite failures | **PRE-EXISTING BASELINE DEBT** | Identical set/count across all runs. Not attributed to any open PR. Not fixed here (rule: do not fix baseline debt under an unrelated gate). |
| 2 collection errors (`test_render_codex.py` → `archive/legacy_python/codex_brain.py` → `arkadia_drive_sync`) | **PRE-EXISTING, environmental import** | Matches documented baseline; not an environment-setup defect. |
| Canonical store materialized by the suite | **FIXED BY PR #144** | Verified: with PR #144 checked out, a full-suite run creates no `data/solspire_projects.db*`. |

## 6. Queue recommendation

All three open PRs are `MERGEABLE` / `CLEAN` against `main @ 002b189`, heads unchanged:

| PR | Head | Scope | Merge interaction |
|---|---|---|---|
| #142 | `59fbb531` | SH-05 gate-artifact provenance — docs only | none |
| #143 | `7d79f38` | Gate-2 production parity — `AGENTS.md`, evidence, `scripts/gate2_backend_observation.py` | none |
| #144 | `09521d2` | `.gitignore` + `tests/conftest.py` | none |

No file overlap between the three diffs — they are independently mergeable. **#144 is the
highest-value merge for suite reliability** because it removes the guard's exposure to
sidecar churn and stops the test session writing the canonical store. **Sovereign merge
required; no merge performed by this pass.**

## 7. Remaining uncertainty

- The race was not directly caught in the act this pass (20, 20, 20, 20 across four runs).
  The attribution rests on the sidecar-visibility experiment, which is deterministic and
  order-independent. A 21-failure reproduction would strengthen it further.
- Whether `data/solspire_projects.db` is intentionally tracked is not asserted here; on
  `main` it is untracked-and-ignored, and `data/solspire_projects.db*` preserves that.
- PR #143 §2 should be updated to point at this attribution so the two records agree.
  That is a one-line evidence edit on PR #143 — **not performed in this pass** (it would
  widen scope across PRs); recorded for the sovereign.
