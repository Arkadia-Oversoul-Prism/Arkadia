# GATE-HYGIENE - Ledger tree reconciliation against live `main`

**Scope:** reconciliation + ledger-convergence evidence. **Evidence-only.**
**Base:** `main` @ `df7a99a` (measured live this pass).
**Ledger under review:** `docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/BASELINE_TEST_DEBT_CLASSIFICATION.md` (measured at `a26af408`).
**Relation:** `a26af408` **is** an ancestor of `df7a99a` - 149 commits apart.

No source, test, workflow, governance or constitutional file is modified by this branch.

---

## 1. Why this artifact exists

The classification ledger was written at `a26af408`. Since then the SH-01 and SH-02 workstreams
merged (`#130`, `#131`, `#132`, plus the env-leak corrections `fc3743f`, `6e481ca`). The ledger's
**section 8 "Proposed next bounded tasks" still recommends `SH-01` as the first task**, and its
Appendix A still lists rows as `FAILED` that now pass.

A naive next heartbeat would have executed `SH-01` a second time - duplicate work against an
already-merged fix. This artifact re-measures the ledger against live `main` so the next pass
reconstructs from evidence instead of stale prose.

---

## 2. Appendix A re-measured against `df7a99a`

Measured fingerprint: `32 failed / 1025 passed / 13 skipped / 2 errors`.
Appendix A lists **51** nodes. Re-measured:

| state | count |
|---|---|
| **still red** on `df7a99a` | **26** |
| **now green** on `df7a99a` (Appendix A claimed FAILED) | **25** |

### 2.1 Still red - 26 nodes

| row | file | bucket |
|---|---|---|
| 1 | `test_agent_run.py` | STALE_ASSERTION |
| 2 | `test_ais_capability_profile_onboarding.py` | STALE_ASSERTION |
| 3 | `test_ais_w2_living_gate_grove_handoff.py` | STALE_ASSERTION |
| 4 | `test_ais_w2_living_gate_grove_handoff.py` | STALE_ASSERTION |
| 5 | `test_ais_w2_living_gate_grove_handoff.py` | STALE_ASSERTION |
| 6 | `test_ais_w2_living_gate_grove_handoff.py` | STALE_ASSERTION |
| 7 | `test_ais_w2_living_gate_grove_handoff.py` | STALE_ASSERTION |
| 8 | `test_ais_w2_living_gate_grove_handoff.py` | STALE_ASSERTION |
| 10 | `test_prism_interior_shell.py` | STALE_ASSERTION |
| 11 | `test_prism_interior_shell.py` | STALE_ASSERTION |
| 12 | `test_prism_interior_shell.py` | STALE_ASSERTION |
| 22 | `test_solspire_p1_experience_01.py` | STALE_ASSERTION |
| 23 | `test_solspire_p1_experience_01.py` | STALE_ASSERTION |
| 27 | `test_steward_filter.py` | STALE_ASSERTION |
| 28 | `test_steward_filter.py` | STALE_ASSERTION |
| 29 | `test_steward_filter.py` | STALE_ASSERTION |
| 38 | `test_engineering_scheduler_bootstrap.py` | DRIFT |
| 39 | `test_engineering_scheduler_bootstrap.py` | DRIFT |
| 41 | `test_identity_spine_w1.py` | DRIFT |
| 42 | `test_m02_reasomate_truth.py` | DRIFT |
| 43 | `test_spiral_grove_registry.py` | DRIFT |
| 44 | `test_spiral_grove_registry.py` | DRIFT |
| 47 | `test_gate_serve_script.py` | ENV / ARTIFACT |
| 48 | `test_gate_status.py` | ENV / ARTIFACT |
| 50 | `test_autonomy.py` | COLLECTION_ERROR |
| 51 | `test_render_codex.py` | COLLECTION_ERROR |

Bucket of the still-red set: `STALE_ASSERTION 16`, `DRIFT 6`, `ENV/ARTIFACT 2`, `COLLECTION_ERROR 2`.
This is **identical** to the batching already in flight (section 3). No new work is implied.

### 2.2 Now green - 25 nodes (stale in the ledger, not open work)

