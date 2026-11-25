# ARK-ONE-IMPLEMENT-001 — Phase 1: Baseline and Gap Map

**Mission:** build the Arkadia One coherent operating environment.
**Phase:** 1 of N — establish ground truth before any repair.
**Branch:** `feature/arkadia-one-coherent-operating-environment`
**Base `main`:** `aef655423433070e581b42c246fa9298234eb460`
**Status:** draft. No merge, deployment or acceptance claimed. Merge execution is human-only.

This record changes **no application code**. It exists so later phases cite a measurement
instead of a recollection, and so the baseline is reproducible from the branch alone.

---

## 1. Repository and branch identity

| Fact | Value |
| --- | --- |
| Repository | `Arkadia-Oversoul-Prism/Arkadia` (id `1126478357`) |
| Visibility | public, fork `false`, archived `false` |
| Default branch | `main` |
| Canonical `main` SHA at fetch | `aef655423433070e581b42c246fa9298234eb460` |
| `main` head commit | `docs(governance): record GOV-04 activation and queue reconciliation (#724)` |
| `main` commit time | 2026-11-25T21:25:19Z |
| Branch protection on `main` | **disabled** (`protection.enabled: false`, `required_status_checks` level `off`) |

`main` was **not** modified by this mission. The branch was created from the SHA above and
nothing was pushed to `main`.

---

## 2. What was actually read (not previous reports)

Every claim in §4 is traceable to one of these files at `aef65542`:

```
web/arkadia_console/package.json                     scripts + engines.node
web/arkadia_console/src/App.tsx                       composition root, auth threshold
web/arkadia_console/src/lib/surfaces.ts               surface registry (15 surfaces)
web/arkadia_console/src/lib/router.ts                 resolvePath / PATH_ALIASES / LENS_ALIASES
web/arkadia_console/src/lib/endpoints.ts              canonical path map
web/arkadia_console/src/lib/apiClient.ts              bearer, failure classification
web/arkadia_console/src/lib/capabilities.ts           capability registry + dispatchable gate
web/arkadia_console/src/lib/surfaceChrome.tsx         rail/status ownership
web/arkadia_console/src/components/Shell.tsx          the one navigation column
web/arkadia_console/src/pages/ArkanaPage.tsx          475 lines
web/arkadia_console/src/pages/SolSpirePage.tsx        148 lines
web/arkadia_console/src/pages/ProjectsPage.tsx        236 lines
web/arkadia_console/src/pages/WorkspacePage.tsx       731 lines
web/arkadia_console/src/pages/WeaverPage.tsx           28 lines
web/arkadia_console/src/pages/EngineeringLabPage.tsx  103 lines
api/canvas_routes.py                                  AO-006 canvas (GET only)
api/main.py                                           include_router(_canvas_router) @2137
.github/workflows/prism-console-contract.yml          the console gate
AGENTS.md                                             build/test conventions
conftest.py, pytest.ini, requirements.txt             test configuration
```

---

## 3. Test baseline — exact commands and results

Run in a **full clone** (`git fetch --unshallow`, 2707 commits) at `aef65542`, with the
repository's own declared toolchain: `pnpm@10.26.1` (from `package.json` `packageManager`)
and Python 3.11 with `requirements.txt`.

| # | Command | Result |
| --- | --- | --- |
| 1 | `PYTHONPATH=. python3 -m pytest tests/architecture -q` | **11 passed** in 13.39s |
| 2 | `cd web/arkadia_console && pnpm install --frozen-lockfile` | **success** (lockfile honoured, no resolution changes) |
| 3 | `cd web/arkadia_console && pnpm exec vitest run` | **8 files / 61 tests passed** in 25.94s |
| 4 | `cd web/arkadia_console && pnpm exec tsc --noEmit` | **clean** (no output, exit 0) |
| 5 | `cd web/arkadia_console && pnpm exec vite build` | **success** — 170 modules, `dist/assets/index-CYGHeCpJ.js` 425.15 kB (gzip 111.33 kB) |
| 6 | `python3 scripts/console_contract_domain.py` | **74** test targets derived |
| 7 | `PYTHONPATH=. python3 -m pytest -q $(python3 scripts/console_contract_domain.py)` | **151 failed, 1073 passed, 64 errors** in 61.60s |

