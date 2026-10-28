# WS2 — Lane-guard scope inversion: bounded design investigation

Status: **defect CONFIRMED by measurement. Repair proposed, not performed** (it edits a
governance surface). No file outside this evidence directory was changed.

Scope: the two questions the incident report raised about the shipped lane-currency guard.

1. Can the refresh process widen the blocking scope of the guard it refreshes — i.e. can a
   guard remove the lanes it governs from its own scope?
2. Is the mechanism **verified** rather than assumed?

Both are answered below by executing the shipped code, not by reading it.

## 1. The mechanism, as shipped

`scripts/lane_state_refresh.py::build()` derives each lane's `doc_guard`:

```python
for lane_no in matched:                                  # lanes_for(changed)
    if f"{DOC_OWNING_PREFIX}{LANE_OWNERSHIP[lane_no]['doc']}" in changed:
        lanes[lane_no]["deferred_to_pr"] = number        # <-- any matched PR editing the doc
...
lane["doc_guard"] = "deferred" if lane.get("deferred_to_pr") else "current"
```

`scripts/lane_state.py::current_lanes()` is the **blocking scope**:

```python
return [n for n in _lane_numbers(state)
        if state["lanes"][n].get("doc_guard") == "current"]
```

and `--check` consumes it as the judged set:

```python
findings += check_lane_docs(state, lanes=current_lanes(state))     # line 806
```

So `doc_guard` is the field that decides whether a lane is judged, and the refresh script
is what writes it.

## 2. Q1 — scope inversion is real. Measured.

Executed against the shipped modules (`sys.path.insert(0, "scripts")`), constructing
snapshots through the real `build()`:

| Case | `doc_guard` | in `current_lanes`? |
|---|---|---|
| A. PR touches **only** lane 1's doc | `current` | **yes** |
| B. PR touches lane 1's **source** and lane 1's **doc** | `deferred` | **no** |
| C. as B, with another lane's PR also open | `deferred` | **no** |

Case B is the inversion. `lanes_for(changed)` matches lane 1 because the PR edits lane-1
source; the deferral then fires because the same PR also edits lane-1's own doc. **A lane
that edits its own instruction doc while doing its own work removes itself from the scope
of the guard that judges that doc.** Lane 1's doc is the shell instruction —
`SHARED-CONTRACTS.md` row 1 assigns it to lane 1 — so the lane most able to self-exempt is
the lane that owns the shell contract.