| row | file | node |
|---|---|---|
| 9 | `test_ais_w6_future_skills_challenge.py` | test_w6_is_self_guided_and_timed |
| 13 | `test_prism_pass_c_surface_ownership.py` | test_codex_resolves_to_solspire_codex |
| 14 | `test_prism_pass_c_surface_ownership.py` | test_echo_field_aliases_resolve_to_solspire_field |
| 15 | `test_prism_pass_c_surface_ownership.py` | test_knowledge_os_resolves_to_solspire_knowledge |
| 16 | `test_prism_pass_c_surface_ownership.py` | test_loops_resolves_to_solspire_loops |
| 17 | `test_prism_pass_c_surface_ownership.py` | test_spiral_codex_not_solspire_field |
| 18 | `test_prism_pass_c_surface_ownership.py` | test_spiral_codex_uses_feed_component |
| 19 | `test_solariun_experience_consolidation_01.py` | test_area_c_solspire_substrate_uses_existing_search_and_context_grammar |
| 20 | `test_solariun_experience_consolidation_01.py` | test_preimplementation_map_is_present_and_bounded |
| 21 | `test_solariun_experience_consolidation_01.py` | test_responsive_composition_and_inspector_exist |
| 24 | `test_spiral_grove_chambers.py` | test_chamber_does_not_invoke_autonomous_generation_or_adjudication |
| 25 | `test_spiral_grove_frontend_projection.py` | test_activity_draft_persistence_is_local_and_not_evidence |
| 26 | `test_spiral_grove_learning_path_projection.py` | test_evidence_assessment_state_are_downstream |
| 30 | `test_weaver_mvp2_08.py` | test_nexus_novanet_canonical_routing_intact |
| 31 | `test_weaver_sci_boundary_01.py` | test_nexus_novanet_alias_intact |
| 32 | `test_weaver_sci_boundary_01.py` | test_product_nav_is_not_operator_authority |
| 33 | `test_weaver_sci_boundary_01.py` | test_solspire_owns_project_workspace_not_global_command |
| 34 | `test_weaver_sci_contract_01.py` | test_nexus_novanet_alias_intact |
| 35 | `test_weaver_sci_contract_01.py` | test_solspire_is_workspace_not_second_sci |
| 36 | `test_ais_w8_canonical_identity.py` | test_w8_ais_projection_reuses_authenticated_uid |
| 37 | `test_ais_w8_canonical_identity.py` | test_w8_no_second_authentication_or_identity_store_is_created |
| 40 | `test_identity_spine_w1.py` | test_ais_profile_exposes_canonical_identity_spine |
| 45 | `test_weaver_w5.py` | test_derived_graph_provenance |
| 46 | `test_weaver_w5.py` | test_http_knowledge_isolation |
| 49 | `test_m01_persistence.py` | test_db_path_honours_data_dir_env |

Provenance - each group was repaired by an **already-merged** commit:

| rows | resolving commit(s) | PR |
|---|---|---|
| 13-18 | `82ce2a8`, `157da8d` | #132 |
| 19-21 | `07f3ea1`, `7afab32` | #132 |
| 30-35 | `9032193`, `788f197` | #130 / #131 |
| 9, 24-26 | `cefb2f5`, `576d9f4` | #131 |
| 36, 37, 40 | `587df17` | #130 |
| 45, 46 | `6e481ca`, `788f197` | env-leak correction |
| 49 | `fc3743f` | SH-01 |

`SH-01` - the ledger's own recommended first task - is **DONE**: `fc3743f`
"gate-hygiene: stop test-session env leakage at import time" is an ancestor of `df7a99a`, and
`tests/test_echofeild_aggregator.py` + `tests/test_m01_persistence.py` pass together in either
order (28 passed). The `SOLSPIRE_PROJECTS_DB` import-time `os.environ[...]` write is gone; the
module now holds a constant `_SOL_DB` and lets `monkeypatch` own the environment.

**Consequence:** section 8 of the ledger is superseded for `SH-01`, and Appendix A over-states
open work by 25 nodes. The ledger should be treated as a *superseded snapshot at `a26af408`*, not
as current task state.

