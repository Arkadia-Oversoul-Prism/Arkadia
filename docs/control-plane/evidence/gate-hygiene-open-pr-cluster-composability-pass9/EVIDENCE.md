# Gate hygiene — pass 9: re-verify pass-8 composition on current main, widen the boundary to the full open-PR population

- **Mode**: read-only measurement on a throwaway worktree + guard extension. No production file,
  authority path, or mutation path modified. No PR merged, nothing pushed to `main`.
- **Observed**: automation run, Python 3.13.15 / pytest 9.1.1, 2026-10-08.
- **Source of truth**: live `git`/`gh` state at observation time, re-derived locally. CI
  conclusions are reported separately from local measurements and are never promoted into
  production truth.
- **Continues**: `gate-hygiene-open-pr-cluster-composability-pass8` (PR #358), same workstream.

---

## 1. Why this pass exists

Pass 8 measured the composability of the uncovered-debt cluster **#354 → #357** on `main`
`f96d5fd2` and recorded the result as `READY FOR SOVEREIGN MERGE`. Two things had changed by the
time of this pass:

1. `main` **advanced** past the pass-8 base. `f96d5fd2` → `4edab519` (PR #359, "Repair N-ATLaS
   Gradio SSE boundary", merged after the pass-8 measurement). #359 touched
   `lab/engineering_lab/natlas.py` and `tests/test_natlas_developer_lab.py`. A composition result
   measured at a stale base is not evidence about the current base, so the claim had to be
   **re-measured**, not re-asserted.
2. Pass 8 measured **only** the four PRs in the cluster. Its manifest listed #354/#355/#356/#357;
   the guard it added encodes that manifest. It therefore could **not** see an overlap between any
   other pair of open PRs. Widening the population to *every* open PR is the point of this pass.

## 2. Reconstructed state

| Ref | SHA |
|---|---|
| `main` (origin) | `4edab519a6033be2c4a1dface2c6e4b012b9be1c` |
| PR #354 head | `536a8c43` (`gate10/cp10-allowlist-deploy-surface-01`) |
| PR #355 head | `73104fdf` (`gate10/n-atlas-workflow-self-trigger-01`) |
| PR #356 head | `1bfbcc4f` (`gate-hygiene/lab-boundary-natlas-surface-01`) |
| PR #357 head | `4c3d8fb8` (`gate-hygiene/solspire-r1-r3-contract-repin`) |
| PR #358 head | `20fd62e2e75cb0938bf6deb7889714eb815e7c33` (this workstream) |

All twelve currently-open PRs are enumerated in `cluster_manifest.json` (§5), each with its
branch head SHA and changed-path list as returned by the live API at observation time.

## 3. Live baseline (re-measured, not inherited)

`python -m pytest tests/ -q -rEf --continue-on-collection-errors`

| Tree | Result | Nodes |
|---|---|---|
| `main` `4edab519` | 16 failed / 1772 passed / 22 skipped / 2 warnings / 1 error | **17** |

- outcomes fingerprint `26c2b4c7b5efb56d0d54ab5888cdf955589f7633490c9a0c33d1ef63bba85798`
- ids fingerprint `571e599f91e680fe41f7318b6000c84dee8edc7c9c0535a3c897c7da89881224`

This **independently reproduces** the baseline pass 8 recorded at `f96d5fd2` — same 17 nodes, same
pair of fingerprints. #359 therefore moved `main` without changing the failing-node set.

## 4. Re-verification of the pass-8 composition on the current base

Merged onto `4edab519` in the order **#354 → #355 → #356 → #357**:

| Step | Conflict |
|---|---|
| #354 | clean |
| #355 | clean |
| #356 | `AGENTS.md` only — union append |
| #357 | `AGENTS.md` only — union append |

Both collisions are the mechanical tail hazard: every gate-hygiene PR appends to the end of
`AGENTS.md`, so each diff hunk claims the file's final line and git cannot auto-merge two such
hunks. Resolution is a union append (both accounts kept, in merge order). No other path in the
four PRs overlaps.

| Tree | Result | Nodes |
|---|---|---|
| composed #354→#357 on `4edab519` | 7 failed / 1781 passed / 22 skipped / 2 warnings / 1 error | **8** |

- outcomes fingerprint `e4415dbc2bd299fe3b9391fd75eed1123023fb0c63201335abf1955309d38f7c`
- ids fingerprint `2a8d57add4e595102c423b40d48c9b380660a1e22d1fc4ee218c9a2f6a2c9d2a`

**Node delta: `main` 17 → composed 8; `-9 / +0`.** Both fingerprints are **byte-identical** to the
pair pass 8 recorded at `f96d5fd2`. The composition result is therefore **not stale**:

- a different base (`4edab519` vs `f96d5fd2`),
- the same absolute node count,
- the same node-set fingerprints,
- zero added nodes,

which is the strongest form of "the base move is immaterial to this cluster" — the composed
*failing set* did not move with `main`, so nothing in #359 interacts with #354-#357.

The 9 removed nodes are exactly the PR-owned set:
`test_m02a_ci_gate_integrity` ×3 (#354), `test_ci_gate_trigger_coverage[n-atlas-developer-lab.yml]`
(#355), `test_engineering_lab_api` ×2 (#356), `test_solspire_r1_governance_convergence` ×2 and
`test_solspire_r3_execution_runtime` ×1 (#357). The remaining 8 are the sovereign-reserved /
unscheduled set (3 × `test_steward_filter`, F-01, SH-07/W8, CE-01, and the `#347`-owned landing
node which is not in this cluster).

## 5. Widening the boundary — the full open-PR population

Pass 8's manifest covered #354-#357. This pass intersected the changed-path lists of **all twelve**
open PRs (#337, #338, #347, #348, #349, #350, #351, #354, #355, #356, #357, #358). Excluding
`AGENTS.md` (the shared tail surface every gate-hygiene PR appends to), **exactly one** overlap
exists across the whole population:

**#337 × #338**, sharing four load-bearing paths:

```
api/lab_routes.py
web/public_prism/src/App.tsx
web/public_prism/src/components/ArkadiaNavigation.tsx
web/public_prism/src/pages/EngineeringLabPage.tsx
```

Merging #337 then #338 onto `4edab519` (a throwaway worktree) conflicts on **all four** files:

| File | Conflict hunks |
|---|---|
| `api/lab_routes.py` | 3 |
| `web/public_prism/src/App.tsx` | 2 |
| `web/public_prism/src/components/ArkadiaNavigation.tsx` | 3 |
| `web/public_prism/src/pages/EngineeringLabPage.tsx` | 7 (add/add) |

### Classification — dependency pair, not independent-overlap hazard

`origin/pr337` is **not** an ancestor of `origin/pr338`, but the two PRs are not independent work:

- #337 body: "Isolated AEAS-01 operator surface over the existing Engineering Lab runtime. Adds
  authenticated native EventStream SSE transport and browser operator shell."
- #338 body: "Isolated browser execution instrument for Engineering Lab verification. Adds a
  Playwright Chromium runner with evidence artifacts … The runner uses real deployed Login
  UI/Firebase auth."
- #338 carries `docs/control-plane/evidence/aeas-01-02-gate-acceptance-01/deployed-render-pr337.json`
  — its evidence is *about* #337's deployment.

This is a **component-plus-instrument** pairing (a surface and the harness that verifies it), not
the hazard the pass-8 guard targets (two independent PRs silently editing the same source). The
correct handling differs, and the difference matters:

- For the pass-8 hazard, the remedy is to **not compose the pair** and surface the overlap.
- For a dependency pair, the pair **must** be reconciled before either lands, and whichever lands
  second must be rebased onto the first. The 15 conflict hunks are exactly that reconciliation
  work — it is **not** a mechanical union append, it is a real semantic merge that only the pair's
  author should perform.

Neither PR is merged by this pass; the classification is recorded so a later pass does not attempt
to compose them blind, and does not mistake them for an independent-overlap hazard.

## 6. Guard extension (`tests/test_open_pr_cluster_composability.py`)

The pass-8 guard read only the pass-8 manifest, so its silence about #337/#338 was vacuous — it was
silent because it never looked. This pass adds:

- `cluster_manifest.json` (pass-9) recording the **full** open-PR population, so the population is
  evidence, not memory.
- `test_full_population_overlaps_are_all_classified_dependency_pairs` — every non-`AGENTS.md`
  overlap across the whole population must be a *classified* dependency pair. An unclassified
  overlap fails the guard and must be surfaced before composition.
- `test_the_337_338_dependency_pair_is_actually_present` — a **positive control**: the detector
  must *find* the pair with the recorded shared paths. Without it, the test above would also pass
  if #338's manifest entry were dropped.
- `test_full_population_detector_flags_an_unclassified_overlap_negative_control` — a **negative
  control** feeding the detector a synthetic unclassified pair; it must be reported.

**Non-vacuity proven** (measured): with `_KNOWN_DEPENDENCY_PAIRS` emptied at runtime, the detector
reports `('337', '338', [4 shared paths])` instead of `[]`. The guard is silent *about the measured
pair* because it recognises it, not because it sees nothing.

The pass-8 tests and manifest are kept unchanged, so the prior values remain reproducible.

## 7. Result classification

- `#354` / `#355`: **VERIFIED** — compose cleanly on the current base, no conflict, no regression.
- `#356` / `#357`: **VERIFIED** — green alone *and* green composed; the only obstacle is the
  mechanical `AGENTS.md` tail overlap.
- Cluster `#354 → #357` re-measured on `4edab519`: **VERIFIED** as a set (17 → 8 nodes, `-9 / +0`,
  fingerprints byte-identical to pass 8). #359's base move is immaterial to this cluster.
- `#337` × `#338`: **CONTRADICTED as "independently mergeable"** — they share four load-bearing
  paths and conflict on all four (15 hunks). Reclassified as a **dependency pair**; both PRs left
  open and unmerged. This is a repository-source claim, not a runtime observation.

## 8. Remaining uncertainty / not claimed

- The composition was measured on a **disposable worktree**, not on `main`; it is a merge-order
  measurement, not production parity, and authorizes no merge.
- The composed tree was not built on the frontend; the Vite build remains environment-blocked.
- The #337/#338 conflict was measured but **not resolved** — resolving it is the pair author's
  semantic work, and this pass does not perform it.
- `test_autonomy.py` collection error is untouched (CE-01, sovereign-reserved).
- CI conclusions for either tree are not claimed; the measurements above are local.