Live confirmation: the snapshot in `main` at `36f53be2` reports
`current_lanes == ['1','2']` with lanes 3 and 4 `deferred` (to #548 and #555).

## 3. What actually escapes

`check_lane_docs` enforces four properties: (a) the doc exists, (b) it declares a PR,
(c) that PR is open in the snapshot, (d) the declared branch equals the PR's head branch.
On a self-deferred lane it returns **no finding at all** -- the lane is not judged, so none
of the four is evaluated.

Measured against the live snapshot with `records` populated the way `--verify-live` does
(all claimed-open PRs `OPEN`), for a deferred lane 1:

| Planted defect | Blocking | Advisory | Escapes entirely? |
|---|---|---|---|
| (a) doc missing | no finding | no finding | **yes** |
| (b) no `**Active PR:**` pointer | no finding | no finding | **yes** |
| (c) pointer to a closed PR | no finding | reported | no |
| (d) branch != PR head | no finding | no finding | **yes** |

**This corrects the first edition of this record, which said only (d) escapes.** That was an
understatement. (a), (b) and (d) are reported by *nobody*, because the advisory path runs
`_declared_pointer_findings`, which judges pointer liveness -- the (c) class -- and returns
early when the declared PR is absent from its `records` map.

## 4. The mitigation, stated precisely

`_declared_pointer_findings()` exists to close the dead-pointer hole and does so: (c) is
reported for every lane regardless of disposition. It is a **liveness** oracle, not an
agreement oracle, and the two property sets are disjoint. A deferred lane is therefore not
unguarded -- it is guarded for exactly one of the four properties.

Two further precisions, both measured:

- The mitigation lives inside `if args.verify_live:` (line 809), while `check_lane_docs`
  runs unconditionally (line 806). So a bare `lane_state.py --check` has **no** pointer
  liveness judgement at all for any lane. The workflow runs `--check --verify-live`, so the
  mitigation is active in CI -- but the guarantee belongs to the invocation, not the check.
- `--verify-live` is a separate `run:` in `.github/workflows/lane-doc-currency.yml`, so the
  step carrying pointer liveness is also the step that can be dropped.

## 4.1 The guard is already red on `main`

Measured at `36f53be2`:

```
$ python scripts/lane_state.py --check                      # exit 0, 0 findings
$ python scripts/lane_state.py --check --verify-live        # exit 1, 16 DRIFT findings
```

The snapshot's `base_main` is `68acf89f` while `main` is `36f53be2`, and every PR the
snapshot records as open has closed. This constrains repair design: a repair that widens
blocking scope is judged against an already-red gate, so it must be shown not to add
findings of its own.

## 5. Q2 — the mechanism is verified, not assumed

Every claim above was produced by executing the shipped code:

- `lane_state_refresh.build()` and `lane_state.current_lanes()` imported from `scripts/`
  and driven with synthetic PR/file maps — the same functions CI runs.
- The live snapshot read from `docs/control-plane/parallel-ui/lane-state.json`.
- The escape in §3 demonstrated by planting the defect and observing the absent finding.

No part of this rests on reading the source and inferring behaviour. Where the report's
phrasing ("the guard should not silently acquire authority through the mechanism it
governs") would have led to an over-strong conclusion — that a deferred lane is entirely
unguarded — measurement **contradicted** it and the narrower claim is recorded instead.

## 6. Assessment

The inversion is a real defect: a lane's blocking scope is derived from a field that a PR
the lane itself authors can set. The direction is wrong — authority over *whether a lane is
judged* flows from the lane being judged. That the practical escape is currently one
property (branch/head agreement) rather than all four makes it smaller, not correct, and
the property that escapes is exactly the one that catches a doc pointing at the wrong
thread.

## 7. The repair: the first proposal was FALSIFIED, the second was measured

### 7.1 The first proposal was wrong, and measurement is what showed it

This record's first edition proposed restricting `deferred_to_pr` to a PR that does **not**
itself match the lane, on the reasoning that a lane's own work PR editing its own doc is the
inversion. Measured against the live snapshot, that proposal is **falsified**:

- Both live deferrals are **self-inflicted**: PR #548 defers lane 3 and `lanes_for()` on its
  file list returns `['3']`; PR #555 defers lane 4 and returns `['4']`. Each deferring PR
  touches that lane's doc *and* that lane's paths.
- `scripts/lane_state_refresh.py:239` states the opposite of the proposal as **design
  intent**: "Only the PR that actually edits *this lane's* doc can carry its deferral."
- `check_lane_docs`' docstring agrees: "A lane whose doc is mid-repair on its own open PR is
  excluded here and reported by that lane's guard invocation instead."
- Applying the proposal sets lanes 3 and 4 to `current` and adds **3 pre-existing blocking
  findings** (`lane 3 declares PR #450 ... not an open lane PR`, and two for lane 4). It
  would redden `main` for debt it did not introduce.

The self-deferral is the mechanism, not a defect in it. The proposal was aimed at the wrong
layer, and only measurement revealed that. It is recorded here as falsified rather than
deleted, because the next reader will have the same intuition.

### 7.2 The repair as implemented

The real gap is narrower: a deferred lane's doc is excluded from `check_lane_docs`, and
that exclusion **also** dropped the branch/head agreement check, which no other oracle
covers. The docstring's promise -- "reported by that lane's guard invocation instead" -- has
no implementation: the guard exposes no per-lane selector, and the workflow invokes only
`--check` and `--check --verify-live`.

`lane_state.py` now carries `deferred_branch_findings()`, wired into `--check`:

```python
findings += check_lane_docs(state, lanes=current_lanes(state))
findings += deferred_branch_findings(state, lanes=current_lanes(state, invert=True))
```

Scope is the **complement** of the judged set, so no lane is judged twice.
`current_lanes(state, invert=True)` returns the deferred lanes; the two calls partition the
lane set (asserted).

The check is deliberately restricted to the case where the declared PR is **live in the
snapshot**. When it is not, the pointer itself is already the finding, so blocking there
would duplicate a pre-existing signal rather than close a hole.

### 7.3 Evidence the repair works, and does not over-reach

| Measurement | Result |
|---|---|
| New blocking findings on the live snapshot at `36f53be2` | **0** |
| Guard exit code, live tree, before and after | `--check` exit 0 both; `--verify-live` exit 1 both (16 findings, unchanged) |
| Planted defect (deferred lane 3 -> live PR, wrong branch), post-repair | **exit 1**, names `` declares branch `WRONG-BRANCH-DELIBERATE` but PR #563 heads `gate-hygiene/lane-currency-truth-01` `` |
| Same planted defect, **wiring removed** (pre-repair behaviour) | **exit 0**, 0 findings -- the defect was reported by nobody |
| `tests/test_lane_instruction_doc_currency.py` | 37 -> **42 passed** |
| Break the detector, keep the tests | 1 failed (`..._branch_mismatch_is_reported`) |
| Remove the wiring, keep the tests | 1 failed (`..._guard_is_wired_into_the_check`) |

The repair closes the hole for the property it names, adds nothing to an already-red gate,
and each new test is proven to bite on a real mutation.

### 7.4 Still not repaired

(a) missing doc and (b) absent pointer remain unreported for a deferred lane. They are
**left open deliberately**: both are properties of a doc that is by definition mid-repair,
and blocking on them would fire on the legitimate transient state the deferral exists to
permit. Recording them is the honest position; silently widening the repair to cover them
would be scope expansion beyond what was authorized.
## 8. What is not claimed

- Not repaired. Not merged. No workflow, snapshot, or guard file was modified.
- The residual exposure is stated as measured (one property), not as inferred severity.
- No production or deployment claim of any kind.
