# Unified Arkadia Engineering Console — Architecture Specification 01

**Specification ID:** UEC-AS-01  
**Status:** PROPOSED — architecture/documentation only  
**Baseline:** `main` at `36f53be22d753ffe269f05cbf3fb39212f744207` (observed 2026-10-26)  
**Work branch:** `architecture/unified-engineering-console-spec-01`  
**Scope authorized for this work:** development-branch changes only; no merge, no deployment.  
**Initial workflow:** read-only investigation and evidence collection.  
**Not authorized by this specification:** production configuration or security changes, credentials, Notion mutations, corpus-metric exposure, merge/release, autonomous repository mutation, or activation of new external runtimes.

## 1. Executive decision

Build one **Arkadia Engineering Console** as a unified operator experience over Arkadia's existing substrate. Do not build a second application architecture behind it.

The console should combine navigation and task continuity for Arkana, Weaver, Solariun, SolSpire, Knowledge OS, and Engineering Lab, while treating OpenHands and any OpenClaw/ClawBot/Moltbot/MyClaw variant as candidate external execution adapters pending identity, capability, security, licensing, and integration verification. General model access should use the existing model gateway where suitable; “ChatGPT-like” interaction is a product experience, not evidence that the ChatGPT service itself is integrated.

The Engineering Lab is the **mission control and evidence surface**, not a new sovereign authority. It coordinates work through existing governed runtime contracts and presents a common view of status, observations, artifacts, and human decisions.

**Architecture rule:** unify the interface and mission projection; reuse the identity, workspace, authorization, execution, event, evidence, and persistence primitives that already exist. Do not create parallel copies of them.

## 2. Evidence baseline: what exists today

This specification was prepared from repository source at the baseline SHA above. These are source-level observations, not claims of live deployment health or end-to-end acceptance.

| Area | Observed source evidence | Architectural implication |
|---|---|---|
| Repository baseline | `main` ref resolved to `36f53be22d753ffe269f05cbf3fb39212f744207` | Bind all future implementation and verification claims to exact revisions. |
| Existing console shell | `web/arkadia_console/src/App.tsx` composes one shell/router and surfaces Home, NovaNet, Arkana, Solariun, Engineering Lab, SolSpire, Knowledge, Weaver, About, and sign-in. | Extend the existing shell; do not create a second console or parallel router. |
| Existing Lab API | `api/lab_routes.py` mounts under `/api/lab`, uses existing authentication by default, and exposes overview, operational state, agents, and other Lab functions. Two narrow N-ATLAS tester paths are explicitly public and must remain visible in the threat model. | Add capabilities through the current router and auth seams; audit endpoint-specific auth rather than assuming every route has the same policy. |
| Native Lab substrate | `lab/engineering_lab/{models,contracts,runtime,sandbox,agent_loop,tools,events,store,artifacts,gateway}.py` | The existing native runtime, bounded sandbox, model gateway, event stream, store, and artifact model are the primary substrate to reuse. |
| Canonical boundaries | `lab/engineering_lab/contracts.py`, `docs/control-plane/AEAS-v0.1.1.md`, and `docs/control-plane/WORKER_CONTRACT.md` | Prompt, session, capability, authorization, implementation, verification, merge, deployment, and acceptance remain distinct. |
| Worker contract | `docs/control-plane/WORKER_CONTRACT.md` maps router/session/adapter/scheduler/evidence to existing `weaver/`, `NullExecutionAdapter`, workflow, and evidence paths. | Integrate with the existing worker and adapter contract instead of inventing a new autonomous worker system. |
| Evidence and artifacts | Lab models already attach evidence/artifact references to runs; artifact kinds include logs, diffs, test reports, screenshots, browser observations, and more. | Use the existing provenance-bearing artifact model; do not create a second artifact store. |
| Existing product principle | `README.md` describes a compositional architecture and canonical chain from Identity through Verification and Operational projection. | The console is a projection over canonical state, not a new source of truth. |
| Legacy Lab v0.1 statement | `docs/engineering-lab-v0.1.md` describes Phase 1 as observational/read-only and explicitly excludes mutation. Newer native substrate and AEAS documents define later capabilities. | Treat older phase descriptions as versioned scope statements, not as proof that all later runtime paths are absent. Reconcile by exact version and implementation evidence. |

