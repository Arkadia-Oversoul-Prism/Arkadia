# `lane-doc-currency` was RED on `main` — stale snapshot, not a lane defect

Boundary: **reconciliation** (the `lane-doc-currency` gate), not a lane feature slice.

- Observed at: 2026-11-01
- Base / repaired against `main`: `dd49891385eb944dfacdfa69ceaef603c79b665d`
- Failing CI run: `41317998445` (`event=push`, `head 9de0e0fb`, `lane-doc-currency` = **FAILURE**)
- Open PRs at measurement: **0**

## 1. Defect

`scripts/lane_state.py --check --verify-live` is the executable step of
`.github/workflows/lane-doc-currency.yml`. On `main` at `dd498913` it exits **1**:

```
DRIFT PR #605 (lane 4 open_prs, lane 4 deferred_to_pr) is recorded as open but is MERGED
      (merge commit 9de0e0fb); re-measure the lane PRs and re-point the lane
```

Two records in `docs/control-plane/parallel-ui/lane-state.json` claimed lane 4 had a live thread:

| field | recorded | actual |
|---|---|---|
| `lanes.4.open_prs[0].number` | `605` | merged (`9de0e0fb`) |
| `lanes.4.deferred_to_pr` | `605` | merged |
| `lanes.4.active_pr` | `605` | merged |
| `unassigned_open_prs[0].number` | `606` | merged (`dd498913`) |

`claimed_open_prs()` deliberately judges both claim sites — an `open_prs` entry and a
`deferred_to_pr` pointer are the same continuity defect, because both tell a successor agent that
a dead thread is handling the lane. The guard is therefore correct; the snapshot was stale.

## 2. Why the snapshot was stale

The snapshot was derived at `observed_at 2026-11-01T08:48:55Z` against `base_main d14c2598`.
`#605` merged at `9de0e0fb` **after** that derivation, and `#606` merged as `dd498913`. No
repository change invalidated the guard's logic; the input to it moved.

This is the recorded `head_sha`-not-judged class, one step further along: the snapshot is a
*derivation*, and a derivation ages the moment a lane PR merges.

## 3. Repair

Two edits, both inside the snapshot's own guarded surface. No guard, workflow, or test logic was
changed — the oracle was not disarmed to make the gate green.

**(a) Re-derive, do not hand-edit** — `lane-state.json` regenerated from live PR state:

```
python scripts/lane_state_refresh.py --write --base-main dd49891385eb944dfacdfa69ceaef603c79b665d
```

Effect: `#605` moves `open_prs` -> `merged_prs` (`9de0e0fb`); lane 4 `active_pr`/`active_branch`
become `null`; `deferred_to_pr` is dropped; `doc_guard` `deferred` -> `idle`; the stale
`unassigned_open_prs` entry for `#606` is cleared. `11 insertions(+), 26 deletions(-)`.

**(b) Re-point the lane doc** — `AGENT-04-ARKANA-WEAVER-LAB.md` carried `**Active PR:** #605`,
which is the pointer `declared_idle()` reads. Because the guard reads the **last** declaration, the
repair is an **append** (21 inserted lines, 0 deleted):

```
**Active thread:** none
```

The appended block names the superseding merge commit and states plainly that lane 4 at zero open
PRs is a **deficit**, not a resting state. The merged pointer block above it is left byte-identical
— this repository's standing rule is that text an oracle line already carries is corrected by
appending a dated supersession, never by rewriting the line.

## 4. Verification

| check | command | result |
|---|---|---|
| offline consistency | `python scripts/lane_state.py --check` | **exit 0** — `doc-guard lanes: ['1','2','3','4']; deferred: []` |
| live oracle (the CI step) | `python scripts/lane_state.py --check --verify-live` | **exit 0** — `4 PR(s) read … (0 claimed-open + declared doc pointers)` |
| lane guard suite | `pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py -q -rEf` | **61 passed** |
| architecture fitness | `pytest tests/architecture -q -rEf` | **11 passed** |
| CP10 boundary | `cp10_mutation_boundary_policy.py --judge` over the changed paths | **exit 0**, PASS |

Before the repair the same live-oracle command exited **1** with the DRIFT line above; that
before/after on an unchanged oracle is the negative control for this repair.

## 5. What is NOT claimed

- No merge, deployment, or acceptance. Merge authority is the sovereign's.
- No lane slice is claimed complete; lane 4 is **idle** and owes its next bounded PR.
- `--verify-live` reads GitHub live. A later merge re-ages this snapshot; the gate going red again
  is a correct signal, not a regression of this repair.
