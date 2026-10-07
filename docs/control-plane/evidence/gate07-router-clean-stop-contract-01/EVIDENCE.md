# GATE-07 — Router clean-stop contract (composition-seam repair)

**Move:** `G07-CLEAN-STOP-CONTRACT`
**Status:** IMPLEMENTED — complete implementation with green targeted proof and zero
regression; awaits sovereign merge.
**Base main:** `74e8ea53a30213db8783e6733679d2f11903de0b`

## Objective

Distinguish a *clean stop* (a trajectory with nothing left to route) from a *blocked
frontier* (a trajectory that still carries a frontier the session could not route) at
the worker → attention composition seam, without editing the frontier's own vocabulary
or in-flight PR #336's router edit.

## Evidence-backed defect

`weaver/engineering_router.py::select_next_move` signals "no move" with blockers in
**both** cases and returns its fallback string *as* a blocker:

```
if not blockers:
    blockers.append("no legal pending move (all complete or dependencies unresolved)")
```

`weaver/attention_bus.py::_engineering_result_is_blocked` classified any
`NO_LEGAL_MOVE` with non-empty blockers as blocked, so the clean stop was pushed as a
HIGH `WEAVER_BLOCKED` `action_required` task every idle hourly session — an alert that
is both false and unactionable. PR #329 captured this as a strict xfail
(`test_clean_completion_stays_quiet_through_the_worker`) and declared the router
contract a separate bounded workstream. This is that workstream.

## Change

- `weaver/engineering_router.py` — publish the fallback string as the named constant
  `CLEAN_STOP_BLOCKER` (single source of truth; no behavioural change).
- `weaver/attention_bus.py` — import the constant and classify: a clean stop is the
  sentinel **and nothing else**; any other blocker (or a mixed list) is a real
  boundary. The clean stop projects as `WEAVER_STATE_CHANGED` INFO, channels
  `(keep,)`; an unroutable frontier stays `WEAVER_BLOCKED` HIGH, `action_required`,
  channels `(tasks, keep, push)`.

Deliberately **not** changed: `ACTIVE_STATUSES` / the `merged_acceptance_pending`
vocabulary (PR #332 records that as a decision-only item; it is the frontier's own
domain and a candidate for a future bounded move).

## Files

| Path | Change |
| --- | --- |
| `weaver/engineering_router.py` | sentinel constant; fallback uses it |
| `weaver/attention_bus.py` | clean-stop classification |
| `tests/test_router_clean_stop_contract.py` | 11-test guard + negative control + workflow-selection guard |

## Proof

Commands run in `/workspace/project/Arkadia` at `74e8ea53` with the change applied.

- **New guard** `python -m pytest tests/test_router_clean_stop_contract.py -q` →
  **11 passed**. Includes the negative control
  (`test_negative_control_nonempty_blockers_rule_would_misfile_the_clean_stop`) proving
  the pre-fix rule misfiles the clean stop, and `test_guard_is_selected_by_a_workflow_…`
  asserting a workflow runs the whole suite and is selected by `weaver/**`
  (`provider-routing.yml`), so the guard actually executes in CI.
- **Cross-workstream** — the fix applied onto PR #329's tree flags
  `test_clean_completion_stays_quiet_through_the_worker` as a **failed strict xfail**,
  exactly as #329's docstring predicted. The lane-1 guard would be satisfied by this
  repair.
- **Targeted** — `tests/test_scheduler_trajectory_conformance.py`,
  `tests/test_trajectory_schema_conformance.py`, `tests/test_workflow_injection_boundary.py`,
  `tests/test_m09_worker_contract.py`, `tests/test_attention_truthfulness.py`,
  `tests/test_attention_bus.py`, `tests/test_engineering_router_status_truthfulness.py`,
  `tests/test_engineering_scheduler_bootstrap.py` → **87 passed, 1 skipped**.
- **Architecture** `python -m pytest tests/architecture -q` → **11 passed** (unchanged).
- **Live path** — worker against `TRAJECTORY-CONSOLE-COMPLETION-01.yaml`: the genuinely
  stuck frontier still yields `WEAVER_BLOCKED` HIGH, `action_required=True`,
  `push=True` (truthful alert preserved). A synthetic clean-stop trajectory yields
  `WEAVER_STATE_CHANGED` INFO with no `push` channel (false alert eliminated).
- **Boot safety** `python -m py_compile api/main.py` → OK (`api/main.py` untouched).
- **CP10 boundary** — `scripts/cp10_mutation_boundary_policy.py --judge` on the changed
  paths → PASS.

## Regression comparison (node identity, not counts)

Full suite `python -m pytest tests/ -q -rEf --continue-on-collection-errors`:

| | failing/error nodes | sha256 |
| --- | --- | --- |
| baseline (`74e8ea53`, working tree stashed) | 11 | `f3e7364703a07b086d70ce6a86e7cc5a5cd5384cd93b69fc0f4be0278bfe2f48` |
| with change | 11 | `f3e7364703a07b086d70ce6a86e7cc5a5cd5384cd93b69fc0f4be0278bfe2f48` |

**Zero node-set delta.** The 10 failures + 1 collection error are pre-existing `main`
debt (steward-filter, AIS/R1/R3, m02-reasomate, CE-01 `weaver.autonomy` collision),
unrelated to this change and recorded, not fixed.

### CI reconciliation (`provider-routing.yml`, job `112844663445`)

`provider-routing` is **red on `main` itself**, not by this change. The job runs the
canonical command `python -m pytest tests/ -q -rEf --continue-on-collection-errors`
(`.github/workflows/provider-routing.yml:42`), the same one used above. Extracted
failing-node sets:

| revision | run / job | failing nodes | sha256 | summary |
| --- | --- | --- | --- | --- |
| `main` @ `17e626cd` | `37539664677` / `112529281094` | 14 | `2d523ab3277db33c6a3d027cd527ea34e3bbbc92c6bef440a84042b2cdad541f` | 14F / 1581P / 20S / 1E |
| PR #342 @ `f2027d3f` | `37636691316` / `112844663445` | 14 | `2d523ab3277db33c6a3d027cd527ea34e3bbbc92c6bef440a84042b2cdad541f` | 14F / 1710P / 20S / 1E |

**Identical 14-node set.** The 1 `ERROR` is the pre-existing CE-01
`tests/test_autonomy.py` module-vs-package collision present in both. The PR's
`+129` passed relative to the older `main` run is the accumulation of other merges
between `17e626cd` and `74e8ea5`, not this change. The new guard
`tests/test_router_clean_stop_contract.py` appears in neither failure nor error list;
had it failed or errored the node set would differ, so it passed in CI.

The absolute node count differs by environment (local 11 vs CI 14) — the documented
dependency/PYTHONPATH delta in this repo, not drift. The load-bearing invariant holds
within each environment: baseline vs change is node-for-node identical (CI `2d523ab3…`,
local `f3e73647…`).

## Remaining uncertainty

- Lane 1 (PR #329) is *not* auto-satisfied by this PR: its strict xfail is declared at
  PR-head and forbids XPASS. The two must compose; #329's xfail must be flipped to a
  plain assertion before or with its merge.
- `merged_acceptance_pending` remains unrecognized by `ACTIVE_STATUSES`; the live
  trajectory stops there as a blocked frontier (truthful). Reconciling that vocabulary
  is PR #332's recorded decision and remains a separate bounded move.

## Authority boundary

No merge, no deploy, no trajectory/schema mutation, no authority-path change. Human
merge only.
