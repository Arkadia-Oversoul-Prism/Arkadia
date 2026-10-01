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

## 6. The 20-PR drain set — arithmetic independently confirmed

Live `gh pr list --state open` at the time of this pass:

```
23 open:  142 143 144 145 146 147 148 149 150 151 152 153 154 155 156 157 158 159 160 161
          162 163 165
```

Removing #162 (evidence), #163 (evidence), and #165 (this pass's evidence) leaves the **20
drain PRs** #163 enumerates — and the arithmetic reconciles exactly:

| component | PRs | count |
|---|---|---|
| the 18-PR clean sequence | 142 144 145 146 148 149 150 151 152 153 154 155 156 157 158 159 160 161 | 18 |
| the two conflict-carrying PRs | 143, 147 | 2 |
| **drain total** | | **20** |
| non-drain evidence PRs open at #163's head | 162, 163 | 2 |
| **open at #163's head** | | **22** ✔ |

**The 20-PR drain claim is arithmetically verified** against live repository state. (#165 is
this pass's own PR and is correctly excluded from the drain.)

## 7. CI state at this pass's head

`gh pr checks 165` at head `fd9d04dda7b11cb45d9c2a4ffa96615470aafb3c`:

| check | result |
|---|---|
| `Full-history secret scan` | **pass** (11s) |
| `Vercel` | **pass** — deployment completed |
| `Vercel Preview Comments` | **pass** |

PR #165: `OPEN`, `draft=false`, `mergeable=MERGEABLE`, `mergeStateStatus=CLEAN`.

Consistent with #163 Addendum 02's correction: the gate names that actually run here are
`Full-history secret scan` and `Vercel Preview Comments` — **not** `sg-02-fe-2-v.yml`, which is
path-filtered and correctly did not trigger on an evidence-only diff (§5).

## 8. Boundary honesty

- **Static determination only.** The `useEffect` / `surfaceMeta` `ReferenceError`-on-render is
  established from the deployed bundle and from a fresh build of `main`. The **rendered
  symptom** is **not** observed — no browser runtime in this sandbox.
- The browser-rendered half stays **`UNKNOWN`** and is **not** promoted. This pass does not
  upgrade it.
- **Production acceptance is `NOT CLAIMED`** — human authority.
- The 20-PR drain composition and the CI-greenness claims were **spot-checked**, not fully
  re-run; the full composition replay is #163's own evidence and is not independently
  reproduced here.

## 9. What this pass does not do

- It does **not** merge, push to `main`, or force-push.
- It does **not** edit `AGENTS.md`, any test, any source file, or any governance surface.
- It does **not** repair `CapabilityChamber.tsx` — repairing it is a product decision
  requiring a separate bounded authorization (§2.3 is the justification, not the mandate).
- It does **not** reclassify any baseline failure, and it **does not** attribute any of the 20
  failures to the drain set.

## 10. Classification

**`VERIFIED`** for #163's source-side defect claim, in full: the render is absent, the blob
matches, the deployed artifact matches the claim byte-for-byte, and the free-identifier
mechanism reproduces both in production and in a fresh build of `main`.

**`VERIFIED` with correction** for the test-attribution detail in §4 (one mount invariant, not
four) and the defect inventory in §2.3 (three defect classes, not two).

**`UNKNOWN`** (unchanged) for browser-rendered symptom.

---

## 6. Correction — the `replaceAll` "defect class" is a lib-target artifact (pass 2)

§2.3 above reports "six errors, three distinct defect classes". That count is **wrong**, and the
error is caused by the command §2.3 itself records: `--target es2020`.

`String.prototype.replaceAll` is defined in `lib.es2021.string.d.ts`. At `--target es2020` the
compiler resolves `lib.es2020`, where `replaceAll` does not exist — so **every** `replaceAll`
call in the tree becomes `TS2551`, on `string` exactly as much as on a string-literal union.
Re-running the *identical* command at a higher target removes all three:

```
--target es2020  ->  3 × TS2551 + 2 × TS2304   (five errors, three classes)
--target es2021  ->  0 × TS2551 + 2 × TS2304   (two errors, two classes)
--target esnext  ->  0 × TS2551 + 2 × TS2304   (two errors, two classes)
```

The line numbers in the `es2020` run are a direct tell: `(25,83)`, `(55,685)`, `(56,142)` —
column 83, 685 and 142 are **end-of-line**, i.e. the last `replaceAll` on each line, not the
first. `LearnerCapabilityStatus` has nothing to do with it; the compiler simply reports the
last such call per line.

**The three `replaceAll` errors are therefore not defects.** Two consequences, both material:

1. **The real defect inventory in `CapabilityChamber.tsx` is two, not three**, and both are
   genuine:
   - `TS2304: Cannot find name 'useEffect'` (`:51`) — line 4 imports only `{ useState }` from
     `react`; the chamber calls `useEffect` at line 51. A real free identifier.
   - `TS2304: Cannot find name 'surfaceMeta'` (`:56`) — `surfaceMeta` is referenced once and
     defined nowhere. A real free identifier.
2. **§2.3's severity note is contradicted by the shipped artifact.** It argues that below
   `ES2021` `replaceAll` is "undefined behaviour" and that the fix is a **compatibility**
   concern. The production bundle contains **5** `.replaceAll(` call sites and ships them
   un-transpiled; the call resolves at runtime on any engine meeting the build's baseline.
   There is no compatibility defect to repair.

### Why this matters for the repair decision (§10 of `WORKSTREAM_STATE.md`)

The two surviving defects are mechanically unambiguous — `useEffect` needs to join the existing
`react` import, and `surfaceMeta` is a dangling reference in a live render path. Neither
requires a product decision. But the **wider repair is still not a safe bounded repair**, for a
reason independent of the miscount:

`ActivityRuntime` is imported at `CapabilityChamber.tsx:4` and **never rendered** (`grep -c
'<ActivityRuntime'` → `0`). The chamber's inline work surface (`learning-activity-work-surface`,
with `evidenceBoundary` / `submitEvidence` / sessionStorage evidence capture) is the surface that
actually renders today, and it is the one the production bundle contains. Re-mounting
`ActivityRuntime` as §4's test demands would place **two** work surfaces in the same render path
with two storage schemas and two completion models. That is a design change, not a bounded
repair, and it is what four SG-04 tests assert.

