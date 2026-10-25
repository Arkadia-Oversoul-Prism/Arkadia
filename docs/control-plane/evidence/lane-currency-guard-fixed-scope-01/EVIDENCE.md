# Lane guard: fixed enforced scope, and the gate green again

**Base:** `36f53be2` (main, 2026-10-25).
**Branch:** `gate-hygiene/lane-guard-fixed-scope-01`.
**Status:** repair implemented and measured. **Not merged; no deployment performed.**

---

## 1. What was repaired

Two distinct defects, both named in `INCIDENT.md`:

| | Defect A — the gate was red | Defect B — scope derived from the activity it judged |
| --- | --- | --- |
| Symptom | `lane_state.py --check --verify-live` exited **1** on `main` | Opening a PR removed its lane from judgement; one broad PR emptied the blocking scope |
| Cause | Snapshot recorded PR #563 as open; #563 closed unmerged 3 min after `3a1088c5` merged | `enforced set = {lanes with doc_guard == "current"}`, and `doc_guard` was computed by `lane_state_refresh.py` from live open PRs |

## 2. Defect B — the repair

`scripts/lane_state.py` gains `CANONICAL_LANES = ("1", "2", "3", "4")` and
`enforced_lanes(state)`, which returns the constant **unioned** with the snapshot's lanes.
The snapshot may only ever *add* a lane, never remove one. `doc_guard` is retained as a
descriptive field so an operator still sees which lanes are mid-repair; it no longer
controls what is judged.

`current_lanes()` is retained as an alias so existing callers and the currency contract's
own assertions keep working.

### 2.1 The second inversion site

The same defect appeared a second time in `--verify-live`. `_declared_pointer_findings`
was scoped to `owned = current_lanes(state)`, so deferring a lane also silenced the fact
that its doc pointed at a closed thread. The call site now passes `enforced`, and the
`advisory`-vs-blocking split (which existed only to soften that scoping) is removed.

The docstring of `_declared_pointer_findings` already recorded the exact hole and — 
importantly — that a *suppression* design had been measured and rejected:

> An earlier draft let a lane suppress this finding by naming an open "owner" PR that
> would re-point the doc. Measurement killed it: the two PRs that would have been named as
> owners each *install* a dead pointer rather than repair one, so the suppression would
> have been false.

This repair is consistent with that finding rather than reversing it: nothing suppresses
the finding now.

### 2.2 Fail closed

`_enforced_set_findings` reports an empty enforced set as drift, so a guard that judges
nothing cannot report success. It also reports a lane that is judged but absent from
`CANONICAL_LANES`, keeping the deliberate duplication visible rather than silently
divergent.

## 3. Acceptance — the probe now passes

`scripts/lane_scope_probe.py` is the executable statement of the invariant. Before the
repair it failed 3 of 4 checks; now:

```
$ python scripts/lane_scope_probe.py
[PASS] one PR cannot exempt its own lane from judgement   {'removed': []}
[PASS] one PR cannot empty the blocking scope             {'judged_after': ['1','2','3','4'], 'of': 4}
[PASS] an empty or fully-deferred snapshot cannot pass vacuously
[PASS] a lane with no ownership entry is still subject to judgement
All 4 checks passed.                                      exit 0
```

## 4. Defect A — the repair, and what it exposed

The snapshot was **re-measured** (`lane_state_refresh.py --write`) rather than patched:
`base_main` → `36f53be2`, lane 3's active PR → #548, #563 removed from lane 3's open list.

Re-measurement alone was **not** sufficient. Once the enforced set stopped being derived,
lanes 3 and 4 became judgeable on every run, and both were carrying dead pointers that
deferral had been hiding:

| Lane | Was declaring | Live state |
| --- | --- | --- |
| 3 | PR #450 | **closed without merging** — a successor following it is sent nowhere |
| 4 | PR #428 | **merged** 2026-10-11 at `71190dd3`; also had no `**Active branch:**` pointer at all |

Both docs received an appended dated status block pointing at their live thread (#548,
#553). Appending is the corpus convention — it preserves the earlier text as provenance.

**Result: `--check --verify-live` exits 0, judging 4 lanes instead of 2.** The gate is
green because the scope is stronger, not because a check was weakened.

### 4.1 A latent trap, recorded rather than triggered

PRs **#548 and #555** each append a status block to the lane doc they touch that declares
a **closed** PR (#526 and #536 respectively — both closed without merging). Merging either
as-is re-introduces a dead pointer in a now-enforced lane. This is not a defect in those
PRs' own scope; it is a consequence of the enforced set widening, and it is recorded here
so the sovereign sees it before merging them.

## 5. Verification

### 5.1 Negative controls — the repair can be undone and it will be noticed

| Control | Applied | Observed |
| --- | --- | --- |
| Restore derived scope in `enforced_lanes` | `CANONICAL_LANES` union replaced with the `doc_guard` filter | probe **exit 1**; **6** fixed-scope tests red |
| Remove the new guard from both path filters | workflow edited | wiring guard red (1 failed, 12 passed) |
| Remove the new guard's executing step | workflow edited | wiring guard red (1 failed, 16 passed) |
| Swap `shipped_scope` for a stub | probe edited | anti-disarm test red |

Every control was restored byte-identically and re-verified green.

The third control **failed on its first attempt** and found a real gap: the wiring guard
asserted the filters named each guard but never that the workflow *executed* it, so a
guard could be selected on every change and run on none. `test_workflow_executes_every_guard_it_selects`
and its converse close that, parametrized over every guard so a future one is covered by
the same rule.

### 5.2 Regression

| Tree | Result |
| --- | --- |
| `main` `36f53be2` | 112 failed, 2279 passed, 111 errors |
| this branch | 112 failed, 2303 passed, 111 errors |

Failing/error **node set identical**: 223 nodes,
`sha256 71bbca1c5dcc6547`, `comm -3` empty. **Zero regression.** The `+24 passed` is this
branch's new test file (14) plus the wiring guard's new parametrizations (3) and the
lane-contract suite's nodes.

`api/main.py` untouched. CP10 mutation boundary PASS on all changed paths.

## 6. What was not done

- No merge. No deployment. No revert. No branch-protection change.
- No check was weakened to make the gate green; the gate is green at a **wider** enforced
  scope than before.
- The four PRs in the queue that this repair does not touch were not modified.

## 7. Next permitted action

Sovereign review of this branch at an exact head. Merging it restores the lane gate to a
trustworthy state and green; merging it is a **production release**, because Render
auto-deploys `main`.
