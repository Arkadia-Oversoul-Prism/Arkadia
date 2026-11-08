# Lane 4 — run-trace vocabulary negative-control integrity

**Pass:** 2026-11-08 (hourly bounded execution, reconciliation edition)
**Lane:** 4 — Arkana + Weaver + Engineering Lab
**Branch:** `lane4/run-trace-vocabulary-control-integrity-01`
**Base `main`:** `f608ecd2b484b75cc39bf37c7a0657e22b1bb6d1` (PR #645 merge)
**Scope:** one test file. No console source, backend contract, registry, authority surface, or
other lane's file is touched.

## 0. Reconciliation state at the start of this pass

Measured live at `2026-11-08T15:06Z`, `gh api repos/.../pulls?state=open` -> **0** open PRs, and the
derived snapshot (`scripts/lane_state_refresh.py --base-main f608ecd2`) reports all four lanes
`doc_guard: idle`, `open_prs: []`, `unassigned_open_prs: []`. Reconciliation is exhausted, so this
pass opens the next bounded lane PR under `11 — LANE NEW-PR AUTHORIZATION` (N1 satisfied).

## 1. Defect — the control restates the detector instead of calling it

`tests/test_lab_run_trace_contract.py` measures the read-only ceiling of the run → work-event →
evidence trace surface. Two live assertions bind the projection's state vocabularies to the Lab
substrate's own vocabularies, using the module-level detector `projection_vocabulary`:

```python
# test_verified_evidence_state_is_a_real_result_state
claimed = projection_vocabulary(_read(TRACE_TS), "VERIFIED_EVIDENCE_STATES")
assert claimed <= states, ...

# test_every_projection_state_vocabulary_is_a_substrate_vocabulary
for name, allowed in (...):
    claimed = projection_vocabulary(source, name)
    assert claimed <= allowed, ...
```

Its negative control, however, never called that detector. It restated the set-difference inline:

```python
# test_negative_control_vocabulary_detector_sees_a_divergent_value  (pre-repair)
states = declared_result_states(_read(CONTRACTS))
assert "APPROVED" not in states
assert {"APPROVED"} - states == {"APPROVED"}      # <- its own copy, not the detector
```

The control could therefore never fail for any edit to the detector the live assertions actually
use: it exercised a second copy of the predicate.

## 2. Measured vacuity (AST-scoped mutation, pre-repair file)

Neutering the **live detector's own body** (`projection_vocabulary` replaced by `return set()`)
and running the live nodes and the control separately:

| file | node | result |
|---|---|---|
| pre-repair | `test_verified_evidence_state_is_a_real_result_state` + `test_every_projection_state_vocabulary_is_a_substrate_vocabulary` (live) | **2 failed** |
| pre-repair | `test_negative_control_vocabulary_detector_sees_a_divergent_value` (control) | **1 passed** |

`live=FAIL control=pass` is the vacuity: the control stayed green while the detector it exists to
prove was disarmed. File restored byte-identically after the mutation (asserted in the harness).

## 3. The repair

- The predicate moves once to a module-level detector the live assertions **and** the control both
  call: `_offending_vocabulary(source, name, allowed) -> set[str]` (the values a projection
  constant names that the substrate cannot record).
- Both live assertions now decide through it.
- The control feeds it the divergent shape and asserts it **is** reported, and additionally asserts
  the repaired input is **not** reported — so a detector that reported everything cannot pass
  either.
- Node count is unchanged at **22** — this binds a control, it adds none.

## 4. Discriminating A/B on the repaired file

Neutering the **shared helper's own body** (patched by its `ast` span, not by a whole-file
`str.replace`) and running the live nodes and the control separately:

| helper forced | live nodes | control |
|---|---|---|
| unmutated | 2 passed | 1 passed |
| `always-dirty` (`return projection_vocabulary(...)`) | **2 failed** | **1 failed** |
| `always-clean` (`return set()`) | 2 passed | **1 failed** |

The control now reddens for an edit to the detector it protects, in **both** polarities, which is
the binding the vacuous version could not provide. The file was restored byte-identically after
every mutation (asserted in the harness).

## 5. Verification

| check | command | result |
|---|---|---|
| target file | `python -m pytest tests/test_lab_run_trace_contract.py -q` | **22 passed** |
| node count | `--collect-only` | **22** (unchanged) |
| console-contract domain (derived, the gate's own inventory) | `python -m pytest $(python scripts/console_contract_domain.py) -q` | `10 failed, 1125 passed` |
| architecture fitness | `python -m pytest tests/architecture -q` | **11 passed** |
| full suite (once, baseline) | `python -m pytest tests/ -q -rEf --continue-on-collection-errors` | `21 failed, 3995 passed, 18 skipped, 1 error` |

The 10 domain failures are all `tests/test_mission_lifecycle_adapter_contract.py` — the documented
missing-`node_modules` TypeScript-toolchain baseline, identical to `main`. They are not attributed
to this change.

### Baseline fingerprint (measured at `main` `f608ecd2`)

```
ERROR tests/test_autonomy.py
FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
FAILED tests/test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated
FAILED tests/test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set
FAILED tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
FAILED tests/test_m01_persistence.py::test_deletion_propagates_to_durable_corpus
FAILED tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
FAILED tests/test_m05_files.py::test_update_file_supports_rename
FAILED tests/test_mission_lifecycle_adapter_contract.py::... (9 nodes)
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
FAILED tests/test_static_ingestion_idempotency.py::test_open_loop_content_is_checksum_stable_through_a_vault_round_trip
```

Per the contract, this pass runs the full suite **once** (baseline). The change is attributed by
the failing/error node **set** and by `--collect-only` node count, not by a second full run. The
target file contributes **zero** nodes to the baseline failing set on either side.

## 6. Gate execution

`tests/test_lab_run_trace_contract.py` **is** in the derived console-contract domain
(`python scripts/console_contract_domain.py` lists it), and `.github/workflows/prism-console-contract.yml`
executes that derived domain — so this guard is judged by a live gate, and the repair does not
depend on wiring it in.

## 7. Boundaries preserved

No console source, backend route, registry entry, authority surface, or other lane's file is
touched. The change strengthens a guard; it does not alter the surface it guards, and it neither
merges, deploys, nor claims acceptance. Merge, production deployment and acceptance remain
human-only.

## 8. Next action

Lane 4's next bounded PR opens only after this one merges. The same defect class
(#631/#634/#636/#637 Lane 1, #635/#640 Lane 2, #638 Lane 3, #639/#641/#642/#643/#645 Lane 4) was
scanned across the whole suite in this pass; the remaining candidates are recorded in §9.

## 9. Recorded, not repaired (separate bounded workstreams)

The AST scan flagged further controls whose helper-call sets do not intersect the live assertions'
in the same file. They were **not** repaired here — one bounded slice per lane PR:

- `tests/test_attention_truthfulness.py::test_negative_control_status_only_rule_would_miss_the_defect`
- `tests/test_natlas_selfhost_contract.py::test_negative_control_detector_flags_a_missing_route`
- `tests/test_prism_solspire_control_plane.py::test_negative_control_detects_the_wrong_advertised_prefix`
- `tests/test_console_facts_value_overflow_contract.py::test_negative_controls_anchor_on_the_live_source`

Each needs its own measurement before classification; a non-intersecting call set is a *candidate*
signal, not proof of vacuity.
