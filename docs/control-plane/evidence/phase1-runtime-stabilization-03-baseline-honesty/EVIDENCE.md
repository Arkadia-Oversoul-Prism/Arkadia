# PHASE 1 · Runtime Stabilization — PASS 3: durable open-PR recon + baseline-honesty reconciliation

**Status:** OBSERVED — recon harness + classification record (repairs no product code)
**Date:** 2026-10-09
**Measured at:** `main` @ `f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8`
**Gate:** Phase 1 (runtime stabilization) · feeds GATE-10
**Predecessor:** `docs/control-plane/evidence/phase1-runtime-stabilization-01/EVIDENCE.md`
**Constraint:** evidence-only · human merge required · no push to `main`

## 1. Objective

Two bounded objectives, both carried from PASS 2's own PENDING list:

1. **Retire the ad-hoc open-PR inventory.** The queue is a live fact; reconstructing
   it from an agent's memory or a previous pass's prose makes continuity depend on
   recollection. The recon is now a durable, read-only harness.
2. **Reconstruct and classify the live baseline test-debt fingerprint**, and name
   the owner of each node — including whether the recorded fixture describes live
   debt.

This artifact repairs no product code, no test assertion, no workflow, no authority
path, and no mutation path.

## 2. Environment (required for reproduction)

```
PYTHONPATH=<repo>/archive/legacy_python \
  python -m pytest tests/ -q --continue-on-collection-errors -rEf
```

`pyyaml` and `archive/legacy_python` are required for full-suite reproducibility.
`-rEf` (not `-rf`) is required: `-rf` suppresses pytest's `ERROR` summary lines, so
a collection error would be invisible to a line-based extractor and the fingerprint
would describe a *subset* of the debt. `--continue-on-collection-errors` is required
or the session interrupts at the CE-01 collection error before running anything.

Recon:
```
python scripts/open_pr_inventory.py          # table
python scripts/open_pr_inventory.py --json   # machine output
```

## 3. Measured baseline — main vs branch

| | `main` @ `f9ced6b6` | branch `phase1/runtime-stabilization-03-baseline-honesty` |
|---|---|---|
| full suite | 15 failed, 1854 passed, 20 skipped, 1 error | 15 failed, 1861 passed, 20 skipped, 1 error |
| failing/error nodes | 16 | 16 |
| outcomes fingerprint | `bfcfe5920c3789302e80c72618e1f280e3577a8395320c89f174147cd11ec733` | `bfcfe5920c3789302e80c72618e1f280e3577a8395320c89f174147cd11ec733` |
| ids fingerprint | `ed5e4714df236078d6eb04cb43197c22403d2c244caa3e7bc7d71d45f6c0a833` | `ed5e4714df236078d6eb04cb43197c22403d2c244caa3e7bc7d71d45f6c0a833` |
| architecture suite | 11 passed | 11 passed |
| `test_m02a_ci_gate_integrity.py` | 3 failed / 61 passed | 3 failed / 61 passed (pre-existing; unaffected) |
| `test_open_pr_inventory.py` | (absent) | 7 passed |

**The failing/error node set is identical on both sides.** The `+7 passed` on the
branch is exactly the new guard file's 7 nodes (`1861 - 1854 = 7`). **Zero regression.**

