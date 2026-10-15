# Prism recursive recovery · Lane 04 · Arkana response provenance

**Branch:** `feat/prism-rec-05-arkana-provenance` (draft PR)
**Lane:** 04 — Arkana / Weaver / Engineering Lab (`docs/control-plane/parallel-ui/AGENT-04-ARKANA-WEAVER-LAB.md`)
**Contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`
**Starting `main`:** `dfbd2304db27746b22f0cda9b6961d1e37fda313`
**Authority:** implement, test, commit, report. **No merge, deployment, or acceptance.**

---

## 1. What was recovered

`POST /api/commune/resonance` returns three retrieval channels beside `reply`
(measured against the handler, `api/main.py:1363-1370`, not inferred from an
archive):

| Channel | Emitted by | Element shape |
|---|---|---|
| `rag_refs` | `_rag_context(message, scrolls)` | `{ id, label, category }` |
| `sources` | `oracle_spine.build_sources(context_package)` | `{ id, title, type, via, excerpt }` |
| `memory` | the resonance handler | `{ session_id, thread_id, project_id, notes_retrieved, source, injected }` |

The archived Prism projected what informed a reply; the canonical console
dropped all three. A reader could see an answer but not whether it cited the
corpus, the private Knowledge OS, or neither.

The slice renders them read-only. It adds no request of its own.

### Provenance invariant preserved

`build_sources` emits a citation **only** when the note was actually part of the
retrieved context handed to the provider; an absent package yields `[]`
(`api/oracle_spine.py:92-118`). The panel honours this: it renders exactly the
channels the response carried and never manufactures a reference. A `memory`
object is present on **every** successful call, so `hasRetrieval` counts a
channel only when a scroll or note was supplied, or `notes_retrieved > 0` — the
bare `injected` flag is not treated as evidence of a citation.

## 2. Files changed

| Path | Change |
|---|---|
| `web/arkadia_console/src/components/arkana/arkanaProvenanceContract.ts` | new — channel types + pure normalisation (`buildProvenance`, `hasRetrieval`) |
| `web/arkadia_console/src/components/arkana/ArkanaProvenancePanel.tsx` | new — read-only render of the three channels |
| `web/arkadia_console/src/lib/arkana.ts` | `askArkana` normalises provenance from the response and returns `ArkanaTurn` |
| `web/arkadia_console/src/pages/ArkanaPage.tsx` | holds provenance per turn and mounts the panel |
| `tests/test_prism_rec_arkana_provenance.py` | new — 15-test source contract with negative controls |
| `docs/control-plane/evidence/prism-rec-05-arkana-provenance/EVIDENCE.md` | this record |

No shared file owned by another lane is touched (`App.tsx`, `router.ts`,
`surfaces.ts`, `endpoints.ts`, `types.ts`, `SurfaceLenses.tsx` — untouched).

## 3. Verification

| Command | Result |
|---|---|
| `corepack pnpm build` (`web/arkadia_console`) | **PASS** — `tsc --noEmit` clean; `85 modules transformed`, `built in 1.57s` |
| `pytest tests/test_prism_rec_arkana_provenance.py tests/test_prism_w4_arkana_thread_history.py tests/test_arkana_thread_history_contract.py` | **47 passed** |
| `pytest tests/architecture -q` | **11 passed** |
| `pytest tests/test_canonical_frontend_routing.py tests/test_frontend_arkadia_console_rebuild_01.py tests/test_console_shell_nav_contract.py tests/test_console_endpoint_registry_contract.py tests/test_console_authority_chain.py tests/test_aeas05_canonical_frontend_acceptance.py` | **85 passed** |
| `pytest tests/test_prism_console_ci_wiring.py tests/test_ci_gate_trigger_coverage.py tests/test_baseline_fingerprint_ci_wiring.py tests/test_m02a_ci_gate_integrity.py` | **197 passed** |
| `printf ... \| python scripts/cp10_mutation_boundary_policy.py --judge` | **PASS** (exit 0) |

### Negative controls (live, not synthetic)

Removing the panel mount from `ArkanaPage.tsx` and re-running the guard reddens
`test_arkana_page_renders_the_provenance_panel` (`1 failed, 14 passed`), then the
file is restored byte-identically. The source-detector negative controls inside
the guard prove the constant-fed-provenance and mutating-request detectors fire.

### CI wiring — no gate edit needed

`tests/test_prism_rec_arkana_provenance.py` names `web/arkadia_console`, so it
joins the derived console-contract domain automatically
(`python scripts/console_contract_domain.py` lists it), and
`prism-console-contract.yml` selects `tests/**` and executes
`$(python scripts/console_contract_domain.py)`. The guard is executed by the
existing gate without any wiring change.

## 4. Baseline comparison (measured, not inherited)

Full suite, one pass:
`python -m pytest tests/ -q -rEf --continue-on-collection-errors`

`8 failed, 2991 passed, 17 skipped, 1 error` — failing/error node set (9 nodes):

```
ERROR  tests/test_autonomy.py
FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
FAILED tests/test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set
FAILED tests/test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated
FAILED tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
FAILED tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
```

Every node is a pre-existing debt class recorded in `AGENTS.md` (the CE-01
`weaver.autonomy` collection error reserved to the sovereign; the
`test_engineering_lab_api.py` authority-boundary pins; the SolSpire
governance-convergence and identity-spine pins). **None** is in the Arkana or
console domain this slice touches, and none is attributed to it.

The new guard adds 15 passing nodes; it is not a second full-suite run.

## 5. Remaining uncertainty / next bounded task

- The panel is display-only by design; no runtime observation of a live reply's
  provenance was made (no credential, no deployment action). The claim is a
  **repository-source** claim, not a production observation.
- Next bounded slice (Lane 04): make a provenance citation inspectable against
  the Knowledge OS graph (the `sources[].id` is the note UUID; a read-only link
  through the existing knowledge slice would close the loop). Not started here.
