# #508 disposition — the stacked base is #502, and #508 is already contained in #553

**Scope:** resolve the disposition of PR #508's stacked base, read-only. Nothing retargeted,
merged, reverted, or deployed.

**Measured:** 2026-10-25, `main` = `36f53be22d753ffe269f05cbf3fb39212f744207`.

---

## 1. The base branch is itself an open PR

`#508` targets `feat/engineering-acceptance-authority`, not `main`. That branch is not an
abandoned scratch branch — it is the head of **PR #502** ("feat(control-plane): introduce
Engineering Acceptance Authority"), an open **draft** targeting `main`.

| Fact | Value |
| --- | --- |
| #508 base ref | `feat/engineering-acceptance-authority` |
| #508 base SHA | `ef82cb9e2d05` |
| #502 head SHA | `ef82cb9e2d05` — **identical** |
| #502 state | open, draft, base `main` |
| commits in the base not in `main` | **17** |

So the structure is a two-level stack: `main` ← `#502` ← `#508`. The guard's finding
("merging it would land its base branch's commits unreviewed") is exactly right, and the
"base branch's commits" are #502's 17.

## 2. Retargeting is not a neutral fix — it widens the review surface

Your caution was correct. Measured both ways:

| View | Files | Insertions |
| --- | --- | --- |
| as-is, diffed against its own base `ef82cb9e` | **3** | 539 |
| retargeted to `main` | **8** | 1,067 |

Retargeting makes the *guard* happy (the base becomes `main`) while handing the reviewer
**2.7× the diff** — #502's content folded into #508's review. That is not a resolution; it
is a transfer of review burden, and it would put 17 commits in front of a reviewer who
opened a 3-file PR.

## 3. #508 is already contained in #553

`#553` (`integration/eaa-dispatch-readonly-evidence-current-main`, head `899d2242`) has a
50-file own-diff against `main`. #508's three files are **all** in that diff, and
**byte-identical** at #553's head:

| File | in #553's own diff | byte-identical at #553 head |
| --- | --- | --- |
| `docs/engineering/github-readonly-evidence-adapter.md` | yes | **yes** |
| `tests/test_github_readonly_evidence_adapter.py` | yes | **yes** |
| `weaver/github_readonly_evidence_adapter.py` | yes | **yes** |

This is the same **byte-identical containment** result I measured for #496/#500/#502/#508
against #553 in the earlier supersession pass. #508 introduces no content that #553 does
not already carry.

**Consequence: #508 does not need to be retargeted or merged. It is superseded by #553.**
Retargeting it would create a second review surface for content that already exists on
another, and the two could drift.

## 4. The `provider-routing` failure is NOT caused by #508

All three stack PRs show a `provider-routing` failure (#502, #508, #553 — one each).
I traced it rather than assuming.

**It is not the `localStorage.setItem` assertion.** That node
(`tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate`)
fails **identically on `main` and on the EAA base** — 1 failed, 9 passed on both. It is
pre-existing and recorded in
`docs/control-plane/evidence/gate-hygiene-baseline-stale-assertion-repair-living-gate-06/`.

**The gate's actual verdict** (job `119433388097`) is 4 failed / 3373 passed, from
`tests/test_history_depth_ci_wiring.py::test_a_workflow_selects_every_input_its_guard_reads`
for `economic-seam-engine.yml`, `provider-routing.yml`, `sg-02-fe-2-v.yml` — plus one more.

**That file does not exist on `main` or on the EAA base** (`git cat-file -e` → absent on
both). It is introduced by the integration branch
`integration/eaa-dispatch-readonly-evidence-current-main`. Run on #553's own tree:

```
3 failed, 19 passed in 7.78s
```

So the `provider-routing` failure originates **inside the #553 stack**, not in #508, and
not in `main`. It is a real finding of that branch's own new guard, failing on that
branch's own tree. It is a **pre-existing property of #553**, and it must be resolved
before #553 merges — it is not attributable to #508, and not attributable to the lane-guard
repair.

## 5. Disposition

| Item | Disposition | Basis |
| --- | --- | --- |
| #508 | **Superseded by #553 — do not retarget, do not merge** | 3/3 files byte-identical and already in #553's own diff |
| #508's base (#502) | leave as-is; it is a legitimate open draft | #502 is the parent of the stack, not an orphan branch |
| #553 | **hold** — carries 4 failing nodes of its own new guard | `test_history_depth_ci_wiring.py`, measured on its tree |
| lane guard #508 finding | **keep enabled** | true positive: the base is not an ancestor of `main` |

The guard's finding remains correct and should not be waived. The resolution is not to
retarget #508 — it is to recognize that #508 is contained in #553 and close it as
superseded, which also removes it from the lane's open-PR set and clears the finding
honestly.

## 6. Correction to my earlier report

I previously described the #508 finding only as "base not an ancestor of `main`, 17 commits
unreviewed". That was accurate but incomplete: I had not identified **which** PR the base
belongs to (#502), nor that #508 is contained in #553. Both are recorded here. The guard's
verdict is unchanged; the *disposition* is now specific.