**Net:** the miscount does not make the repair safe. It does make two of the three "defect
classes" vanish, which *reduces* the stated justification for the repair rather than supporting
it. The mount question remains the blocking one and still requires sovereign authorization.

---

*This evidence artifact was created by an AI agent (OpenHands) on behalf of the human sovereign.*

---

## Addendum A — independent re-verification of pass 2 (third pass)

**Type:** bounded evidence pass. **No source, test, or governance change.** Two evidence files.
**Base:** `main` @ `002b189dd95e41c9b4f4cca33d08b4121453d289` (unchanged).
**Verified head:** `3171ac28e6b2172cb067479185d20ba0faf1870a` (pass 2).

Every figure below was re-derived from a fresh clone, live GitHub API reads, a fresh local build
of `main`, and direct HTTP reads of production. Nothing was inherited from pass 1 or pass 2.

### A.1 Pass-2's central correction — reproduced exactly

The pass-2 claim that the `replaceAll` "defect class" is a `lib`-target artifact is **confirmed
byte-for-byte**. Re-running pass 1 §2.3's own command at three targets:

```
--target es2020  ->  3 × TS2551 + 2 × TS2304   (5 errors, 3 classes)
--target es2021  ->  0 × TS2551 + 2 × TS2304   (2 errors, 2 classes)
--target esnext  ->  0 × TS2551 + 2 × TS2304   (2 errors, 2 classes)
```

The surviving two, at their exact compiler columns:

```
(51,3):   error TS2304: Cannot find name 'useEffect'.
(56,377): error TS2304: Cannot find name 'surfaceMeta'.
```

**`--target es2021` and `--target esnext` both yield exactly 2 errors.** The `replaceAll` class
does not exist. The end-of-line column argument is also confirmed directly: the three reported
columns (83, 685, 142) are each the **last** `replaceAll` occurrence on lines 25, 55, 56, and
each line holds exactly one `replaceAll`. Pass-2's diagnosis and remedy are correct.

### A.2 Correction to §2.3's severity note — item-level, and it strengthens pass 2

Pass-2 (§6.2) calls §2.3's severity note "contradicted by the shipped artifact" and cites the
bundle's 5 `.replaceAll(` sites. **The direction of the correction is right; its magnitude is
understated.** The shipped sites are not merely "some replaceAll calls on `string`" — they are
*exactly* the chamber's five.

| | source `CapabilityChamber.tsx` | shipped bundle (production ≡ fresh) |
|---|---|---|
| `replaceAll(` call sites | **5** | **5** |

