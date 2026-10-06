# WORKSTREAM STATE · gate07-attention-truthfulness

**Workstream:** hourly bounded-execution loop repair (scheduler → trajectory → router → attention)
**Gate:** GATE-07 (durable Weaver loop)
**Owner of execution:** OpenHands (Weaver pass) · **Authority:** human sovereign
**PR:** #323 · **Branch:** `gate07/attention-truthfulness`
**BASE_MAIN:** `451e41a`
**Head at record time:** `c0314bd3c27c7fc4d43e5e53297126a0c5da938d`

## Status

IMPLEMENTED — code + guard + evidence committed, PR open, awaiting human merge.
Repository-source claim only; no runtime or production observation is made.

## What changed

`weaver/attention_bus.py::build_engineering_attention_event` decided salience from the
status alone, so `NO_LEGAL_MOVE` was always a quiet `WEAVER_STATE_CHANGED` at `INFO`
(`action_required=false`, `push_delivery=false`). Returned **with blockers** it means the
trajectory still carried an unroutable frontier, and that stop must reach the sovereign.

Added `_engineering_result_is_blocked()` and used it for `event_type` / `high`:
`NO_LEGAL_MOVE` with blockers → `WEAVER_BLOCKED` / `HIGH` / `action_required` / push.
Clean `NO_LEGAL_MOVE` and `READY_FOR_REVIEW` are unchanged. No new mutation, authority,
merge, or deploy surface.

## Verification (measured)

| command | result |
| --- | --- |
| `pytest tests/test_attention_truthfulness.py -q` | 9 passed |
| `+ tests/test_attention_bus.py tests/test_engineering_scheduler_bootstrap.py -q` | 31 passed |
| `pytest tests/architecture -q` | 11 passed |
| `pytest tests/ -q -rEf --continue-on-collection-errors` | 12F / **1519P** / 18S / 1E |

Failure node-set sha256 `c7037c80f12c1c49d067903d2ab7e87ae335f94528a304d4b9698686689e4195`
(13 nodes) — identical to the `451e41a` baseline. Zero node-set delta; `+9 passed` is the
new guard file.

Negative control: reverting the rule to status-only fails 5 guard tests; restoring → 9
passed. `test_clean_no_legal_move_stays_quiet` catches an over-broad repair.

## Relationship to the sibling stack

#319 (scheduler trajectory conformance) → #321 (schema status enum + CI-live schema
guard) → #322 (router reports unrecognized status). This PR is downstream and touches
disjoint files (`weaver/attention_bus.py`, `tests/test_attention_truthfulness.py`, this
evidence dir). No open PR touches `attention_bus`. Composes with the stack without
conflict.

## Next bounded task (NOT authorized yet — proposed)

Confirm the sibling stack reaches the sovereign: once #319/#321/#322/#323 are merged,
re-run `scripts/gate2`-style read-only observation on the hourly scheduler to confirm a
live unroutable frontier now produces a pushed `WEAVER_BLOCKED` event. This needs a real
hourly run (runtime evidence), so it is a separate pass and not part of this PR.

## Explicit non-goals for this PR

Trajectory `completion_rule` / nested `moves` data-loss concern (separate proposed
workstream); schema enum (#321); router routing (#322); `api/main.py`; CP10 allowlist;
`AGENTS.md` encoding.

## Standing constraint reminder

`NEVER MERGE` — human sovereign merges. No push to `main`. `api/main.py` untouched by
this workstream.
