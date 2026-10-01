> # ⚠️ PASS 04 CORRECTION — READ THIS FIRST
>
> This artifact was merged to `main` via PR #166 (`47e4128`). **The merge landed the
> wrong chamber variant, and the numbers below do not describe what is on `main`.**
>
> What actually happened: PR #166 was squash-merged from a head that pointed at the
> branch's **oldest** head (`0ebb9c4`, chamber blob `5c78fcbcd`), not the branch's final
> state (`6786763`, chamber blob `20f58649`). The merged commit `47e4128` is
> **single-parent** (`0fe6d0d` only) and touched just 4 files. Neither `8000a81` (the
> repair) nor `d90ed58` (Pass 02 evidence) is an ancestor of `main`.
>
> Consequences on `main` `47e4128`:
> - `CapabilityChamber.tsx` = `5c78fcbcd` — **no** `ActivityRuntime` import, **no** mount,
>   **no** SG-03 boundary literal.
> - `SpiralGrovePage.tsx` — the Nexus canonical header change from `8000a81` **did not
>   land**.
> - Measured full suite: **20 failed / 1121 passed / 1 error** — byte-identical failing-node
>   set to `main` `0fe6d0d` (`comm` diff empty). PR #166 produced a **net-zero** delta.
>
> **The numbers in this file are Pass 02's, measured on the pre-merge branch tree. They
> were never true of `main`, and they are not true now.** Do not cite them.
>
> The corrected repair is on branch `gate02/capability-chamber-union-repair-02`
> (see `docs/control-plane/evidence/gate02-capability-chamber-union-repair-02/EVIDENCE.md`).
> It restores the union chamber `20f58649` **and** the `SpiralGrovePage` canonical header
> `be992d63`, measured at **1 failed / 29 passed** on the SG suite (the single remaining
> failure is pre-existing `main` debt) and **17 failed / 1124 passed** on the full suite
> (3 fixed, 0 new).

# GATE-02 — CapabilityChamber merge-loss repair (bounded)

