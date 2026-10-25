# Re-verification before the close decision — read-only

**Purpose:** confirm the supersession relationship still holds at *current* heads before any
close action is authorized, and establish what the close would and would not change.
**Nothing closed, merged, retargeted, reverted, or deployed.**

**Measured:** 2026-10-25. `main` = `36f53be22d753ffe269f05cbf3fb39212f744207`.

---

## 1. Supersession still holds at current heads

| PR | Head | State | Base |
| --- | --- | --- | --- |
| #508 | `071ecd8c5f3b` | open, draft | `feat/engineering-acceptance-authority` |
| #502 | `ef82cb9e2d05` | open, draft | `main` |
| #553 | `899d22424d78` | open, draft | `main` |
| #568 | `6aa0f85c4b2e` | open, draft | `gate-hygiene/lane-guard-authority-boundary-01` |

`#508.base.sha == #502.head.sha` → **true**. The stack is `main` ← #502 ← #508, unchanged.

`#508` own diff against its base: **3 files, 539 insertions**.
`#553` own diff against `main`: **50 files**.

**Containment, byte-compared at the current heads:**

| File | in #553's own diff | byte-identical at #553 head |
| --- | --- | --- |
| `docs/engineering/github-readonly-evidence-adapter.md` | yes | **yes** |
| `tests/test_github_readonly_evidence_adapter.py` | yes | **yes** |
| `weaver/github_readonly_evidence_adapter.py` | yes | **yes** |

**SUPERSESSION HOLDS.** No drift since the earlier measurement.

## 2. Closing #508 does NOT by itself clear the guard finding

This is the material correction of this pass, and it changes the order of operations.

`_base_branch_findings` iterates `claimed_open_prs(state)` — the **snapshot**, not live
GitHub. The finding is produced from `lane-state.json`'s `lanes["4"]["open_prs"]` entry for
#508, which records `base_ref: "feat/engineering-acceptance-authority"`.

Demonstrated by simulation on a detached worktree: removing #508 from lane 4's
`open_prs` (what a post-close `lane_state_refresh.py` run would produce) makes the gate
exit **0**:

```
lane4 open_prs before: [499, 508, 525, 535, 547, 550, 553, 555]
lane4 open_prs after : [499, 525, 535, 547, 550, 553, 555]
enforced lanes: ['1','2','3','4'] ... lane instruction docs consistent with snapshot
EXIT=0
```

**Consequence:** the closure and the snapshot re-measurement are two steps, not one.
Closing #508 on GitHub leaves the finding in place until the snapshot is refreshed, because
the snapshot is the guard's input. Conversely a refresh alone — with #508 still open —
would simply re-record the same stacked `base_ref` and keep the gate red.

The correct sequence is therefore **close #508 → re-run `lane_state_refresh.py` → the
finding clears because the input changed**, not because the check was relaxed.

## 3. New scope finding: the stacked-PR check does not cover unassigned PRs

`_base_branch_findings` scans **lane-claimed** PRs only (`claimed_open_prs`). PRs in the
snapshot's `unassigned_open_prs` are never inspected for `base_ref` — `grep -n
"unassigned_open_prs" scripts/lane_state.py` returns **nothing** in any finding path.

This matters because **#568 is itself stacked** — its base is
`gate-hygiene/lane-guard-authority-boundary-01` (#567's branch) — and it sits in
`unassigned_open_prs`. The check whose docstring cites #568 as its motivating example
therefore **cannot report #568**:

```
claimed_open_prs: [499, 508, 525, 535, 547, 548, 549, 550, 553, 554, 555, 562, 564]
#568 claimed by a lane?  False
#508 claimed by a lane?  True  ['lane 4 open_prs']
```

This is **not** a defect in the repair and **not** a reason to distrust the #508 finding —
#508's finding is correct. It is a **coverage limit** to record: the check protects the
lane-governed set, and an unassigned PR with the same structural hazard is outside it.
Repairing it would widen the check's domain, which is a separate bounded change and must
not be bundled into this one.

## 4. `provider-routing` remains a #553-internal finding

Unchanged from the prior pass, restated because it governs the #553 hold: the 4 failing
nodes come from `tests/test_history_depth_ci_wiring.py`, a file **absent on `main` and on
the EAA base**, introduced by the integration branch. On #553's own tree: **3 failed, 19
passed**. It must be resolved before #553 merges.

## 5. State of the recommended sequence

| Step | Status after this pass |
| --- | --- |
| 1. Re-verify supersession at current heads | **DONE** — holds, no drift |
| 2. Authorize + close #508 as superseded, linking #553 | **NOT AUTHORIZED, NOT PERFORMED** |
| 3. Re-run checks on #568's exact head; record SHA + run IDs | pending closure |
| 4. Keep #553 blocked on its own guard failures | holds — 3 failed on its tree |
| 5. Resolve #548's lane-3 pointer | pending |
| 6. Reassess #567 → #568 as a separate release decision | pending |

**Additional step surfaced by §2:** after closing #508, the snapshot must be re-measured
before the #568 finding clears. Closing without refreshing will look like the close "did not
work".

## 6. Boundary

No close, merge, retarget, revert, or deployment was performed. The disposition is
recommended, not executed; execution authority is the human's. The supersession evidence in
§1 is the support for the close decision, not the decision itself.
