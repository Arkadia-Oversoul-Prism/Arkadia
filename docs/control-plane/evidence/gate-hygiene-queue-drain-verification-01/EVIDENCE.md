# gate-hygiene — 20-PR queue drain : independent verification + Gate 2 runtime closure

Pass: `gate-hygiene/queue-drain-verification-01`
Date: 2026-10-01 (UTC)
Base main: `002b189dd95e41c9b4f4cca33d08b4121453d289`
Authority: no merge, no push to `main`, no force-push. Human-only merge.

**Type:** bounded evidence pass. **No source, test, or governance change.**

This pass **independently reproduces** PR #159's and PR #162's composition measurements
from a full clone, corrects one claim in #162's evidence, and closes the *runtime* half of
the Gate 2 boundary using #143's own observation harness.

---

## 1. What was re-measured, and against what

Every number below was produced in this pass on a worktree cut from `main` @ `002b189`.
Nothing is inherited from #159, #162, or the contract document.

| measurement | value |
|---|---|
| `main` SHA | `002b189dd95e41c9b4f4cca33d08b4121453d289` |
| `tests/architecture` | **11 passed** (1.26 s) |
| full suite on clean `main` | **20 failed / 1039 passed / 13 skipped / 2 errors** |
| `api/main.py` | 2519 / 2600 lines; `py_compile` OK |

> The contract's stated baseline (`804 passed / 54 failed / 12 skipped`, arch `9/10`) is
> **stale**. #159 and #162 already recorded this; this pass confirms it a third time from a
> fresh clone.

Run command for every full-suite figure:

```bash
PYTHONPATH=archive/legacy_python python3 -m pytest tests/ -q --continue-on-collection-errors
```

`--continue-on-collection-errors` is required: without it the two pre-existing collection
errors (`tests/test_autonomy.py`, `tests/test_render_codex.py`) mask the rest of the run.

## 2. Composition — independently reproduced

`git merge --no-edit` each PR head, in order, onto a worktree cut from `main`.

| sequence | result |
|---|---|
| **18 PRs** — `157 156 155 151 152 153 154 142 144 145 146 148 149 150 158 159 160 161` | **clean at every step** |
| **all 20 PRs** — the 18 plus `#143`, `#147` (inserted before `#150`) | **CONFLICT at `#150`: `AGENTS.md` only** |

This reproduces #162 §3 exactly. The conflict is a **single path** (`AGENTS.md`), it is
surfaced by **`#150`**, and excluding `#143` and `#147` removes it. `#147` is stacked on
`#143`'s branch (`base = gate-hygiene/gate2-production-parity-02`), so `#143`'s `AGENTS.md`
bytes reach the tree through `#147`.

## 3. Greenness — reproduced, and one claim in #162 corrected

| tree | failed | passed | skipped | errors |
|---|---|---|---|---|
| clean `main` `002b189` | 20 | 1039 | 13 | 2 |
| drain set (18 PRs), **unpatched** | **19** | **1090** | 15 | 1 |
| drain set (18 PRs), **#159 repair applied** | **18** | **1091** | 15 | 1 |

Both composed figures match #159's table exactly. **The unpatched composition is not
green** — it carries one failure the clean baseline does not:

```
FAILED tests/test_documented_route_contract.py::test_health_route_documentation_matches_the_served_app
```

> ### Correction to PR #162
>
> #162 §6 states *"Introduced by the queue: NONE"* and reports the drain tree as
> **18 failed / 1091 passed**. That figure is the tree **with #159's repair already
> applied**. Measured without the repair the same tree is **19 failed / 1090 passed**.
>
> #162's own §7 contains the correct numbers and says the repair "must be **applied** (not
> merely attached) before or during #159's merge, or the drain set lands 1 node red." So
> §6's headline is inconsistent with §7 of the same document. The defect is not the
> measurement — it is that **§6 reads as a merge-authorising green result when the tree a
> sovereign would actually get is red by one node.**
>
> The node-set delta versus `main` is therefore **2 fixed / 1 introduced** unpatched, and
> **3 fixed / 0 introduced** patched.

**Fixed by the queue** (in `main`, absent from drain — patched tree):

