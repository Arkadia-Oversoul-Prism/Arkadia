# WORKSTREAM STATE — gate-hygiene / GATE-07

Pass: `gate07/worker-attention-composition-guard-01`
Reconstructed: 2026-10-06 · BASE_MAIN `4587890efe0a4090aa9ffbf55413bcb4fe01e2bd`
PR: #329 (base `main`, review-gated, no auto-merge)

## Current state

| item | evidence |
|---|---|
| canonical clone | `main`, `origin/main` = `4587890` (#327) |
| active workstream | GATE-07 — durable Weaver loop / hourly bounded execution |
| this pass | pin the worker→attention composition seam + record the composed defect |
| PR | #329, OPEN, review-gated, `auto_merge = null` |
| depends on | PR #322 (router status truthfulness), PR #323 (attention truthfulness) |
| frontier | a composed clean `NO_LEGAL_MOVE` reaches attention as a pushed HIGH block |

## Relationship to PR #322 / #323

#322 pins the router half (a defect is *named*). #323 pins the attention half
(`NO_LEGAL_MOVE`+blockers *classifies* as a pushed block). Neither pins the worker seam
between them — the layer the scheduler actually invokes. This pass pins that seam and
records the defect the composition exposes.

## Defect and state (measured)

| | value |
|---|---|
| `select_next_move` blockers on clean completion | `['no legal pending move (all complete or dependencies unresolved)']` |
| `_engineering_result_is_blocked` predicate | always true for `NO_LEGAL_MOVE` |
| composed clean completion | `WEAVER_BLOCKED` / `HIGH` / push (false alert) |
| scheduler intent for `NO_LEGAL_MOVE` | clean stop / success (only `FAILED` exits 1) |
| guard outcome | 4 passed, 1 strict xfail (the defect) |
| regression | zero failing/error node-set delta vs. `main` |

## Next bounded task (proposed, not executed)

1. **Repair the router `NO_LEGAL_MOVE` blockers contract** — distinguish "nothing to
   route, nothing wrong" (no blocker) from "nothing to route *because* something is
   wrong" (blocker present), then drop the strict xfail. This changes a contract consumed
   by `test_engineering_router_status_truthfulness.py` and
   `test_attention_truthfulness.py`, so it needs its own regression boundary and
   sovereign authorization. Do **not** fold it into this pass.
2. **No other seam** — the worker→attention path is the last unpinned layer of the
   hourly stop identified in this workstream.
3. **The seam guard runs in no CI workflow** — measured at this pass:
   `grep -rn "test_attention_truthfulness\|test_worker_attention_composition" .github/workflows/`
   returns nothing, while `test_engineering_router_status_truthfulness.py` is wired into
   `weaver-mvp2-validation.yml` (paths + run step). `arkadia-engineering-scheduler.yml`'s
   `pull_request` path filter lists neither the attention half-guard nor this seam guard,
   and its job runs only the two conformance tests. A guard that runs nowhere is
   decoration (the `tests/architecture` lesson). Wiring it means editing a CI workflow —
   a distinct surface — so it is **proposed**, not executed here. Decide which workflow
   owns the seam (scheduler vs. weaver-mvp2-validation) before wiring.

## Deterministic next-action block

- **Current state:** seam pinned, defect recorded, PR #329 open and review-gated.
- **Evidence:** `EVIDENCE.md` (this directory); fingerprints in §6.
- **Blockers:** none for this pass. The repair (task 1) is blocked on authorization.
- **Authorized action:** sovereign review of PR #329.
- **Forbidden actions:** merge, auto-merge, repair the router contract inside this PR,
  widen scope to unrelated baseline debt.
- **Completion condition:** sovereign merges PR #329, or requests changes.
