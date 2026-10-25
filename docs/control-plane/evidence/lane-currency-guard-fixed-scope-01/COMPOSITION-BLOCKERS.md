# Composition blockers — precise characterization (read-only)

**Purpose:** replace the two composition blockers' summaries with measured detail, so the
release decision rests on the actual defect rather than a label.
**Nothing merged, closed, retargeted, reverted, or deployed.**

**Measured:** 2026-10-25. `main` = `36f53be22d753ffe269f05cbf3fb39212f744207`.

---

## Blocker 1 — #553's `provider-routing` failures

**Verdict: a true positive. #553 introduces 3 genuinely new failing nodes.**

`provider-routing.yml` is a **comparative** gate: it runs the suite at the merge base as a
baseline and fails only on nodes the candidate introduces (judge step, deliberately *not*
`continue-on-error`).

The raw `FAILED` list contains **4** nodes. Classified against #553's merge base
`04e1b83b89e5` (2026-10-15):

| Node | At merge base | Classification |
| --- | --- | --- |
| `test_history_depth_ci_wiring.py::test_a_workflow_selects_every_input_its_guard_reads[economic-seam-engine.yml]` | file **ABSENT** | **NEW — introduced by #553** |
| `…[provider-routing.yml]` | file **ABSENT** | **NEW — introduced by #553** |
| `…[sg-02-fe-2-v.yml]` | file **ABSENT** | **NEW — introduced by #553** |
| `test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | file **PRESENT** | pre-existing — fails on `main` and on the EAA base alike (1 failed / 9 passed on both) |

`tests/test_history_depth_ci_wiring.py` does not exist on `main` **or** on the EAA base. It
arrives with the integration branch. Run on #553's own tree: **3 failed, 19 passed**.

**What the new guard demands, and why it fails.** It asserts that any workflow judging
`tests/test_m02a_ci_gate_integrity.py` must select *every input that guard reads* in its
`paths:` filter. The failures name the missing inputs:
`musical-intention-engine/06-EXPERIMENTS/EXP-001.md` (for `provider-routing.yml`),
`musical-intention-engine/OPENHANDS-MVP-01.md` (for `economic-seam-engine.yml`), and
`enterprises/eden-food-systems/tasks.seed.json` (for `sg-02-fe-2-v.yml`).

This is the **same defect class** already recorded for this repository: a path filter that
omits an input the guard reads, so a change to that input alters what the guard asserts
without executing it. The guard is correct and the three workflows genuinely have the gap.

**So the blocker is real and specific:** either the three `paths:` filters gain the missing
inputs, or the branch's new guard must be reconciled with them. It is **not** attributable to
#508, not attributable to the lane-scope repair, and not a false positive to be waived.

## Blocker 2 — #548's lane-3 pointer, and a larger finding behind it

**Verdict: the "stale pointer" framing understates it. #548 would delete the live-verification
guard from `scripts/lane_state.py`.**

### 2.1 The pointer is stale in #548's own tree, and its green is self-referential

Lane 3's doc names three `**Active PR:**` lines. `declared_pr` takes the **last** match
(`matches[-1]`), so the pointer that governs is the final one:

| line | pointer | state |
| --- | --- | --- |
| 4 | `#431` | merged |
| 33 | `#450` | closed unmerged |
| **66** | **`#526`** | **closed unmerged** |

On `main`, the same doc's last pointer resolves to **#548** (open) — because `main`'s doc has
a later, correct entry. In **#548's own tree**, `declared_pr` returns **#526**, a closed
unmerged PR. #548's own snapshot also records `deferred_to_pr: 526`.

**#548's `lane-doc-currency` check reports `success` anyway** (started 2026-10-16T04:41:24Z).
Why: `main`'s workflow runs `python scripts/lane_state.py --check --verify-live`, but
**#548's tree does not contain `--verify-live`** — `grep -nE "verify-live"
.github/workflows/lane-doc-currency.yml` in #548's worktree returns nothing, and its
`lane_state.py` rejects the flag (`error: unrecognized arguments: --verify-live`). The dead
pointer is never evaluated because the checker on that branch cannot detect it.

**This is the same class as the lane-scope defect already under investigation:** a change that
removes the mechanism which would have reported it, and a green result that therefore cannot
be read as evidence.

### 2.2 The larger finding — #548 reverts the guard

Measured against `main`:

```
git diff --stat origin/main 3da97fa5316f -- scripts/lane_state.py
 1 file changed, 29 insertions(+), 458 deletions(-)
```

Symbol census (`_pr_state_findings|verify_live|fetch_pr_records`):

| revision | count |
| --- | --- |
| `main` | **8** |
| #548 `3da97fa5316f` | **0** |

#548's last commit touching the file is `9c57e87f` (2026-10-16); `main`'s is `3a1088c5`
(2026-10-25). #548 branched from merge base `04e1b83b` (2026-10-15) and never picked up the
live-verification work. Its branch is **not** an ancestor of `main`, so this is a genuine
divergence, not a stale checkout.

**Consequence:** #548 is not merely "missing a pointer repair". Merging it as-is would remove
the authoritative live PR oracle (`fetch_pr_records`, `_pr_state_findings`, the `--verify-live`
surface) that the lane model depends on — and it would do so while its own checks read green,
because the checker it removes is the one that would have flagged the removal.

Its `mergeable_state` is `dirty` (conflict), which is consistent: `lane_state.py`,
`lane-state.json`, and the lane-3 doc are all contended with `main`.

### 2.3 What #548's disposition should therefore be

Not "hold until the pointer is repaired" — that implies a one-line doc fix. The measured
condition is: **#548 must be rebased onto current `main` so it stops reverting
`lane_state.py`, and its lane-3 doc must name a live PR as its last pointer.** Both are
required; either alone leaves a hazard. Whether that rebase is worth doing, versus closing
#548 as superseded by the lane-3 work already on `main`, is a human decision — I have not
taken it.

## Blocker 3 (newly surfaced) — lane 3's pointer on `main`

Independent of #548: `main`'s lane-3 doc currently resolves to **#548**, which is `dirty` and
carries the revert above. So lane 3's live pointer on `main` names a PR that cannot merge
without damaging the guard. That is a lane-3 continuity question in its own right, separate
from #548's own disposition.

## Summary

| Blocker | Measured condition | Classification |
| --- | --- | --- |
| #553 `provider-routing` | 3 new failing nodes; `test_history_depth_ci_wiring.py` absent at merge base; 3 workflows omit inputs their judge reads | **true positive — needs a real fix** |
| #548 | reverts `lane_state.py` (458 deletions, 0/8 guard symbols); lane-3 last pointer is closed #526; green is self-referential | **hazard — rebase required, or close as superseded** |
| lane 3 on `main` | points at #548, which carries the revert | continuity question, separate from #548 |

None of the three is attributable to the #508 closure or to the lane-scope repair. All three
are composition-level and must be resolved before the `#567 → #568` release decision.
