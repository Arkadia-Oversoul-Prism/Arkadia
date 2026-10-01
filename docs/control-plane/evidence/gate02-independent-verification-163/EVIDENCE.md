# GATE-02 — Independent verification of PR #163's source-side defect claim

**Type:** bounded evidence pass. **No source, test, or governance change.**
**Subject:** `Arkadia-Oversoul-Prism/Arkadia` PR **#163**
(`gate-hygiene/queue-drain-verification-01`), head `1e9d4002948674d643540e1260fa9341c295c805`.
**Base:** `main` @ `002b189dd95e41c9b4f4cca33d08b4121453d289`.

**Method:** every claim below was re-derived from a fresh clone, live GitHub API reads, and a
fresh local build of `main`. No claim is inherited from #163's prose.

---

## 1. Baseline fingerprint, independently re-measured

Established **before any change**, on `main` @ `002b189`, in this sandbox with third-party
dependencies installed:

```
PYTHONPATH=archive/legacy_python python -m pytest tests/ -q --continue-on-collection-errors
```

| measurement | contract's stated baseline | #163's claim | **this pass** |
|---|---|---|---|
| full suite | 804 / 54 / 12 / 2 err | 20 / 1039 / 13 / 2 err | **20 failed / 1039 passed / 13 skipped / 2 errors** |
| `tests/architecture` | 9/10 | 11 passed | **11 passed** |
| `api/main.py` | — | 2519 / 2600 | **2519 / 2600**, `py_compile` OK |

**Result: exact match to #163 on all three.** The contract's stated baseline
(804/54/12, arch 9/10) is **stale** — this is the fourth independent confirmation.

### Failing-node fingerprint (pinned, so a delta is attributable)

`20 failed` — the exact node set:

```
tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
tests/test_engineering_scheduler_bootstrap.py::test_blocked_dependency_skips_move
tests/test_engineering_scheduler_bootstrap.py::test_dry_run_evidence
tests/test_gate_serve_script.py::test_root_index_redirect_and_script_exists
tests/test_gate_status.py::test_gate_files_and_fetch_handling
tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
tests/test_solspire_r2_github_mutation.py::test_legacy_commit_file_fails_closed_without_network_write
tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
tests/test_spiral_grove_activity_runtime.py::test_chamber_preserves_sg03_downstream_boundary
tests/test_spiral_grove_activity_runtime.py::test_runtime_dispatches_all_eight_kinds_to_deterministic_renderers
tests/test_spiral_grove_activity_runtime.py::test_runtime_is_mounted_by_the_capability_chamber
tests/test_spiral_grove_activity_runtime.py::test_spiral_grove_uses_the_nexus_canonical_header
tests/test_spiral_grove_registry.py::test_ais_catalog_supports_progressive_creative_workflow
tests/test_spiral_grove_registry.py::test_registry_rejects_prerequisite_cycle
tests/test_steward_filter.py::test_allows_mythic_with_action
tests/test_steward_filter.py::test_blocks_identity_claims
tests/test_steward_filter.py::test_compress_to_choices
```

`2 errors` — collection only: `tests/test_autonomy.py`, `tests/test_render_codex.py`
(matches #163's "unchanged in both").

---

## 2. `CapabilityChamber.tsx` — the defect is real, and it is **three** defects

### 2.1 Source identity

`CapabilityChamber.tsx` on `main`:

```
git rev-parse HEAD:web/public_prism/src/components/spiral-grove/CapabilityChamber.tsx
-> 0cde2f782f1c17d6269334b2d4c56c166485d06e
```

#163 Addendum 02 claims the blob is `0cde2f782f1c`. **Confirmed, byte-for-byte.**

### 2.2 The render is genuinely absent

```
grep -c "<ActivityRuntime" CapabilityChamber.tsx   ->  0
```

`import ActivityRuntime from './ActivityRuntime'` (line 4) is present; no mount exists.
**#163's central claim is confirmed: `main` imports the runtime and never renders it.**

### 2.3 `tsc` — the defect class is wider than #163 recorded

Run against `main`'s own source (no `tsconfig.json` exists in `web/public_prism`; `tsc` was
driven with explicit flags):

```
node node_modules/typescript/bin/tsc --noEmit --jsx react-jsx --esModuleInterop \
  --skipLibCheck --target es2020 --moduleResolution bundler --module esnext \
  src/components/spiral-grove/CapabilityChamber.tsx
```

```
(25,83):  error TS2551: Property 'replaceAll' does not exist on type 'LearnerCapabilityStatus'.
(51,3):   error TS2304: Cannot find name 'useEffect'.
(55,685): error TS2551: Property 'replaceAll' does not exist on type 'LearningWorkMode'.
(56,142): error TS2551: Property 'replaceAll' does not exist on type 'LearningWorkMode'.
(56,377): error TS2304: Cannot find name 'surfaceMeta'.
```

**Six errors, three distinct defect classes.**

