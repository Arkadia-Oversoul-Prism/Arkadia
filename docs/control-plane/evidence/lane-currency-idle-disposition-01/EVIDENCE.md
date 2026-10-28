# Lane instruction-doc currency — the idle disposition (EVIDENCE)

**Workstream:** gate-hygiene / lane-currency-idle-disposition-01
**Branch:** `gate-hygiene/lane-currency-idle-disposition-01`
**Base main:** `9195334c6baba0b9349a1d931bc5773614944cd1`
**Observed:** 2026-10-28
**Status:** REPAIRED, tested, pushed for review. Production acceptance NOT CLAIMED
(this workstream does not deploy). Merge authority is the human sovereign's.

---

## 1. What was actually wrong

`Lane Doc Currency` (`.github/workflows/lane-doc-currency.yml`) was **red on `main`**.
The failing invocation is the *last* step, line 75:

```
run: python scripts/lane_state.py --check --verify-live
```

`--check` alone passed. The live oracle is what failed, and the reason is not a
stale doc — it is that the guard was **unsatisfiable for an empty lane**.

### 1.1 The measured state

Live `open` PRs across the whole repository: **0**. Every PR the snapshot had
recorded as open had merged or closed unmerged. Lane 3's doc pointed at **PR #450
(CLOSED, unmerged)** — a dead thread offered to a successor agent.

### 1.2 The structural defect

`lane_state_refresh.py` classified a lane holding no open PR as `current`:

```python
lane["doc_guard"] = "deferred" if lane.get("deferred_to_pr") else "current"
```

`current` means *judged*, and `check_lane_docs` judges a `current` lane by
requiring its doc to declare an `**Active PR:**` that is open in the snapshot.
A lane holding no open PR **cannot** name one. So for every idle lane the guard
demanded a fact that could not truthfully exist, and reported drift no matter what
the doc said. The gate could only be satisfied by writing a false pointer into a
lane doc — the exact defect the guard exists to prevent.

**This is the load-bearing finding:** the red gate was not a data-staleness
problem to be refreshed away. Refreshing the snapshot alone leaves the gate red,
because the unsatisfiable requirement survives the refresh.

---

## 2. The repair

A third disposition, `idle`, for a lane that holds no open PR. It is a **truthful
state, not an exemption** — which is the design constraint the whole repair turns
on. An `idle` lane is still judged; it must *positively state* that it holds no
active thread.

| File | Change |
| --- | --- |
| `scripts/lane_state_refresh.py` | emit `idle` when a lane has no open PRs (was `current`) |
| `scripts/lane_state.py` | `_IDLE_RE` + `declared_idle()`; `_disposition_findings` accepts and validates `idle`; `current_lanes()` scope is now "not `deferred`", so idle lanes stay judged; `check_lane_docs` handles the idle form |
| `docs/.../lane-state.json` | regenerated from live GitHub (schema `arkadia.lane-state/1.2`, base `9195334c`) |
| `docs/.../AGENT-0{1,2,3,4}-*.md` | append-only `**Active thread:** none` status block |

### 2.1 Why the declaration is positive, not silent

A doc that simply omits its pointer is indistinguishable from a doc that *forgot*
to declare one — and "forgot to declare" is the drift class this guard exists to
catch. So silence cannot spell "no active thread"; the doc must say it:

```
**Active thread:** none
```

`declared_idle()` is **last-wins**, compared by *position* rather than by kind, so
an appended `**Active PR:**` supersedes an earlier idle block and vice versa. That
is what lets a lane keep its earlier wave-header pointers as provenance while
declaring the current truth — and it means the guard reads the newest declaration,
not the first.

### 2.2 The claim is checked, not trusted

An idle declaration is cross-checked against the snapshot in **both** directions:

- `check_lane_docs`: a doc that declares idle while its lane still lists open PRs
  is reported. That is the continuity failure *in the opposite direction* — an
  instruction telling a successor agent to stand down while live work exists.
- `_declared_pointer_findings`: the pointer-liveness suppression is conditional on
  **both** facts (doc declares idle **and** the lane lists no open PRs). A lane
  that declares idle while holding open PRs keeps its pointer judged, so an idle
  claim cannot be used to hide live work.

`_disposition_findings` also rejects `idle` combined with `deferred_to_pr`.

---

## 3. Test-side repair (8 failures)

`tests/test_lane_instruction_doc_currency.py` reported **8 failures**. None was a
guard defect; all 8 were test-side, in two classes.

### 3.1 Class A — pins of live data the reconciliation legitimately superseded (4)

`test_live_pointer_check_agrees_with_the_committed_docs`,
`test_lane_one_shell_doc_is_guarded_current`,
`test_lane_one_shell_doc_does_not_name_a_merged_pr`,
`test_disposition_check_flags_an_unknown_disposition`.

These asserted `declared_pr(doc) in open_prs` and `doc_guard == "current"`. With
zero open PRs repo-wide, the first is unsatisfiable and the second is false — the
test pinned the *old* vocabulary and the *old* live data. They now assert the
disjunction the guard actually implements (a lane with open PRs points at one; a
lane without them declares idle), and accept the `current`/`idle`/`deferred`
vocabulary.

### 3.2 Class B — controls that could not execute (4)

