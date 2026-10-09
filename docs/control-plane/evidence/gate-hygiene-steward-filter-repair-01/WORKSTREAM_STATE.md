# WORKSTREAM STATE — gate-hygiene / steward-filter-repair-01

## Current state

| Field | Value |
|---|---|
| Status | IMPLEMENTED — verified in-repo; sovereign review required |
| Base main | `24a00f856a0286cbb464a4b585117dd57a2646fa` |
| Branch | `gate-hygiene/steward-filter-repair-01` |
| Changed paths | `weaver/filters/steward.py`, `tests/test_steward_filter.py` |
| Target tests | 12 passed (was 5 passed / 3 failed) |
| Full-suite delta | 21 → 18 failing nodes; zero introduced |
| Architecture | 11/11 |
| Mutation boundary | PASS |
| Next bounded task | none assigned — this workstream closes at merge |
| Owner | unowned before this pass; owned here |
| Authorization required | merge only |

## Next action block

- **Authorized:** human review and merge of this PR.
- **Forbidden:** merge by an agent, push to `main`, force-push, workflow or governance
  change, authority-path change, scope expansion into the other 18 baseline nodes.
- **Completion condition:** the three `tests/test_steward_filter.py` nodes are absent from
  the main full-suite failure set and the four new pins are present and passing.

## Ownership map (measured this pass, `main` @ `24a00f85`)

Every baseline failure node is accounted for. None is orphaned after this PR.

| Nodes | Owner |
|---|---|
| `test_steward_filter` ×3 | **this PR** |
| `test_ais_capability_profile_onboarding` ×1 | PR #347 |
| `test_ci_gate_trigger_coverage[n-atlas-developer-lab.yml]` ×1 | PR #355 |
| `test_engineering_lab_api` ×2 | PR #356 |
| `test_solspire_r1_*` ×2, `test_solspire_r3_*` ×1 | PR #357 |
| `test_agents_md_encoding_adjudication` ×4 | PR #361 |
| `test_identity_spine_w1` ×1, `test_m02_reasomate_truth` ×1 | PR #363 |
| `test_m02a_ci_gate_integrity` ×3 | PR #354 |
| `test_ais_w2_living_gate_grove_handoff` ×1 | unassigned — proposed workstream |
| `test_autonomy` (collection error) | CE-01, reserved to the sovereign |
