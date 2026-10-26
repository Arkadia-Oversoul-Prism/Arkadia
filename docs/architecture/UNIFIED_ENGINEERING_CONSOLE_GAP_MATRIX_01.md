# Unified Engineering Console — Source-to-Requirement Gap Matrix 01

**Artifact:** UEC-GAP-01  
**Status:** INVESTIGATION IN PROGRESS — source-level evidence matrix  
**Branch:** `architecture/unified-engineering-console-spec-01`  
**Baseline reviewed:** `main` at `36f53be22d753ffe269f05cbf3fb39212f744207`  
**Prior architecture spec:** `docs/architecture/UNIFIED_ENGINEERING_CONSOLE_SPEC_01.md`  
**Scope:** inspect existing implementation and tests; propose no application-code changes in this pass. No merge, deployment, production configuration, credentials, Notion mutation, or corpus-metric exposure.

## 1. Executive finding

The repository already contains a meaningful portion of the proposed unified console and governed read-only engineering workflow. The first implementation should therefore be **a reconciliation and integration task, not a greenfield build**.

Confirmed at source level:
- one declared console shell and surface registry already includes Engineering Lab, Arkana, Solariun, SolSpire, Knowledge OS, and Weaver;
- Engineering Lab has a broad authenticated API, native session/run/agent models, bounded sandbox, model gateway, events, store, artifact canvas, and a multi-turn agent loop;
- the current Engineering Lab page is intentionally read-mostly and explicitly leaves authorization/execution acts unwired;
- tests already cover route boundaries, sandbox read-only defaults, owner scoping, evidence linkage, artifact rendering, state non-collapse, and the distinction between review and human acceptance;
- the older Weaver worker contract exists alongside the newer native Lab runtime. They are complementary contracts, but the integration seam and source-of-truth mapping must be documented rather than assumed.

Not yet established:
- a complete end-to-end run of the selected workflow on this exact baseline;
- the full runtime auth matrix by endpoint with live HTTP responses;
- whether the frontend and backend contract tests all pass at this baseline;
- whether the existing native agent loop can perform the desired investigation without adding any persistence or external side effect beyond its explicitly scoped event/evidence recording;
- whether any OpenHands or OpenClaw-family runtime is installed or integrated.

**No application implementation is authorized or proposed by this matrix.** This is a source review, not a runtime acceptance report.

## 2. Status vocabulary

- **PRESENT:** source implementation and relevant contract/tests were found.
- **PARTIAL:** a real implementation exists, but the requirement is broader, split across surfaces, or not yet end-to-end verified.
- **GAP:** the reviewed evidence does not show the required capability.
- **RISK:** a boundary or ambiguity needs explicit validation before integration.
- **UNKNOWN:** evidence was not sufficient to claim either presence or absence.

A test's existence is evidence of intended contract coverage, not proof that the test passed in this review. No CI suite was run as part of this source-only pass.

## 3. Source-to-requirement matrix