```
ERROR  tests/test_render_codex.py                                              (PR #149)
FAILED tests/test_engineering_scheduler_bootstrap.py::test_blocked_dependency_skips_move  (PR #148)
FAILED tests/test_engineering_scheduler_bootstrap.py::test_dry_run_evidence               (PR #148)
```

**Pre-existing and unchanged:** `ERROR tests/test_autonomy.py` (`load_autonomy_config`).

## 4. The #159 repair is load-bearing — verified by applying it

`patches/health-row-doc-repair.patch` was extracted from `pr-159` and applied to the
composed drain tree:

```
git apply --check  ->  clean
tests/test_documented_route_contract.py:  1 failed / 8 passed  ->  9 passed
full suite:  19 failed / 1090 passed  ->  18 failed / 1091 passed
```

`DEPLOYMENT_GUIDE.md` only; `+5/-4`. No other file moves.

**Defect mechanism.** PR #154 adds `GET /health` to `api/main.py` but does **not** touch
`DEPLOYMENT_GUIDE.md` — its diffstat is `api/main.py`, one evidence pair, one test file.
PR #156 authors the route-contract guard, which requires a *table row* for every served
route. Merged alone each is correct (#156's file is absent on #154, so the test never runs
there; #154 serves `/health` with no guard present). Merged together the guard sees a
served `/health` with no documented row.

**Correct home for the repair:** the defect originates in #154 (route added, documentation
not updated). The patch applies cleanly to `main` **and** to the drain tree, and is
idempotent, so it can be applied at the **#154 step** — as #159 itself recommends — or
carried in a small hygiene PR that must merge **before #159**. It should not be left as an
unapplied artifact on the branch it is needed for.

## 5. CP10 mutation boundary

Every path in the drain set's diff was judged against the canonical policy module:

```bash
python3 scripts/cp10_mutation_boundary_policy.py --judge   # stdin: union of drain diff paths
-> Mutation boundary PASS (M02A legitimate-surface + constitutional denylist)   exit=0
```

The 21 unique paths (including `AGENTS.md`, `DEPLOYMENT_GUIDE.md`, `api/main.py`, the
`docs/control-plane/evidence/**` trees, `tests/**`, and #160's `web/public_prism/`
build-integrity files) are all admitted. **No allowlist omission.**

## 6. Gate 2 — the runtime boundary, observed

#143 ships a read-only observation harness (`scripts/gate2_production_observation.py`,
stdlib only, holds no Vercel credential, performs no mutation). It was run unmodified this
pass. Its output:

```
main SHA                 : 002b189dd95e41c9b4f4cca33d08b4121453d289
newest Production deploy : 002b189dd95e  id=6749238709  2026-09-30T01:23:16Z
  ref == sha == main     : True
alias https://arkadia-prism.vercel.app/ -> HTTP 200
SOURCE-LINEAGE CLOSURE   : all 12 candidate Production SHAs descend from the last commit
                           touching a frontend build input (b377a01) -> True
```

| link | classification |
|---|---|
| current main resolved | **VERIFIED** |
| main → deployment identity | **VERIFIED** (`002b189dd95e`, ref == sha == main) |
| deployment build output observed | BLOCKED |
| alias reachable | **VERIFIED** |
| alias → deployment SHA binding | UNKNOWN — *immaterial*: all candidates share frontend source |
| build ↔ source lineage | **VERIFIED** (marker set matches, source closed) |
| browser-rendered UI correctness | UNKNOWN |
| production acceptance | **NOT CLAIMED** (human authority) |

The deployment identity question is **answered**: production serves a build whose source is
`main` @ `002b189`. Alias→SHA is unobservable *and* immaterial, because every candidate SHA
descends from the last frontend-build-input commit, so all candidates compile identical
frontend source.

## 7. Gate 2 — a real defect found in the runtime surface (source-side)

The harness flagged one marker **absent** from the deployed artifact although present in
source:

```
activity-runtime-draft.v1:   0 deployed / >0 expected   ->  SG-04 REGRESSION
```