### 3.1 Correction to my own first measurement

The first run of check 7 was taken in a **`--depth 50` shallow clone** and read
`153 failed, 1071 passed, 64 errors`. Two nodes failed only because history was absent:

```
FAILED tests/test_console_posture_currency.py
  AssertionError: MAP_DERIVED_FROM=ae847dd is not a commit in this repository
FAILED tests/test_lane_instruction_doc_currency.py
  AssertionError: ['lane 1: PR #423 cannot be adjudicated -- merge commit 972c3423 is not
                   in this clone (shallow checkout?); liveness is UNKNOWN, not a pass']
```

After `git fetch --unshallow` both pass, and the reading becomes **151 failed / 1073 passed /
64 errors**. The shallow figures are recorded here rather than discarded because the gate
itself fetches `fetch-depth: 0` for exactly this reason: a depth-1 checkout turns a wiring
defect into what reads as a product defect.

### 3.2 The failures are attributable, not assumed

Checks 1–6 are green. Check 7's failures cluster into **two measured classes**, and neither is
an Arkadia One behaviour defect:

**(a) Node-version capability gap — the dominant class.** `package.json` pins
`engines.node: "24.x"`; `prism-console-contract.yml` installs `node-version: 24`. This sandbox
has **Node 20.20.2**. Node 24 loads a `.ts` ESM module directly; Node 20 does not:

```
TypeError [ERR_UNKNOWN_FILE_EXTENSION]: Unknown file extension ".ts"
  for .../src/components/opportunities/opportunityRadarContract.ts
  code: 'ERR_UNKNOWN_FILE_EXTENSION'    Node.js v20.20.2
tests/test_prism_opportunity_entry_flow.py:604: AssertionError
```

and, for the router guard:

```
AssertionError: router evaluation failed: [eval]:10
  SyntaxError: Unexpected identifier 'SurfaceId'
tests/test_console_shell_nav_contract.py:447
```

Every guard that spawns `node` against TypeScript sources fails this way. **This is an
environment gap in the measuring sandbox, not branch debt** — the CI gate installs Node 24
before running the same suite.

