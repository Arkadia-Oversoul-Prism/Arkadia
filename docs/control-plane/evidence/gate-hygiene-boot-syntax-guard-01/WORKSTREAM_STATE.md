# WORKSTREAM STATE — gate-hygiene

Pass: `gate-hygiene/boot-syntax-guard-01`
Reconstructed: 2026-10-05 · BASE_MAIN `4550531e1912e46d231a45f27ca801810def699d`

## Current state

| item | evidence |
|---|---|
| canonical clone | `main`, non-shallow, ancestry intact |
| BASE_MAIN | `4550531e…` (#290) |
| active workstream | gate-hygiene independent PR verification |
| open cluster | #293, #294, #295, #296 — all OPEN, none merged |
| this pass | boot-syntax boundary guard (new test, 5 tests) + cluster evidence |

## Cluster disposition (measured, not inherited)

| PR | verdict | basis |
|---|---|---|
| #293 | CONTRADICTED | `api/main.py` at head → `SyntaxError` line 1584; also 2894 lines (294 over budget) |
| #294 | merge-safe on authority dimension | workflow read-only + no untrusted interpolation; bridge is observational + idempotent |
| #295 | VERIFIED | CP10 non-admitted tracked paths 18 → 0 |
| #296 | VERIFIED | `api/main.py` 2805 → 2594; architecture 1F/10P → 11P |

Ordering constraint: #296's `api/arkana_signal_routes.py` is the correct home for
#293's signal logic. #293 must not merge as-is; its logic should be re-targeted
onto #296's post-extraction structure before any new signal route is added.

## Test / baseline fingerprint at this pass

- `tests/test_boot_syntax_boundary.py` — 5 passed
- `tests/architecture` — main 1F/10P; with #296 11P
- `python -m py_compile api/main.py` — OK
- full suite — not run this pass (no `fastapi`/`pydantic` in this environment)

## Next bounded task

Sovereign review of the cluster merge order, specifically:
1. #296 (restores the architecture budget) — highest leverage, verified.
2. #295 (restores the CP10 invariant on `main`) — verified.
3. #294 — safe on the authority dimension; companion boundary test unverified here.
4. #293 — do not merge; re-target onto post-#296 structure.

## Proposed, not executed

- Boot-syntax CI job (`.github/workflows/`) so the boundary is enforced on PRs.
  Needs a dependency decision and touches the CI boundary → separate bounded work.

## Gate-hygiene loop risk

Each verification pass adds a PR that the next pass must verify. This pass reduces
the risk by carrying a *continuous* guard (a test that runs in the suite) rather
than a one-shot prose verification: the boundary survives without another pass.