The five source sites and the five bundle sites correspond 1:1, and all five operate on
`string`/template-literal values. The correct statement is therefore stronger than pass-2's:
**the artifact contains precisely the same five call sites §2.3 flagged, all of them
string-valued, all shipping un-transpiled.** There is no compatibility defect at any severity —
not "5 un-transpiled calls somewhere", but "the flagged calls themselves ship and resolve".
This *widens* the gap between §2.3's note and reality; it does not change the conclusion.

Also confirmed: the bundle contains **zero** `replaceAll` sites attributable to the
tree-shaken-out `ActivityRuntime`, consistent with §3.1.

### A.3 New finding — the committed build output is stale (not previously recorded)

Neither pass recorded this. On `main`, three bundle identities exist, and they do not agree:

| artifact | bundle ref | bytes | status |
|---|---|---|---|
| **committed** `web/public_prism/dist/index.html` | `index-CStL2fKK.js` | — | **tracked, never built from current source** |
| **fresh build of `main`** | `index-xiYlcBh3.js` | 1 941 274 | reproducible |
| **production** (Vercel) | `index-CHFFyuSc.js` | 2 025 825 | live |

- The committed `dist/index.html` is **byte-identical to a fresh build except for the bundle
  hash** — i.e. it is a genuine past build output, tracked in git.
- The bundle it references, `index-CStL2fKK.js`, **is not committed and is not buildable** —
  `git log --all` for that path is empty; a clean `vite build` produces `index-xiYlcBh3.js`.
- Production serves `index-CHFFyuSc.js`, which corresponds to **neither** the committed nor the
  fresh-built bundle.

**Interpretation, stated at its true strength.** Vercel's `vercel.json` sets
`outputDirectory: web/public_prism/dist` with no `buildCommand`, so **Vercel builds from source
at deploy time** and does not serve the committed `dist/`. That means the stale committed
`dist/index.html` is **inert with respect to production** — it is not a second mutation path and
it does not affect the deployed artifact. What it *is* is a tracked build-output file whose
referenced asset cannot be regenerated from the repository — a provenance inconsistency, not a
runtime defect.

**What this does and does not change:**

- It does **not** weaken §3 or §3.3. The source-side defect claim is unaffected: the free
  `useEffect` identifier and the free `surfaceMeta` identifier are present in production and in
  a fresh build of `main` alike (§A.4), and production still matches the bytes #163 described.
- It does **not** establish that production is stale. Production differs from a fresh build,
  and the cause of that difference is **not determined by this pass** — see A.5.
- It is a **new, unowned** hygiene item. It is *not* a bounded repair here, and this pass does
  not touch it. Recorded for the sovereign as a candidate workstream, per the contract's
  NO SELF-EXPANSION rule.

### A.4 Defect markers — production and fresh build agree on every one

| marker | production | fresh build of `main` |
|---|---|---|
| bare `useEffect(` (free call) | **1** | **1** |
| global `useEffect` decl | **0** | **0** |
| `.useEffect(` property calls | **93** | **93** |
| `'activity-surface-'` | **0** | **0** |
| `'activity-runtime-draft'` | **0** | **0** |
| `'learning-activity-work-surface'` | **1** | **1** |
| `'sg03-contract-boundary'` | **1** | **1** |
| `'spiral-grove'` | **4** | **4** |
| free `surfaceMeta` | **1** | **1** |
| `'evidence-capture'` | **3** | **3** |
| `.replaceAll(` | **5** | **5** |

Every §3.1, §3.2 and §11 marker is **confirmed on both artifacts**. The §3.3 conclusion — that
the defect is source-side and the deployed artifact matches `main` faithfully *in every
defect-relevant respect* — stands.

The lone bare call, re-located independently:

```js
,[b,v]=x.useState(""),[w,S]=x.useState(!1);useEffect(()=>{if(!(typeof window>"u"))try{u(window.localStorage.getItem(o)||"")
```

The bundle's 104 `useEffect` tokens reconcile completely with no residue:
`93` property calls + `1` bare call + `4` object-literal keys + `1` assignment + `5` alias
references (`x.useEffect` / `N2.useEffect` / `O1.useEffect` in the `useLayoutEffect` fallbacks)
= **104**. No unresolved global declaration exists; the one bare call has no binding.

### A.5 Item-level corrections to this pass's own predecessors

1. **§3.3's phrase "matches `main` faithfully" needs one qualifier.** Production's bundle is
   **84 551 bytes larger** than a fresh build of `main` (2 025 825 vs 1 941 274), while every
   defect-relevant marker agrees. "Faithfully" is verified **at the marker level**, not at the
   byte level. The cause of the size delta is **`UNKNOWN`** to this pass and is not promoted.
