# GATE-HYGIENE — CI gate trigger coverage boundary (01)

## Status

IMPLEMENTED / VERIFIED (repository-source). Awaiting sovereign merge.
No production or deployment claim is made here.

## BASE

- Repository: `Arkadia-Oversoul-Prism/Arkadia`
- BASE_MAIN: `4550531e1912e46d231a45f27ca801810def699d`
  ("Research: define WorkEvent review, completion, and production acceptance (#290)")
- Observed: 2026-10-05 (Weaver hourly pass)

## Defect (measured, not inferred)

`tests/test_m02a_ci_gate_integrity.py` already pins the lesson that a CI gate must
be selected by the surfaces it judges — its own contract surfaces must appear in
the workflow trigger filter, and the `push` / `pull_request` filters must be
identical. That lesson was never generalised beyond the CP10 mutation boundary.

`provider-routing.yml` ("Provider Routing Verification") runs
`python -m pytest tests/architecture -q` on every pull request, but its
`pull_request.paths` filter names neither `tests/architecture/**` (the assertions
it executes) nor its own workflow file. Measured consequences:

1. A change to `tests/architecture/**` does not select the workflow that runs the
   architecture suite. The gate that judges the assertions can itself be changed
   unjudged.
2. A change to `.github/workflows/provider-routing.yml` does not select the
   workflow. Its gate logic can be rewritten unjudged.

Live corroboration: on PR #294 the job reported the architecture failure
`api/main.py has grown to 2805 lines (budget: 2600)`. The same failure is present
on `main` @ `4550531` (architecture `1F/10P`) and is reachable by a change that
never selects this workflow — the gate is real but not reliably triggered.

## Change

- `.github/workflows/provider-routing.yml` — add `tests/architecture/**` and
  `.github/workflows/provider-routing.yml` to `pull_request.paths`.
- `tests/test_ci_gate_trigger_coverage.py` (new) — states the invariant once,
  generically, over **every** workflow that runs pytest:
  1. a workflow that runs pytest on `pull_request` must be selected by its own file;
  2. `push` and `pull_request` path filters must be identical when both are declared;
  3. a workflow that runs `tests/architecture` must be selected by `tests/architecture/**`.
  The path selector and the pytest detector each carry a negative control, so a
  rewrite of a workflow cannot silently disarm the boundary.

## Scope boundary (deliberately not widened)

The architecture suite also asserts a line budget for `api/main.py`, so `api/**`
arguably belongs in the filter of any workflow that runs the suite. It is **not**
added here: `provider-routing.yml` also runs `pytest tests/ -q`, which carries
pre-existing `main` failures, so adding `api/**` would turn every API pull request
red with debt it did not introduce — a blast-radius expansion, not a repair. The
`api/**` widening is recorded as proposed work; a gate must stop being
baseline-red before its trigger is widened.

## Evidence

Environment: local clone, `main` @ `4550531`, Python 3, `pytest` available.

| Check | Command | Result |
|---|---|---|
| New boundary test | `pytest tests/test_ci_gate_trigger_coverage.py -q` | **33 passed** |
| Detector negative control | selector against the pre-fix filter | pre-fix: own-file `False`, arch-tests `False`; post-fix: `True`, `True` |
| Architecture fitness | `pytest tests/architecture -q` | `1F/10P` — identical to `main`; the single failure is the pre-existing line-budget debt |
| Full suite | `pytest tests/ -q -rEf --continue-on-collection-errors` | `19F/1444P/22S/1E`, 20 nodes |
| Regression delta | `scripts/baseline_fingerprint.py` | outcomes `d7fe13dd60c33af8628d37fa6daad045f7bcf47831bd06f2787316e89e7a3807` — **identical to the recorded main baseline**; `+33 passed` = exactly the new file |
| MVP2 boundary set | the workflow's exact 7-file invocation | **63 passed** (main parity) |
| CP10 gate integrity | `pytest tests/test_m02a_ci_gate_integrity.py -q` | `3F/52P` — identical to `main`; all three are the pre-existing `research/**` allowlist omission from #290 |
| Workflow injection boundary | `pytest tests/test_workflow_injection_boundary.py -q` | **22 passed** |

CP10 admits both changed paths (`--judge` → PASS), so this PR cannot redden the
mutation boundary on merge.

### Independent verification of PR #294 (read-only, worktree)

Checked out `origin/pull/294/head` in a throwaway worktree and ran the boundary
suite directly. Result: **4 failed, 6 passed**, failing exactly

- `test_enterprise_verification_creates_no_review_record`
- `test_enterprise_chain_has_no_review_concept`
- `test_no_review_record_type_or_table_exists_anywhere_in_the_backend`
- `test_verification_exists_without_any_review`

`main` @ `4550531` and this branch both pass all 10. This independently reproduces
the reported regression on the PR head (not merely on an ancestor). #294 must not
be merged until the review-record boundary is reconciled.

## Known debt left untouched

- `api/main.py` is 2805 lines against a 2600 budget → architecture `1F/10P` on
  `main`. Decomposition is carried by PR #296; not re-litigated here.
- CP10 allowlist omits `research/**` (from #290) → 3 CP10 fitness failures on
  `main`. A bounded allowlist workstream, not fixed here.

## CI verification (post-push, observed)

Branch `gate-hygiene/ci-gate-trigger-coverage-01`, head
`2e3661a1b4141809a9ad120ff19aaf68e81dac5f`, PR #300. Runs observed 2026-10-05.

| Check-run | Result |
|---|---|
| `provider-routing` | **failure** |
| `Full-history secret scan` | success |

The `provider-routing` job failed at its **`Relevant architecture regression`** step
(`Broader test suite` skipped). The single failure is
`tests/architecture/test_layer_boundaries.py::test_api_main_line_count_within_budget`
— `api/main.py has grown to 2805 lines (budget: 2600)`.

**This is pre-existing debt, not a regression from this branch.** Re-measured directly:
`pytest tests/architecture -q -rEf` yields `1 failed, 10 passed` with the *identical*
failing node on both `main` @ `4550531` and this branch. No file touched by this PR
affects `api/main.py` (`git diff origin/main` = 4 paths, none of them `api/main.py`).

Note the trigger asymmetry this branch repairs is visible in the failure itself: the
job runs the architecture suite but its pre-fix filter named neither
`tests/architecture/**` nor its own file. **The fix works** — a change to
`tests/architecture/**` now selects this gate.

Consequence recorded for the sovereign: this branch cannot be green while `main` is
baseline-red on the same node. Green requires PR #296 (`api/main.py` decomposition) to
land first, or an explicit decision to accept the gate as red-by-inheritance. The
failure is **unchanged**, not introduced.

## Next authorized action

Sovereign review and merge of this branch. No further work begins inside this PR.
