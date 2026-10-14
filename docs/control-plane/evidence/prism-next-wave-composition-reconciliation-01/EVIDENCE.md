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

## 8. Re-measurement at live heads — §3's "union pending" is superseded (2026-10-13)

§3–§6 above were measured against the *merge-base* heads `d3e978d1` (#493) and `31d66332` (#501).
Both branches have since advanced. Re-derived from the live API at base `origin/main` `49809f45`:

| PR | Live head | Draft | Mergeability |
|---|---|---|---|
| #492 | `2fe22cdf` | yes | MERGEABLE/CLEAN |
| #493 | **`255d665f`** | yes | MERGEABLE/CLEAN |
| #497 | `cc1e8f7c` | yes | MERGEABLE/CLEAN |
| #498 | `e7086afd` | yes | MERGEABLE/CLEAN |
| #501 | `31d66332` | yes | MERGEABLE/CLEAN |
| #504 | `aab4dbf8` | yes | MERGEABLE/CLEAN |

### 8.1 The union is already performed — #493's head strictly contains #501

`feat/prism-next8-04-automation-grammar` advanced `d3e978d1` → `255d665f` (`6bda6978`,
"prism-lane4: compose both Lab projections (automation-grammar + canonical-loop)"). #493's head now
renders **both** projections:

```
web/arkadia_console/src/pages/EngineeringLabPage.tsx:6   import { LabAutomationGrammar } ...
:7   import { ExecutionLoop } ...
:45  <ExecutionLoop ... />
:72  <LabAutomationGrammar />
```

Measured containment, `git diff --numstat 255d665f 31d66332 ':(exclude)docs'` — the *only*
entries are **deletions** of content #493 adds:

```
0  314  tests/test_lab_automation_grammar_contract.py
0  109  tests/test_prism_next_wave_composition_reconciliation_01.py
0  370  tests/test_prism_w4_automation_grammar.py
0  182  web/arkadia_console/src/components/lab/LabAutomationGrammar.tsx
0  498  web/arkadia_console/src/components/lab/labAutomationGrammar.ts
0    3  web/arkadia_console/src/pages/EngineeringLabPage.tsx
```

`git diff --quiet 255d665f 31d66332 -- tests/test_prism_w4_canonical_loop_mount.py` → **IDENTICAL**.
`ExecutionLoop.tsx` and `test_prism_w4_canonical_loop_mount.py` are already on `main`; #501's sole
non-doc delta over `main` is the 3-line `EngineeringLabPage.tsx` mount, which #493's head already
carries. **#501 is subsumed.** The §7.1 recommendation ("compose #501 in") is therefore already
satisfied and is superseded by this measurement.

### 8.2 §3.2's "61 passed" is superseded by a clean four-lane composition

#493's head also carries `tests/test_prism_next_wave_composition_reconciliation_01.py` — **identical**
to this branch's copy (`git diff <#504> origin/feat/prism-next8-04-automation-grammar --
tests/test_prism_next_wave_composition_reconciliation_01.py` → empty). The composition guard is
not novel to #504; it is the shared lane-4 artifact.

Four-lane composition measured in a detached worktree on `origin/main` `49809f45`, applying
`#497 + #498 + #492 + #493` in that order: **every patch applied cleanly** (no `UU` on any file;
disjoint file sets hold, since #493 subsumes #501).

```
python -m pytest tests/test_console_shell_nav_contract.py \
  tests/test_knowledge_timeline_paging.py tests/test_prism_opportunity_entry_flow.py \
  tests/test_prism_w4_automation_grammar.py tests/test_prism_w4_canonical_loop_mount.py \
  tests/test_lab_automation_grammar_contract.py -q -rEf
→ 179 passed in 8.19s

python -m pytest tests/test_prism_next_wave_composition_reconciliation_01.py -q
→ 5 passed          (both projections present on the composed tree)

cd web/arkadia_console && corepack pnpm exec tsc --noEmit   → exit 0
corepack pnpm build → ✓ built in 1.57s (84 modules; dist/assets/index-uAYAcU92.js)
```

### 8.3 The guard's negative control, proven on the real file

The composed-tree pass in §8.2 is only meaningful because the guard reddens when a side is
absent. Proven against the real `EngineeringLabPage.tsx`, not a fixture — applying the #504 guard
onto the single-projection tree `31d66332` yields:

```
FAILED tests/test_prism_next_wave_composition_reconciliation_01.py::test_a_mounted_lane4_projection_requires_all_of_them
   AssertionError: ... is missing ['automation-grammar'] ... 1 failed, 4 passed
```

So the guard is silent pre-composition, red on a one-sided merge, green on the union.

### 8.4 Classification delta

| Item | §3–§6 said | Re-measured 2026-10-13 |
|---|---|---|
| #493 ⨯ #501 textual conflict | CONTRADICTED | **RESOLVED in #493's head** (`255d665f`); #501 subsumed |
| Union resolution | VERIFIED in a composed worktree (61 passed) | **VERIFIED**, four-lane, 179 passed + build green |
| Composition guard location | this (#504) branch | also on #493's branch (identical blob) |
| Merge / deploy / acceptance | NOT CLAIMED | **NOT CLAIMED** (unchanged; outside authority) |

**Not performed:** no merge, no deploy, no acceptance. §8 is a measurement of live branch heads,
not a merge recommendation. The sovereign still chooses the merge order; a PR that is *subsumed*
(#501) is not thereby *approved* — closing it is a sovereign action, recorded here as a proposal.

## 9. Composition guard derivation repair (pass 2026-10-14)

**Scope:** the guard's *domain*. No page, component, or lane source was edited.
**Authority:** inspection, implementation, test only. No merge, deploy, or acceptance.

### 9.1 Defect — the guard judged a hand-maintained table, not the lane-4 set

§8 wrote the guard with a static projection table of two entries
(`<LabAutomationGrammar`, `<ExecutionLoop`). Lane 4 has since grown two more
projections, and the table could not see them. Measured at the live heads
(2026-10-14), the guard is green on every one of them while remaining blind to the
mount that the tree in question actually adds:

| tree | page mounts | guard markers known | guard verdict |
|---|---|---|---|
| `main` | AgentRegistry, ArtifactCanvas, ModelGateway, SessionList | 2 | 5 passed |
| `#493` | + `ExecutionLoop`, `LabAutomationGrammar` | 2 | 5 passed |
| `#512` | + `LabOperationalSurfaces` | 2 | 5 passed |
| `#524` | + `LabAuthorityReadings` | 2 | 5 passed |

**One-sided composition, measured.** Composing #512 x #524 in a worktree
(`git apply --3way`, no conflict markers) yields a page mounting *both* new
surfaces — 5 passed. Then dropping only the `<LabAuthorityReadings` mount, the shape
a one-sided conflict resolution produces, still reported:

```
.....                                             [100%]
5 passed in 0.08s
```

That is the defect: the negative control in §8.3 was proven with a marker the *table*
names (`<LabAutomationGrammar`). For a projection the table does not name, the guard
has no negative control at all and reports success on a page that lost a lane's
user-visible surface.

### 9.2 Repair — derive the projection set from the corpus

`tests/test_prism_next_wave_composition_reconciliation_01.py` now derives its markers
rather than restating them. Each lane-4 contract test already pins its projection with
a literal mount assertion against a variable bound to the page
(`assert "<LabX" in page`); the detector reads those same literals via
`projections_in_module()` and maps each marker to its pinning test. Two invariants are
stated:

1. every derived projection present in the page implies **all** of them are present
   (silent pre-composition, so a tree that legitimately carries no lane is not reddened);
2. every lane-4 component the page *imports* from `components/lab/` is also *rendered*
   — the merge-loss shape where a hand-resolved merge keeps the `import` and drops the
   render.

Derived set per tree: `main` 4, `#493` 6, `#512` 5, `#524` 5.

### 9.3 Proven on the real file, both directions

```
one-sided composed tree (LabAuthorityReadings dropped):
  FAILED test_a_mounted_lane4_projection_requires_all_of_them
  FAILED test_every_imported_lane4_component_is_rendered
  2 failed, 8 passed

restored composed tree:                      10 passed
main / #493 / #512 / #524 (coherent trees):  10 passed each
```

Controls, all in-file: the negative control drops a marker from the **derived** set, so
it fails if the guard regresses to a static table; a positive control asserts the union
is silent; and a paired control proves `assert "X" not in page` (an *absence* pin, as in
#512's own surface contract) does not enter the marker set. **The absence-pin control was
itself proven to have teeth:** widening both detectors to `(?:not\s+)?in` reddens it
(`1 failed, 9 passed`), and the guard restores byte-identically to `10 passed`.

### 9.4 CI execution site — corrected measurement

An earlier reconnaissance note in this pass claimed the guard was referenced by no
workflow. That was a **false negative from grepping the literal path**: the console gate
executes its inventory through the *derived* domain
(`python -m pytest -q $(python scripts/console_contract_domain.py)`), which lists
`tests/test_prism_next_wave_composition_reconciliation_01.py` (domain size 22 on this
tree). `tests/test_prism_console_ci_wiring.py` -> 30 passed. No wiring change is needed,
and none was made.

### 9.5 Verification and boundary

```
python -m pytest tests/test_prism_next_wave_composition_reconciliation_01.py -q  -> 10 passed
python -m pytest tests/test_prism_next_wave_composition_reconciliation_01.py \
    tests/test_prism_console_ci_wiring.py tests/test_m02a_ci_gate_integrity.py -q -> 106 passed
python -m pytest tests/architecture -q                                          -> 11 passed
printf '<guard path>\n' | python scripts/cp10_mutation_boundary_policy.py --judge -> ADMITTED
```

This is a **test-side** change; no lane source, page, or component is modified, so no
lane's ownership is crossed and the composition hazard itself is untouched. Merge order
remains the sovereign's. **Not performed:** no merge, no deploy, no acceptance.