The fingerprint pair `bfcfe592…` / `ed5e4714…` **independently reproduces** the value
recorded by PASS 2 (PR #385) at the same `main`. It is also corroborated by PR #375,
which records the same pair at ancestor `a47ea928`, with the node set unchanged over
`a47ea928..f9ced6b6`.

### 3.1 The recorded fixture is a strict subset, not stale debt

`tests/fixtures/baseline_node_set.txt` holds **10** nodes hashing to
`9a54f5b478d1135f27ab9e54d95706f03eae1ceb5d4c1f3ae075bffc4208ab38` /
`124bfdfd078fe878fe7c9de358ba271e977c4f7b73909b9d7d016b9ae9c1e87f`.
A live run on `main` reports **16** nodes. The difference is **not** stale — measured:

- **in fixture, not live: 0** — no entry is a node that now passes; the fixture's own
  `LIVE_RED_SHOULD_NOT_PASS_NODES` guard (8 nodes) is honoured, and all 10 recorded
  nodes still fail.
- **live, not in fixture: 6** — unrecorded live debt (below).

So the fixture is a well-formed **subset** of live debt, not a superseded list. Its
own guard pins it to canonical constants and does **not** measure live (no
`subprocess`, no `pytest.main`, no `--collect`), so a green guard is not evidence
that the recorded set describes live debt. Removing entries is out of scope here
(pinned by `LIVE_RED_SHOULD_NOT_PASS_NODES` and the canonical constants); recording
the six uncovered nodes' ownership is the honest action.

## 4. Node classification — all 16 owned

| # | node | class | owner |
|---|---|---|---|
| 1 | `test_m02a_ci_gate_integrity.py::test_allowlist_admits_every_tracked_top_level_prefix` | real (CP10 omission for `deploy/`) | PR **#354** |
| 2 | `test_m02a_ci_gate_integrity.py::test_allowlist_covers_every_tracked_surface` | real (CP10 omission for `deploy/`) | PR **#354** |
| 3 | `test_m02a_ci_gate_integrity.py::test_delegated_verdict_admits_every_tracked_surface` | real (CP10 omission for `deploy/`) | PR **#354** |
| 4 | `test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set` | test-side pin drift (`/api/lab/engineering/n-atlas/*`) | PR **#356** |
| 5 | `test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated` | test-side pin drift (`require_auth` → `require_lab_auth`) | PR **#356** |
| 6 | `test_steward_filter.py::test_allows_mythic_with_action` | test-side literal defect | PR **#365** |
| 7 | `test_steward_filter.py::test_blocks_identity_claims` | test-side literal defect | PR **#365** |
| 8 | `test_steward_filter.py::test_compress_to_choices` | test-side literal defect | PR **#365** |
| 9 | `test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver` | test-side pin (refactor `d6585687` moved `execute_patch` → `weaver/execution.py`) | PR **#357** |
| 10 | `test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical` | test-side pin (same refactor) | PR **#357** |
| 11 | `test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools` | test-side pin (same refactor) | PR **#357** |
| 12 | `test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route` | superseded pin (ADR: consumers do not resolve the base URL) | PR **#363** |
| 13 | `test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key` | superseded pin (`1f872f0` replaced the helper with `ACTIVE_THREAD_KEY`) | PR **#363** |
| 14 | `test_ais_capability_profile_onboarding.py::test_home_is_offer_led_and_keeps_arkadia_entry_points` | superseded pin (Landing copy `2b87e8ef`) | PR **#347** |
| 15 | `test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | recorded fixture node · no open PR | fixture (recorded) |
| 16 | `tests/test_autonomy.py` (collection error) | CE-01 `weaver.autonomy` module-vs-package collision | sovereign-reserved |

**No unowned debt.** The three CP10 nodes are the only *real* (non-test-side) failures;
the rest are test-side literal/pin defects or the sovereign-reserved CE-01 collision.

### 4.1 Re-pin or mask? — #363 adjudicated by measurement

A re-pin is only legitimate if the property it asserts still holds. Measured on `main`:

- `test_oracle_runtime_uses_the_shared_session_key` (#363) replaces its
  `arkanaSessionId` demand with `ACTIVE_THREAD_KEY` + `threadStorageKey`. On `main`,
  `ArkanaCommune.tsx` contains `ACTIVE_THREAD_KEY` **2×** and `threadStorageKey` **5×**,
  and the cited commit `1f872f0` ("wire Arkana Commune to first-class threads") is an
  ancestor of `main`. The re-pin is **backed by source**, not a mask.
- `test_node_entry_is_ais_signup_not_a_separate_diagnostic_route` (#363) replaces raw
  copy pins with `AIS_PROFILE_PATH`, and #363 moves `NodeEntry.tsx` from an inline
  `${API_BASE}/api/me/ais-profile` to the constant. Consistent with the canonical
  ADR that consumers do not resolve the base URL.

Both are legitimate test-side re-pins.

## 5. Delivered: `scripts/open_pr_inventory.py`

**Defect fixed (the documented PENDING item).** GitHub's *list* endpoint
(`GET /repos/{owner}/{repo}/pulls?state=open`) omits `mergeable` and
`mergeable_state`; only the *detail* endpoint exposes them. An inventory that reads
`pr["mergeable"]` off a list item raises `KeyError: 'mergeable'`. Verified live: the
list payload's key set contains neither field; the detail payload contains `mergeable`.

**Design.**
- Reads `mergeable` **only** from the detail endpoint; `mergeable`/`mergeable_state`
  are declared optional (`DETAIL_ONLY_KEYS`) and a missing value reports
  `LIST_ENDPOINT` rather than crashing.
- `mergeable: null` (GitHub still computing) reports `UNKNOWN`, not a false `conflict`.
- A detail-endpoint failure degrades that PR to `LIST_ENDPOINT` without aborting the
  inventory.
- Stdlib-only, read-only (only `GET`), never prints the token, importable module with
  a `--json` machine output.

**Guard:** `tests/test_open_pr_inventory.py` (7 tests) — no network. It proves the
harness tolerates a list record lacking `mergeable`, treats `null` as `UNKNOWN`,
distinguishes `clean`/`conflict`, merges detail into list records over a fake API,
degrades on a detail failure, and carries a **negative control** that feeds the naive
`pr["mergeable"]` read and asserts it raises `KeyError` — so the documented defect
cannot be silently unmasked by a future change to the list payload without a control
failing.

**Delivered recon (live, at `f9ced6b6`): 29 open PRs.** Their merge states are now
re-derivable by any operator, e.g. `#354 clean:unstable`, `#357 clean:unstable`,
`#361 clean:unstable`, `#363 clean:unstable`, `#365 clean:unstable`; `#338`/`#356`
are `conflict:dirty` (not composable).

## 6. Regression boundary

- Failing/error node **set** unchanged (`bfcfe592…`/`ed5e4714…` identical both sides).
- Architecture fitness: **11 passed** (both sides).
- CP10 mutation-boundary judge on this PR's diff: **PASS**, RC 0.
- New guard file: **7 passed**.

## 7. Authority boundary

Read-only recon + a stdlib script and its guard test. No merge, no push to `main`, no
authority/mutation path touched, no scope expansion. `api/main.py` untouched. **Human
merge required.**

## 8. Remaining uncertainty

- The six unrecorded live nodes (§3.1) are owed a reconciliation of
  `tests/fixtures/baseline_node_set.txt` against the live set — proposed work, not
  performed here (the fixture is pinned and its removal is a separate bounded task).
- The `engineering_lab_api.py` pins repair an authority surface (`api/lab_routes.py`);
  that remains sovereign-only (PR #356 owns the test-side pins).
- Gate 2 production parity remains `BLOCKED` on Vercel Deployment Protection; unchanged
  by this pass.