---

## 3. Ledger convergence - the shared-file append conflict

Three open PRs append to a byte-region-adjacent tail of the same ledger file:

| PR | head (measured) | ledger diff |
|---|---|---|
| #135 | `90544c95` | +128 / -0 |
| #136 | `a9196512` | +85 / -0 |
| #137 | (open) | +40 / -4 |

All three report `mergeable=true / state=clean` against `main`, because **no pair of them shares a
base commit** - mergeability is computed against `main`, so the three-way collision is invisible
until they merge against *each other*.

**Measured** (fresh branches off `df7a99a`, real merge commits):

| merge order | result |
|---|---|
| `#135` then `#136` | clean |
| `#135` then `#137` | **#137 conflicts** |
| `#136` then `#135` | clean |
| `#136` then `#135` then `#137` | **#137 conflicts** |
| `#137` then `#135` | **#135 conflicts** |
| `#137` then `#136` | **#136 conflicts** |
| `#138` `#133` `#135` `#136` `#137` | **#137 conflicts** |

Ignoring #138 (different file), **every ordering of #135 / #136 / #137 conflicts with exactly one
PR**, and **#137 conflicts in every ordering** - it is the one carrying the residual `-4`
deletion, so it is the only order-dependent party.

**Safe sequence:**

1. Merge **#133** (test file + its own new evidence dir - touches no shared ledger).
2. Merge **#138** (separate audit doc - no shared ledger).
3. Merge **#135** then **#136** in either order (measured clean).
4. Merge **#137** LAST. It will still conflict on the shared ledger; resolve by **union-append**
   (keep both evidence sections; it is append-only, so both sections are independent).

Re-measure after each merge - the ordering above binds only to the head SHAs in the table.

---

## 4. Preconditions verified this pass

- `main` = `df7a99a`; working tree clean; `origin/main` == `main`.
- Architecture fitness: **11/11**.
- `tests/test_m02a_ci_gate_integrity.py` (the live-corpus allowlist invariant): **49/49**.
- CP10 `LEGIT` admits `docs/**` - this branch's new evidence dir is inside the boundary.
- #133 head checks: `Full-history secret scan` pass, `Vercel` pass, `Vercel Preview Comments` pass.
- PR repairs verified locally: #135 -> `test_prism_interior_shell.py` 5 passed;
  #136 -> `test_agent_run.py` 6 passed; #137 -> `test_solspire_p1_experience_01.py` 5 passed.

`api/main.py` was **not touched** by this pass; the 2600-line boot budget is unaffected.

---

## 5. What #133 is, precisely

`gate-hygiene/SH-02 batch 6: repair Living Gate / W2 stale assertions (nodes 3-8)`.

Measured on its head `b8e6afc`: **9 passed / 1 failed**. The failure,
`test_no_firebase_persistence_in_gate`, is **deliberately left failing** and is documented in the
test's own docstring as *FINDING F-01 - a proxy-invalidation awaiting a sovereign decision:* the
gate genuinely carries no `firebase`/`firestore` reference, but `LivingGate.tsx` now uses
`sessionStorage` for a tab-scoped diagnostic handoff. Re-pinning the guard to permit
`sessionStorage` would loosen a persistence boundary - a governance call, not test hygiene.

So #133 is **PARTIAL by design**, not "nodes 3-8 repaired". It is correct to merge; the remaining
node is a sovereign item, not a defect in the batch.

---

## 6. Non-claims

- **No production or runtime claim.** Nothing here is deployment evidence; the Gate-2
  main -> deployment -> runtime boundary from `AGENTS.md` is untouched by this artifact.
- **No new gate status.** No gate is opened, closed, or promoted.
- **No baseline debt is fixed here.** No test, source or workflow file is modified.
- **No reclassification** of `REGISTERED_ARCHITECTURAL_DEBT`.

## 7. Authorization

Reconciliation + convergence evidence only. No merge, no authorization, no identity-boundary
change, no scope expansion. The sequence in section 3 is a **measured recommendation**; the
sovereign decides merge order and timing.
