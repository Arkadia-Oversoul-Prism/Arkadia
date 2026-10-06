# GATE-07 · Attention truthfulness — an unresolved hourly stop must reach the sovereign

**Workstream:** hourly bounded-execution loop repair (scheduler → trajectory → router → attention)
**Gate:** GATE-07 (durable Weaver loop)
**Status:** IMPLEMENTED (repository-source proof; not a production claim)
**Base main:** `451e41a`
**Branch:** `gate07/attention-truthfulness`

## 1. Defect

`weaver/attention_bus.py::build_engineering_attention_event` derived salience from the
status alone:

```python
event_type = "WEAVER_STATE_CHANGED" if status not in {"FAILED", "BLOCKED"} else "WEAVER_BLOCKED"
high = status in {"FAILED", "BLOCKED"} or not execution.get("ok", True)
```

`NO_LEGAL_MOVE` therefore became a plain `WEAVER_STATE_CHANGED` at `INFO` with
`action_required = false` and `push_delivery = false`. But `NO_LEGAL_MOVE` is only a
*clean* stop when the router has nothing to report. When it is returned **with
blockers**, the trajectory still carried a frontier the session could not route:

| blocker (live) | origin |
| --- | --- |
| `invalid trajectory structure` | structural slip — the live hourly failure `37379043890` |
| `unrecognized move status: …` | the G12-A/G12-C `merged_acceptance_pending` slip (PR #322) |
| `G12-B: missing dependency …` | unresolved dependency |
| `G12-B: scope/spec missing` | incomplete move spec |

Measured before the repair (public builder, base `451e41a`):

```
FAILED           blockers=1 -> type=WEAVER_BLOCKED       sev=HIGH  action=True  push=True
NO_LEGAL_MOVE    blockers=1 -> type=WEAVER_STATE_CHANGED sev=INFO  action=False push=False
BLOCKED          blockers=0 -> type=WEAVER_BLOCKED       sev=HIGH  action=True  push=True
READY_FOR_REVIEW blockers=0 -> type=WEAVER_STATE_CHANGED sev=INFO  action=True  push=True
```

The hourly loop could stop on an unroutable frontier and the sovereign would receive no
push and no action flag — the same "green/silent while work remains" class the sibling
PRs address at the schema (#321) and router (#322) layers.

## 2. Change

`weaver/attention_bus.py` — one helper, one call site:

```python
def _engineering_result_is_blocked(result: dict[str, Any]) -> bool:
    status = str(result.get("status") or "UNKNOWN")
    if status in {"FAILED", "BLOCKED"}:
        return True
    return status == "NO_LEGAL_MOVE" and bool(result.get("blockers"))
```

`NO_LEGAL_MOVE` **with** blockers now projects as `WEAVER_BLOCKED`, `HIGH`,
`action_required = true`, push delivery. A clean `NO_LEGAL_MOVE` (no blockers) is
unchanged: `WEAVER_STATE_CHANGED` / `INFO` / no push. `READY_FOR_REVIEW` is unchanged.

No new mutation path, no authority change, no merge/deploy surface. This module converts
an already-produced state into bounded delivery intents; the repair only stops it from
under-reporting one.

## 3. Proof

Guard: `tests/test_attention_truthfulness.py` (9 tests), public API only.

| command | result |
| --- | --- |
| `pytest tests/test_attention_truthfulness.py -q` | 9 passed |
| `pytest tests/test_attention_truthfulness.py tests/test_attention_bus.py tests/test_engineering_scheduler_bootstrap.py -q` | 31 passed |
| `pytest tests/architecture -q` | 11 passed |
| `pytest tests/ -q -rEf --continue-on-collection-errors` | 12 failed / **1519 passed** / 18 skipped / 1 error |

Negative controls (the guard's teeth, measured by reverting the rule to status-only):

* reverted rule → **5 failed** (`test_no_legal_move_with_blockers_is_pushed[4 params]`,
  `test_negative_control_status_only_rule_would_miss_the_defect`); restored → 9 passed.
* `test_clean_no_legal_move_stays_quiet` fails if the repair is widened to flag *every*
  `NO_LEGAL_MOVE`, so the detector cannot be satisfied by over-reporting.

Selection: `test_guard_is_selected_by_a_workflow_that_runs_the_whole_suite` fails unless
some workflow runs `pytest tests/ -q` **and** is path-selected by `weaver/**`
(`provider-routing.yml`). A guard nothing executes is decoration.

## 4. Regression boundary

Failure node-set (sorted `FAILED`/`ERROR` lines) on this branch:

```
sha256 c7037c80f12c1c49d067903d2ab7e87ae335f94528a304d4b9698686689e4195  (13 nodes)
```

This is **exactly** the recorded baseline for base `451e41a` — zero node-set delta. The
only count movement is `1510 → 1519 passed`, which is precisely the 9 added guard tests.
All 12 failures and the `test_autonomy.py` collection error are pre-existing main debt
(the CE-01 `weaver.autonomy` module-vs-package collision is reserved to the sovereign and
was not touched).

## 5. Relationship to the sibling PRs

#319 (scheduler trajectory conformance) → #321 (schema status enum + CI-live schema
guard) → #322 (router reports unrecognized status). This PR sits downstream of all three
and touches disjoint files (`weaver/attention_bus.py`, `tests/test_attention_truthfulness.py`,
this evidence doc), so it composes with the stack without conflict. The layer it closes is
the last mile: even when the schema and router correctly *identify* an unroutable
frontier, the sovereign notification path must not file it as a quiet INFO event.

## 6. Remaining uncertainty

* Repository-source claim only. No runtime/deployment observation is made or implied.
* The trajectory data-loss concern around `completion_rule` / nested `moves` in the #319
  edits is a separate proposed workstream and was not investigated here.
