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

## 5. Evidence

- `docs/control-plane/evidence/gate02-independent-verification-163/EVIDENCE.md`

## 6. Authorization required

Sovereign review. **Do not merge** — merge is human-only.

1. Accept #163's defect claim as independently verified (it is).
2. Note the two precision corrections when reading #163 §7 and Addendum 02 §2.2.
3. **Authorize a separate bounded pass** to repair `CapabilityChamber.tsx` — all **three**
   defect classes, not two. Owned by no PR in the drain queue; all 22 queue heads carry
   `main`'s blob `0cde2f782f1c`, so merging the queue will not fix it.

## 7. Boundary honesty

- The `ReferenceError`-on-render is a **static** determination (artifact + fresh build). The
  **rendered symptom is not observed** — no browser runtime in this sandbox. That half stays
  **`UNKNOWN`** and is not promoted.
- The 20-PR drain composition and CI-greenness claims were **spot-checked**, not fully
  replayed.
- **Production acceptance: NOT CLAIMED.**

## 8. Next bounded task

`CapabilityChamber.tsx` repair — a single file, three defect classes, six `tsc` errors, four
baseline tests asserting the invariant. Requires its own authorization (product decision, not
hygiene).

---

*This state file was created by an AI agent (OpenHands) on behalf of the human sovereign.*