| ID | Requirement | Existing source evidence | Status | Finding / next evidence |
|---|---|---|---|---|
| UEC-01 | One canonical frontend shell | `web/arkadia_console/src/App.tsx`, `components/Shell.tsx`, `lib/router.ts` | PRESENT | Reuse the existing composition root and router; do not create a second shell. Confirm all paths against the actual deployed artifact only in a separately authorized observation pass. |
| UEC-02 | One declared surface registry | `web/arkadia_console/src/lib/surfaces.ts` declares home, novanet, arkana, solariun, engineering-lab, solspire, knowledge, weaver, about, login. | PRESENT | Registry is the current surface authority. New tabs should map to existing product boundaries or be justified by evidence; do not create alias surfaces for the same capability. |
| UEC-03 | Existing Engineering Lab read model | `pages/EngineeringLabPage.tsx`, `LabOperationalSurfaces.tsx`, `LabSessionList.tsx`, `LabAuthorityReadings.tsx` | PRESENT / PARTIAL | Page renders overview, loop, provider status, authority readings, sessions, artifacts, agent registry, gateway, automation grammar. It is not yet a complete mission investigation/report workflow. |
| UEC-04 | Complete Lab route inventory | `api/lab_routes.py` | PRESENT at source level | 27 route decorators found in the file; complete method/path inventory is in §4. Must keep this inventory synced with router tests. |
| UEC-05 | Authenticated-by-default Lab routes | `require_lab_auth`, router dependency `Depends(require_lab_auth)`, `tests/test_engineering_lab_api.py` | PRESENT with explicit exceptions | The router is authenticated by default; exactly two paths are explicitly public for N-ATLAS tester flow. Test endpoint-level effective auth and ownership, not just decorator presence. |
| UEC-06 | Owner/workspace-scoped records | `lab/engineering_lab/store.py`, `models.py`, session/project checks in `api/lab_routes.py`; substrate and artifact tests | PRESENT | Reuse Firebase UID and canonical SolSpire workspace/project identity. Add no parallel identity/workspace model. Verify every new projection preserves owner filtering. |
| UEC-07 | Explicit authorization records | `contracts.py`, `runtime.py`, `POST .../authorize`, substrate and authority tests | PRESENT; not a read-only action | Human-originated authorization is a separate state transition. The selected workflow must not call this endpoint or create authorization records. |
| UEC-08 | Read-only sandbox primitives | `sandbox.py`: default policy, path resolution, command allowlist, read-only Git subcommands, sanitized environment; `tests/test_engineering_lab_substrate.py` | PRESENT at unit-contract level | Reuse the sandbox. Before dispatch, verify actual policy values, root binding, network policy, and that the chosen operation set excludes writes. |
| UEC-09 | Read-only multi-turn worker | `agent_loop.py`, `tools.py`, runtime tool mapping | PRESENT / PARTIAL | Loop supports bounded MODEL → TOOL → observation turns and terminal states. Need a focused audit of tool registry + effective permissions to establish a strictly read-only configuration for this mission. Do not infer safety from the loop docstring alone. |
| UEC-10 | Weaver engineering worker contract | `weaver/engineering_worker.py`, `weaver/execution_adapter.py`, `docs/control-plane/WORKER_CONTRACT.md` | PRESENT | Worker lifecycle stops at review; default `NullExecutionAdapter` refuses live execution. This is a separate contract from the native Lab agent loop. Map the intended relationship before choosing a single entry path. |
| UEC-11 | Evidence schema with provenance | `lab/engineering_lab/contracts.py:EvidenceRecord`, `models.py:AgentRun`, `artifacts.py:ArtifactView`, `events.py`, `store.py` | PRESENT / PARTIAL | Existing types already link subject, workspace, session, run, agent, artifact, and evidence references. Map the proposed finding schema to these types; do not create a second evidence database or generic provenance field without demonstrating a missing field. |
| UEC-12 | Event continuity | Lab `AgentEvent` stream in `events.py`; SolSpire `WorkEvent`; Weaver `OperationalEvent` | PRESENT as distinct record classes | Lab event persistence is best-effort and reports a persistence error on the emitted record; do not represent a live event as durably recorded unless persistence was confirmed. Preserve all event namespaces and source identity. |
| UEC-13 | Evidence/artifact display | `artifacts.py`, `LabArtifactCanvas.tsx`; `tests/test_lab_artifact_canvas_contract.py`, `tests/test_prism_w4_lab_read_model.py` | PRESENT | Renderer map and truthful unavailable states exist. Reuse the current canvas and renderer map. UI affordances are not execution or authorization. |
| UEC-14 | Run/evidence trace integrity | Lab run/session view, run trace component/projection, `tests/test_lab_run_trace_contract.py`, `tests/test_prism_w4_run_evidence_trace.py` | PRESENT | Existing tests explicitly cover dangling, unreferenced, duplicate, unattributed, and unverified evidence; reuse this trace rather than adding a new timeline ledger. |
| UEC-15 | Review distinct from acceptance | `contracts.py` state machine; `labRunTrace.ts`; trace/read-model tests | PRESENT | `READY_FOR_REVIEW` does not imply human acceptance; `COMPLETED` is a human terminal. Preserve this state vocabulary in every new projection. |
| UEC-16 | Read-only mission report | No single canonical mission-investigation report contract identified in reviewed sources | GAP / UNKNOWN | First prove whether existing artifact/evidence contracts can represent the report. If not, propose a projection over existing records before adding a new persisted model. |
| UEC-17 | Route-level negative auth tests | `tests/test_engineering_lab_api.py`, `tests/test_authority_boundary.py`, substrate tests | PARTIAL | Relevant tests exist, but this review did not execute them and did not map every route to an observed 401/403/owner isolation result. Produce route × auth × side-effect table from test bodies and run results before implementation. |
| UEC-18 | Console/backend endpoint mapping | `web/arkadia_console/src/lib/endpoints.ts` plus Lab components | PRESENT / PARTIAL | Canonical endpoint map exists. Audit every Lab component request against served GET routes and identify unused, duplicated, or mutation-capable endpoint references. |
| UEC-19 | One mission/run control plane | Native Lab runtime plus Weaver worker/router/adapter and SolSpire workspace | PARTIAL / RISK | Multiple established subsystems exist. Their existence is not necessarily duplication; the gap is a verified mapping between them. Do not add another scheduler, event bus, identity, store, or authority layer. |
| UEC-20 | External runtime adapters | Existing Lab adapter descriptors and provider gateway; no evidence in reviewed files that OpenHands/OpenClaw-family is wired as a production adapter | UNKNOWN | Verify exact project identity, version, installation/configuration, license, permission envelope, network boundary, and refusal tests before any integration proposal. |
| UEC-21 | Strictly read-only first workflow | Sandbox/read tools exist, but endpoint inventory includes POST routes that create sessions, authorize, execute, change state, create automations, run N-ATLAS, resolve voice, or run the agent loop | PARTIAL | Design the workflow using GET observations and a separately audited read-only worker configuration. Do not call mutation-shaped routes as a shortcut. If the mission requires a durable report artifact, obtain a separate decision on where/how to write it. |
| UEC-22 | Exact baseline and honest states | Git refs, evidence records, gateway status descriptors, tests for truthful unavailable states | PRESENT as primitives | Every result must include exact SHA, time, source, and status. No provider/configuration claim should be inferred from code defaults or stale deployment evidence. |
| UEC-23 | Production and release boundary | AEAS v0.1.1, `contracts.py` human-only states, API route comments/tests | PRESENT as documented contract | This work does not merge or deploy. No production configuration/security fix is implied or authorized by the gap matrix. |