2. **§7's CI table row `Vercel — pass`** is correct but was **unverifiable via `check-runs`.**
   The Vercel deployment is a **commit status**, not a check-run. On head `3171ac28…`:
   `check-runs total_count = 2` (`Vercel Preview Comments`, `Full-history secret scan`), and
   `combined status = success` with one status, `Vercel = success`. The table should be read as
   2 check-runs + 1 commit status. §7's head `fd9d04dda7b1` yields the **identical** result, so
   the row is accurate for both heads.
3. **§4's test-attribution table is confirmed at item level**, with one line-number precision
   note: the four pytest-reported assertion lines (`:73`, `:85`, `:110`, `:115`) are exact, and
   the function definitions sit at `:82`, `:107`, `:115` per source. §4's mapping of each failing
   assertion to its file (chamber mount / `ActivityRuntime.tsx` / chamber copy /
   `SpiralGrovePage.tsx`) is correct in all four rows. The `:115` collision between the header
   test's **definition** line and §4's cited **assertion** line is benign — §4 cites the
   pytest-reported assertion line, which is the right one.
4. **Duplicate `## 6` heading** exists in the pass-2 file (one at §6 "Adjacent claims", one at
   §6 "Correction — the replaceAll defect class"). Cosmetic; not corrected here to keep this
   pass's diff additive.

### A.6 Adjacent claims re-verified

| claim | result |
|---|---|
| `"/health"` absent from `api/main.py` | **confirmed** — 0 occurrences |
| `scripts/cp10_mutation_boundary_policy.py` present | **confirmed** — 8461 bytes |
| `api/main.py` budget | **confirmed** — 2519 / 2600, `py_compile` OK |
| `CapabilityChamber.tsx` blob `0cde2f782f1c…` | **confirmed** — `0cde2f782f1c17d6269334b2d4c56c166485d06e` |
| `<ActivityRuntime` render absent | **confirmed** — 0 occurrences |
| SG-03 boundary strings / `generateExercise` / `createEvidence` | **confirmed** — 2 / 0 / 0 in chamber |
| open PR count | **confirmed** — 23 (`142 … 163 165`); drain arithmetic reconciles to 20 |
| PR #165 shape | **confirmed** — `OPEN`, `draft=false`, `mergeable=true`, 2 files, +536/−0, docs-only |
| branch diff vs `main` | **confirmed** — docs-only, 2 files, 536 insertions |

### A.7 Classification

- **`VERIFIED`** — pass-2's `lib`-target correction (§A.1), the two surviving defects, every
  defect marker on both artifacts (§A.4), and all §5/§6/§11 adjacent claims (§A.6).
- **`VERIFIED` with item-level correction** — §2.3's severity note (§A.2: the 5 shipped
  `replaceAll` sites *are* the flagged ones, so the note is contradicted more strongly than
  recorded); §7's Vercel row (§A.5.2: commit status, not check-run).
- **`NEW`** — stale committed `dist/index.html` (§A.3). Inert with respect to production;
  provenance inconsistency only. **Unowned; requires its own bounded authorization.**
- **`UNKNOWN`** — the cause of the production/fresh bundle size delta (§A.5.1); the
  browser-rendered symptom (unchanged from pass 1/2 — no browser runtime in this sandbox).
- **`NOT CLAIMED`** — production acceptance. Human authority.

## Appendix B — Pass 4: item-level decomposition of the SG-04 cluster

The predecessor document `gate-hygiene-sg04-canonical-header-merge-regression-01` classifies the
four SG-04 failures as a **"cluster-level merge-loss"** (its §5.4 and §6) and attributes the
`:107` failure to the **absence** of the SG-03 downstream-boundary literal. Pass 4 tested that
classification at the byte level. **One of its two premises is falsified.**

### B.1 The `:107` premise is falsified — the literal is duplicated, not absent

The predecessor's §6 table lists "SG-03 downstream-boundary literal" as **absent** on `main`.
It is not absent. `CapabilityChamber.tsx` on `main` carries the boundary paragraph **twice**:

| # | chamber copy (verbatim) |
|---|---|
| 1 | `Evidence submission, assessment, and capability-state mutation remain explicit downstream stages.` |
| 2 | `Evidence submission, assessment, and capability-state updates remain separate explicit downstream stages.` |

The node asserts a **third** string that matches neither:

```
tests/test_spiral_grove_activity_runtime.py:110
assert "Evidence submission, assessment, and capability-state updates remain separate downstream stages." in chamber
```

