# WORKSTREAM STATE — GATE-02 independent verification of PR #163

**Workstream:** `gate02/independent-verification-163`
**Gate:** GATE-02 (human-origin authority) — verification half of the runtime boundary
**Base:** `main` @ `002b189dd95e41c9b4f4cca33d08b4121453d289`
**Head:** `gate02/independent-verification-163`
**Status:** `VERIFIED` (with two precision corrections) — **sovereign review required**

---

## 1. What this pass did

Independently re-derived every checkable claim in PR **#163**
(`gate-hygiene/queue-drain-verification-01`) from a fresh clone, live GitHub API reads, and a
fresh local build of `main`. No claim was inherited.

Primary focus: **the claimed real source-side defect in `CapabilityChamber.tsx`.**

**No source, test, or governance change.** Two evidence files added.

## 2. Baseline fingerprint (established before any change)

```
main @ 002b189
full suite : 20 failed / 1039 passed / 13 skipped / 2 errors
architecture: 11 passed
api/main.py : 2519 / 2600, py_compile OK
```

Exact match to #163. The contract's stated baseline (804/54/12, arch 9/10) is **stale** —
fourth independent confirmation. The 20-node failing set is pinned verbatim in `EVIDENCE.md` §1
so a future delta is attributable.

## 3. Verification result — #163's defect claim

| element | verdict |
|---|---|
| blob `CapabilityChamber.tsx` = `0cde2f782f1c…` | **VERIFIED** (exact) |
| `<ActivityRuntime` render absent on `main` | **VERIFIED** (`grep -c` → 0) |
| deployed bundle sha256 `33861ef9…`, 2 025 825 bytes | **VERIFIED** (exact) |
| importer bundled / import tree-shaken out | **VERIFIED** (literals ×1 / ×0 as claimed) |
| `useEffect` is a free identifier in the artifact | **VERIFIED** (0 global decls, 1 bare call, 92 `x.useEffect(`) |
| defect is source-side, not a stale deploy | **VERIFIED** (fresh build of `main` reproduces the signature) |

**PR #163's central claim stands, independently reproduced end to end.**

## 4. Two precision corrections

**(a) Defect inventory is wider than recorded.** `tsc` on `main`'s own source yields **6 errors
across 3 distinct defect classes**, not the 2 #163 enumerated:

| defect | location | in #163? |
|---|---|---|
| `useEffect` called, never imported | `:51` | yes |
| `<ActivityRuntime>` imported, never rendered | `:4` / no mount | yes |
| **`surfaceMeta` referenced, never defined** | `:56` | **no** |
| **`replaceAll` on `LearnerCapabilityStatus` union** | `:25` | **no** |
| **`replaceAll` on `LearningWorkMode` union** | `:55`, `:56` | **no** |

Defect 3 (`surfaceMeta`) is a hard `ReferenceError` on the **same render path** as defect 1 —
`surfaceMeta` is a free identifier exactly as `useEffect` is.

**(b) Test attribution in pass 01 §7 over-groups.** Measured per-test, only
`::test_runtime_is_mounted_by_the_capability_chamber` (`:85`) asserts the dropped-mount
invariant. The other three assert `ActivityRuntime.tsx` internals (`:73`), chamber copy
(`:110`), and `SpiralGrovePage.tsx`'s `<h1>` (`:115`) — three different files' worth of
assertions sharing one test file.

**Neither correction weakens #163's conclusion.** All four are genuine pre-existing baseline
debt, correctly excluded from drain-set attribution.

## 5. The 20-PR drain set — arithmetic confirmed