**(b) Pre-existing `main` debt already attributed in open PRs.** Several failing files are
being repaired by currently-open draft PRs (e.g. `test_prism_w4_lab_pr_state.py` by #683,
the GOV-04 literal pins by #725, `test_lab_repository_surface_contract.py` by #680). These
fail identically on unmodified `main`; they are not introduced here.

**Consequence for this mission:** the reliable, version-independent baseline is checks 1–6
plus the vitest/tsc/build triad, all green. Check 7's absolute count is **not** usable as a
pass/fail oracle from Node 20 and is recorded as an environment measurement. Phase 2 should
either run it under Node 24 or scope it to the non-Node guards.

---

## 4. Gap map

Legend — `EXISTS_AND_VERIFIED` (capability present and exercised by a green check) ·
`EXISTS_BUT_BROKEN` (present, measurably failing) · `MISSING` (no implementation) ·
`UNSAFE` (present and reaches an authority/credential boundary it should not) ·
`UNVERIFIED` (present; no observation was possible in this environment).

### 4.1 Arkana

| # | Capability | Location | Verified state | Required correction | Relevant test | Risk / dependency |
| --- | --- | --- | --- | --- | --- | --- |
| A1 | Four operating modes (research / reason / create / plan) with per-mode prompt guidance | `pages/ArkanaPage.tsx:31-45`, `MODE_GUIDANCE` | **EXISTS_AND_VERIFIED** — mode select, `aria-pressed`, placeholder, guidance string all wired | none | vitest `ArkanaOverlay.test.tsx` (16) | — |
| A2 | Streaming reply with abort, regenerate, copy, read-aloud | `pages/ArkanaPage.tsx` + `lib/arkana.ts`, `components/ReadAloud.tsx` | **EXISTS_AND_VERIFIED** — `AbortController` per turn, `isAbortError` classified, partial content kept with status `Stopped` | none | vitest; `test_arkana_mode_workspace_contract.py` | SSE transport correctness not observed (§4.1 A7) |
| A3 | Research mode retrieves real corpus evidence and keeps it visible | `ArkanaPage.runTurn` → `endpoints.knowledgeSearch` | **EXISTS_AND_VERIFIED** — shape is validated (`isKnowledgeSearchData`), the turn is *refused* with an explicit "no records" message rather than synthesising when empty | none | `test_knowledge_status_read_boundary.py` (errors on Node 20) | depends on Knowledge OS corpus |
| A4 | Provenance panel per turn | `components/arkana/ArkanaProvenancePanel.tsx`, `arkanaProvenanceContract.ts` | **EXISTS_AND_VERIFIED** — rendered only when `turn.provenance` is present; never fabricated | none | vitest | — |
| A5 | Conversation-history rail in the one shell | `ArkanaThreadHistory` via `useSurfaceChrome` | **EXISTS_AND_VERIFIED** — the *same* component the Workspace mounts; the rail is published, not self-rendered | none | `surfaceChrome.test.tsx` (10) | — |
| A6 | External web research | `ArkanaPage.tsx` research note | **MISSING — declared, not a defect.** The surface states it in-line: *"External web research is not enabled in this mode."* | product decision, not a repair | — | if added, must not claim sources it did not fetch |
| A7 | Streaming transport correctness (`/api/commune/resonance/stream`) | `lib/endpoints.ts:arkanaResonanceStream` | **UNVERIFIED** — no live backend was exercised from this sandbox; the JSON path is authoritative by design | needs a live observation, not a code change | — | blocked on a running backend |

### 4.2 SolSpire

| # | Capability | Location | Verified state | Required correction | Relevant test | Risk / dependency |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | Lens strip addressable at `/enterprise/<lens>`, strip and address bar agreeing | `pages/SolSpirePage.tsx:56-110` + `components/SurfaceLenses.tsx` | **EXISTS_AND_VERIFIED** — driven by the shared `SurfaceLenses`, one lens list | none | `SolspireReconciliation.test.tsx` (8) | — |
| S2 | Field lens: real project field through Opportunity Radar + control plane | `SolSpirePage.tsx` `section === "field"` | **EXISTS_AND_VERIFIED** — reads `endpoints.solspireProjects`; when the read is not ready it says so rather than showing an empty board | none | `test_prism_solspire_control_plane.py`, `test_prism_opportunity_entry_flow.py` | latter errors on Node 20 |
| S3 | `enterprise` lens | `SolSpirePage.tsx` → `NotYetWired` | **MISSING — declared.** Names `/solspire/enterprise/workspaces` and states no console projection exists | build the projection, or keep the disclosure | `test_prism_solspire_control_plane.py` pins advertised contracts | `enterprise_router.py` exists; no UI |
| S4 | `voice` lens | same | **MISSING — declared.** Names `/solspire/voice/events` | same | same | governed chain has no console surface |
| S5 | `proposals` lens | same | **MISSING — declared**, and deliberately: *a decision is a human act on the authority chain* | same | same | offering a control here would be `UNSAFE` |
| S6 | Unknown section | `!LENS_IDS.has(section)` | **EXISTS_AND_VERIFIED** — lists the reconciled lenses instead of silently showing the field view | none | `SolspireReconciliation.test.tsx` | — |

### 4.3 Projects

| # | Capability | Location | Verified state | Required correction | Relevant test | Risk / dependency |
| --- | --- | --- | --- | --- | --- | --- |
| P1 | Project list from the one shared read | `pages/ProjectsPage.tsx` via `useProjectContext` | **EXISTS_AND_VERIFIED** — no second request; `projects.state === "ready"` gated | none | — | shared with Workspace |
| P2 | Filter with honest empty / no-match states | `ProjectsPage.tsx:186-206` | **EXISTS_AND_VERIFIED** — three distinct states (`projects-empty`, `projects-no-match`, list), differentiated from a failed read | none | — | — |
| P3 | Per-project detail + tasks / files / events | `ProjectsPage.tsx` `ProjectDetail`, `RecordList` | **EXISTS_AND_VERIFIED** — `asItems` returns `null` for a non-list shape and renders `NotYetWired` rather than inventing a list | none | `test_knowledge_projects_boundary.py` | sub-resources are `additionalProperties: true` in OpenAPI, so no schema is assumed |
| P4 | Opening a project *selects* it, shared with Arkana and the Lab | `ProjectsPage.tsx` `useEffect` → `selectProject` | **EXISTS_AND_VERIFIED** — `Discuss in Arkana` / `Open Engineering Lab` land on the same project | none | — | — |
| P5 | Runtime-context canvas not forked from Solariun | imports `ProjectRuntimeCanvas` | **EXISTS_AND_VERIFIED** — one component, two surfaces | none | `test_prism_solariun_runtime_context_ui.py` | — |

### 4.4 Workspace

| # | Capability | Location | Verified state | Required correction | Relevant test | Risk / dependency |
| --- | --- | --- | --- | --- | --- | --- |
| W1 | One conversation reaching every capability, `@token` scoped | `pages/WorkspacePage.tsx` `parseToken` | **EXISTS_AND_VERIFIED** — and *not* merely by hiding buttons: a hand-typed `@authorize` is refused because `dispatchable === false` is filtered in `parseToken`, not only in the render | none | `test_arkana_mode_workspace_contract.py` | — |
| W2 | Capability registry cannot advertise an unwired route | `lib/capabilities.ts` | **EXISTS_AND_VERIFIED** — each entry names endpoint + the surface that already reads it; `COMPOSER_TOKENS` requires `verified && dispatchable !== false` | none | `capabilities.test.ts` | — |
| W3 | Turn persisted to the project thread; failure surfaced, never swallowed | `lib/projectConversation.ts` + `persistTurn` | **EXISTS_AND_VERIFIED** — a failure sets `threadNote` with status + kind; the turn stays visible | none | — | server bridge `solspire/conversation_bridge.py` |
| W4 | Mission-lifecycle strip driven by the canonical chain | `lib/missionLifecycle.ts`, `projectLifecycle` | **EXISTS_AND_VERIFIED** — Accept/Release unavailable *by construction* (no backend record); a stage with no evidence renders unknown, not complete | none | `test_mission_lifecycle_adapter_contract.py` | needs `node_modules/typescript` (present here → passes) |
| W5 | Weaver + Lab composed into the workspace, not duplicated | `WorkspacePage.tsx` `panels` | **EXISTS_AND_VERIFIED** — `ApprovalLedger`, `LabRepositoryContext`, `LabSessionList` imported, each keeping its own reads | none | `surfaceChrome.test.tsx` | — |
| W6 | One rail, one header | `lib/surfaceChrome.tsx`, `components/Shell.tsx` | **EXISTS_AND_VERIFIED** — owned publication with a monotonic owner token; dedupe by value; stale cleanup cannot erase a successor's chrome | none — the AO4-01 loop is genuinely repaired | `surfaceChrome.test.tsx` (10), `test_console_shell_nav_contract.py` | the nav guard errors on Node 20 only |

### 4.5 Weaver

| # | Capability | Location | Verified state | Required correction | Relevant test | Risk / dependency |
| --- | --- | --- | --- | --- | --- | --- |
| V1 | Read models: approval ledger, work loop, session ladder, deployed agents | `pages/WeaverPage.tsx` → `WeaverOrchestration` | **EXISTS_AND_VERIFIED** — composes real reads | none | `test_prism_w4_weaver_approval_ledger.py` (fails on Node 20) | — |
| V2 | Authorize / execute / transition / run-agent | `WeaverPage.tsx` → `NotYetWired` | **MISSING — deliberately, and correctly.** The surface states: *"an approval is not an execution, and a run at the review boundary is not acceptance."* Wiring these here would be `UNSAFE` | keep it unwired; the acts belong to the Lab `MissionWorkspace` | same | human authority boundary |
| V3 | Cross-surface orchestration counts | `components/weaver/CanvasOrchestration.tsx:342` → `endpoints.canvas` | **EXISTS_AND_VERIFIED** — vitest asserts server-reported counts render | none | `CanvasOrchestration.test.tsx` (6) | API is GET-only (`api/canvas_routes.py`) |

### 4.6 Engineering Lab

| # | Capability | Location | Verified state | Required correction | Relevant test | Risk / dependency |
| --- | --- | --- | --- | --- | --- | --- |
| L1 | Mission workspace is primary; evidence collapsed | `pages/EngineeringLabPage.tsx` — `MissionWorkspace` above `<details>` | **EXISTS_AND_VERIFIED** | none | `exercise_mission_workspace.py` (gate) | — |
| L2 | Diagnostics: overview, operational surfaces, execution loop, N-ATLAS provider | `EngineeringLabPage.tsx` + `components/lab/*` | **EXISTS_AND_VERIFIED** — `readLoopStages` returns `[]` for a malformed payload, so no stage is inferred | none | — | — |
| L3 | Capability disclosure (what the Lab can and cannot do) | `LabCapabilityDisclosure.tsx` | **EXISTS_AND_VERIFIED** | none | `test_lab_repository_surface_contract.py` (fails: Node 20) | — |
| L4 | Lab PR-state read | `LabPrState.tsx`, `labPrState.ts`, `api/lab_routes.pr_state` | **UNVERIFIED** — the handler selects its branch from ambient `GITHUB_TOKEN`; this sandbox had none. The no-token premise is *pinned* by `test_prism_w4_lab_pr_state.py`, which is itself repaired by open PR **#683** | land #683; do not re-repair here | `test_prism_w4_lab_pr_state.py` | credential-dependent |

### 4.7 Cross-surface findings

| # | Finding | State | Note |
| --- | --- | --- | --- |
| X1 | `endpoints.canvas` declared but consumed by exactly one surface | **UNVERIFIED** | two *files* reference it (`CanvasOrchestration.tsx`, `endpoints.ts`); that is not a defect, but the canvas is not yet the unifying read Phase 2 will need it to be |
| X2 | Module docstring in `AGENTS.md` still points at `web/public_prism/` and a 2600+ line `api/main.py` | **EXISTS_BUT_BROKEN (documentation)** | the active console is `web/arkadia_console`, `api/main.py` is held at a 2600-line budget by extracting routers (e.g. `canvas_routes.py`). An agent following `AGENTS.md` edits a path that is no longer the product | doc-only correction; no runtime effect |
| X3 | `main` has no branch protection and no ruleset | **UNSAFE (platform posture)** | measured in open PR **#726**; provider/configuration decisions are reserved to the sovereign, so this mission does not change it |
| X4 | Console-contract domain requires Node 24 | **UNVERIFIED (environment)** | see §3.2(a). The suite is green under the pinned toolchain in CI; it cannot be judged from Node 20 |

---

## 5. What Phase 1 deliberately did not do

- No application code, test, workflow, governance document, credential or deployment
  configuration was modified.
- The failing guards were **not** repaired. Repairing `test_prism_w4_lab_pr_state.py` here
  would collide with open PR **#683**, which owns it — that is the composition defect this
  phase exists to avoid.
- No search for the missing historical 75-file package.
- No merge, deployment, force-push, history rewrite, branch-protection or required-check
  change. No push to `main`.

## 6. Dependencies for Phase 2

1. **Node 24** in the measuring environment, or scope the domain run to the non-Node guards.
   Without it every TypeScript-adapter guard is uninformative.
2. **Open repair PRs** own several failing nodes (notably #683 → `test_prism_w4_lab_pr_state.py`;
   #725 → the GOV-04 literal pins). Land or reconcile those before attributing the nodes here.
3. **A live backend** for the two `UNVERIFIED` items (A7 SSE, L4 PR-state with a token).
4. **`X2`** (stale `AGENTS.md` paths) should be corrected early in Phase 2: it misdirects any
   agent that reads it before the code.