| # | defect | location | recorded by #163? |
|---|---|---|---|
| 1 | `useEffect` called, never imported (`import React, { useState }`) | `:51` | **yes** (Add. 02 §2.2) |
| 2 | `<ActivityRuntime>` imported, never rendered (dead import) | `:4` import / no mount | **yes** (pass 01 §7) |
| 3 | `surfaceMeta` referenced but never defined (used as `style={surfaceMeta}`) | `:56` | **no** |
| 4 | `replaceAll` called on a **string-literal union** — `LearnerCapabilityStatus` (`'NOT_STARTED' \| …`) | `:25` | **no** |
| 5 | `replaceAll` called on `LearningWorkMode` (same class) | `:55`, `:56` | **no** |

Defect 3 and 4/5 were flagged in this pass's pre-existing working notes; #163's pass 01 §7 and
Addendum 02 §2.2 enumerate only 1 and 2. The file carries **three** independent defect classes,
not two.

**Severity note.** Defect 4/5 is *not* merely a type-level nit. `replaceAll` is ES2021; the
union members are string literals so the call is well-typed at *runtime* — but under any
`lib` target below `ES2021` it is undefined behaviour, and it is a type error regardless.
Defect 3 (`surfaceMeta`) is a **hard `ReferenceError` on the same render path** as defect 1:
`surfaceMeta` is a free identifier exactly as `useEffect` is, and it is referenced in the
`open === true` branch (line 56) — the branch reached *only after* the chamber opens.

### 2.4 Why `vite build` does not catch any of this

```
vite build  ->  PASS (3438 modules transformed)
```

esbuild **strips types and does not type-check**. The build succeeding is not evidence that
the source is sound. This is why defects 1–5 survived to `main`.

---

## 3. Deployed artifact — independently re-observed

The strongest available runtime test, re-run from scratch against production:

| check | #163's claim | **this pass** |
|---|---|---|
| SPA shell | 997 bytes, one bundle ref | **HTTP 200, 997 bytes** |
| bundle ref | `assets/index-CHFFyuSc.js` | **`assets/index-CHFFyuSc.js`** |
| bundle bytes | 2 025 825 | **2 025 825** |
| bundle sha256 | `33861ef9b06f6fdf261f1f447ab6e28723b3843abe1f79953c1ac5621f1e5bc2` | **`33861ef9b06f6fdf261f1f447ab6e28723b3843abe1f79953c1ac5621f1e5bc2`** |

**Exact match.** Production serves the artifact #163 described.

### 3.1 Literal distribution — the importer is bundled, the import is not

| literal | #163's claim | **this pass** |
|---|---|---|
| `sg03-contract-boundary` | ×1 | **×1** |
| `learning-activity-work-surface` | ×1 | **×1** |
| `spiral-grove` | ×4 | **×4** |
| `activity-surface-` | ×0 | **×0** |
| `activity-runtime-draft` | ×0 | **×0** |
| `activity-runtime-complete` | ×0 | **×0** |

**Exact match.** `CapabilityChamber`'s own literals ship; `ActivityRuntime`'s do not.
The tree-shaking alternative is excluded by direct observation.

### 3.2 Addendum 03's free-identifier proof — reproduced exactly

