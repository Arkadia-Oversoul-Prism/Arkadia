# Gate hygiene — measured composability of the current uncovered-debt PR cluster (#354/#355/#356/#357)

- **Mode**: read-only measurement on a throwaway worktree + one new guard test. No production
  file, authority path, or mutation path modified. No PR merged, nothing pushed to `main`.
- **Observed**: automation run, Python 3.13 / pytest 9.1.1.
- **Source of truth**: live `git`/`gh` state at observation time, re-derived locally. CI
  conclusions are reported separately from local measurements and are never promoted into
  production truth.

---

## 1. Why this pass exists

The open-PR clusters that reduce baseline debt have been queued independently. Several of them
edit the *same* files — most notably the tail of `AGENTS.md`, which every gate-hygiene PR
appends to (the contention hazard already recorded in
`gate-hygiene-open-pr-queue-merge-order-map-01`). A PR that is green **alone** can still collide
with a sibling, and a set of green PRs is not evidence that the set is green. This pass measures
the composition directly rather than asserting it.

## 2. Reconstructed state

| Ref | SHA |
|---|---|
| `main` (origin) | `f96d5fd27d40110196ec22b114808efc0eb9dc05` |
| PR #354 head | `536a8c43` (`gate10/cp10-allowlist-deploy-surface-01`) |
| PR #355 head | `73104fdf` (`gate10/n-atlas-workflow-self-trigger-01`) |
| PR #356 head | `1bfbcc4f` (`gate-hygiene/lab-boundary-natlas-surface-01`) |
| PR #357 head | `4c3d8fb8` (`gate-hygiene/solspire-r1-r3-contract-repin`) |
| PR #347 head | `3f3024d9` (`gate-hygiene/landing-headline-repin-01`) — older base |

All four cluster heads are descendants of `f96d5fd2` (zero `main` commits between the base and
the heads).

## 3. Live baseline (re-measured, not inherited)

`python -m pytest tests/ -q -rEf --continue-on-collection-errors -p no:randomly`

| Tree | Result | Nodes |
|---|---|---|
| `main` `f96d5fd2` | 16 failed / 1770 passed / 22 skipped / 1 error | **17** |

- outcomes fingerprint `26c2b4c7b5efb56d0d54ab5888cdf955589f7633490c9a0c33d1ef63bba85798`
- ids fingerprint `571e599f91e680fe41f7318b6000c84dee8edc7c9c0535a3c897c7da89881224`

Node → owner map (every failing node is carried or classified):

| Node | Owner |
|---|---|
| 3 × `test_m02a_ci_gate_integrity` | **#354** |
| `test_ci_gate_trigger_coverage[n-atlas-developer-lab.yml]` | **#355** |
| 2 × `test_engineering_lab_api` | **#356** |
| 3 × `test_solspire_r1/r3` | **#357** |
| `test_ais_capability_profile_onboarding` | **#347** (older base) |
| 3 × `test_steward_filter` | classified F-02, Genesis-origin, not stale assertions |
| `test_ais_w2…::test_no_firebase_persistence_in_gate` | F-01 PROXY-INVALIDATION, awaiting sovereign |
| `test_identity_spine_w1…` + `test_m02_reasomate_truth…` | escalated SH-07 / W8 identity |
| `test_autonomy.py` (collection) | CE-01, sovereign-reserved |

## 4. Composition — measured, in merge order

Merged onto `f96d5fd2` in the order **#354 → #355 → #356 → #357**:

| Step | File touched | Conflict |
|---|---|---|
| #354 | `scripts/cp10_mutation_boundary_policy.py`, `AGENTS.md`, evidence | clean |
| #355 | `.github/workflows/n-atlas-developer-lab.yml` | clean |
| #356 | `tests/test_engineering_lab_api.py`, `AGENTS.md`, evidence | **`AGENTS.md`** |
| #357 | `tests/test_solspire_r1/r3`, `AGENTS.md`, evidence | **`AGENTS.md`** |

Both collisions are the same mechanical hazard: every one of these PRs appends to the file tail,
so each diff hunk header is `@@ -866,3 +866,N @@`. Git cannot auto-merge two hunks that both
claim the end of the same file. Resolution is a **union append** (not a choice between sides):
#354's account, then #356's, then #357's. No other path in any of the four PRs overlaps.

Composed tree: **`8f2b06ae03401c2ac02a46d6de076dd89fc75a4d`** (disposable worktree; not a
repository branch).

## 5. Composed measurement

`python -m pytest tests/ -q -rEf --continue-on-collection-errors -p no:randomly`

| Tree | Result | Nodes |
|---|---|---|
| composed #354→#357 | 7 failed / 1779 passed / 22 skipped / 1 error | **8** |

- outcomes fingerprint `e4415dbc2bd299fe3b9391fd75eed1123023fb0c63201335abf1955309d38f7c`
- ids fingerprint `2a8d57add4e595102c423b40d48c9b380660a1e22d1fc4ee218c9a2f6a2c9d2a`

**Node delta: `main` 17 → composed 8; `-9 / +0`.** Zero nodes added — the composition introduces
no regression. The remaining 8 are exactly the sovereign-reserved / unscheduled set in §3.

Individually re-verified on each PR's own tip (uncomposed):

| Tree | Test file | Result |
|---|---|---|
| #354 | `test_m02a_ci_gate_integrity.py` | 64 passed |
| #355 | `test_ci_gate_trigger_coverage.py` | 48 passed |
| #356 | `test_engineering_lab_api.py` | 5 passed |
| #357 | `test_solspire_r1/r3` | 8 passed |
| #347 | `test_ais_capability_profile_onboarding.py` | 4 passed |

## 6. Result classification

- `#354` / `#355`: **VERIFIED** — compose cleanly, no conflict, no regression.
- `#356` / `#357`: **VERIFIED subject to a mechanical union-append resolution of `AGENTS.md`**.
  They are green alone *and* green composed; the only obstacle is textual tail overlap.
- Cluster `#354→#357`: **VERIFIED** as a set (0 added nodes).
- `#347`: green on its own tip; separate (older) base, not part of this composition.

## 7. Remaining uncertainty / not claimed

- The composition was measured on a **disposable worktree**, not on `main`; it is a merge-order
  measurement, not production parity. It does not authorize any merge.
- The composed tree was not built on the frontend; Vite build remains environment-blocked.
- `test_autonomy.py` collection error is untouched (CE-01, sovereign-reserved).
- CI conclusions for the composed tree are not claimed; the measurement above is local.

## 8. Guard added (kept, not claimed)

`tests/test_open_pr_cluster_composability.py` encodes the one invariant a future pass must not
silently break: independent gate-hygiene PRs in this cluster may overlap **only** on `AGENTS.md`.
A future pass that has two live PRs editing the same test/script source is a real semantic
conflict, not a tail-append one, and must be surfaced before composition. The guard carries a
negative control that feeds it a same-file pair and asserts it is reported.
