# gate-hygiene · pass 8 — open-PR queue composability (12 PRs) + constitutional-boundary contradiction

Evidence-only pass. **No source, test, governance, `.bootstrap/`, or `AGENTS.md` change.**
Base `main` = `73b65bac34056cb4fbc58c486ad5348df4885cab` (`Merge pull request #243`,
2026-10-04T05:28:36Z). Observation timestamp 2026-10-04T06:1xZ. Stdlib/`pytest`
measurements only; no merge, no push to `main`.

Companion to pass 7 (`gate-hygiene/open-pr-queue-composability-pass7`, PR #224, merged).

## 0. Purpose and scope

Pass 7 composed a **9-PR** queue (#215–#223) and pinned one next bounded task. The queue has
since turned over almost completely (one PR merged, twelve new). This pass re-derives the
live queue, re-proves composability at the current tips, re-measures the baseline, and
classifies the one new *structural* fact: a constitutional boundary guard that is red on
`main` and contradicted by live product surface.

Out of scope (explicit non-goals): repairing the boundary contradiction, repairing frontend
literal pins, editing `.bootstrap/` or `AGENTS.md` (do not carry pass-7 "reconcile" work into
this pass), any merge.

## 1. Live open-PR queue (measured via the REST API)

`GET /repos/Arkadia-Oversoul-Prism/Arkadia/pulls?state=open` → **12** open PRs.

| # | branch | tip SHA | base | surface |
|---|--------|---------|------|---------|
| 245 | `gate10/persist-phase1-runtime-state-01` | `9277e5363ba470eea9507f9915b991c0e1c19db8` | `357fbd8` | `.bootstrap/` + evidence |
| 246 | `fix/console-field-focus-deep-presentation` | `13af648fbae8088c01a4eca54cb4ba6344e51858` | `357fbd8` | console + `console_authority_router.py` + test |
| 247 | `fix/console-personal-field-projection` | `4072d4812985561fa1027eb2c10e29848719c37c` | `357fbd8` | console only |
| 248 | `gate10/console-capture-safe-id-repair-01` | `96511b028b68eabc5a538f29a81c2fce0ad3b152` | `357fbd8` | `console_authority_router.py` + test + evidence |
| 249 | `test-hygiene/review-route-boundary-false-positive-01` | `8b27c44e7d3d47b5ad1e585abe104c64cbc5fd8c` | `357fbd8` | docs + tests |
| 250 | `weaver-echofield-resolver-import-repair-01` | `6aaac9fb045de3ed85f976773d23ce1d2013930d` | `357fbd8` | weaver + tests (only red PR) |
| 251 | `test-hygiene/frontend-literal-pins-01` | `2b7a706ca81e2f67e303c73151be0c4d62d3f5de` | `357fbd8` | test-hygiene + evidence |
| 252 | `gate10/boundary-contradiction-01` | `715c6c834491882bcb5d9936df9dfdba3bb6db15` | `357fbd8` | records the evidence/verification boundary contradiction (§6) |
| 253 | `test-hygiene/oci-runtime-daemon-probe-01` | `55165407c45e2c0d70c5c59f1f16b3390548d3cb` | `357fbd8` | test-hygiene |
| 254 | `test-hygiene/commit-file-refusal-contract-01` | `e60351239b482ffc9a7062857a078d00d0380d7d` | `357fbd8` | test-hygiene |
| 255 | `security(ci): remove command injection` | `f9e19bdf651ac325d71c4bbd873d85401cf70906` | `73b65ba` | workflow + `AGENTS.md` + test + evidence |
| 256 | `gate-hygiene/spiral-grove-registry-cycle-ordering-01` | `b3d0038685d981465585095333b040f277122efd` | `73b65ba` | registry cycle-ordering repair + evidence |

All heads were fetched as `refs/pull/<n>/head` and **byte-verified** against the live API
`head.sha` (12/12 match). All `mergeable=True`. #245–#254 are based on `357fbd8` (one merge
behind `main`); #255–#256 are based on current `main` `73b65ba`.

## 2. Composition re-proof (independent, at live tips)

Fresh worktree off `main` `73b65ba`; merged in queue order #245 → #246 → … → #256.

```
OK #245 -> 29862cd   OK #246 -> 580d615   OK #247 -> 5330c86   OK #248 -> a7fd182
OK #249 -> 1218c1a   OK #250 -> 43045f3   OK #251 -> a2c4026   OK #252 -> 514778e
OK #253 -> a8ff8b0   OK #254 -> 99bee70   OK #255 -> 3bb119a   OK #256 -> 4e4993d
composed tree = 4e4993df24b6a083f2e0a70858d92d8174682932
```

**Zero conflicts** across all twelve, despite `console_authority_router.py` being written by
#246 and #248 and `tests/test_console_authority_chain.py` by #246 and #248 — the hunks are
disjoint.

Protected surfaces on the composed tree (`4e4993d`):

| check | result |
|---|---|
| `python -m py_compile api/main.py` | **OK** |
| `api/main.py` line count | **2582** / 2600 budget |
| `pytest tests/architecture -q` | **11 passed** |
| CP10 `--judge` on all `git ls-files` | **RC 0 — PASS** |

## 3. Baseline and composed-tree measurement (identical invocation)

Command (both trees): `PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q
--continue-on-collection-errors`.

| tree | result | failing+error nodes | outcomes fingerprint |
|---|---|---|---|
| `main` `73b65ba` | 23 failed / 1368 passed / 19 skipped / 1 error | **24** | `762a38ae…` |
| composed `4e4993d` | 12 failed / 1411 passed / 20 skipped / 1 error | **13** | `6ba6a8d4…` |

Node-set delta (set difference, **not** counts): **removed 11 / added 0**. The queue fixes 11
baseline nodes and introduces **zero** regressions. The 11 removed:

```
test_solspire_p1_experience_01.py::test_p1_1_arkana_context_pack
test_solspire_p1_experience_01.py::test_p1_1_not_authorization
test_solspire_project_execution_service.py::test_actual_oci_runtime_hardens_process_and_mount
test_solspire_project_instantiation_ui.py::test_arkana_injects_bounded_project_context_and_scopes_threads
test_solspire_project_instantiation_ui.py::test_project_runtime_context_uses_canonical_spines_without_inventing_project_bindings
test_solspire_project_instantiation_ui.py::test_projects_ui_uses_server_owned_template_catalog
test_solspire_project_templates.py::test_eden_template_declares_living_larder_without_claiming_it_is_live
test_solspire_r2_github_mutation.py::test_legacy_commit_file_fails_closed_without_network_write
test_spiral_grove_registry.py::test_ais_catalog_supports_progressive_creative_workflow
test_spiral_grove_registry.py::test_registry_rejects_prerequisite_cycle
test_verification_review_boundary.py::test_no_http_surface_exposes_review_as_a_first_class_record
```

The 13 still-failing on the composed tree are all pre-existing on `main` (§5). This is a
composability result, **not** a merge recommendation: it says the sequence is order-safe and
regression-free, not that any individual PR is approved.

## 4. The queue does not cleanly close the baseline

`tests/fixtures/baseline_node_set.txt` (18 entries, written at `d798811`) and the live
24-node `main` set do not coincide; after the queue composes, 13 nodes remain red. Those 13
are classified in §5. Of them:

- **2** are a **constitutional contradiction** requiring sovereign adjudication (§6).
- **11** are stale frontend/source **literal pins** — the recurring defect class recorded in
  `AGENTS.md` (test demands a literal the source does not emit). PR #251 repaired six of
  these; it does **not** touch the remaining set. `tests/fixtures/baseline_node_set.txt`
  lists only 2 of the 11 (the `spiral_grove_registry` pair), so the fixture itself is stale.

## 5. Classification of the 13 composed-tree failures

| node(s) | class | evidence |
|---|---|---|
| `test_steward_filter.py::{test_blocks_identity_claims, test_allows_mythic_with_action, test_compress_to_choices}` | source/test misalignment | filter no longer blocks `"You have transcended"`; `compress_to_choices` leaves `"More noise"` in — read the source literal before assuming a code bug |
| `test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | stale pin | asserts no `sessionStorage`; source intentionally uses it for the diagnostic handoff |
| `test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route` | stale pin | demands `"Let's form your node."`, absent from render |
| `test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key` | stale pin | demands `arkanaSessionId` in `ArkanaCommune` |
| `test_solspire_r1_governance_convergence.py::{…builders_delegate_to_weaver, …weaver_governance_is_canonical}` | test-side | governance-convergence pins |
| `test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools` | test-side | runtime boundary pin |
| `test_authority_api_enterprise_boundary.py::test_authorized_identity_is_the_control_case_and_creates_both_records` | test/env | `ValueError: authenticated authority identity is required` |
| `test_evidence_verification_boundary.py::test_no_http_route_creates_evidence_or_verification` | **CONSTITUTIONAL** | see §6 |
| `test_workevent_evidence_boundary.py::test_no_http_route_exposes_evidence_verification_or_the_enterprise_walk` | **CONSTITUTIONAL** | see §6 |
| `ERROR tests/test_autonomy.py` | collection error | `weaver.autonomy` module-vs-package collision (`AGENTS.md`) |

## 6. Constitutional contradiction — EVIDENCE/VERIFICATION boundary vs. the console authority chain

> **Already recorded — do not duplicate.** Open PR **#252**
> (`gate10/boundary-contradiction-01`, docs-only) fully records this contradiction, including
> the two sovereign dispositions (A: amend the boundary records / B: withdraw the routes). This
> section is a **cross-reference and independent confirmation** at `main` `73b65ba`, not a new
> workstream. Nobody should open a second PR against this boundary.

**Not caused by the queue. Red on `main` `73b65ba` for at least two revisions.**

Two boundary guards assert that **no HTTP route creates or exposes evidence/verification**:

```python
# tests/test_evidence_verification_boundary.py::test_no_http_route_creates_evidence_or_verification
assert ".evidence(" not in text   # solspire/console_authority_router.py FAILS here
...
assert "evidence" not in joined   # route paths: .../evidence FAILS here
```

The file `solspire/console_authority_router.py` **does** create them over HTTP:

```
204: @router.post("/executions/{execution_id}/evidence")
212:     evidence = store.evidence(...)
269: @router.post("/verification")
276:     verification = store.verify(...)
```

So `.evidence(`/`.verify(` are present in a route source and `/verification` is a route path.

History (linear, both ancestors of `main`):

- `.evidence(` added by `c052cee` (`feat(console): expose governed authority chain`).
- Boundary assertion added by `ae847dd` (PR #180, 2026-10-??), **after** the route.

The console route is **live product surface**, not dead code: the Android console calls it:

```
arkadia-console-android/.../ConsoleRepository.kt:83  -> POST /solspire/authority/executions/{id}/evidence
arkadia-console-android/.../ConsoleRepository.kt:88  -> POST /solspire/authority/verification
```

### Why this is a hard stop, not a repair

The two guards encode a *constitutional* boundary ("EVIDENCE ≠ VERIFICATION" — evidence is
created only by the store, and is HTTP-readable **only as a control-room projection**). The
console authority chain encodes the opposite design: a governed, human-authorized UI that
posts evidence and verification. Only the sovereign can decide which statement is canonical.
This pass therefore **does not edit either side** and does not open a code PR against it.

Both nodes are absent from `tests/fixtures/baseline_node_set.txt`, so the fixture does not
"own" them and cannot excuse the red.

**Proposed bounded workstream (requires sovereign direction):**

1. If the console chain is canonical → the two guards are stale pins; repair them *test-side*
   to assert the real invariant (store-only persistence, projection-only read) rather than a
   blanket route-string ban. That is a test-hygiene task.
2. If the boundary is canonical → the console routes (and `ConsoleRepository.kt` callers) are
   a new mutation path and must be withdrawn. That is a governance/constitutional change
   (SOVEREIGN-only).

## 7. PR #250 `provider-routing` red — root cause

`provider-routing.yml` runs on paths `weaver/**`, `providers/**`, `tests/test_weaver_k2.py`,
`tests/test_key_pool.py`, `docs/verification/PROVIDER-ROUTING-AUDIT-BASELINE.md`.

At #250 head `6aaac9f`: `mvp2-validation` **success**, `Full-history secret scan` **success**,
`provider-routing` **failure**. Step-by-step: `Targeted K2 and key-pool regressions` passes,
`Relevant architecture regression` passes (11/11); the failing step is **`Broader test suite`**
(`python -m pytest tests/ -q` with **no** `--continue-on-collection-errors`). That bare form
**interrupts at the `tests/test_autonomy.py` collection error (exit 2)** and under-reports the
run; it is not a regression attributable to #250. The remaining status failure is
`Vercel – console`, pre-existing on `357fbd8` (both Vercel contexts fail there).

**Classification: BLOCKED / environment-baseline, not a #250 defect.** The workflow's final
step queries the whole suite without the collection-error tolerance every other measurement
in this repo uses; that is a workflow-hygiene observation, not a code defect in #250.

## 8. What this pass does *not* claim

- It does **not** claim the queue is merge-ready or approved. Merge = sovereign.
- It does **not** claim production parity. No deployment identity was resolved this pass.
- It does **not** resolve the §6 contradiction; it names it and stops at the authority boundary.
- The composed-tree numbers are a fresh worktree measurement; `tests/test_engineering_lab_agent_loop.py::test_agent_loop_does_not_mutate_repository`
  is known-intermittent under the full suite (`AGENTS.md`) and was not observed red in either
  run this pass.

## 9. Deterministic resume block

- **State**: evidence pass complete; one docs-only PR.
- **BASE_MAIN**: `73b65bac34056cb4fbc58c486ad5348df4885cab`.
- **Composed tree**: `4e4993df24b6a083f2e0a70858d92d8174682932` (12 PRs, zero conflicts,
  −11/+0 nodes).
- **Authorized action**: sovereign review of this evidence PR.
- **Next bounded task (requires authority)**: the §6 sovereign ruling, which PR #252 already
  requests — decide (A) amend the Gate-03/04 records + boundary guards, or (B) withdraw the
  console evidence routes. This pass opens **no** competing repair; re-entry condition is a
  recorded ruling in `docs/control-plane/evidence/gate10-boundary-contradiction-01/`.
- The 11 non-constitutional failures (§5) remain a candidate test-hygiene workstream, but PR
  #251 already repairs six literal pins and PRs #253/#254 assert adjacent contracts — drain
  those first before proposing a further literal-pin pass.
- **Forbidden**: merging; pushing to `main`; editing `.bootstrap/`/`AGENTS.md`; repairing
  baseline debt inside this PR.