| check | #163 Add. 03 | **this pass** |
|---|---|---|
| `(globalThis\|window\|self).useEffect` | 0 | **0** |
| `(var\|let\|const\|function) useEffect` | 0 | **0** |
| bare `useEffect(` calls | 1 | **1** |
| `x.useEffect(` calls (minifier's React alias) | 92 | **92** (93 total `.useEffect(` = 92 `x.` + 1 `current.`) |
| `useEffect=` assignment | internals shim | **`useEffect=function(e`** |

**Exact match on every figure.** The lone bare call sits inside the `CapabilityChamber`
chunk:

```js
,y]=x.useState(""),[b,v]=x.useState(""),[w,S]=x.useState(!1);useEffect(()=>{if(!(typeof window>"u"))try{u(window.localStorage.getItem(o)||"")
```

Its 92 siblings resolve through the minifier's `x` alias; this one does not. A resolvable
global would have been resolved. **A lone bare reference is the signature of a free
identifier.** Addendum 03's corrected label
(`ReferenceError: useEffect is not defined` **on render**) is **confirmed** — the defect is
*more* consequential than Addendum 02 recorded, not less.

### 3.3 Reproduced from `main`'s own source, not just from production

A **fresh local build of `main`** (bundle `index-xiYlcBh3.js`, 1 941 274 bytes) reproduces the
same signature:

| check | fresh build of `main` |
|---|---|
| bare `useEffect(` | **1** |
| global `useEffect` decl | **0** |
| `activity-runtime-draft` | **0** |
| `learning-activity-work-surface` | **1** |

**This closes the loop:** the defect is **source-side**, it is present in `main`'s bytes, and
the deployed artifact matches `main` faithfully. It is **not** a stale deployment, and **not**
an artifact-only anomaly.

---

## 4. Precision correction to #163's §7 (test attribution)

#163 pass 01 §7 groups four failing tests under the claim that they "assert exactly this
invariant" — the dropped `<ActivityRuntime>` mount:

```
FAILED tests/test_spiral_grove_activity_runtime.py::test_runtime_is_mounted_by_the_capability_chamber
FAILED tests/test_spiral_grove_activity_runtime.py::test_runtime_dispatches_all_eight_kinds_to_deterministic_renderers
FAILED tests/test_spiral_grove_activity_runtime.py::test_chamber_preserves_sg03_downstream_boundary
FAILED tests/test_spiral_grove_activity_runtime.py::test_spiral_grove_uses_the_nexus_canonical_header
```

Measured per-test, the failing assertions are **not** all the same invariant:

| test | line | failing assertion | attributed to |
|---|---|---|---|
| `::test_runtime_is_mounted_by_the_capability_chamber` | `:85` | `assert "<ActivityRuntime activity={activity} />" in chamber` | **dropped mount** ✔ |
| `::test_runtime_dispatches_all_eight_kinds_to_deterministic_renderers` | `:73` | `assert 'data-testid="activity-surface-research"' in runtime` | **`ActivityRuntime.tsx`** — the *imported file*, not the chamber |
| `::test_chamber_preserves_sg03_downstream_boundary` | `:110` | `assert "Evidence submission, assessment, and capability-state updates remain separate downstream stages." in chamber` | **chamber copy/doctrine**, not the mount |
| `::test_spiral_grove_uses_the_nexus_canonical_header` | `:115` | `assert "<h1" not in page` (fails on `SpiralGrovePage.tsx`) | **`SpiralGrovePage.tsx`** — a different file entirely |

Only **one of four** is the dropped-mount invariant. The other three are distinct
`ActivityRuntime.tsx` / chamber-copy / `SpiralGrovePage.tsx` assertions that happen to sit in
the same test file.

**This does not weaken #163's conclusion** — all four are genuine pre-existing baseline debt,
correctly excluded from the drain set's attribution, and the mount defect is real (§2.2). It
narrows the *mechanism* claim: "the repository already asserts this invariant in four failing
tests" should read **one** test asserts the mount invariant; the file holds four failures
across three files' worth of assertions.

Corroborating prior evidence: `docs/control-plane/evidence/gate-hygiene-sg04-canonical-header-merge-regression-01/EVIDENCE.md`
already records the `<h1>` failure as a **`SpiralGrovePage.tsx` route-dependence defect**, and
independently records the `CapabilityChamber` dead import at `:4` — consistent with this pass.

---

## 5. Adjacent claims spot-checked

| claim | #163 | **this pass** |
|---|---|---|
| `"/health"` absent from `api/main.py` on `main` (#154 adds it) | absent | **absent (0 occurrences)** |
| `sg-02-fe-2-v.yml` is **path-filtered** on `pull_request` (CP10 did not run on most drain PRs) | path-filtered | **confirmed** — workflow declares `paths:` incl. `web/public_prism/**`, `lab/**`, `api/lab_routes.py`, named tests |
| CP10 policy module is the single copy | `scripts/cp10_mutation_boundary_policy.py` | **present (8461 bytes)** |
| `api/main.py` line budget | 2519 / 2600 | **2519 / 2600**, `py_compile` OK |

---

## 6. Boundary honesty

- **Static determination only.** The `useEffect` / `surfaceMeta` `ReferenceError`-on-render is
  established from the deployed bundle and from a fresh build of `main`. The **rendered
  symptom** is **not** observed — no browser runtime in this sandbox.
- The browser-rendered half stays **`UNKNOWN`** and is **not** promoted. This pass does not
  upgrade it.
- **Production acceptance is `NOT CLAIMED`** — human authority.
- The 20-PR drain composition and the CI-greenness claims were **spot-checked**, not fully
  re-run; the full composition replay is #163's own evidence and is not independently
  reproduced here.

## 7. What this pass does not do

- It does **not** merge, push to `main`, or force-push.
- It does **not** edit `AGENTS.md`, any test, any source file, or any governance surface.
- It does **not** repair `CapabilityChamber.tsx` — repairing it is a product decision
  requiring a separate bounded authorization (§2.3 is the justification, not the mandate).
- It does **not** reclassify any baseline failure, and it **does not** attribute any of the 20
  failures to the drain set.

## 8. Classification

**`VERIFIED`** for #163's source-side defect claim, in full: the render is absent, the blob
matches, the deployed artifact matches the claim byte-for-byte, and the free-identifier
mechanism reproduces both in production and in a fresh build of `main`.

**`VERIFIED` with correction** for the test-attribution detail in §4 (one mount invariant, not
four) and the defect inventory in §2.3 (three defect classes, not two).

**`UNKNOWN`** (unchanged) for browser-rendered symptom.

---

*This evidence artifact was created by an AI agent (OpenHands) on behalf of the human sovereign.*
