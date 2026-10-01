# gate-hygiene — Scheduler Bootstrap Test-Spec Repair — Evidence

**Gate:** gate-hygiene (test-spec integrity for the Engineering Lab scheduler)
**Authority:** Human sovereign (merge and authorization retained exclusively by the sovereign)
**BASE_MAIN:** `002b189dd95e41c9b4f4cca33d08b4121453d289`
**Branch:** `gate-hygiene/scheduler-bootstrap-testspec-repair-01`
**Status:** VERIFIED (tests + fingerprint delta); merge is human-only.

## 1. Objective (bounded)

Two tests in `tests/test_engineering_scheduler_bootstrap.py` were recorded pre-existing
main debt:

- `test_blocked_dependency_skips_move`
- `test_dry_run_evidence`

Both were **unfalsifiable rather than merely red**, because the trajectory they read had
moved underneath them. Every move in
`docs/control-plane/TRAJECTORY-ARKADIA-TRUTHFULNESS-01.yaml` is now `completed`
(M01–M09, M02A — all ten, verified in §3), so the router correctly returns
`NO_LEGAL_MOVE`. The tests asserted that *some* move is always selected, so they failed
for the right reason but for the wrong test: they conflated the **routing algorithm**
with the **live trajectory's completion state**.

This pass repairs the test specification only. The router is untouched.

### Provenance of the recorded debt

The two tests are recorded as pre-existing main debt in three places:

- `docs/phase1/CONTINUATION_LEDGER.md` lines **111–112** (exact failing set).
- `docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/BASELINE_TEST_DEBT_CLASSIFICATION.md`
  rows **38–39**, classified `DRIFT`.
- `docs/control-plane/evidence/m03-novanet/VERIFICATION.md` line 94.

### Refinement of that classification

The classification's stated root cause is *"the scheduler finds no legal move in the
checked-in trajectory — the trajectory and the scheduler have drifted apart."* That is
accurate as an observation but mislocates the defect. `NO_LEGAL_MOVE` is the **correct**
router behaviour once every move is `completed`; the workflow itself treats it as a clean
stop (`arkadia-engineering-scheduler.yml`: only `status == "FAILED"` exits non-zero, with
the comment *"NO_LEGAL_MOVE is clean stop (success)"*). The drift is therefore not between
trajectory and scheduler — it is between the **trajectory's completion state and the test
specification**. Classifying these as `DRIFT` in the router would have pointed a future
pass at `weaver/engineering_router.py`, which is not defective.

## 2. Change set

| File | Change |
|---|---|
| `tests/test_engineering_scheduler_bootstrap.py` | Routing-algorithm tests now supply a synthetic trajectory via a new `_synthetic_trajectory()` helper instead of depending on the live trajectory's completion state. Synthetic move IDs live in a `T*` namespace (`T01`, `T02`) so they cannot collide with the live `M*` completion index. `test_blocked_dependency_skips_move` lists the dependent **first** so the router must actively skip it on the unmet dependency rather than returning the prerequisite by list order. `test_dry_run_evidence` asserts the exact evidence line (`"Move: T01" in human.read_text().splitlines()`) instead of a loose substring. New `test_live_trajectory_dry_run_is_truthful` asserts the live dry-run's human artifact agrees with its own JSON status. |

`weaver/engineering_router.py` is **unmodified** — `git diff` against `HEAD` is empty.
`api/main.py` is untouched (2519 lines, budget 2600).

## 3. Live trajectory state (derived, not assumed)

```
trajectory status: authorized-for-review-gated-execution
max_active_moves: 1
review_gate: required_after_every_move
  M01 | completed | deps= []
  M02 | completed | deps= ['M01']
  M02A | completed | deps= ['M02']
  M03 | completed | deps= ['M02A']
  M04 | completed | deps= ['M01']
  M05 | completed | deps= ['M04']
  M06 | completed | deps= ['M05']
  M07 | completed | deps= []
  M08 | completed | deps= ['M07']
  M09 | completed | deps= ['M08']
```

## 4. Verification