## 4. Complete Lab API route inventory (source-level)

Source: `api/lab_routes.py` at the reviewed baseline. Router prefix is `/api/lab`.

### GET routes — observational candidates, still subject to auth and side-effect review

| Path | Observed role | Read-only workflow suitability |
|---|---|---|
| `GET /overview` | Deterministic Lab substrate overview | Candidate; verify its contents and cost. |
| `GET /engineering/overview` | Runtime operational overview, integrations, Android, voice, automation grammar | Candidate; authenticated; verify no hidden side effects in report helpers. |
| `GET /engineering/loop` | Canonical loop stages | Candidate. |
| `GET /engineering/agents` | Subject-scoped agent list | Candidate. |
| `GET /engineering/sessions` | Subject-scoped session list | Candidate. |
| `GET /engineering/sessions/{session_id}` | Subject-scoped session view | Candidate; inspect run/evidence joins and missing-state handling. |
| `GET /engineering/artifacts` | Subject-scoped artifact list; optional session filter | Candidate. |
| `GET /engineering/canvas/{artifact_id}` | Subject-scoped artifact renderer descriptor | Candidate. |
| `GET /engineering/automations` | Subject-scoped automations and grammar | Candidate. |
| `GET /engineering/gateway` | Provider/gateway descriptor | Candidate; reports configuration/effective status, not proof of live successful inference. |
| `GET /engineering/n-atlas/catalog` | N-ATLAS descriptor and boundary | Public exception; do not treat as a general identity or provider integration. |
| `GET /engineering/integrations` | Integration descriptors | Candidate; inspect whether descriptors read only local configuration. |
| `GET /engineering/android` | Android capability report | Candidate. |
| `GET /engineering/android/session/{session_id}` | Session projection | Candidate; authenticated and session-scoped. |
| `GET /engineering/voice` | Voice boundary report | Candidate. |
| `GET /engineering/pr/{number}` | Read-only PR state | Candidate only if external GitHub read/network access is separately within the mission's approved envelope; truthful unavailable state required. |

The route-level auth dependency covers these routes except the explicitly public N-ATLAS catalog path. A GET method is not, by itself, proof of no side effects; helper implementations still need inspection.

### POST routes — excluded from the initial read-only mission