A competing explanation had to be excluded before this could be called a deployment defect:
`ActivityRuntime.tsx` might simply be tree-shaken out of the bundle. **It is not.** The
deployed bundle (`assets/index-CHFFyuSc.js`, 2 025 825 bytes, fetched and grepped directly)
contains `CapabilityChamber`'s own literals — `sg03-contract-boundary` ×1,
`learning-activity-work-surface` ×1, `spiral-grove` ×4 — while `ActivityRuntime`'s
(`activity-surface-`, `activity-runtime-draft`) are ×0. The importer is bundled; the import
is not.

**Cause, established from history:**

| commit | `import ActivityRuntime` | `return <ActivityRuntime …>` |
|---|---|---|
| `74f5494` (introduces both files) | present | **present** |
| `44e1c99` (`feat(ais): capture explicit local evidence from grove work`) | **removed** | **removed** |
| `ff80b8c` (merge `main` into `sg-04-learning-activity-runtime`) | re-added | **still absent** |
| `b377a01` → `main` | present | **still absent** |

`git merge-base --is-ancestor ff80b8c main` → true, and `CapabilityChamber.tsx` on `main` is
byte-identical to `ff80b8c`. So `main` today imports `ActivityRuntime` and **never renders
it** — a dead import. The deployed artifact matches `main` faithfully; this is **not** a
stale deployment.

The repository already has four failing tests asserting exactly this invariant:

```
FAILED tests/test_spiral_grove_activity_runtime.py::test_runtime_is_mounted_by_the_capability_chamber
FAILED tests/test_spiral_grove_activity_runtime.py::test_runtime_dispatches_all_eight_kinds_to_deterministic_renderers
FAILED tests/test_spiral_grove_activity_runtime.py::test_chamber_preserves_sg03_downstream_boundary
FAILED tests/test_spiral_grove_activity_runtime.py::test_spiral_grove_uses_the_nexus_canonical_header
```

They are **pre-existing baseline debt** (present on `main`, unchanged by the queue) and
**must not** be attributed to any PR in the drain set.

**Correction to the harness's own wording:** its label "SG-04 REGRESSION" is a *source-vs-
artifact marker diff*, not evidence that a deploy regressed. Here source and artifact agree.
The regression was introduced in source at `44e1c99` and shipped. The label should read
`SOURCE-SIDE MOUNT REGRESSION (deployed artifact matches main)`.

## 8. #143 — substantive work is separable

`#143` is `AGENTS.md (+265/-83)` plus eight new files that never touch `AGENTS.md`:

```
scripts/gate2_backend_observation.py      330   tests/test_gate2_backend_observation.py   179
scripts/gate2_browser_observation.py      289   tests/test_gate2_browser_observation.py   177
scripts/gate2_production_observation.py   378
docs/control-plane/evidence/gate-hygiene-gate2-production-parity-02/{EVIDENCE,WORKSTREAM_STATE}.md
```

The harness and its tests are self-contained and **already proven useful** (§6, §7 above ran
unmodified). Re-cutting #143 as `#150`'s `AGENTS.md` bytes + these eight files is
**feasible and conflict-free** — a candidate for a later bounded pass, not this one.

## 9. What this pass does not do

- It does **not** merge, push to `main`, or force-push.
- It does **not** apply #159's repair to `main` or to any PR branch.
- It does **not** edit `AGENTS.md`, any test, any source file, or any governance surface.
- It does **not** fix the four `test_spiral_grove_activity_runtime.py` failures — they are
  baseline debt, and repairing them is a product decision (§7), not hygiene.
- It does **not** claim production acceptance, and it does **not** promote a
  `NOT CLAIMED` boundary to `VERIFIED`.

## 10. Classification

`VERIFIED` for the queue measurements and the Gate 2 **source/identity** chain.
`BLOCKED` for deployment build-output observation and browser-rendered UI correctness
(no Vercel credential; no browser runtime in this sandbox).

**Sovereign actions requested:**

1. Merge **#150**. Do **not** merge **#143**. Close **#147** as superseded.
2. Drain the remaining 18 in any order — but **apply `health-row-doc-repair.patch` at the
   #154 step** (or land it in a hygiene PR before #159), or the drain lands **1 node red**.
3. Note that #162's §6 headline ("Introduced: NONE", 18/1091) describes the *patched* tree;
   unpatched it is 19/1090. Do not read #162 §6 as green-on-merge.
4. Optionally authorise a later bounded pass to re-cut #143's harness onto `#150`'s bytes.
