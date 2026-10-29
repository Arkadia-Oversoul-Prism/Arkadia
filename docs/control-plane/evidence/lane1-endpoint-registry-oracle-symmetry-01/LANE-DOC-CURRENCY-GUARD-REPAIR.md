# Lane 1 — lane-doc currency guard: declared_idle reads the wrong pointer

Bounded repair of the lane-instruction-doc currency oracle, appended to the
existing Lane 1 draft PR #588. No new PR was opened; this continues the open
lane thread (N6 — continuation, not duplication).

## Defect (measured, evidence-backed)

`scripts/lane_state.py::declared_idle` compared the idle declaration against the
**first** `_PR_RE` match instead of the last:

```python
pr = _PR_RE.search(text)                      # first match
...
return pr is None or idle.start() > pr.start()
```

`declared_pr` (the sibling function) already documents and implements
**last-wins**. The docstring of `declared_idle` promises the same: "an appended
`**Active PR:**` supersedes an earlier idle declaration". The implementation
contradicted its own contract.

### Reproduction

Doc shape: a pointer, then the idle declaration, then a **newer** pointer.

```
**Active PR:** [#121](x)

**Active thread:** none

**Active PR:** [#6825](x)

**Active PR:** [#11099](x)
```

positions: pointers at `[0, 51, 78]`, idle at `26`.

| function | result | meaning |
|---|---|---|
| pre-repair `declared_idle` | `True` | reads pointer #121 (before the idle) → reports the lane **idle** |
| repaired `declared_idle` | `False` | reads pointer #11099 (after the idle) → reports the lane **live** |

`declared_pr` returns `11099` in both. The newest declaration is #11099, which
follows the idle line, so the lane is live and the idle line is superseded.
Pre-repair the guard reports a lane with an open thread as idle — the guard
silently stops judging a live lane.

### Negative control

Six shapes, corrected oracle, all as expected:

| shape | declared_idle | expected |
|---|---|---|
| idle before newest pointer (stale doc) | False | False |
| idle after newest pointer (fresh doc) | True | True |
| no idle at all (live thread) | False | False |
| idle only (lane holds nothing) | True | True |
| idle then one pointer (thread opened) | False | False |
| pointer then idle (thread closed) | True | True |

## Second defect — lane 1 did not own its own contract test

`scripts/lane_state_refresh.py::LANE_OWNERSHIP` for lane 1 listed
`tests/test_console_shell_nav_contract.py` but not
`tests/test_console_endpoint_registry_contract.py`. PR #588 changes that file,
so the refreshed snapshot classified #588 as unowned and left lane 1 idle. Lane 1
owns its endpoint-registry contract test; the omission made a Lane 1 PR
unassignable to Lane 1.

## Third defect — the synthetic control was not hermetic

`tests/test_lane_instruction_doc_currency.py::_state_with_open_lane` deep-copied
the live snapshot and overrode one lane. Any `deferred_to_pr` / `doc_guard`
already present on the *other* lanes leaked into the synthetic state. Once the
snapshot truthfully recorded lane 1 as deferred, the control
`test_deferred_branch_guard_does_not_judge_current_lanes` failed on a lane it
never constructed. The helper now clears live deferrals before applying its own
synthetic shape.

## Composition matrix (measured)

`declared_idle` repair (B) + ownership repair (C) + refreshed snapshot, on two trees:

| tree | variant | `test_lane_instruction_doc_currency.py` | `--check` |
|---|---|---|---|
| `main` b5bc34cb | none | 46 passed | 0 |
| `main` b5bc34cb | C only | 3 failed, 43 passed | 0 |
| `main` b5bc34cb | B only | 46 passed | 0 |
| `main` b5bc34cb | B+C | 3 failed, 43 passed | 0 |
| #588 eb80bcca | none | 46 passed | 0 |
| #588 eb80bcca | C only | 2 failed, 44 passed | 0 |
| #588 eb80bcca | B only | 3 failed, 43 passed | **1** |
| #588 eb80bcca | B+C | 2 failed, 44 passed | 0 |

Reading: **B alone is green on `main` but red on #588's own tree.** #588's
`AGENT-01-SHELL.md` appends its `**Active PR:** #588` pointer, so the corrected
oracle finally sees lane 1 as live — and then requires the doc to agree with a
snapshot that still lists lane 1 as idle. Repairing the oracle without refreshing
the snapshot turns the guard red on the very branch that owns the doc. The
snapshot refresh and the oracle repair are a single atomic change.

C alone is red on **both** trees: the refresh then assigns #588 to lane 1 while
lane 1's doc still says idle, and `test_live_pointer_check_agrees_with_the_committed_docs`
catches the disagreement. C is only safe together with the refreshed snapshot.

## Verification (all measured at this head)

| check | result |
|---|---|
| `pytest tests/test_lane_instruction_doc_currency.py` | **46 passed** |
| `pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py` | **58 passed** |
| `python scripts/lane_state.py --check` | exit **0** |
| `python scripts/lane_state.py --check --verify-live` | exit **0** |
| `pytest tests/architecture` | **11 passed** |

`--check --verify-live` output: `doc-guard lanes: ['2','3','4']; deferred: ['1']`
— lane 1 is deferred because its own open PR #588 edits `AGENT-01-SHELL.md`,
which is the correct disposition, not an exemption.

## Files changed

| file | change |
|---|---|
| `scripts/lane_state.py` | `declared_idle` reads the last pointer (4 lines) |
| `scripts/lane_state_refresh.py` | lane 1 owns its endpoint-registry contract test (1 line) |
| `tests/test_lane_instruction_doc_currency.py` | synthetic control resets live deferrals; lane-1 disposition accepts `deferred` (6 lines) |
| `docs/control-plane/parallel-ui/lane-state.json` | refreshed from live PR state at base `b5bc34cb` |

## Recorded, not repaired

- **`unassigned_open_prs` is never judged.** `lane_state_refresh.py` writes it
  (line 289) and prints it (line 390), but `grep -rn unassigned_open_prs` finds
  **no** reader in `lane_state.py` or its tests. The committed snapshot lists
  #587 there while #587 is merged and *is* `main` HEAD `b5bc34cb`. A merged PR
  cannot be "unassigned open"; the field is a write-only artifact. Wiring it
  into a decision changes what the gate judges, so it is recorded as a separate
  bounded workstream rather than repaired inside this slice.
- **`check_lane_docs` returns `[]` when a lane's doc declares a PR that the
  snapshot calls idle** (`lane 1: open_prs=[], unassigned=[588]`, doc declares
  #588 → no finding). Adding that check changes gate behaviour and needs its own
  evidence; recorded, not repaired.

## Authorization boundary

This slice is a guard/observability repair inside Lane 1's ownership. It alters
no authority, identity, governance, approval, or deployment surface. The PR
remains a **draft** and is not merged by this agent — merge and acceptance are
the human sovereign's.