| Path | Observed role | Why excluded |
|---|---|---|
| `POST /engineering/agents` | Register agent in store | Persistent mutation. |
| `POST /engineering/sessions` | Open session | Persistent state creation. |
| `POST /engineering/sessions/{session_id}/authorize` | Record human-originated authorization and transition | Consequential authority record; expressly out of scope. |
| `POST /engineering/sessions/{session_id}/execute` | Execute bounded task | May run tools and create evidence/artifacts; not read-only by method or contract. |
| `POST /engineering/sessions/{session_id}/transition` | Change session state | Persistent state mutation. |
| `POST /engineering/automations` | Create automation | Persistent mutation and future execution risk. |
| `POST /engineering/automations/{automation_id}/state` | Change automation state | Persistent mutation. |
| `POST /engineering/n-atlas/test-session` | Create anonymous tester workspace/agent/session/authorization and mint scoped tester token | Public exception with state creation and credential issuance; explicitly excluded. |
| `POST /engineering/n-atlas/run` | Invoke provider and record run/event/evidence | External model execution plus persistence; excluded. |
| `POST /engineering/voice/resolve` | Resolve voice command | May initiate intent resolution or related work; excluded until body and call graph are proven pure/read-only. |
| `POST /engineering/sessions/{session_id}/run-agent` | Run bounded native agent loop | Execution, model calls, tool calls, and event persistence; excluded from the first route-only pass. It may be considered only after a separate worker/tool-envelope audit and explicit authorization. |

### Public-route exceptions

The source defines `_PUBLIC_NATLAS_PATHS` as exactly:
- `/api/lab/engineering/n-atlas/catalog`
- `/api/lab/engineering/n-atlas/test-session`

The first is a read-only descriptor path. The second creates a tester workspace/session, records scoped authorization, and returns a short-lived tester token. This distinction is important: **the route is intentionally public, but the public capability is narrow; it must not become a general console identity bypass.**

## 5. Authorization and execution boundary matrix

| Boundary | Existing mechanism | What it proves | What remains to verify |
|---|---|---|---|
| Identity | `require_auth` + verified UID; SolSpire workspace/project owner checks | Authenticated identity and scoped ownership are first-class | Route-by-route HTTP tests and all new projection joins. |
| Capability | `ROLE_CAPABILITIES`, `AgentToolAccess`, tool registry | Declared role/tool ceiling | Exact effective tool set at dispatch for this mission; never assume role alone is enough. |
| Human authorization | Authorization record, scope ref, operations, duration; runtime checks | A human-originated authorization can be linked to a session | Read-only mission should avoid creating authorization state; determine whether observation-only access needs a separate policy or only existing GET reads. |
| Sandbox | Path policy, command allowlist, read-only Git subcommand set, sanitized environment | There are enforcement primitives and tests | Confirm actual policy/root/network values and no shell escape for the selected exact command set. |
| Worker lifecycle | Native agent loop terminals; Weaver lifecycle ends at review | Bounded stop states and no implicit merge/deploy | Establish which worker path is canonical for the first workflow; compare event/evidence semantics. |
| Evidence | EvidenceRecord, AgentRun refs, ArtifactView, event records | Traceable record primitives exist | Audit mandatory fields, persistence failure semantics, and end-to-end joins for a read-only report. |
| Acceptance | `READY_FOR_REVIEW` distinct from human `COMPLETED` | Review is not acceptance | Ensure the UI never labels a successful read-only run as accepted/verified without corresponding evidence. |
| Release | AEAS and API contract prohibit autonomous merge/deploy | Release is outside the worker's authority | No release action is part of this branch scope. |

## 6. Existing read-only worker path: evidence and unresolved questions

### Present primitives

1. `lab/engineering_lab/agent_loop.py` implements a bounded multi-turn loop and terminal states `DONE`, `BLOCKED`, `ERROR`, `HUMAN_AUTHORIZATION_REQUIRED`.
2. `lab/engineering_lab/tools.py` exposes filesystem list/read, candidate-edit proposal, bounded terminal, Git status and Git diff tool specs. The candidate-edit tool is described as a review-only proposal and is marked non-mutating, but must remain excluded from this investigation's tool allowlist to keep the workflow strictly observational.
3. `lab/engineering_lab/sandbox.py` defines read-only defaults, path escape checks, command allowlists, a constrained Git subcommand set, sanitized environment, and operation evidence.
4. `runtime.py` derives effective tools from capability ceiling ∩ agent tool envelope ∩ authorization operations. Missing authorization is intended to mean no tools for consequential runs.
5. `weaver/engineering_worker.py` defines WAKE → LOAD → VALIDATE → ROUTE → PLAN → EXECUTE → CHECKPOINT → VERIFY → REPORT → TERMINATE and defaults to `NullExecutionAdapter`; its attention outbox and optional delivery path must be considered if this worker is used.
6. `events.py` appends Lab events durably on a best-effort basis and records persistence errors on the emitted record. A live event alone is not proof of durable evidence.
7. `store.py` reuses the canonical SolSpire SQLite database and owner-scopes records. It is not a new store to reproduce in the console.

