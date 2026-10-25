# #508 closed as superseded by #553 — execution record

**Authorization:** explicit human authorization to close #508 as superseded by #553.
**Scope held:** close only. No merge, no retarget, no revert, no deployment.
**Measured:** 2026-10-25. `main` = `36f53be22d753ffe269f05cbf3fb39212f744207`.

---

## 1. Pre-mutation verification

Re-measured immediately before acting, not restated:

| PR | Head | State | Base |
| --- | --- | --- | --- |
| #508 | `071ecd8c5f3b` | open, draft | `feat/engineering-acceptance-authority` |
| #502 | `ef82cb9e2d05` | open, draft | `main` |
| #553 | `899d22424d78` | open, draft | `main` |

`#508.base.sha == #502.head.sha` → **true**.

Byte-comparison immediately before the mutation:

| File | in #553's own diff | byte-identical at #553 head |
| --- | --- | --- |
| `docs/engineering/github-readonly-evidence-adapter.md` | yes | yes |
| `tests/test_github_readonly_evidence_adapter.py` | yes | yes |
| `weaver/github_readonly_evidence_adapter.py` | yes | yes |

**HOLDS.** Proceeded.

## 2. The close

- Supersession comment posted: https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/508#issuecomment-6399470449
- `PATCH /pulls/508 {"state":"closed"}` → `closed_at 2026-10-25T15:23:41Z`

**Independently verified after the call:**

```
state        = closed
merged       = False
merged_at    = None          <- a close, NOT a merge
#508 in live open PRs?  False   (22 open PRs remain)
```

`state_reason` returned `None` despite `"not_planned"` being sent. Recorded rather than
reconciled: the closure is confirmed by `state`, `merged` and the live open-PR list, so the
disposition is unambiguous; the unrecorded reason field is a cosmetic API detail.

## 3. Snapshot refresh (conditional, performed only after confirming closure)

Confirmed `state == "closed"` before refreshing, then ran `lane_state_refresh.py --write`.

**Before/after comparison — the guard requested for exactly this step:**

| lane | before `open_prs` | after `open_prs` | changed? |
| --- | --- | --- | --- |
| 1 | [550, 562] | [550, 562] | no |
| 2 | [564] | [564] | no |
| 3 | [548, 549, 554] | [548, 549, 554] | no |
| 4 | [499, **508**, 525, 535, 547, 550, 553, 555] | [499, 525, 535, 547, 550, 553, 555] | **yes — #508 only** |

`deferred_to_pr`, `doc_guard` and `active_thread` for every lane: **unchanged**.
`closed_unmerged`: gained **508**, lost nothing.
`base_main`: unchanged (`36f53be2`).

`unassigned_open_prs` gained **569** and **570** — PRs that appeared on the repository
during this pass, not refresh artifacts. The refresh observed real activity; it did not
reassign anything unexpectedly.

**Verdict: only the expected state changed.** No unrelated lane reassignments or pointer
churn.

## 4. The gate, and a negative control

After closure + refresh:

```
enforced lanes: ['1', '2', '3', '4']; doc_guard (descriptive): ['1','2'] current, ['3','4'] deferred
lane instruction docs consistent with snapshot (4 enforced lanes)
EXIT=0
```

The #508 finding is gone, and the gate is green **judging 4 lanes** — the finding cleared
because the input changed, not because a check was relaxed.

### 4.1 Negative control — and a correction to my own earlier analysis

**First attempt did not bite, which is how the error surfaced.** I injected a fabricated PR
(#9999) into lane 4 with `base_ref: "some-other-branch"`. The gate went red — but on
`HTTP 404 ... UNKNOWN`, not on the base-branch check. A control that fires for the wrong
reason proves nothing about the check under test.

Second attempt: I claimed a **real** open PR (#569) in lane 4 with a fabricated
`base_ref`. Result: **exit 0** — the control did **not** bite. This falsified my stated
mechanism.

Third attempt, decisive: I claimed the **really-stacked** #568 in lane 4, with the snapshot
deliberately recording `base_ref: "main"` (a lie). The finding fired anyway, quoting the
**live** value:

```
DRIFT PR #568 (lane 4 open_prs) targets base branch
'gate-hygiene/lane-guard-authority-boundary-01', not 'main'; it is STACKED
```

**Corrected mechanism.** `_base_branch_findings` iterates `claimed_open_prs(state)` — the
**snapshot** — to choose *candidates*, but reads `base_ref` from the **live API record**
(`records.get(number)` → `record.get("base").get("ref")`). The snapshot does not supply the
value; it supplies the *set of PRs examined*.

**Correction to `PR508-REVERIFICATION.md` §2.** That document said the finding "comes from
`lane-state.json`'s lane 4 `open_prs` entry for #508, which records `base_ref: ...`". That
was wrong: the value is live. The **conclusion** it supported still holds — close and
refresh are two separate steps — but the reason is different, and the earlier document
should be read with this correction:

- **Closing #508 alone** leaves it a **candidate** in the snapshot. The live record then
  reports it closed, producing the *other* finding ("is recorded as open but is CLOSED
  without merging") — so the gate stays red, for a different reason. Demonstrated: re-adding
  closed #508 to lane 4 produced both the dead-thread finding **and** the stacked finding.
- **Refreshing alone** (with #508 still open) re-records it as a candidate with a live
  stacked base — still red.
- **Both steps** remove it from the candidate set, and the finding clears. Verified: exit 0.

So the two-step requirement is real; only my explanation of *why* was wrong.

## 5. What this does and does not establish

**Established:**
- #508 is closed, not merged. Its content is carried by #553.
- The lane-4 snapshot no longer claims #508; the change is isolated to that entry.
- The gate passes at 4 enforced lanes; the detector is still armed (proven by §4.1).
- #553's `provider-routing` failures remain a **separate, unresolved** blocker
  (`tests/test_history_depth_ci_wiring.py`, 3 failed / 19 passed on its own tree).

**Not established — explicitly not claimed:**
- **#568 is not green and not released.** This pass did not re-run #568's CI. A cleared
  #508 finding is not a green gate and not release acceptance.
- No merge, retarget, revert or deployment occurred.
- #548's lane-3 pointer is still unresolved; #555's ordering fragility is unchanged.
- The `unassigned_open_prs` coverage limit stands (see `PR508-REVERIFICATION.md` §3) and was
  **not** repaired here.
