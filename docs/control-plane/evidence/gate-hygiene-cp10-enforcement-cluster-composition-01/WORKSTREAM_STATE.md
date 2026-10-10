# WORKSTREAM_STATE — gate-hygiene / CP10 enforcement-cluster composition

## Workstream
GATE-10 (governed execution) · gate-hygiene **composition measurement**. Not a
gate advance; a cross-PR integration measurement.

## Objective
Prove that open CP10 PRs **#388** and **#390** compose without semantic collision
and independently of merge order, with zero failing/error node-set regression,
and leave a reusable harness that makes the next composition claim one command.

## Bounded scope
- Allowed paths: `scripts/compose_pr_pair.py`, `tests/test_compose_pr_pair.py`,
  this evidence directory.
- Explicit non-goals: repairing `deploy/` (#354 owns it); repairing baseline
  debt; merging; widening to other PR pairs; touching `api/main.py`.

## Base / inputs (observed, 2026-10-10)
- BASE_MAIN `f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8` (origin/main == local main).
- #388 head `63b3ce9b7c643f99ffe3d5a776a0e7fc99ea3408` (base f9ced6b6).
- #390 head `277585512ead857f4855b20594c52403edba7ff1` (base f9ced6b6).

## Result
- Merge overlap: 1 path (`AGENTS.md`, append-only prose).
- Forward tree == reverse tree == `a0bd8d1ac4fecaed5eb5f0f87428accb1b876ec3` → **order-independent**.
- Composed full-suite failing/error node set: **identical** to `main` (same 16
  nodes); fingerprint `bfcfe5920c3789302e80c72618e1f280e3577a8395320c89f174147cd11ec733`.
- main: 15F / 1838P / 36S / 1E. Composed: 15F / 1907P / 36S / 1E. `+69` passed
  == the two guards' new collected tests (118 → 187); no baseline node moved.
- `tests/test_m02a_ci_gate_integrity.py` on composed tree: 64P / 3F — the 3 are
  the pre-existing `deploy/` allowlist nodes owned by #354.
- `tests/test_ci_gate_trigger_coverage.py`: 120P. `tests/architecture`: 11P.
- Critically: #390's inserted `trigger_coverage.outcome` assertion does not break
  #388's truthfulness pin (`test_continue_on_error_gates_are_still_enforced_by_outcome` passes).

## Status
IMPLEMENTED → evidence PR opened for human review. **No merge.**
Authorization required: human merge only.

## Next bounded task (proposed, not executed)
The two `test_engineering_lab_api.py` nodes and the identity-spine node in the
baseline set are unowned drift on `main`; the Lab nodes touch an authority
surface (`api/lab_routes.py`) and are sovereign-only. Propose separately.