**Pass:** gate02 / bounded repair 01
**Date:** 2026-10-01
**BASE_MAIN:** `002b189dd95e41c9b4f4cca33d08b4121453d289` (Merge PR #141)
**Branch:** `gate02/capability-chamber-merge-loss-repair-01`
**Class:** IMPLEMENTED (source repair + full-suite equivalence proof; frontend build environment-blocked)
**Authority required:** human merge only. No merge, no push to `main`, no force-push performed.

---

## 1. Bounded objective

Repair the merge-loss defect in
`web/public_prism/src/components/spiral-grove/CapabilityChamber.tsx` such that the file
equals the content the canonical merge `ff80b8c` **silently discarded from its own second
parent**, and prove by measurement that the repair introduces no test-node delta.

Completion condition: repaired blob == `ff80b8c^2` blob, and the full-suite failing-node
set is byte-identical to `main`.

---

## 2. Independent verification of the source-side defect claim (PR #163)

PR #163 (`gate-hygiene/queue-drain-verification-01` @ `1e9d40029486`) claimed two
source-side defects. Both are **independently confirmed here**, and a **third defect it
did not enumerate** was found. One claim is **corrected**.

### 2.1 The merge invented a hybrid state present in neither parent

Three revisions of the same path were compared token by token:

| Token | `ff80b8c^1` (`cef5a59`) | `ff80b8c^2` (`5c78fcb`) | `ff80b8c` (merge) |
|---|---|---|---|
| `import React, { useEffect, useState }` | 0 | **1** | **0** |
| `import ActivityRuntime from './ActivityRuntime'` | **1** | 0 | **1** |
| `const surfaceMeta` | 0 | **1** | **0** |
| `<ActivityRuntime` (render site) | **1** | 0 | **0** |
| `learning-activity-work-surface` (inline surface) | 0 | **1** | **1** |

Blobs: `ff80b8c^1` = `cef5a5938dba8efa4ef4ab0426365a431d2aee57`,
`ff80b8c^2` = `5c78fcbcd713057556d7257e51dab295f82888cc`,
`ff80b8c` = `0cde2f782f1c17d6269334b2d4c56c166485d06e`.

**Finding.** The merge resolution took the *inline surface* from parent 2 (`:1` in the
table) but took the *import line* from parent 1. The resulting file is a state that
**exists in neither parent**:

- parent 2 declares `useEffect` and `surfaceMeta` and uses the inline surface — coherent;
- parent 1 imports `ActivityRuntime` and renders `<ActivityRuntime>` — coherent;
- the merge imports `ActivityRuntime`, **never renders it** (dangling import), **drops the
  `useEffect` binding** while retaining the inline surface that depends on it, and **drops
  the `surfaceMeta` style anchor** the inline surface references.

This is a hand-resolved merge that was not recompiled. It is a *partial* adoption of the
`ActivityRuntime` refactor, not a deliberate design choice.

### 2.2 Correction to #163: the dangling import is a third defect, not "by design"

PR #163 records the dangling import as an observation but classifies only two defects
(`useEffect` binding + `surfaceMeta`). The dangling `import ActivityRuntime` is a distinct
third defect: it is a dead import that exists only because of the same botched resolution.
The repair removes it, which is what makes the repaired file **byte-identical** to
`ff80b8c^2` rather than merely equivalent. Two-defect framing understates the loss.

### 2.3 PR #163's own evidence misattributes one failing test

PR #163 attributes the failure of `test_chamber_preserves_sg03_downstream_boundary` to
*merge-loss of the SG-03 downstream-boundary literal*. **This is falsified.**

The test asserts the literal
`"Evidence submission, assessment, and capability-state updates remain separate downstream stages."`

The chamber actually contains:

```
capability-state mutation remain explicit downstream stages          (1 occurrence)
capability-state updates remain separate explicit downstream stages  (1 occurrence)
```

Both are near-misses; the demanded literal is **absent in every revision** — including the
coherent `ff80b8c^2`. The `:110` failure is therefore **not merge-loss**; it is a
test/source literal near-miss. Repairing the merge loss cannot and does not fix it.
Attributing it to the merge would have produced an unfalsifiable "repair didn't work"
signal.

---

## 3. Design contradiction between the two open PRs — resolved by measurement

Two open PRs carried competing designs for the same file:

- **#163** — treats the inline work-surface design as canonical.
- **#165** — `gate02/independent-verification-163` @ `5a3d30201b5f` — models a "restore the
  `ActivityRuntime` mount" design.

The contradiction was resolved empirically rather than by argument:

1. **All three revisions of the path are the same blob.** `main`, `#163` head, and `#165`
   head all resolve to blob `0cde2f782f1c17d6269334b2d4c56c166485d06e`. Neither PR modifies
   the file. **There is no live merge conflict** — the file is identical everywhere.
2. **No open PR touches the file at all.** All 23 open PR heads were queried through the
   GitHub API; `CapabilityChamber.tsx` appears in **zero** changed-file sets.
3. **Three independent test files pin the inline design**:
   `tests/test_spiral_grove_activity_runtime.py` (asserts
   `data-testid="learning-activity-work-surface"` is in the chamber),
   `tests/test_ais_w5_evidence_capture.py` (asserts `activity-draft.v1`),
   `tests/test_spiral_grove_chambers.py`.
4. **The mount design is falsified by construction.** A faithful mount variant (import +
   render + removal of the inline surface) *increases* failures from 4 to 6: it satisfies
   `test_runtime_is_mounted_by_the_capability_chamber` but breaks
   `test_chamber_preserves_sg03_downstream_boundary` and the W5 draft-persistence pins.

**Conclusion: the inline design is canonical.** The mount design is rejected. #165's
"restore the mount" premise is a mis-diagnosis, not an alternative architecture.

### 3.1 Test-name discrepancy in #165's pass-4 citation

#165's pass 4 cites `test_spiral_grove_boundary_is_enforced` as a test it observed failing.

- `git grep` over the **entire `#165` head tree** (`5a3d30201b5f`) returns **no match**.
- `git grep` over `main` returns **no match**.
- The name appears **0 times** in `#165`'s own `EVIDENCE.md`.

The nearest real names are `test_sandbox_command_allowlist_is_enforced` and
`test_state_non_collapse_is_enforced`, both in `tests/test_engineering_lab_substrate.py`
— a different subsystem entirely.

**Classification: non-reproducible citation.** Per contract this is recorded, not
silently reconciled. It is a **documentation defect only** — it does not affect this
repair, and no code change is proposed for it. It does mean #165's pass-4 failure list
should not be relied on as a test fingerprint without re-derivation.

---

## 4. The repair is mechanically determined, not designed

The repair reproduces the merge's own discarded parent blob:

```
repaired blob         5c78fcbcd713057556d7257e51dab295f82888cc
ff80b8c^2 blob        5c78fcbcd713057556d7257e51dab295f82888cc
44e1c99 (main-line)   5c78fcbcd713057556d7257e51dab295f82888cc
main blob             0cde2f782f1c17d6269334b2d4c56c166485d06e
```

`git diff ff80b8c^2 -- <path>` after the repair is **empty**.

Two lines change (`+2 -2`):

1. `import React, { useState } from 'react'` → `import React, { useEffect, useState } from 'react'`
2. `-import ActivityRuntime from './ActivityRuntime'` (dangling import removed)
3. `+const surfaceMeta: React.CSSProperties = { ... }` (style anchor restored)

Because the result is byte-identical to a commit that was already authored and tested
on the main line, this is **loss restoration, not new design**. No new abstraction,
mutation path, authority path, or evidence mechanism is introduced. Scope is one file.

---

## 5. Verification

### 5.1 Regression boundary — full-suite fingerprint comparison

Both trees were run in isolated worktrees with the same interpreter and environment:

```
PYTHONPATH=archive/legacy_python python -m pytest tests/ -q --continue-on-collection-errors
```

| Tree | Result |
|---|---|
| `/tmp/wt-main` (detached `002b189`) | 48 failed, 761 passed, 12 skipped, 27 errors |
| repaired branch | 48 failed, 761 passed, 12 skipped, 27 errors |

**Failing-node set delta: NONE.** Normalised `FAILED`/`ERROR` node lists are
byte-identical:

```
sha256 113fa7fa6c950e424a60efa15cfff8322ff967cd57af127b13796ff55556da20  (main)
sha256 113fa7fa6c950e424a60efa15cfff8322ff967cd57af127b13796ff55556da20  (repaired)
```

75 failing nodes each, identical names, identical set. The repair changes **zero** test
outcomes in this environment.

### 5.2 Focused SG-04 suite

```
tests/test_spiral_grove_activity_runtime.py
tests/test_ais_w5_evidence_capture.py
tests/test_spiral_grove_chambers.py
tests/test_spiral_grove_frontend_projection.py
tests/test_spiral_grove_learning_path_projection.py
tests/test_ais_w4_personalized_grove.py
-> 4 failed, 42 passed
```

The 4 remaining failures are the pre-existing near-misses / test-side defects, all
unaffected by this repair:

| Failing test | Cause | Classification |
|---|---|---|
| `test_runtime_dispatches_all_eight_kinds_to_deterministic_renderers` | test asserts the *expanded* literal `data-testid="activity-surface-research"`; source emits the *template* `` data-testid={`activity-surface-${kind}`} `` (`ActivityRuntime.tsx`) | test-side assertion-form defect |
| `test_runtime_is_mounted_by_the_capability_chamber` | asserts `<ActivityRuntime activity={activity} />`; canonical design is inline, not mounted | test-side / design contradiction (see §3) |
| `test_chamber_preserves_sg03_downstream_boundary` | literal near-miss (see §2.3) | test-side literal defect |
| `test_spiral_grove_uses_the_nexus_canonical_header` | asserts `"<h1" not in page` on `SpiralGrovePage.tsx`, which contains one `<h1>` | test-side / different file |

### 5.3 Protected surfaces

| Gate | Result |
|---|---|
| `tests/architecture -q` | **11 passed** |
| `python -m py_compile api/main.py` | OK (untouched) |
| `api/main.py` line budget | 2519 / 2600 (untouched) |
| CP10 mutation boundary `--judge` over changed paths | **PASS** |
| `vite build` | environment-blocked (no registry access) — **not** claimed as verified |

---

## 6. Baseline reconciliation (recorded, not fixed)

The contract's recorded baseline (`main := 6038989`, 804 passed / 54 failed / 12 skipped /
2 collection errors) does **not** match this environment's measurement
(761 passed / 48 failed / 12 skipped / 27 errors). This is an **environment delta**
(missing optional dependencies turning collection errors into per-test errors, and
`archive/legacy_python` resolution), not a repository regression: `main` was measured
directly and produced this fingerprint, and the repaired tree reproduced it exactly.

The environment-independent claim this pass makes is the **relative** one: *no node-set
delta*. That claim does not depend on the absolute baseline.

Baseline debt is **not** repaired in this pass, per contract rule.

---

## 7. Scope and authority boundary

**Changed:** one source file + this evidence directory.

**Not changed:** no test files (the four remaining failures are test-side defects and are
deliberately **not** "fixed" here — that would be scope expansion into a separate bounded
workstream), no `api/main.py`, no governance code, no authority path, no mutation path.

**Authority:** merge is reserved to the human sovereign. This pass performed no merge, no
push to `main`, and no force-push.

**Remaining uncertainty:**

1. `vite build` could not run — the repair is not build-verified, only test-verified.
2. The four SG-04 failures need their own bounded workstream (test-side defects vs design
   contradiction). Proposed, not executed.
3. #165's pass-4 test-name citation is non-reproducible and should be re-derived before
   its fingerprint is trusted.

**Next bounded task (proposed, not executed):** a separate bounded PR reconciling the four
SG-04 test-side defects, or a human decision that the inline design supersedes the mount
tests. This is deliberately outside this PR's scope.
