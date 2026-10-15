# Open-PR inventory reconciliation — decision record

**Baseline (frozen):** `7580bd8f0ca2925518d78775f9a323ff0df8bc66`
**Ledger captured:** 2026-10-15T11:54:45Z · **live re-verified:** 2026-10-15T15:53:56Z
**Candidate held unchanged:** #535 @ `8b6eadd77aa1751efd2bc3b69722a1af8e8e1c72`
**Authority:** read-only review. No merge, close, rebase, retarget, push, commit, or deployment.

---

## 1. Ledger validation

| Check | Result |
|---|---|
| Record count | 45 |
| Unique PR numbers | 45 (no duplicates) |
| Live open PRs at re-verify | 45 — identical set |
| Head SHA drift since capture | 0 |
| Every PR has a disposition | yes |
| Dispositions within taxonomy | yes (integrate / combine / close-as-superseded / hold / repair) |
| Head + base SHAs are full 40-char | yes |

Live re-verification was performed independently in this pass (`pulls?state=open`), not
inherited from the capture: the set is identical, so the ledger is current, not stale.

## 2. Seven closure candidates — behavior/artifact review

Blob identity alone is insufficient, as the review correctly required. The decisive test is
each candidate's **own test files, run against `main`'s source tree** in a detached worktree at
`7580bd8f` (deps installed from `requirements.txt`; earlier dependency-only failures excluded).

| PR | Head | Own tests vs `main` source | Residual | Disposition |
|---|---|---|---|---|
| #512 | `f8da5158` | 30 + 12 passed | `EngineeringLabPage.tsx` mount-set is a subset of `main` | **close-as-superseded** |
| #530 | `f54d463c` | 7 passed | subset | **close-as-superseded** |
| #524 | `aad8a986` | 8 passed | subset | **close-as-superseded** |
| #493 | `255d665f` | 22 + 27 + 12 + 5 passed | subset | **close-as-superseded** |
| #504 | `a9cefd21` | 3 + 11 passed | subset | **close-as-superseded** |
| #501 | `31d66332` | 12 passed | mount + test present; **evidence doc absent** | **partially superseded** |
| #503 | `37e89b4a` | (workflow) | workflow **absent from `main`, present in #535** | **not superseded — routed to #535** |

`main` is a strict superset of every closure candidate's mount set (verified per-PR by
extracting `<Component` mounts from `EngineeringLabPage.tsx` on both sides). Residual
`EngineeringLabPage.tsx` differences are **stale-base artifacts**: each candidate derives from
`49809f45`, so its page lacks the sibling projections `main` now carries. The residuals are not
unintegrated requirements.

### #501 — the one genuine gap
`docs/control-plane/evidence/prism-w4-canonical-loop-mount-01/EVIDENCE.md` (84 lines) is absent
from `main` and from #535. The mount itself and `test_prism_w4_canonical_loop_mount.py` are
present and pass. Closing #501 abandons an evidence artifact — classify as **partially
superseded**, not fully superseded.

### #503 — ledger correction
The `eaa-base-baseline.yml` workflow is **absent from `main`** and **present in #535**. It was
misfiled as a closure candidate; it is an EAA-chain item already carried by the candidate.

## 3. The two conflict pairs — resolved, with proven resolutions

`git merge-tree` demonstrated real conflicts. Both were composed in detached worktrees and
tested.

### #497 + #505 — conflict in `tests/test_console_shell_nav_contract.py`
`router.ts` merges **cleanly**; only the test's alias list conflicts (both sides append entries
to the same list). **Resolution: union of both lists.** Measured: `38 passed`.
The two PRs are complementary — #497 reconciles `/nexus/*` sub-paths, #505 reconciles
`/home`, `/knowledge-os`, `/gate`, `/living-gate`. Neither subsumes the other.

### #511 + #514 — conflict in `web/arkadia_console/src/App.tsx`
Both edit the `Shell` render. They are **not** an ancestor chain
(`git merge-base --is-ancestor 7af66444 e48cbf26` → false); they are independent changes from
the same base. #511 introduces `handleNavigate` (sign-in return-to); #514 wraps the body in
`ErrorBoundary`. **Resolution: keep #511's `onNavigate={handleNavigate}` and wrap the body in
#514's `ErrorBoundary`.** Measured: `38 passed` across both suites; frontend build succeeds.

