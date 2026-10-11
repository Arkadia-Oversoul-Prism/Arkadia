# Workstream 1 — shared endpoint/route contract reconciliation (next2, pass 2)

**Status:** implementation + evidence. No merge, deployment, or acceptance.
**Prepared:** 2026-10-11
**Branch:** `feat/prism-next2-01-shell-contract-map` (PR #429, draft)
**Base:** `main` `f390526ab14e122fef358ef9b9e1cd438509463c`
**Instruction:** `docs/control-plane/parallel-ui/AGENT-01-SHELL.md`
**Contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` (§3, §8)

## 0. Revision binding

| Item | Value | How measured |
|---|---|---|
| `main` | `f390526ab14e122fef358ef9b9e1cd438509463c` | `git rev-parse origin/main` |
| This branch, before this pass | `616aeae9e3885e330e873f098ab989f1e7551ad4` | `git rev-parse HEAD` |
| PR #429 | open, draft, `mergeable: true` | `GET /repos/.../pulls/429` |
| PR #430 head | `e6780d47af247b994fb76f0ef921fb99527dbac3` | `GET /repos/.../pulls/430` |
| PR #431 head | `a2024fbae7b5c993d0089364ad251f3dfe06a747` | `GET /repos/.../pulls/431` |
| PR #432 head | `dcb3e2f219e0b440be6b5f17081680790527f104` | `GET /repos/.../pulls/432` |

All three feature PRs are open, draft, and `mergeable: true`, each with **one** changed
file at this measurement (its own `AGENT-0N-*.md` instruction file). No feature-owned
source path is modified by any of them yet, so there is no current overlap to reconcile
beyond the recorded contract requests below.

## 1. What the three merged slices actually request (measured, not assumed)

Read from each slice's merged evidence on `main`, not from PR prose:

| Slice | Merge | Registry request |
|---|---|---|
| Shell/endpoints (W1 pass 1) | `67696372` | added `knowledgeSearch`, `labSessions`, `labAgents`, `labArtifacts`, `labGateway`, `labNAtlasCatalog`, `labSession(id)` |
| Opportunity (W2) | `11a81fb2` | **none** — `prism-parallel-02-opportunity-radar-01/EVIDENCE.md` §5: "No route, surface id, endpoint constant, or shared type is requested: the contract module carries its own paths and types" |
| Knowledge search (W3) | `3b606450` | none — reads `endpoints.knowledgeSearch`, which already existed |
| Arkana / Lab (W4) | `f390526a` | `labAutomations`, and a first-class `labCanvas(id)` / `labSession(id)` (`prism-w4-arkana-thread-history-01/EVIDENCE.md:391`) |

## 2. Served-route verification

Read from `api.main:app`'s served OpenAPI schema in this environment:

| Path | Methods | Verdict |
|---|---|---|
| `/api/lab/engineering/artifacts` | `get` | served |
| `/api/lab/engineering/artifacts/{artifact_id}` | — | **not served** |
| `/api/lab/engineering/canvas` | — | **not served** |
| `/api/lab/engineering/canvas/{artifact_id}` | `get` | served |
| `/api/lab/engineering/automations` | `get`, `post` | served |
| `/api/lab/engineering/automations/{automation_id}` | — | not served |
| `/api/lab/engineering/automations/{automation_id}/state` | `post` | served (mutation — deliberately unwired) |
| `/api/lab/engineering/sessions/{session_id}` | `get` | served |
| `/api/knowledge/search` | `post` | served (POST-only) |
| `/api/commune/resonance` | `post` | served (POST-only) |
| `/solspire/buyer-recon/projects/{project_id}` | `get` | served |

**The canvas route is a sibling, not a sub-resource.** This is the load-bearing finding
of this pass: `/engineering/canvas/{artifact_id}` is not `/engineering/artifacts/{id}`,
and the bare canvas root is not a route. Two consequences, both acted on:

1. A `labCanvasRoot: "/api/lab/engineering/canvas"` registry entry would be **rejected**
   by the served-path guard (`test_every_declared_endpoint_is_served_by_the_canonical_app`),
   because the app serves no handler at that exact path.
2. `labCanvas` therefore derives its base from the declared artifacts collection by
   substituting the terminal segment, and the substitution is asserted — a registry
   rename cannot degrade it into a silent no-op that composes a 404.

## 3. Changes in this pass

| File | Change |
|---|---|
| `web/arkadia_console/src/lib/endpoints.ts` | `+labAutomations` entry; `+labCanvas(id)` builder derived from `endpoints.labArtifacts` with a substituted terminal segment; `labSession(id)` unchanged (re-verified) |
| `tests/test_console_endpoint_registry_contract.py` | `+_canvas_route_template` shared derivation; `+test_lab_canvas_builder_derives_from_artifacts_and_encodes`; `+test_lab_canvas_builder_composes_the_served_route`; `+test_registry_declares_the_automations_collection`; `+test_detector_flags_an_artifacts_sub_resource_canvas_path` (negative control) |
| `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` | §1 branch map head refreshed to `616aeae9`; **new §8** — reconciliation record (entries added, requests declined with reasons, recorded-not-repaired findings) |
| `docs/control-plane/parallel-ui/AGENT-01-SHELL.md` | **new** "Measured contract facts" section so the next pass does not re-derive them |

### 3.1 Declined, with the reason

`buyerRecon: "/solspire/buyer-recon"` was drafted and then **reverted**. The owning
workstream explicitly declined a shared constant in its merged evidence, and the path is
handler-derived in `opportunityRadarContract.ts` from `solspire/buyer_recon_router.py`.
Adding it would create a *second* declaration of the same contract — the opposite of
reconciliation. Recorded in §8.2 rather than executed.

## 4. Verification (measured in this environment)

| Check | Command | Result |
|---|---|---|
| Endpoint-registry guard | `pytest tests/test_console_endpoint_registry_contract.py -q -rEf` | **15 passed** (was 11) |
| Focused contract set | `pytest tests/test_console_endpoint_registry_contract.py tests/test_console_shell_nav_contract.py tests/test_canonical_frontend_routing.py tests/test_aeas05_canonical_frontend_acceptance.py tests/test_prism_w4_lab_read_model.py tests/test_prism_w4_arkana_thread_history.py tests/test_lab_artifact_canvas_contract.py tests/test_lab_agent_registry_contract.py tests/test_knowledge_search_boundary.py tests/test_arkana_thread_history_contract.py -q -rEf` | **157 passed** |
| Architecture fitness | `pytest tests/architecture -q -rEf` | **11 passed** |
| Console typecheck | `corepack pnpm exec tsc --noEmit` | exit 0 |
| Console build | `corepack pnpm build` | exit 0 — 74 modules, assets emitted |
| CP10 admission | `scripts/cp10_mutation_boundary_policy.py --judge` on all four paths | PASS (exit 0) |

### 4.1 Live negative controls (both proven on the real file, then restored)

| Control | Mutation of `endpoints.ts` | Result |
|---|---|---|
| NC1 | remove the `labAutomations` entry | **1 failed** (`test_registry_declares_the_automations_collection`), 14 passed |
| NC2 | replace the canvas builder body with the pre-repair composition (append the id to the artifacts collection) | **2 failed** (`test_lab_canvas_builder_composes_the_served_route`, `test_detector_flags_an_artifacts_sub_resource_canvas_path`), 13 passed |

Both were restored byte-identically (`git status --porcelain` clean against the intended
diff) and the guard returned to 15 passed.

### 4.2 Baseline comparison — zero node-set delta

Both trees measured in **this environment**, same command, same dependency set
(`python -m pytest tests/ -q -rEf --continue-on-collection-errors`):

| | `main` @ `f390526a` (worktree) | this branch |
|---|---|---|
| Summary line | 27 failed, 2342 passed, 17 skipped, 1 error | 27 failed, 2346 passed, 17 skipped, 1 error |
| Failing/error nodes | 28 | 28 |
| Node-set sha256 | `521c63e1b75d3369aa6ca40e96c12268bd9c9b633e7584d514dd421e54ecdebe` | same |
| `comm -3` on the sorted `FAILED`/`ERROR` lines | — | **empty** |

The `+4 passed` (2342 → 2346) is exactly this file's added node count:
`--collect-only` → **15** on this branch vs **11** on `main`.

The 28 pre-existing nodes are unchanged and unrepaired: the `weaver.autonomy`
module-vs-package collection error, the two `tests/test_engineering_lab_api.py`
pins (`api/lab_routes.py` is an authority surface — sovereign-only), the
Landing/NodeEntry copy pins, and the `test_voice_*` set (missing optional
dependency in this sandbox). None is caused by, or repaired by, this pass.

## 5. Explicit non-claims

- No merge, no production deployment, no acceptance. Canonical production remains
  `https://arkadia-qzu4.onrender.com` (ADR-016).
- No Vercel deployment was created, promoted, or treated as evidence.
- No feature-owned path (`pages/NovaNetPage.tsx`, `components/opportunities/**`,
  Knowledge OS modules, Arkana/Weaver/Lab components) was edited.
- No backend authority, runtime, or deployment configuration was changed.
- The W4 read surface for automations is **not** mounted here; that is Workstream 4's
  bounded follow-up now that the registry entry exists.

## 6. Next bounded move

Taken in this pass (see §7): the registry guard's detector domain was widened from
`useHydration` arguments to `apiRequest` **literals** — the bounded, decidable half of
the gap recorded in §8.4. The remaining Workstream 1 candidates are the next
shell/navigation gap from the live inventory.

## 7. Second bounded move — widened one-registry detector

`useHydration` always receives its path as a page-local expression, so the original
detector could judge every argument. `apiRequest` does not: its dominant shape is
`useHydration<T>(path, (p) => apiRequest<T>(p))`, where the path is a *callback
parameter* — not a page-local decision, and not decidable without interprocedural
analysis. The widened detector therefore flags **string and template literals only**
and leaves registry-derived expressions, parameters, and local bindings alone by
construction. A literal is precisely the second, unreviewed endpoint contract the guard
exists to catch.

| Check | Result |
|---|---|
| Registry guard | **17 passed** (was 15) |
| Live negative control | planting `apiRequest<VersionInfo>("/api/invented/route")` in `pages/HomePage.tsx` reddens `test_no_page_passes_a_literal_path_to_api_request`; restored byte-identically (`git status --porcelain` shows only the intended test edit) |
| In-source control | `test_request_detector_is_not_trivially_true` pins both polarities — a string literal **and** a template literal must be reported; five legitimate shapes (registry member, three parameter forms, the `useHydration` callback form) must not |

Without the in-source control, a detector that matched nothing would pass on any tree,
including one that inlines every path.

**Deliberately still out of scope:** `ProjectOpportunityRadar`'s `readPath` prop
(Workstream 2's composition) and `KnowledgeGraphPanel`'s `readGraph(path)` (Workstream
3's). Both receive their path from a caller; judging them is not a shell-owned decision.