### Required follow-up inspection before code

- Read the entire `ToolRegistry.invoke` path and its sandbox implementation for all tools that could be exposed to the investigation.
- Read the full `execute_bounded_task` and `run-agent` route call graphs, including when they write session/run/event/evidence/artifact rows.
- Establish whether a no-session, no-write, read-only repository scan can use an existing session without changing state, or whether a new session is necessarily persisted. Do not create a session until that side effect is explicitly included in scope.
- Inspect `api/lab_routes.py` PR route's outbound request behavior and timeouts; do not enable external network merely because the endpoint is GET.
- Inspect test fixtures and exact negative assertions in the Lab API, sandbox, agent loop, and authority tests; then run focused tests only in an approved development environment.
- Compare native Lab run/evidence records with Weaver's task/checkpoint/evidence records and identify the authoritative record for each field.

## 7. Duplicate versus complementary components

| Components | Assessment | Rule |
|---|---|---|
| `App.tsx` / `Shell.tsx` / `surfaces.ts` | Complementary parts of one console shell | Preserve one router and one registry. |
| Engineering Lab page / Lab components | A composed read model, not separate product shells | Extend the page and current components where needed. |
| Lab `AgentEvent` / SolSpire `WorkEvent` / Weaver `OperationalEvent` | Distinct semantics, not interchangeable duplicates | Unified timeline may project them together only with original type, source, ID, sequence, and provenance intact. |
| Native Lab runtime / Weaver engineering worker | Overlapping responsibilities but different contracts and execution seams | Mapping audit required; do not introduce a third worker, scheduler, or execution adapter stack. |
| Lab store / SolSpire shared SQLite database | Lab tables in the canonical shared persistence substrate | No new database or second evidence store. |
| Lab artifact canvas / existing Arkadia renderers | Existing renderer reuse contract | No competing artifact renderer stack. |
| Lab provider gateway / possible ChatGPT or OpenHands integration | Existing provider abstraction plus candidate external adapters | Verify capability and policy fit before adding another router or provider-selection layer. |
| Solariun / SolSpire / Knowledge OS | Distinct product/workspace boundaries already declared in the surface registry | Do not merge their ownership models into a new universal workspace object. |

## 8. First-workflow requirements: revised, evidence-led

The first mission should be implemented, if later authorized, as a **read-only projection over existing repository and Lab evidence**, not as a new mission database.

Required output fields should first be mapped to existing types:
- exact repo/ref/SHA and observation time;
- source path/URL and observed value/excerpt or digest;
- finding state: observed, derived, unknown, blocked, contradicted;
- link to existing session/run/event/artifact/evidence IDs when they already exist;
- collection method and limits;
- explicit unresolved items and negative results.

If the investigation itself needs a persisted artifact, the storage mechanism is a separate design decision: first check whether an existing artifact/report path supports this safely. This source-review pass has not created an investigation session, run, artifact, external task, or Notion record.

## 9. Next evidence gates

1. **Route/auth matrix:** extract each Lab route's method, authentication behavior, owner scope, state side effects, and corresponding test. Distinguish source assertions from executed test results.
2. **Tool-envelope audit:** prove the exact read-only tool set and path/command/network restrictions for the first workflow.
3. **Evidence mapping:** field-by-field mapping from the draft finding/report requirement to `EvidenceRecord`, `AgentRun`, `ArtifactView`, `AgentEvent`, and existing canonical records.
4. **Console coverage map:** each rendered Lab component → endpoint → HTTP method → source type → state side effects → test. Mark unused and duplicated calls.
5. **Worker reconciliation:** compare native Lab agent loop and Weaver worker against AEAS and WORKER_CONTRACT; recommend one entry path with rationale, no code changes.
6. **Focused test run:** only after the above static audit, execute the relevant existing tests in an authorized development environment and record exact command, baseline, result, and limitations.
7. **Human review:** return a gap matrix with proposed minimal changes. No application code changes until the implementation scope is separately confirmed.

## 10. Scope and status

- This matrix is documentation/evidence work only.
- No application code, credentials, production configuration, external runtime, or Notion record was changed.
- No merge, deployment, or pull request was performed.
- The read-only investigation workflow has **not** yet been claimed as end-to-end verified.
- This artifact does not grant authority to call mutation-capable endpoints or run the agent loop.