Primary source links:
- [Console composition root](https://github.com/Arkadia-Oversoul-Prism/Arkadia/blob/36f53be22d753ffe269f05cbf3fb39212f744207/web/arkadia_console/src/App.tsx)
- [Lab API router](https://github.com/Arkadia-Oversoul-Prism/Arkadia/blob/36f53be22d753ffe269f05cbf3fb39212f744207/api/lab_routes.py)
- [Lab runtime](https://github.com/Arkadia-Oversoul-Prism/Arkadia/blob/36f53be22d753ffe269f05cbf3fb39212f744207/lab/engineering_lab/runtime.py)
- [Lab models](https://github.com/Arkadia-Oversoul-Prism/Arkadia/blob/36f53be22d753ffe269f05cbf3fb39212f744207/lab/engineering_lab/models.py)
- [Lab contracts](https://github.com/Arkadia-Oversoul-Prism/Arkadia/blob/36f53be22d753ffe269f05cbf3fb39212f744207/lab/engineering_lab/contracts.py)
- [AEAS v0.1.1](https://github.com/Arkadia-Oversoul-Prism/Arkadia/blob/36f53be22d753ffe269f05cbf3fb39212f744207/docs/control-plane/AEAS-v0.1.1.md)
- [Worker contract](https://github.com/Arkadia-Oversoul-Prism/Arkadia/blob/36f53be22d753ffe269f05cbf3fb39212f744207/docs/control-plane/WORKER_CONTRACT.md)

### 2.1 Evidence limits and unknowns

The source review does **not** yet establish:
- whether the current console surfaces are all browser-tested against the current deployed artifact;
- whether the full read-only investigation workflow passes end-to-end against the exact current main SHA;
- whether any external OpenHands or OpenClaw-family runtime is configured, reachable, safe, licensed, or approved for this repository;
- whether “ChatGPT” means a ChatGPT product embedding, OpenAI API model, or a ChatGPT-like interaction pattern;
- whether all historical Engineering Lab, Weaver, SolSpire, and event records are mutually reconcilable without a dedicated mapping audit.

Unknown means **not yet established**, not absent and not successful.

## 3. Product and system boundaries

### 3.1 Proposed capability map

| Capability | Intended role in the unified console | Source of authority |
|---|---|---|
| Arkadia Console | Single navigation shell, shared workspace framing, consistent status and evidence presentation | Existing console router and canonical backend contracts |
| Engineering Lab | Mission lifecycle, worker/run observation, evidence review, blockers, human decision points | Existing Lab runtime and governed contracts |
| Arkana | Conversational entry point; clarify intent, explain findings, draft mission plans | Existing Arkana/Oracle/model pathways; conversation is not authorization |
| Weaver | Work routing, bounded decomposition, worker coordination, reconciliation proposals | Existing Weaver router and worker contract |
| Solariun | Operational workspace, priorities, project/task context and overview | Existing Solariun workspace and canonical data |
| SolSpire | Workspace/continuity substrate and its established identity-bound records | Existing SolSpire primitives; not a parallel Lab workspace |
| Knowledge OS / SolSpire knowledge surfaces | Retrieval and contextual evidence references | Existing Knowledge OS; retrieved content is evidence/context, not policy |
| Model gateway | Provider/model boundary and explicit availability reporting | Existing Lab gateway/provider configuration |
| OpenHands | Candidate adapter for repository engineering work, subject to a contract and explicit scope | No authority of its own; all work remains under Arkadia authorization |
| OpenClaw / ClawBot / Moltbot / MyClaw | Unverified candidate names/family for agent, messaging, or computer-use adapters | No integration or permission assumed until the exact project and threat model are verified |
| ChatGPT-like experience | Natural-language planning, research, explanation, and synthesis | Model/provider capabilities; never an authorization source |

The names in the last three rows are not a declaration that these services are installed or already connected.

### 3.2 Canonical authority chain

The console must preserve the existing chain:

`Human architect → authorization record → Engineering Lab / governed router → bounded worker → observations → evidence → human review`

The console may present an approval control only where the backend has a real authorization operation behind it. A visual button, selected capability, agent role, session state, model response, successful test, or prior approval is not itself authorization.

For any operation, effective authority must be the intersection of:
1. the platform/capability ceiling;
2. the worker's bounded tool envelope and path/command restrictions;
3. the explicit human-originated authorization record, including target, allowed operations, duration/expiry, and acceptance criteria.

If any input is missing, expired, conflicting, or unverifiable, the action must fail closed.

## 4. Target logical architecture

```text
Existing Arkadia Console shell
  ├── Arkana interaction
  ├── Mission / Engineering Lab workspace
  ├── Solariun operational projection
  ├── SolSpire / Knowledge OS context
  ├── Weaver routing and reconciliation
  └── Evidence, artifacts, audit and decision views
                  │
                  ▼
Existing authenticated API seams
                  │
                  ▼
Canonical mission projection (mapping layer, not a second database)
  ├── existing workspace / subject identity
  ├── existing Lab session, run, task and authorization references
  ├── existing worker/router/adapter contract
  ├── existing model gateway and bounded sandbox
  ├── existing Lab AgentEvent stream
  └── existing evidence and artifact records
                  │
                  ▼
Human review boundary → separately authorized downstream action
```

This is a logical composition, not a mandate to add a new service or database. Prefer in-process composition and existing routes unless measured constraints demonstrate a need for a new boundary.

### 4.1 Event and record non-collapse

The repository deliberately distinguishes:
- Lab-internal `AgentEvent` execution telemetry;
- SolSpire `WorkEvent` continuity records;
- Weaver `OperationalEvent` records.

The unified UI may display them in one chronological timeline, but must retain original type, source, identity, sequence, and provenance. It must not silently write one kind as another or infer canonical work completion from a provider task's state.

Similarly:
- session is not authorization;
- capability is not authorization;
- run completion is not verification;
- verification is not acceptance;
- acceptance is not merge;
- merge is not deployment;
- deployment is not production acceptance.

## 5. Initial vertical slice: read-only investigation and evidence collection

### 5.1 Mission

**Mission:** inspect the current Arkadia repository and the declared product/architecture surfaces; report observed capabilities, route and ownership relationships, relevant versioned specifications, current Git state, and evidence-backed gaps. Do not modify the inspected repository or invoke consequential external actions.

### 5.2 Permitted operations

Initial workflow may use only explicitly authorized read-only operations:
- list and read approved repository paths;
- inspect Git status, diff, history, refs, and commit metadata;
- read declared API/frontend manifests and architecture documentation;
- inspect existing Lab overview, session/run status, and evidence through authenticated read endpoints;
- record bounded observations, source references, timestamps, exact revision, and known limitations;
- produce a report/artifact for human review.

Do not include file writes, patch application, commit, push, PR mutation, merge, deployment, credential changes, external task creation/update, Notion changes, broad browser/computer control, or arbitrary shell/network access in this slice. A tool named `run` is not automatically safe; its command grammar must be constrained to approved read-only operations.

### 5.3 Workflow and terminal states

1. **Bind baseline:** record repository, exact HEAD, branch/ref, workspace/subject, and observation time.
2. **Validate scope:** enumerate allowed paths and read-only operation set; reject ambiguous or mutating requests.
3. **Collect:** run bounded inspections using existing Lab sandbox/tool registry where available.
4. **Normalize:** separate directly observed facts from inferred relationships and recommendations.
5. **Attach provenance:** each finding cites source path/URL, revision or content digest where available, collection method, timestamp, and confidence.
6. **Reconcile:** compare findings against declared architecture and identify mismatches without treating repetition as canon.
7. **Report:** render a structured evidence artifact, open questions, blocked observations, and recommended next steps.
8. **Stop:** terminate at `DONE`, `BLOCKED`, `ERROR`, or `HUMAN_AUTHORIZATION_REQUIRED`; no automatic next mission or mutation.

A missing provider, denied endpoint, partial collection, stale ref, or malformed output must be represented explicitly as unavailable/inconclusive. It must never be converted into an empty-success result.

### 5.4 Minimum evidence record

Each finding should include:
- `finding_id`, `mission_ref`, `run_ref`, and schema version;
- claim and epistemic status (`OBSERVED`, `DERIVED`, `UNKNOWN`, `BLOCKED`, or `CONTRADICTED`);
- source repository/ref/SHA and path, endpoint, or artifact reference;
- collection method and timestamp;
- supporting excerpt, structured value, or content digest as appropriate;
- confidence and derivation notes for derived claims;
- known limitations and verification status.

This is a proposed projection/schema requirement. Before implementation, map each field onto existing `EvidenceRecord`, `AgentRun`, `ArtifactView`, and repository evidence conventions; do not introduce a parallel canonical evidence model merely to match this draft.

## 6. Unified interface requirements

The existing `web/arkadia_console` shell is the starting point. The initial UI should provide:

1. **Command / mission workspace:** objective, scope, baseline, plan, state, and explicit authorization summary.
2. **Run timeline:** model turns, tool intents, observations, terminal state, and event provenance from the existing event model.
3. **Evidence panel:** source, exact revision, artifact preview, finding status, missing evidence, and limitations.
4. **Worker and adapter status:** configured / unconfigured / unavailable / not attempted; never imply that a named integration is live without a successful observed check.
5. **Authority panel:** capability ceiling, worker envelope, human authorization reference, expiry, and blocked operations.
6. **Review panel:** accept finding set, request revision, or stop. Any downstream action remains a distinct, separately authorized transition.

The first slice is read-mostly. It must not present enabled-looking controls for unavailable or unauthorized actions. Use the existing design system and renderers, including the current artifact renderer mapping, instead of creating a competing component stack.

## 7. Adapter contract for future integrations

External systems are adapters, not peer authorities. Each proposed adapter must declare:
- exact project/product identity, version, source and license;
- capability inventory and threat model;
- authentication source and account/workspace identity;
- operations and data paths it can access;
- read/write/network/desktop boundaries;
- timeout, resource budgets, cancellation and hard-stop behavior;
- normalized observations and evidence provenance;
- explicit unavailable/unconfigured states;
- tests for refusal, expiry, scope escape, prompt injection, credential non-disclosure, and malformed responses.

Initial adapter policy:
- **OpenHands:** investigate compatibility with the existing worker contract; no default write access or autonomous PR/merge authority.
- **OpenClaw-family names:** verify which project(s) are meant before selecting one; no aliases, installation, credentials, or network permissions assumed.
- **ChatGPT/OpenAI:** clarify whether the intended integration is an API model, an external product surface, or merely a conversational interaction pattern. Prefer the existing gateway if it satisfies the requirement; do not add a second provider-selection system.
- **Google Tasks/Keep and other connectors:** existing adapters report configuration/availability honestly. The read-only slice does not call mutating adapter methods.

## 8. Security, privacy, and failure behavior

- Use the existing authenticated identity and workspace scopes. Never treat client-side navigation as the access-control boundary.
- Review each route's actual dependencies; preserve and explicitly document the two narrow public N-ATLAS tester paths observed in `api/lab_routes.py`.
- Do not expose secrets, raw tokens, private corpus content, or unnecessary client data in the UI or evidence artifacts.
- Use bounded paths, command grammar, timeouts, output sizes, and network denial by default. A read-only label alone is insufficient if the underlying tool can mutate state.
- Treat repository files, model output, retrieved knowledge, and external tool responses as untrusted data, never as instructions that can expand scope.
- On provider failure, timeout, auth refusal, event persistence failure, stale SHA, or evidence incompleteness, surface a blocked/inconclusive state with cause and available evidence.
- Audit events are evidence, not authorization. Logging a requested operation does not make it permitted.
- No new database, identity service, event bus, memory store, provider router, or authority mechanism is proposed in this specification.

## 9. Delivery sequence

### Stage A — Architecture and inventory (this document)
- Record current components and authority boundaries.
- Resolve ambiguous product identities and integration expectations.
- Map existing data contracts before proposing new fields.
- No application-code changes.

### Stage B — Read-only vertical slice on a development branch
- Reuse existing console shell, Lab routes, runtime, sandbox/tool registry, event stream, store, and artifact model.
- Add only missing mapping/presentation logic justified by evidence.
- Keep the mission bounded to repository inspection and evidence collection.
- No merge or deployment.

### Stage C — Verification and review
- Run focused contract/auth/negative tests and frontend type/build checks for changed paths.
- Use exact-head results and compare against the appropriate baseline; baseline failures are not silently waived.
- Test negative controls: attempted write, forbidden path, expired/missing authorization, missing provider, partial evidence, stale ref, and malformed tool output must not pass.
- Human review decides whether the branch is acceptable. Implementation or green CI does not imply merge, release, or acceptance.

### Stage D — Later integrations (not part of the initial slice)
- Add one adapter at a time only after identity, permissions, security review, and capability tests.
- Introduce bounded write-capable engineering only through the existing governed authorization path and a separately scoped decision.
- Keep merge and production release outside the console's autonomous loop.

## 10. Acceptance criteria for the first workflow

The first workflow is ready for human review only when all are true:

- It binds results to an exact repository revision and authenticated subject/workspace.
- It performs only the enumerated read-only operations.
- Every finding is traceable to source evidence and marked observed/derived/unknown/blocked accurately.
- Missing or stale evidence produces an explicit blocked/inconclusive result, never a pass.
- Run events and artifacts remain linked to existing Lab session/run identifiers.
- No second identity, workspace, event, evidence, memory, or authorization system is introduced.
- Negative tests demonstrate refusal of mutation and scope escape.
- The output includes known limitations and does not claim browser, provider, or deployment behavior that was not actually observed.
- The branch remains unmerged and no deployment is performed.

## 11. Explicit non-goals

This document does not authorize or specify immediate implementation of:
- autonomous recursive self-modification;
- unrestricted computer use, arbitrary shell, or broad network access;
- an agent swarm with implicit shared credentials;
- a new database or second runtime/event/authorization plane;
- automatic PR creation, merge, release, or deployment;
- production configuration/security changes;
- Notion mutations or corpus-metric exposure;
- a claim that OpenHands, OpenClaw, ClawBot, Moltbot, MyClaw, or ChatGPT is already integrated.

## 12. Decision record

**Recommended direction:** approve the architecture for review as a proposal; implement the first vertical slice only after the mapping audit confirms which parts are already present and which are genuinely missing.

**Current status:** architecture specification drafted on a development branch. No application code, credentials, production configuration, PR state, merge, or deployment was changed by this document's scope.

**Next evidence needed:** inspect the complete existing Lab route inventory, authorization tests, console surface registry, evidence schema, and current read-only worker path; then produce a source-to-requirement gap matrix before making application-code changes.