Both resolutions are **additive** — no assertion weakened, no guard removed.

## 4. #539 and #482 — triage

### #539 — external-dependency failure, not candidate defect
Docs-only (`EVIDENCE.md` + `lane-snapshot.json`). Failing checks are
`beta-beta-01-english` and `bundle-beta-evidence`, both from `n-atlas-external-beta.yml`, which
calls the external HuggingFace Space `koladeodunope-ednai-natlas-runtime.hf.space`.
**Classification: environment/external blocker.** Evidence: the same workflow **succeeds** on
#540 (`47bb0f98`) and #544 (`78d63e4e`); within the failing run `beta-02-hausa` **passed** while
`beta-01-english` failed — a docs-only diff cannot cause that. Not attributable to #539.

### #482 — ledger correction: this is a repair, not baseline debt
Earlier recorded as "hold — provider-routing is baseline debt." That is **wrong**.
`provider-routing.yml` on `main` uses the default `actions/checkout@v4` (no `fetch-depth`).
#482 adds `fetch-depth: 0` plus a `tests/test_history_depth_ci_wiring.py` guard (547 lines).
Four of the twelve provider-routing failures are the `test_agents_md_encoding_adjudication`
nodes, which resolve pinned revisions out of git history. Measured: with full history that file
is **21 passed, 2 skipped**; on a shallow clone it is `4 failed`.
**Classification: repair — reclassify from `hold` to `integrate`-candidate (it fixes a defect
`main` carries).**

## 5. Ordered execution plan (proposed — NOT executed)

The 29 "integrate" PRs are a candidate pool, not a queue. Ordering constraints:

1. **#482 first** — it changes the judging surface (`provider-routing.yml`) every later PR is
   judged by. Landing it first makes subsequent CI verdicts trustworthy.
2. **Conflict pairs as single units** — #497+#505 and #511+#514, each merged as one composed
   change with the resolution above. Do not integrate them independently.
3. **#525 remains excluded** — see below.
4. Remaining 25 integrations — sequence by dependency after re-deriving exact bases.

## 6. #525 — the exclusion is intentional, and it is an either/or

My earlier ledger classified #525 as "repair." That is also **wrong**, and this is the most
consequential correction in this pass.

#525 re-adds `LabWorkLoop.tsx` and mounts it on `WeaverPage`. #533's evidence records this as
**deliberately reverted** to satisfy "exactly one canonical work-loop mount." I tested the claim
rather than accepting it:

- Clean `main`: `test_prism_w4_lane4_render_integrity.py` → **7 passed**
- Clean `main` + #525's two source files → **1 failed, 6 passed**
  (`test_control_the_real_pre_mount_page_reports_the_canonical_loop`)
- Restore clean `main` → **7 passed**

`main`'s `WeaverPage.tsx` has no `LabWorkLoop`; #525's own test file (92 lines) is absent from
`main` and its assertions fail 6/38 against `main`'s tree.

So: #525's capability is genuinely unabsorbed, **and** integrating it breaks #530's
sole-consumer control. The two cannot both hold. The resolution is a **design decision for the
sovereign** — either the canonical loop is mounted once (Lab page, `main`'s current state) or
twice (adding the Weaver surface, which requires re-deriving #530's control premise). It is not
a mechanical repair, and it is not mine to decide.

**Disposition: `hold — design decision required`** (was `repair`).

## 7. Corrections to the previous ledger

| Item | Previous | Corrected | Basis |
|---|---|---|---|
| #482 | hold (baseline debt) | repair (fixes shallow-checkout defect) | `fetch-depth: 0` + 21-passed measurement |
| #503 | close-as-superseded | carried by #535 | file absent from `main`, present in #535 |
| #501 | close-as-superseded | partially superseded | evidence doc absent from both |
| #525 | repair | hold — design decision | controlled experiment; breaks sole-consumer control |

## 8. Safety declaration

No merge, close, rebase, retarget, push, commit, or deployment occurred. `main` remains
`7580bd8f`; #535 remains `8b6eadd7` and draft. The ledger artifact is untracked. All composition
experiments ran in detached worktrees under `/tmp`. EAA/dispatch PRs #502, #503, #508, #500,
#499, #496 were not advanced.

## 9. Next authorized action

Sovereign decision on #525 (one mount vs two), then authorization of the ordered plan in §5.
