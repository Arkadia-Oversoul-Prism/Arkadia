# WORKSTREAM STATE — gate-hygiene

Pass: `gate-hygiene/api-main-budget-ceo-chat-extraction-01`
Reconstructed: 2026-10-05 · BASE_MAIN `44f5fe38d555e36cdd895114277013f691ba57ed`

## Current state

| item | evidence |
|---|---|
| canonical clone | `main`, fetch `--all --prune` clean, ancestry intact |
| BASE_MAIN | `44f5fe3…` (#303 merge) |
| active workstream | api/main.py 2600-line architecture budget |
| defect | `main` @ `44f5fe3` → `api/main.py` **2602** lines; architecture **10/11** |
| this pass | move Phase C CEO chat → `api/ceo_chat_routes.py`; main.py **2427** |
| result | **19F/1483P**, node-set delta **-1 (budget only), 0 new**; architecture **11P** |

## Open PR queue at reconstruction (live)

| PR | title | state |
|---|---|---|
| #307 | fix(console): establish idempotent capture reconciliation | OPEN, draft |
| #306 | test(prism): conformance harness for 9-cell branching and contradiction | OPEN |

Neither touches `api/main.py`.

## Stale branches (no open PR)

- `architecture/main-line-budget-restoration-01` — `api/main.py` 2594; based on older `main`
- `gate07/main-py-line-budget-restore` — `api/main.py` 2512; based on older `main`

Both carry large unrelated diffs. Superseded by this minimal pass.

## Baseline fingerprint at this pass

Measured, not inherited. `PYTHONPATH=<repo>/archive/legacy_python`,
`pytest tests/ -q -rEf --continue-on-collection-errors`.

- `main` @ `44f5fe3`: **20 failed / 1482 passed / 20 skipped / 1 error** (includes budget test)
- branch: **19 failed / 1483 passed / 20 skipped / 1 error**
- node-set delta: the budget test only; no new failure, no new error

The contract's cited baseline (`6038989 · 804p/54f · 9/10`) does not reproduce; this
measurement supersedes it for this pass.

## Next bounded task (authorized envelope)

Sovereign merge of this PR restores architecture to 11/11. Separate, non-consequential
candidates only (do not start inside this PR):

- Delete/close the two stale budget branches (sovereign action).
- Env/order-dependent baseline nodes (`test_steward_filter`,
  `test_verification_review_boundary`) remain their own debt workstream — not touched here.

## Authorization

ACTION: sovereign review required. No merge performed by this agent.
