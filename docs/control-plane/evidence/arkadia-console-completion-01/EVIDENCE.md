# ARKADIA-CONSOLE-COMPLETION-01 — Voice authority-boundary guard

Workstream: Arkadia Console completion (review-gated execution)
Pass: 1
Base main: `74e8ea53a30213db8783e6733679d2f11903de0b`
Branch: `gate12/voice-authority-boundary-guard-01`
PR: #340

## Objective

Pin the load-bearing claim of unreviewed commit `74e8ea5` — that the Arkadia
Voice pipeline introduces **no second authority path** — as a test, against the
real canonical code path.

## Defect (evidence-backed)

`74e8ea5` ("feat(solspire): Arkadia Voice governed speech pipeline and operator
console", 2026-10-07) has **no associated pull request** and changed the
authority surface directly on `main`:

- extracted `authorize_proposal_sync` out of the SolSpire authorize route
  (`solspire/console_authority_router.py`, +14);
- added a `project_update` branch to the canonical
  `solspire/execution_runtime.py` (+32);
- added `solspire/voice_pipeline.py` (1257 lines) whose module docstring
  asserts *"no second executor, no second proposal ledger, no second
  authority"*.

None of the 118 tests shipped with that commit pin the property. Reading the new
test files shows the claim is untested: removing the canonical authority hop and
minting a local authorization leaves every existing voice test green.

## Scope (bounded)

- **Added:** `tests/test_voice_authority_boundary.py` (6 tests).
- **Not changed:** no production code, no `api/main.py`, no governed surface.

## What the guard proves

1. `authorize()` with no approval returns `state == "APPROVAL_REQUIRED"` and
   mints **zero** canonical authority rows.
2. The `HumanAuthorityEvent` + `Authorization` the approved path persists are the
   **canonical** rows (`ew_authority_events` / `ew_authorizations`), with
   `origin == "human"` and `action == "APPROVE_PROPOSAL"`.
3. The pipeline reaches authorization **through** `authorize_proposal_sync`
   (spied on the module the route uses).
4. `voice_pipeline` decides no proposal and writes no authority ledger itself.
5. **Negative control:** a fabricated local authority (appended outside the
   canonical path) persists zero canonical rows and the guard fires.

## Evidence / tests run

| check | result |
|---|---|
| `pytest tests/test_voice_authority_boundary.py` | 6 passed |
| voice suite | 124 passed (was 118) |
| `pytest tests/architecture -q` | 11 passed |
| `pytest tests/test_m02a_ci_gate_integrity.py -q` | 64 passed |
| `python -m py_compile api/main.py` | OK (2434 lines, budget 2600) |

## Baseline comparison — failing/error node SET (load-bearing invariant)

Full suite, `-rEf --continue-on-collection-errors`:

| tree | passed | failed | skipped | error | node-set sha256 |
|---|---|---|---|---|---|
| clean `main` (guard absent) | 1703 | 10 | 20 | 1 | `f3e7364703a07b08…` (11 nodes) |
| branch (guard present) | 1709 | 10 | 20 | 1 | `f3e7364703a07b08…` (11 nodes) |

Node sets byte-identical. `+6 passed` is exactly the new tests. Zero regression.

## Pre-existing debt explicitly attributed (not fixed here)

- `tests/test_autonomy.py` collection error — CE-01 `weaver.autonomy`
  module-vs-package collision, reserved to the sovereign.
- `tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools`
  — `ExecutionRuntime.execute()` raises `PermissionError` before creating a
  worker, while the test still expects `results[0]["code"] == "MUTATION_DISABLED"`.
  The raise is byte-identical at `74e8ea5` and its parent `17e626c` and is blamed
  to `144d601` ("Converge SolSpire and Weaver mutation boundaries"), which
  predates the voice commit. Baseline debt; `74e8ea5` only added the
  `project_update` branch. Not introduced by this branch, not repaired here.
- Remaining 7 failures are pre-existing and unchanged.

## Remaining uncertainty

- This is a **repository-source** claim. It does not assert production parity;
  Gate 2 production observation remains `BLOCKED` on Vercel Deployment
  Protection SSO.
- Non-vacuity was proven out-of-tree (fabricated local authority → 0 canonical
  rows, guard fires); that probe was removed and is not part of the PR.

## Authority boundary

Human sovereign review/merge only. No merge, no self-authorization, no
consequential follow-on work in this PR.