Live `gh pr list --state open` at this pass: **23 open**
(`142 143 144 145 146 147 148 149 150 151 152 153 154 155 156 157 158 159 160 161 162 163 165`).
Subtracting the three evidence PRs (#162, #163, #165) leaves **20 drain PRs** =
18 clean (142 144 145 146 148 149 150 151 152 153 154 155 156 157 158 159 160 161)
+ 2 conflict-carrying (143, 147). Reconciles to 22 open at #163's head. **Confirmed.**

## 6. CI at this pass's head

`Full-history secret scan` **pass**, `Vercel` **pass**, `Vercel Preview Comments` **pass**.
PR #165 `OPEN`, `draft=false`, `MERGEABLE`, `CLEAN`. Note `sg-02-fe-2-v.yml` correctly did
**not** trigger on an evidence-only diff — it is path-filtered.

## 7. Evidence

- `docs/control-plane/evidence/gate02-independent-verification-163/EVIDENCE.md`

## 8. Authorization required

Sovereign review. **Do not merge** — merge is human-only.

1. Accept #163's defect claim as independently verified (it is).
2. Note the two precision corrections when reading #163 §7 and Addendum 02 §2.2.
3. **Authorize a separate bounded pass** to repair `CapabilityChamber.tsx` — all **three**
   defect classes, not two. Owned by no PR in the drain queue; all 22 queue heads carry
   `main`'s blob `0cde2f782f1c`, so merging the queue will not fix it.

## 9. Boundary honesty

- The `ReferenceError`-on-render is a **static** determination (artifact + fresh build). The
  **rendered symptom is not observed** — no browser runtime in this sandbox. That half stays
  **`UNKNOWN`** and is not promoted.
- The 20-PR drain composition and CI-greenness claims were **spot-checked**, not fully
  replayed.
- **Production acceptance: NOT CLAIMED.**

## 10. Next bounded task

`CapabilityChamber.tsx` repair — a single file, four baseline tests asserting the mount
invariant. Requires its own authorization (product decision, not hygiene).

**Revised in pass 2** (see §11): the defect inventory is **two** `tsc` errors in **two** classes,
not six errors in three classes. The three `replaceAll` errors were an artifact of the
`--target es2020` flag used to run `tsc`, not defects. The surviving two (`useEffect`,
`surfaceMeta`) are both real free identifiers and both mechanically unambiguous to repair — but
they are **not** what the four SG-04 tests assert, and repairing them does not satisfy those
tests.

---

## 11. Pass-2 state (independent verification, second pass)

| Field | Value |
|---|---|
| `BASE_MAIN` | `002b189` |
| Branch head | `gate02/independent-verification-163` |
| Source parity with `main` | **identical** — branch diff vs `main` is docs-only (2 files) |
| Full suite fingerprint | `20 failed / 1039 passed / 13 skipped / 2 errors` — matches baseline exactly |
| Architecture tests | 11 passed |
| Fresh `vite build` of `main` | succeeds, 6.78s, bundle `index-xiYlcBh3.js` |
| Bundle forensics | fresh build ≡ production on every marker: `sg03-contract-boundary` 1/1, `learning-activity-work-surface` 1/1, bare `surfaceMeta` 1/1, `evidence-capture` 3/3, `.replaceAll(` 5/5 |
| Defect inventory (corrected) | 2 errors / 2 classes in `CapabilityChamber.tsx` |
| Repair classification | **not a safe bounded repair** — mount is a design change |

**Two material corrections this pass:**

1. **The `replaceAll` defect class does not exist.** `replaceAll` is ES2021; the §2.3 command
   used `--target es2020`, which resolves `lib.es2020` and makes *every* `replaceAll` — on
   `string` as much as on a union — a `TS2551`. The reported columns (83, 685, 142) are
   end-of-line, i.e. the last call per line. At `--target es2021`/`esnext` all three vanish.
   The production bundle ships 5 `.replaceAll(` sites un-transpiled, so the "undefined
   behaviour below ES2021" severity note is contradicted by the artifact itself.
2. **`PersonalEchofeild.tsx` `TS1109` is reachability-limited, not a repo-wide blocker.** The
   file has no production `src/` importers; excluding it the whole tree yields 38 errors across
   20 files, of which `CapabilityChamber.tsx` contributes exactly 2.

**Unchanged:** `ActivityRuntime` is imported at `:4` and never rendered (`<ActivityRuntime` → 0).
The inline `learning-activity-work-surface` is what ships. Four SG-04 tests assert the mount, so
the repair remains an authorization-requiring design change.

---

*This state file was created by an AI agent (OpenHands) on behalf of the human sovereign.*

---

## 12. Pass-3 state (independent re-verification of pass 2)

| Field | Value |
|---|---|
| `BASE_MAIN` | `002b189dd95e41c9b4f4cca33d08b4121453d289` (unchanged) |
| Verified head | `3171ac28e6b2172cb067479185d20ba0faf1870a` |
| Source parity with `main` | **identical** — branch diff vs `main` is docs-only (2 files, +536) |
| `tsc` `CapabilityChamber.tsx` @ `es2020` | 5 errors (3 × `TS2551` + 2 × `TS2304`) |
| `tsc` @ `es2021` / `esnext` | **2 errors** (`:51 useEffect`, `:56 surfaceMeta`) — `replaceAll` class absent |
| Production vs fresh `main` build | **agrees on all 11 defect markers** |
| Production bundle | `index-CHFFyuSc.js`, 2 025 825 B, sha256 `33861ef9…` |
| Fresh `main` build | `index-xiYlcBh3.js`, 1 941 274 B |
| Open PRs | 23 (`142 … 163 165`) → 20 drain + 3 evidence |

**Pass-2's central correction is confirmed exactly.** `--target es2021` and `--target esnext`
both yield precisely the two `TS2304` free-identifier errors; the three `TS2551` `replaceAll`
errors are a `lib.es2020` artifact and disappear. The reported columns (83/685/142) are
end-of-line, the last `replaceAll` per line.

**Three item-level findings this pass:**

1. **§2.3's severity note is contradicted *more strongly* than pass 2 recorded.** The shipped
   bundle's 5 `.replaceAll(` sites are not incidental — they are **exactly** the chamber's five
   source sites, 1:1, all string-valued, all un-transpiled. There is no compatibility defect at
   any severity. (Direction unchanged; magnitude widened.)
2. **NEW — the committed `dist/index.html` is stale.** `main` tracks a build output referencing
   `index-CStL2fKK.js`, which is neither committed nor reproducible from source (a clean build
   yields `index-xiYlcBh3.js`). Production serves `index-CHFFyuSc.js` — neither of the two.
   Because `vercel.json` sets `outputDirectory` with no `buildCommand`, Vercel builds from
   source at deploy time, so the stale file is **inert with respect to production** — a
   provenance inconsistency, not a runtime defect. **Unowned; not acted on; requires its own
   bounded authorization.**
3. **Production is 84 551 B larger than a fresh build of `main`** while every defect marker
   agrees. "Matches `main` faithfully" is verified **at marker level, not byte level**. The
   cause of the delta is **`UNKNOWN`** and is not promoted.

**Unchanged from pass 2:** `ActivityRuntime` imported at `:4`, never rendered (`<ActivityRuntime`
→ 0). The inline `learning-activity-work-surface` is what ships. Four SG-04 tests assert the
mount, so the repair remains an authorization-requiring design change. The repair decision is
**not** made easier by this pass.

### CI at pass-3 (both heads)

| head | check-runs | commit status |
|---|---|---|
| `3171ac28` (pass 2/3) | `Vercel Preview Comments` pass, `Full-history secret scan` pass | `Vercel` success |
| `fd9d04dd` (pass 1, cited in §7) | same two, pass | `Vercel` success |

§7's table is accurate, but note the deployment is a **commit status**, not a check-run — the
row is not visible in `check-runs`.

### Authorization required (unchanged)

Sovereign review. **Do not merge** — merge is human-only.

1. Accept #163's defect claim as independently verified (it is), with pass-2's two corrections
   and this pass's three item-level findings.
2. **Authorize a separate bounded pass** to repair `CapabilityChamber.tsx` — two `tsc` defects
   (`useEffect`, `surfaceMeta`), both mechanically unambiguous, **neither** of which satisfies
   the four SG-04 tests. The mount question is the blocking design decision.
3. **Note the stale committed `dist/index.html`** as a new unowned hygiene candidate — recorded,
   not executed.

### Boundary honesty

- Static determinations only. The browser-rendered symptom stays **`UNKNOWN`**.
- **Production acceptance: NOT CLAIMED.**
- No merge, no push to `main`, no force-push, no source/test/governance change.