```
pytest tests/test_engineering_scheduler_bootstrap.py -q  -> 13 passed in 0.15s
pytest tests/architecture -q                             -> 11 passed in 1.30s
python -m py_compile api/main.py                         -> OK, 2519 lines (budget 2600)
```

### Baseline fingerprint (BASE_MAIN `002b189`, change reverted)

```
20 failed, 1041 passed, 11 skipped, 2 errors in 117.39s
```

### Post-change fingerprint (this branch)

```
18 failed, 1044 passed, 11 skipped, 2 errors in 117.44s
```

### Delta — exact, not approximate

The two failures that disappear are precisely the two this pass targets. No other
fingerprint movement.

```
- FAILED tests/test_engineering_scheduler_bootstrap.py::test_blocked_dependency_skips_move
- FAILED tests/test_engineering_scheduler_bootstrap.py::test_dry_run_evidence
```

The remaining 18 failures and 2 collection errors are pre-existing main debt,
**fingerprint-unchanged**, and are explicitly not addressed here:

```
FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
FAILED tests/test_gate_serve_script.py::test_root_index_redirect_and_script_exists
FAILED tests/test_gate_status.py::test_gate_files_and_fetch_handling
FAILED tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
FAILED tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED tests/test_solspire_r2_github_mutation.py::test_legacy_commit_file_fails_closed_without_network_write
FAILED tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
FAILED tests/test_spiral_grove_activity_runtime.py::test_runtime_dispatches_all_eight_kinds_to_deterministic_renderers
FAILED tests/test_spiral_grove_activity_runtime.py::test_runtime_is_mounted_by_the_capability_chamber
FAILED tests/test_spiral_grove_activity_runtime.py::test_chamber_preserves_sg03_downstream_boundary
FAILED tests/test_spiral_grove_activity_runtime.py::test_spiral_grove_uses_the_nexus_canonical_header
FAILED tests/test_spiral_grove_registry.py::test_registry_rejects_prerequisite_cycle
FAILED tests/test_spiral_grove_registry.py::test_ais_catalog_supports_progressive_creative_workflow
FAILED tests/test_steward_filter.py::test_blocks_identity_claims
FAILED tests/test_steward_filter.py::test_allows_mythic_with_action
FAILED tests/test_steward_filter.py::test_compress_to_choices
ERROR  tests/test_autonomy.py            (pre-existing: load_autonomy_config)
ERROR  tests/test_render_codex.py        (pre-existing: arkadia_drive_sync)
```

Note: the full suite aborts at collection without
`--continue-on-collection-errors`; both runs used that flag so the comparison is
like-for-like.

## 5. Falsifiability (negative controls)

Each repaired assertion was proven to fail when the behaviour it guards is broken.
The router was mutated for the control, then restored to pristine (`git diff` empty).

| Control | Mutation | Result |
|---|---|---|
| NC-1 | Router ignores `depends_on` | `test_blocked_dependency_skips_move` fails at line 95 |
| NC-2 | Artifact stops naming the selected move | `test_dry_run_evidence` fails at line 133 |
| NC-3 | Human artifact misreports status | `test_live_trajectory_dry_run_is_truthful` fails at line 151 |

The tests are therefore not tautological: they can distinguish correct routing from
incorrect routing.

## 6. What this does and does not claim

- **Claims:** the two named tests now pass, they are falsifiable, the router is
  untouched, and the fingerprint delta is exactly those two tests.
- **Does not claim:** any change to routing behaviour, any fix to the other 18
  pre-existing failures, or any progress on a gated move. No move is advanced by this
  pass; the trajectory remains terminal with `review_gate: required_after_every_move`.

## 7. Remaining uncertainty

- The pre-existing 18 failures / 2 errors are unattributed in this pass beyond
  "fingerprint-unchanged". Attributing them is separate bounded work, not this gate.
- `vite_build` remains environment-blocked and was not attempted.
- This pass produces no runtime/deployment evidence and makes no production claim.

## 8. Authorization required

Sovereign review and merge. No self-merge, no force-push, no direct `main` mutation.
