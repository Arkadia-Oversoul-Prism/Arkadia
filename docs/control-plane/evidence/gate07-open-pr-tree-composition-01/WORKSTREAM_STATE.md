# WORKSTREAM STATE — gate07/open-pr-tree-composition-01

## Current state

- BASE_MAIN: `1775f3e1271842688f5026b59bfb0d393db6db04` (#318 merge)
- Branch: `gate07/open-pr-tree-composition-01` @ `1775f3e`
- PR: (this one)
- Classification: `VERIFIED` (repository-source composition measurement). No
  production-parity claim, no acceptance claim, no merge.

## Objective closed

No artifact on `main` or in any open PR stated whether the **full** open-PR tree composes.
PR #324 measured only the runtime chain `#319/#320/#321/#322/#323` and explicitly excluded
`#324/#325/#326/#327/#306`. This pass measures all ten heads against `BASE_MAIN`.

## Evidence

- Sequential merge of all ten heads: **9 clean, 1 collision**.
- Collision is `#320` ↔ `#327`, confined to `.gitignore` and
  `tests/test_repo_hygiene_gitignore.py`, both at the same append anchors.
- Conflict is **positional, not semantic**: disjoint artifacts, disjoint rules, disjoint tests.
  Union resolution is mechanically determined and drops no intent from either PR.
- Union-resolved tree: `tests/test_repo_hygiene_gitignore.py` → **10 passed**
  (all four new tests from both PRs collect and pass).
- `tests/architecture` on composed tree → **11 passed**, matching base.
- Full suite node-set: base **12 nodes** → composed **11 nodes**. Delta is exactly
  `test_arcana_weaver_fusion.py::test_arcana_weaver_fuses_project_canvas_weaver_and_arkana_runtime`
  (repaired by #326, its stated purpose). **Zero new failures.**
- Node-set sha256: base `5e782bf9…`, composed `f3e73647…`.

## Merge-order constraint (proposed to sovereign, not executed)

1. #321 after #319 (stacked base).
2. #320 and #327 both hit the same two anchors — the second to merge needs the union
   resolution. Safe, but not a conflict-free GitHub merge.
3. No constraint among #322/#323/#324/#325/#326/#306.

## Measured main defects (recorded, not repaired here)

| item | class | note |
|---|---|---|
| `tests/test_autonomy.py` collection error | pre-existing / reserved | CE-01 `weaver.autonomy` module-vs-package collision; sovereign-reserved |
| `tests/test_steward_filter.py` ×3 | pre-existing debt | present on base and composed identically |
| `tests/test_ais_capability_profile_onboarding.py` | pre-existing debt | present on base and composed identically |
| `tests/test_ais_w2_living_gate_grove_handoff.py` | pre-existing debt | present on base and composed identically |
| `tests/test_identity_spine_w1.py` | pre-existing debt | present on base and composed identically |
| `tests/test_m02_reasomate_truth.py` | pre-existing debt | present on base and composed identically |
| `tests/test_solspire_r1_governance_convergence.py` ×2 | pre-existing debt | present on base and composed identically |
| `tests/test_solspire_r3_execution_runtime.py` | pre-existing debt | present on base and composed identically |
| `api/main.py` line budget | convention | not re-measured here; this change does not touch it |

## Not claimed

- Production parity (Gate 2 stays open, `BLOCKED` on provider auth).
- Any PR's own CI green.
- Any acceptance or merge.

## Next bounded task (proposed)

Either (a) the sovereign resolves #320/#327 by union and merges the tree, or (b) a separate
bounded workstream is opened for the `test_steward_filter.py` debt if the sovereign elects to
treat it as its own workstream. No dependent move may be selected while G12-B is in progress
(`routing_invariants`).
