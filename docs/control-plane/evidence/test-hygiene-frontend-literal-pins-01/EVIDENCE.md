# test-hygiene/frontend-literal-pins-01 — frontend/source literal-pin repair

**BASE_MAIN**: `357fbd83001924e909979fbaebdedbd991a2aadb` (`Merge pull request #244`)
**Branch**: `test-hygiene/frontend-literal-pins-01`
**Scope**: test-side literal pins only. No production source, no governance surface,
no authority path, no `api/main.py`.

## Objective

Repair the frontend/source **test-side literal pins** recorded in the Phase 1 runtime
stabilization classification, so the tests assert the surfaces that actually carry the
governance property instead of retired copy.

## Defect class

Frontend/SG tests in this repository are **source-level string assertions**. Two recurring
failure modes (both present here):

1. The test demands a literal the source no longer emits, while the *property* is intact
   on a different surface (retired copy, reworded heading, Python string-concatenation
   split).
2. The test pins a **stale value** that the canonical source has since renamed.

In every case the correct repair is to assert the real surface — never to edit production
source to satisfy a stale literal.

## Nodes repaired (6)

| Node | Test-side defect | Assertion now targets |
|---|---|---|
| `test_solspire_project_instantiation_ui.py::test_projects_ui_uses_server_owned_template_catalog` | asserted lowercase `runtime integration is verified separately` | `Runtime integration is verified separately.` — the sentence the source emits (`ProjectsWorkspace.tsx:125`) |
| `...::test_arkana_injects_bounded_project_context_and_scopes_threads` | asserted 4 project-scoped endpoint literals inline in `SolSpireExperience.tsx` | the bounded `runtime-context` read the overlay owns + the project-scoped reads on the surfaces that own them (`ProjectKnowledgeGraph.tsx`, `WorkspaceActionSurfaces.tsx`, `ProjectDashboard.tsx`) |
| `...::test_project_runtime_context_uses_canonical_spines_without_inventing_project_bindings` | pinned a literal split across a Python string concatenation (`console_router.py:609-611`) | `Project records are data/evidence, not authority.` — the emitted sentence |
| `test_solspire_p1_experience_01.py::test_p1_1_arkana_context_pack` | demanded retired literal `NO SILENT FULL-CORPUS DUMP` | the panel's own honesty disclosure (`.arkana-context-honesty`), which carries the bounded-context claim |
| `...::test_p1_1_not_authorization` | demanded retired literal `Displayed context only` | `bounded context` / `injected into each Arkana turn` in the same disclosure |
| `test_solspire_project_templates.py::test_eden_template_declares_living_larder_without_claiming_it_is_live` | pinned `read_only_snapshot_v0_1` (value appears nowhere in the tree) | `disposable_container_candidate_patch_v1` — the canonical value (`project_templates.py:90`) |

## Verification (run on this tree)

```
python -m py_compile api/main.py                                     -> OK (2582 / 2600 budget)
python -m pytest tests/architecture tests/test_m02a_ci_gate_integrity.py -q -> 66 passed
git diff --name-only | python scripts/cp10_mutation_boundary_policy.py --judge -> RC 0, PASS
python -m pytest tests/test_solspire_project_instantiation_ui.py \
  tests/test_solspire_p1_experience_01.py tests/test_solspire_project_templates.py -q -> 16 passed
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q \
  --continue-on-collection-errors                                   -> 21 failed / 1369 passed / 20 skipped / 1 error
```

## Node-set delta (attribution is by node set, never by count)

Sorted `FAILED`/`ERROR` node sets, base `357fbd8` vs this branch:

| | base `357fbd8` | this branch |
|---|---|---|
| failing + error node set | 28 | **22** |

- **New nodes: none** (`comm -13` empty) — zero regressions.
- **Removed nodes: exactly the 6 repaired above** (`comm -23`).

## Remaining uncertainty (recorded, not reconciled silently)

1. The two authority-boundary nodes
   (`test_evidence_verification_boundary.py::test_no_http_route_creates_evidence_or_verification`,
   `test_workevent_evidence_boundary.py::test_no_http_route_exposes_evidence_verification_or_the_enterprise_walk`)
   are **not** test-side defects. Their assertions are correct: `console_authority_router.py`
   calls `store.evidence(...)` and exposes `.../evidence` and `.../verification` over HTTP,
   and `api/nodes.py` routes `weaver/runs/{run_id}/evidence`. These are genuine
   authority-surface questions reserved to the sovereign (PR #250 territory). This PR does
   **not** touch them.
2. `test_solspire_project_execution_service.py::test_actual_oci_runtime_hardens_process_and_mount`
   fails on **Docker unavailability** — an environment boundary, not a literal pin.
3. The `test_autonomy.py` collection ERROR (`weaver.autonomy` module/package collision)
   remains sovereign-reserved.
4. `tests/fixtures/baseline_node_set.txt` staleness is not addressed here.

## Authorization

Human authority is required to merge. Nothing is merged; no push to `main` occurred.
