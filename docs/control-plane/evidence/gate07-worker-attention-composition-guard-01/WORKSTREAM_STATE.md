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
3. **CI wiring — CLOSED in pass 2 of this PR.** Measured at pass 1:
   `grep -rn "test_attention_truthfulness\|test_worker_attention_composition" .github/workflows/`
   returned nothing, while `test_engineering_router_status_truthfulness.py` is wired into
   `weaver-mvp2-validation.yml`. A guard that runs nowhere is decoration (the
   `tests/architecture` lesson). The seam and attention half-guards are now in that
   workflow's `push` **and** `pull_request` path filters and executed by a
   `Worker→attention composition seam guard` step, pinned by
   `test_guard_is_selected_and_executed_by_a_workflow` with three measured negative
   controls. See `EVIDENCE.md` §9. The workflow that already owns the router half was
   chosen over `arkadia-engineering-scheduler.yml` so all three halves are judged in one
   place; no new authority or mutation path is created.

## Deterministic next-action block

- **Current state:** seam pinned, defect recorded, CI wiring closed **and observed in CI**,
  PR #329 open and review-gated at head `a8692c1` (run `37444445640`, step 9
  `Worker→attention composition seam guard` -> success, `14 passed, 1 xfailed`).
- **Evidence:** `EVIDENCE.md` (this directory), §6 fingerprints, §9 CI wiring, §9.1 CI
  runtime observation.
- **Blockers:** none for this pass. The repair (task 1) is blocked on authorization.
- **Authorized action:** sovereign review of PR #329.
- **Forbidden actions:** merge, auto-merge, repair the router contract inside this PR,
  widen scope to unrelated baseline debt.
- **Completion condition:** sovereign merges PR #329, or requests changes.

## Pass 4 - verification and evidence correction (supersedes the block above)

- **Head moved:** `e96778b` -> `2c5ef4f` (evidence-only commit; no source, test, or
  workflow change). The block above cites `a8692c1`, which is superseded.
- **Evidence correction:** `EVIDENCE.md` section 10 named `a086825` as the debt document's
  last clean revision; it is itself corrupt. The last clean revision is `d848f3d6e`, and
  the counts re-derived against it are recorded append-only in section 11. Section 10 is
  left in place so the superseded measurement stays inspectable.
- **Decisive control:** a single-CP1252 repair of line 0 round-trips yet still emits
  `U+201A U+00C4 U+00EE`, so the single-codec criterion is necessary but not sufficient.
  This is why the audit is stated as a chain over an oracle, not a codec candidate list.
- **Baseline (this pass), `main` @ `4587890`, `-rEf`:** 10 failed / 1590 passed / 20
  skipped / 1 xfailed / 1 collection error in 148.41s; node-set sha256
  `fdc792071b6b4af45ea91782de08992605a04b40ed62ce9d00b771cdf2843cb1` (11 nodes). The
  execution contract's `804 / 54 / 12 / 2` fingerprint no longer binds to current `main`.
- **Guard re-confirmed** as a real seam guard: drives `EngineeringWorker.run()`, negative
  control removes `_record_attention` and asserts the composed event is absent, strict
  xfail records the idle-hour false-alert defect.

### Deterministic next-action block (pass 4)

- **Current state:** PR #329 at head `2c5ef4f`, `MERGEABLE`/`UNSTABLE`; CI
  `mvp2-validation` pass, `Full-history secret scan` pass, `Vercel Preview Comments` pass.
- **Evidence:** `EVIDENCE.md` section 6 fingerprints, section 9 CI wiring, section 9.1 CI
  runtime observation, section 11 encoding correction; PR #329 comment (pass-4 glance).
- **Blockers:** none for this pass. The router `NO_LEGAL_MOVE` blockers-contract repair is
  still blocked on authorization and remains a separate bounded workstream.
- **Authorized action:** sovereign review and merge of PR #329.
- **Forbidden actions:** merge, auto-merge, repair the router contract inside this PR,
  widen scope to baseline debt or the two encoding documents section 10 scopes out.
- **Completion condition:** sovereign merges PR #329, or requests changes.

