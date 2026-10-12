# Prism Next-Wave Composition Reconciliation — EVIDENCE

**Scope:** composition/integration analysis of the Prism next-wave parallel UI workstreams.
**Authority:** inspection, implementation, test only. No merge, deployment, prevalence, or
acceptance is performed or claimed.
**Base revision measured:** `origin/main` = `49809f45274f2f81b24e01fefdfb3009e8717495`
(merge of PR #490, `gate10/natlas-selfhost-wiring-execution-01`).
**Measured:** 2026-10-12.

## 1. Live PR inventory (re-derived from the GitHub API this pass)

| PR | State | Draft | Mergeability | Head | Lane |
|---|---|---|---|---|---|
| #492 | OPEN | yes | MERGEABLE/CLEAN | `aab097aa` | Lane 2 — Opportunity Radar pipeline strip + per-entry ADVANCE |
| #493 | OPEN | yes | MERGEABLE/CLEAN | `d3e978d1` | Lane 4 — read-only Lab automation grammar projection |
| #496 | OPEN | yes | MERGEABLE/CLEAN | `967f30d9` | Control-plane workstream/portfolio evidence refresh |
| #497 | OPEN | yes | MERGEABLE/CLEAN | `cc1e8f7c` | Lane 1 — legacy `/nexus` sub-route deep links |
| #498 | OPEN | yes | MERGEABLE/CLEAN | `e7086afd` | Lane 3 — truthful older-event paging |
| #501 | OPEN | yes | MERGEABLE/CLEAN | `31d66332` | Lane 4 — mount the canonical work-loop projection |
| #502 | OPEN | yes | MERGEABLE/**UNSTABLE** | `ef82cb9e` | Control-plane — "Engineering Acceptance Authority" |
| #503 | OPEN | yes | MERGEABLE/**UNSTABLE** | `37e89b4a` | Test — EAA exact-base regression baseline |

Heads are observations, not pins. Each lane branch and PR was independently inspected.

**Boundary note (recorded, not executed):** #502/#503 introduce a new "Engineering Acceptance
Authority". Authority-model changes are a HARD STOP surface reserved to the human sovereign
(`AUTHORITY_MODEL`, `IDENTITY_BOUNDARY`, `CREATE_SECOND_AUTHORITY_PATH`). They are also the only
two PRs reading `MERGEABLE/UNSTABLE`. They were not modified, merged, or reconciled here.

## 2. Measured baseline (this environment, `main` @ `49809f45`)

Command:

```
python -m pytest tests/ -q -rEf --continue-on-collection-errors
```

Result: **12 failed, 2954 passed, 22 skipped, 1 error in 208.91s**.

Failing/error node set (13 nodes), sha256
`c1e7243980f343402809d910d233a5a64f578f47203a62de0eeaf7b8f29c7040`:

```
ERROR  tests/test_autonomy.py
FAILED tests/test_agents_md_encoding_adjudication.py::test_cli_summarises_the_oracle_without_crashing
FAILED tests/test_agents_md_encoding_adjudication.py::test_corruption_origin_is_re_derivable
FAILED tests/test_agents_md_encoding_adjudication.py::test_exit_code_does_not_call_a_divergent_clean_file_verified
FAILED tests/test_agents_md_encoding_adjudication.py::test_live_file_verdict_matches_its_state
FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
FAILED tests/test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set
FAILED tests/test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated
FAILED tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
FAILED tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
```

All 13 are known, documented pre-existing debt (AGENTS.md: the four
`test_agents_md_encoding_adjudication` nodes on a shallow clone; the two
`test_engineering_lab_api` pins; the CE-01 `test_autonomy` module/package collision; and the
remaining governance/runtime pins). **None is attributable to the next-wave lane PRs.**

`python -m pytest tests/architecture -q` → 11 passed (expected 11).

## 3. Cross-PR composition hazard — Lane 4 (#493 ⨯ #501)

This is the load-bearing finding: **it is a composition hazard no single PR can observe.**

### 3.1 Textual conflict is real and measured

Both #493 (`d3e978d1`) and #501 (`31d66332`) are branched from the same merge-base
`49809f45` and both modify `web/arkadia_console/src/pages/EngineeringLabPage.tsx` — a file owned
exclusively by **Lane 4** in `SHARED-CONTRACTS.md` §1, so no other lane could have caused or
detected the collision.

Reproduced in a detached worktree: applying #501's patch onto #493's head yields a **`UU`**
(unmerged) state on `EngineeringLabPage.tsx`. The contested region is the module import block —
#493 adds `LabAutomationGrammar`, #501 adds `ExecutionLoop` plus the `readLoopStages` helper.
Both introduced *new* imports at the same location; git cannot silently merge them, and each
branch is individually green against its own tree.

### 3.2 Union resolution is semantically coherent (measured)

Because the two PRs add *independent* surfaces, the correct resolution is a union, not a choice.
Resolved in the worktree as: both imports retained, `readLoopStages` retained, and **both**
components rendered (the automation-grammar projection and the canonical work-loop projection).

Verification on the composed, reconciled tree:

```
python -m pytest tests/test_prism_w4_canonical_loop_mount.py \
                 tests/test_prism_w4_automation_grammar.py \
                 tests/test_lab_automation_grammar_contract.py -q -rEf
→ 61 passed in 2.79s
```

Both render sites coexist (`<ExecutionLoop` and `<LabAutomationGrammar>`), and the negative
controls each PR carries still hold:

- #501's contract asserts the loop projection reaches no mutating Lab path and does not import
  `apiRequest` / `useHydration` — still true after the union;
- #493's grammar-contract test asserts the automation-grammar projection is read-only — still
  true after the union.

No unresolved conflict markers remain.

### 3.3 Disposition

| Fact | Value |
|---|---|
| Conflicting PRs | #493 (`d3e978d1`) and #501 (`31d66332`), both Lane 4 |
| Merge-base | `49809f45` (current `main`) |
| Conflicted file | `web/arkadia_console/src/pages/EngineeringLabPage.tsx` |
| Conflict type | textual (`UU`); adjacent new import blocks |
| Correct resolution | union (both surfaces are independent) |
| Composed-tree targeted tests | 61 passed |
| Who can resolve it | the Lane 4 owner, in a lane-4 branch — **not** this analysis branch |

**This analysis does not resolve the conflict in the lane.** Per `SHARED-CONTRACTS.md`
(`do not edit a file another lane owns`; integration goes through the owning workstream), the
union belongs on Lane 4's branch, not on a cross-lane analysis branch. This document provides
the measured evidence, the exact conflict, and the verified resolution so the Lane 4 owner can
apply it as one bounded change. Reported as a **proposed, classified, bounded** item.

## 4. Lane 1 (#497) verified independently

`feat/prism-next9-01-nexus-alias` / PR #497, head `cc1e8f7c`, draft, MERGEABLE/CLEAN.

Changed files: `web/arkadia_console/src/lib/router.ts`,
`tests/test_console_shell_nav_contract.py`,
`docs/control-plane/evidence/prism-next9-01-nexus-alias/EVIDENCE.md`.

- `router.ts` extends `resolvePath` so an alias reconciles the legacy inbound *namespace*, not
  only its root — `/nexus/ims`, `/nexus/grove`, `/nexus/larder`, `/nexus/distribution` now
  resolve to NovaNet's sectioned surface instead of being discarded to `home`. The change is
  source-grounded in the archived hub (`archive/frontend/arkadia-prism/web/public_prism/src/App.tsx:71-72`)
  and claims nothing about backend serviceability of a legacy sub-view.
- Targeted proof: `python -m pytest tests/test_console_shell_nav_contract.py -q` → **32 passed**.
- Ownership: all three paths are Lane-1 owned. No cross-lane overlap. **No composition hazard
  observed** between #497 and #492/#498/#501 (disjoint file sets).

## 5. Gate wiring observation (recorded, not repaired)

`.github/workflows/prism-console-contract.yml` executes the console contract, and its domain is
*derived at call time* by `scripts/console_contract_domain.py` (`derive_domain`, `DOMAIN_NEEDLES`,
`SURFACES = web/arkadia_console/**`, `api/frontend_routes.py`). A previous pass
(`gate10-prism-console-contract-domain-completion-01`, PR #439) established that a
content-derived domain grows silently and that a hand-maintained list in the workflow can drift.
Two lane PRs here add new console-contract test files
(`tests/test_prism_w4_canonical_loop_mount.py`, the lane-2/lane-3 contract tests); whether each
is inside the gate's derived domain should be re-checked by the lane that merges them. Recorded
as an observation; not repaired under this analysis scope.

## 6. Classification

| Item | Classification |
|---|---|
| #493 ⨯ #501 textual conflict | **CONTRADICTED** (each PR green alone; the pair cannot both merge as-is) |
| Union resolution | **VERIFIED** in an isolated composed worktree (61 passed) |
| #497 (Lane 1) | **VERIFIED** in isolation (32 passed); no overlap |
| #492 / #496 / #498 | inspected; no hazard observed against the other lanes |
| #502 / #503 (EAA) | **BLOCKED** for this pass (authority-model surface, sovereign-only) |
| Baseline fingerprint | recorded; unchanged by any lane PR |
| Merge / deploy / acceptance | **NOT CLAIMED** (outside authority) |

## 7. Next authorized action

1. **Lane 4 owner:** apply the union resolution to `EngineeringLabPage.tsx` on one Lane-4
   branch (preferring the older PR #493 as the base and composing #501 in), then close the
   superseded PR so both surfaces land in one bounded change. Do not merge both unreconciled.
2. **Lane 4 owner:** confirm both new contract tests are selected by the console-contract gate.
3. **Human sovereign:** decide the #493/#501 order and whether #502/#503 (EAA authority change)
   proceeds; that decision is outside agent authority.
