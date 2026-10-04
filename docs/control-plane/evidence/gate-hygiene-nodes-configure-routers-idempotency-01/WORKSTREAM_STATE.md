# WORKSTREAM_STATE — gate-hygiene/nodes-configure-routers-idempotency-01 (SH-09)

**Observation timestamp**: 2026-10-04 (UTC), this run's environment
**Repository**: `Arkadia-Oversoul-Prism/Arkadia`

## Current state (derived from live evidence, not memory)

| item | value |
|---|---|
| `origin/main` | `1b7c089f237a1a8ea11791ab060525b0e36e2029` |
| local `HEAD` at start | same SHA, branch `main`, clean tree |
| branch point | `1b7c089f237a…` (merge of PR #261, SH-08) |
| working branch | `gate-hygiene/nodes-configure-routers-idempotency-01` |
| open PRs at reconstruction | **#262** (`3eefcb0`), **#263** (`46abb15`), both `MERGEABLE`/`UNSTABLE` |
| this pass | new bounded workstream `SH-09` |

## Completed

- **SH-08** (`test-hygiene/authority-boundary-control-case-identity-01`) — merged as PR #261
  (`1b7c089f237a`).
- **Live state reconstructed**: `origin/main == local HEAD == 1b7c089f237a`; clean tree;
  open PRs #262/#263 read directly via the API (not from prose).

## This pass — SH-09

**Defect**: `api.nodes.configure_routers()` mutated the module-level `api.nodes.router`
singleton on every call, so the seam test's second call double-included the injected
sub-routers and `app.openapi()` emitted **29** duplicate-operation-ID warnings
(5 `api/ais_profile.py` + 24 `api/lab_routes.py`). Order-dependent: seam→health = 29,
health→seam = 0. Route serving unaffected.

**Change**: re-entry guard in `api/nodes.py`; new regression test
`test_configure_routers_is_idempotent` in `tests/test_nodes_composition_seam.py`.

**Classification**: `VERIFIED` — implementation exists, required tests pass, negative
control proves the test detects the defect, protected architecture suite passes, and the
full-suite failure node set is byte-identical to base.

## Residual baseline failures (NOT touched — separate workstream)

All 9 reproduce on base `1b7c089` and on this head with an identical node set. Each needs
a product/architectural/sovereign decision; none is a safe test-side repair:

| node | classification |
|---|---|
| `test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | F-01 proxy-invalidation (test body documents it) |
| `test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route` | NodeEntry identity/route split (product) |
| `test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key` | SH-07 shared-session key (architectural) |
| `test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver` | SH-03 family — r1 `DERIVED`/spec drift |
| `test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical` | SH-03 family — `execute_patch` canonicalisation |
| `test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools` | r3 block-by-return vs block-by-raise (product) |
| `test_steward_filter.py::test_blocks_identity_claims` | SH-06 stem-match policy (product) |
| `test_steward_filter.py::test_allows_mythic_with_action` | SH-06 stem-match policy (product) |
| `test_steward_filter.py::test_compress_to_choices` | SH-06 stem-match policy (product) |
| `ERROR tests/test_autonomy.py` | pre-existing collection error (CE-01) |

## Next bounded task (deterministic next-action block)

- **Current state**: SH-09 implemented and verified on
  `gate-hygiene/nodes-configure-routers-idempotency-01`, PR open, awaiting sovereign merge.
- **Evidence**: `docs/control-plane/evidence/gate-hygiene-nodes-configure-routers-idempotency-01/EVIDENCE.md`.
- **Blockers**: none for SH-09. The 9 residual failures are blocked on product/sovereign
  decisions, not on repository work.
- **Authorized action**: open the PR; notify sovereign; take no further mutation on this
  branch after it is merge-ready.
- **Forbidden actions**: merge; push to `main`; force-push; begin the residual-failure
  workstream inside this PR; edit `api/main.py` or any governance/authority surface.
- **Completion condition**: PR contains this state file + EVIDENCE.md; the two directly
  affected suites and `tests/architecture` pass; full-suite node set equals base; a human
  merges.