Copy 2 is the asserted sentence with the single word **`explicit`** removed — a **near-miss
rewording**, not a deleted property. The word `explicit` is present in both surviving copies, so
the governance property (SG-03 work surface does not cross the evidence boundary) is **enforced
twice over** on `main`. The assertion fails only because it is a byte-exact literal rather than a
property check.

Consequence for classification: `:107` is **not** merge-loss. It is a **literal near-miss against
a duplicated property**. Whether it should be repaired by reword (test-side) or by converging the
two chamber copies (source-side) is a **judgement call, not a mechanical repair** — see B.4.

### B.2 The other three nodes survive the predecessor's classification

| node | line | classification | evidence |
|---|---|---|---|
| `::test_runtime_is_mounted_by_the_capability_chamber` | `:82` | **CONFIRMED merge-loss** | `<ActivityRuntime` count in chamber = **0**; sole reference is `import ActivityRuntime from './ActivityRuntime'` at `:4` — a dangling import |
| `::test_runtime_dispatches_all_eight_kinds_to_deterministic_renderers` | `:110` | **CONFIRMED assertion-form defect** | `ActivityRuntime.tsx:106` emits `` data-testid={`activity-surface-${kind}`} ``; the test demands the *expanded* literal `data-testid="activity-surface-research"`. The property holds; the assertion does not match its own template. |
| `::test_spiral_grove_uses_the_nexus_canonical_header` | `:115` | **CONFIRMED merge regression** | `SpiralGrovePage.tsx` contains exactly **1** `<h1`; assertion demands 0. Both Nexus anchors (`:888` heading, `:909` mount) are satisfied. |

Corroboration that the chamber mount was **lost rather than deliberately relocated**: the eight
named renderers `ResearchSurface`, `WritingSurface`, `BuildSurface`, `ReflectionSurface`,
`PresentationSurface`, `FieldSurface`, `CreativeSurface`, `CollaborativeSurface` are all present
in `ActivityRuntime.tsx`, and the `switch (activity.kind)` dispatch is intact — the runtime is
complete but **unreachable**. 8 of the file's 12 nodes pass.

### B.3 Static/dynamic split (new precision)

The cluster is **not** four instances of one defect class. It splits cleanly:

| class | nodes | count | character |
|---|---|---|---|
| **STATIC / test-side** | `:107` (near-miss literal), `:110` (assertion form) | 2 | no rendered-behaviour change required |
| **DYNAMIC / source-side** | `:82` (mount), `:115` (header ownership) | 2 | both change rendered UI structure |

This split matters because it is **different from the predecessor's premise** (4/4 merge-loss)
and **different from pass 2/3's premise** (2 `tsc` defects, neither of which satisfies any SG-04
node). Neither predecessor distinguished the static half from the dynamic half.

### B.4 New finding: the `:115` repair has a *test-internal* inconsistency

`:115` asserts **two opposite things about the same file**:

```
assert "<h1" not in page          # SpiralGrovePage must have NO header
assert "The Spiral Grove" not in page   # SpiralGrovePage must NOT contain the string at all
```

`SpiralGrovePage.tsx` is mounted at **two** locations, only one of which supplies a heading
(`App.tsx:134` for `view === 'grove'`; `NexusPage.tsx:888` for `activeTab === 'university'`).
Satisfying the assertion **strips the `<h1>` on the `grove` route**; restoring the header
**duplicates it** under `university`. This confirms the predecessor's §4 tension and adds one
item: the assertion's own second clause forbids the string `"The Spiral Grove"` from appearing in
the page file **even as a label, title, or accessibility string** — so no conditional-render
repair can satisfy it. **`:115` cannot be satisfied by any source change that keeps the `grove`
route headed.** It requires either a source change *plus* an assertion change, or the sovereign
accepting a headless `grove` route. Both are product decisions.

### B.5 Boundary honesty

- **No source, test, governance, or deployment change.** Evidence files only.
- **No merge, no push to `main`, no force-push, no reclassification of baseline debt.**
- The predecessor's `:82` / `:110` / `:115` classifications are **confirmed**; its `:107`
  classification is **falsified** and corrected above. This is a correction *of* a sibling
  evidence document, not a weakening of any gate.
- No node is repaired here. The two static nodes are plausibly inside the `gate-hygiene`
  test-only envelope; the two dynamic nodes are not.
- **Static determinations only.** No deployment identity, no browser observation. The
  browser-rendered symptom remains **`UNKNOWN`**; production parity is **not claimed**.

---

*This addendum was created by an AI agent (OpenHands) on behalf of the human sovereign.*