`test_detector_flags_a_branch_that_does_not_match_its_pr`,
`test_deferred_lane_branch_mismatch_is_reported`,
`test_deferred_lane_with_a_matching_branch_is_not_reported`,
`test_deferred_branch_guard_does_not_judge_current_lanes`.

Each read a live PR out of the snapshot (`state["lanes"]["3"]["open_prs"][0]`).
With every lane idle that is an `IndexError` — the control **could not run at
all**, so the guard it was meant to prove was unproven while the suite stayed red
for an unrelated reason. They now build their own shape via a new
`_state_with_open_lane()` helper, which keeps the control's power (it still feeds
the detector the defect it claims to detect) without coupling it to what happens
to be open today.

**Deliberately not done:** the controls were not deleted or skipped. A skipped
negative control is the same defect as an absent one.

---

## 4. Evidence

### 4.1 The CI-critical path is green

```
$ python scripts/lane_state.py --check --verify-live
live PR state: 4 PR(s) read from Arkadia-Oversoul-Prism/Arkadia (0 claimed-open + declared doc pointers)
base main: 9195334c6baba0b9349a1d931bc5773614944cd1 (current: 9195334c6baba0b9349a1d931bc5773614944cd1)
doc-guard lanes: ['1', '2', '3', '4']; deferred: []
lane instruction docs consistent with snapshot (4 guarded lanes)
exit 0
```

All four lanes are `idle` and all four are **judged** — `deferred: []`, so no lane
is out of the blocking scope.

### 4.2 Live negative controls (the guard is not disarmed)

Run against the real files in the working tree, then restored byte-identically.

| Control | Mutation | Result |
| --- | --- | --- |
| NC1 | replace lane 1's idle declaration with a pointer to a closed PR | `exit 1`, drift reported |
| NC2 | declare lane 1 idle while the snapshot lists an open lane PR | `exit 1`, `lists open lane PRs [...]` |
| restore | — | `exit 0`, `lane instruction docs consistent with snapshot (4 guarded lanes)` |

NC2 is the important one: it proves the idle state cannot be used to suppress a
live-thread finding. NC1 proves the guard still bites on a dead pointer.

### 4.3 Targeted tests

```
$ python -m pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py -q
58 passed
```

```
$ python -m pytest tests/architecture -q
11 passed
```

```
$ python -m py_compile api/main.py   # P1-A guard
OK   (api/main.py under the 2600 budget; file untouched by this workstream)
```

### 4.4 Full suite (one pass, as budgeted)

```
$ python -m pytest tests/ -q -rEf --continue-on-collection-errors
8 failed, 3630 passed, 20 skipped, 1 error in 254.78s
```

Failing/error node set (9 nodes), sha256
`c280ddc616fe4f4e9110bf4e6b6e538783a83d3764148d8a6d7ac45f6e8bc46b`:

```
ERROR   tests/test_autonomy.py                                    (CE-01 module-vs-package collision, reserved to the sovereign)
FAILED  tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
FAILED  tests/test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set
FAILED  tests/test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated
FAILED  tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
FAILED  tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
FAILED  tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED  tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED  tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
```

**Attribution.** Zero of the 9 nodes belong to the lane-doc surface:

```
$ grep -c "lane_instruction_doc\|lane_currency\|lane_state" <node set>
0
```

and none of the 6 failing files references `lane_state`, `lane-state`,
`parallel-ui`, or `lane_state_refresh` (0 matches each). `lane-state.json` is read
by exactly one test file — `tests/test_lane_instruction_doc_currency.py` — which is
fully green. The 9 nodes are pre-existing main debt, recorded here and **not
repaired**: the two `test_engineering_lab_api.py` pins touch `api/lab_routes.py`,
an authority surface carrying the Lab mutation boundary, so repairing them is
sovereign-gated.

The 8 lane-doc-currency failures that motivated this pass are **absent** from the
node set, which is the direct evidence the repair landed.

---

## 5. Scope and boundaries

Touched paths, all admitted by `scripts/cp10_mutation_boundary_policy.py --judge`:

```
docs/control-plane/parallel-ui/AGENT-01-SHELL.md
docs/control-plane/parallel-ui/AGENT-02-NOVANET-OPPORTUNITY.md
docs/control-plane/parallel-ui/AGENT-03-SOLARIUN-KNOWLEDGE.md
docs/control-plane/parallel-ui/AGENT-04-ARKANA-WEAVER-LAB.md
docs/control-plane/parallel-ui/lane-state.json
scripts/lane_state.py
scripts/lane_state_refresh.py
tests/test_lane_instruction_doc_currency.py
```

- No protected authority, identity, K15/K3 governance, approval enforcement, or
  constitutional architecture is altered.
- `api/main.py` is untouched and compiles.
- Lane docs are append-only; no earlier line was rewritten, so each lane's
  provenance survives.

---

## 6. What remains open

1. **Four lanes are idle.** Under the lane scheme a lane at zero open PRs while
   reconciliation is exhausted is a deficit, not a resting state. Opening each
   lane's next bounded draft PR is the correct next action, and it is not taken in
   this pass — the pulse's budget went to the red gate. This is recorded as a
   deficit, not a completion.
2. **`--verify-live` fails closed on a GitHub outage** (by design). A transient
   outage reddens the step; re-run it. The safe direction for a staleness check.
3. The 9 pre-existing full-suite nodes above remain unrepaired, two of them
   sovereign-gated.

Merge authority, deployment, and acceptance remain the human sovereign's.
