# ARKADIA-CHIEF-001 — Gate 0 Integration Map

**Status:** Gate 0 reconnaissance complete; runtime implementation not authorized by this document.  
**Repository baseline inspected:** `main` at the GitHub content revision returned during this pass (the inspected source paths resolve to commit `a1009ddfb485d60b2717b73ff7ae02c417d1ef21`).  
**Scaffold branch:** `feat/chief-agent-foundation-001`.  
**Purpose:** identify the canonical seams, reuse boundaries, and unresolved contracts before any runtime code is written.

> This is a source-level integration map. It is not a production health check, deployment inventory from provider control planes, or proof that every optional router is mounted in the live process.

## 1. Executive integration decision

Build the Executive Office as a **feature module inside the canonical Arkadia FastAPI application**, with its own router, contracts, policy adapter, and UI surface in the existing Arkadia Console. It must not become a second intelligence spine, identity provider, memory database, approval engine, or execution runtime.

The best initial integration shape is:

```
Arkadia Console (web/arkadia_console)
        │ Firebase-authenticated API client
        ▼
Canonical FastAPI app (api/main.py)
        │ router composition; preserve main.py line budget
        ▼
Executive Office router + service adapters (new; not yet implemented)
        ├── Identity: api.auth.require_auth → verified Firebase uid
        ├── Intelligence: api.oracle_spine → Knowledge OS context engine
        ├── Provider selection: api.key_pool / existing provider adapters
        ├── Workspace: solspire.workspace_manager
        ├── Proposals & decisions: solspire.proposal_manager / proposal_router
        ├── Authorization: solspire.console_authority_router
        ├── Governed read-only dispatch: weaver.console_adapter
        ├── Engineering mutations: existing Weaver K15 → K3 path only
        └── Records: Knowledge OS + canonical SolSpire SQLite records
```

**Integration principle:** the Executive Office coordinates and presents these existing systems. It does not take ownership of their authority or data.

## 2. Canonical interfaces and reuse map

| Concern | Existing canonical source | What it already provides | Executive Office integration |
|---|---|---|---|
| Authentication | `api/auth.py` | Firebase Admin token verification in production; `require_auth`; profile includes verified `uid`, role and access level | Require this dependency on every private Executive Office route. Never accept a caller-supplied subject/role as identity. |
| Role / governance identity | `api/auth.py`, node registry, `governance/roles.json` | Role/access-level projection; Flamekeeper / access-level ≥3 governance check in approval boundaries | Use existing verified principal for founder approval. A separate service principal mapping is still missing. |
| Conversational intelligence | `api/oracle_spine.py` | `retrieve_arkana_context`, `build_memory_block`, archival helpers, provenance from the exact injected context | Add a thin adapter; do not call a model directly from a new parallel agent brain. |
| Context retrieval | `knowledge/context_engine.py` | `assemble_context`, owner-scoped notes, project/thread context, graph expansion and bounded timeline injection | Use for retrieval, with explicit owner scope and project/thread constraints. |
| Knowledge persistence | `knowledge/vault.py`, `knowledge/db.py`, `knowledge/timeline.py` | Markdown vault + SQLite index; owner-stamped notes; append-only timeline events | Reuse only after selecting the correct human-owned subject and note/event types. Do not create a second memory store. |
| Provider/key routing | `api/key_pool.py`, provider key store, `api/key_manager.py` | Round-robin Gemini key selection and cooldown handling | Current clear shared path is Gemini key acquisition, not a proven provider-neutral gateway. Inspect the actual model call adapter before choosing a multi-provider contract. |
| Workspace | `solspire/workspace_manager.py` | One canonical workspace bound to a verified subject UID | Resolve founder workspace through authenticated UID. Do not create an agent-owned parallel workspace. |
| Proposals / feedback / decisions | `solspire/proposal_manager.py`, `solspire/proposal_router.py` | Subject/workspace-bound proposal lifecycle; ACCEPTED is not authorization | Express recommended consequential work as proposals. Acceptance alone must not execute. |
| Authorization | `solspire/console_authority_router.py`, `weaver/enterprise_orchestration.py` | Human governance check; separate Authorization record; scope/constraints; execution attempt and evidence/verification chain | Reuse exact sync/route boundary. Executive Office must never mint authorization or widen a scope. |
| Read-only governed execution | `weaver/console_adapter.py` | Filesystem read/list and git status/diff; sandbox is write-disabled, network-disabled; tool must be in authorization scope and read_only constraint | Candidate first execution adapter after Gate 1/2. Keep allowlist narrow and repository root explicit. |
| Engineering changes | Engineering Lab / Weaver K15 → K3 | Canonical governed repository mutation path; SolSpire generic runtime explicitly blocks engineering mutation tools | Never dispatch repository writes through a new agent executor or generic SolSpire runtime. |
| Continuity events | `solspire/workevent_manager.py` | Subject/workspace-bound WorkEvent with artifact, decision, execution and evidence references | Record workflow continuity using existing event contract; distinguish observation, proposal, decision, execution and verification. |
| Enterprise evidence | `weaver/enterprise_orchestration.py` | Canonical proposal, authority event, authorization, execution attempt, evidence and verification records | Link report assertions and execution outcomes to stable evidence references; verification remains a separate act. |
| Existing generic execution | `solspire/execution_runtime.py` | In-process plan lifecycle; owner_uid; blocks engineering mutation | Not suitable as Chief Agent's durable executive scheduler or authority plane. Reuse only for compatible bounded non-engineering workflows if reviewed. |
| Console navigation | `web/arkadia_console/src/lib/surfaces.ts`, router and shell | Declarative surface registry; canonical UI routes; auth-required surface metadata | Add an Executive Office surface through the existing surface registry and shell, not a second SPA. |
| Frontend API convention | `web/arkadia_console/src/lib/apiConfig.ts` and shared API client | Canonical API base/origin and authenticated client conventions | Use the shared client and token provider; do not introduce raw fetch origins or stale env conventions. |

## 3. Identity and subject boundary

**Observed contract**
- Production authentication is Firebase-backed; `api.auth.require_auth` is the existing required route dependency.
- The authenticated profile carries a verified `uid`, plus role and access-level attributes derived through the existing profile/node registry path.
- SolSpire workspaces, proposals, WorkEvents and enterprise records are scoped to that verified subject.
- `api/approval_routes.py` requires authenticated users and separately checks governance authority for approval decisions.

**Gap — service identity is not yet designed.**
- No source inspected establishes a dedicated `ARKADIA-CHIEF-001` Firebase principal, custom-claim contract, workload identity, or secure service-to-founder subject delegation.
- Do not impersonate the founder by reusing a personal UID or by accepting a subject UID in request JSON.
- Gate 1 must choose between a dedicated machine principal with explicit subject/workspace grants, or a narrowly scoped service-to-service identity mechanism that still preserves the human owner as the data subject. This choice needs a security design and tests before private routes are implemented.

## 4. Intelligence and provider routing

**Canonical intelligence seam:** `api.oracle_spine` is the reusable conversational seam. It retrieves Knowledge OS context through `knowledge.context_engine.assemble_context`, preserves the exact context package for source attribution, and supports archival continuity. The context engine enforces owner scoping; that protection must not be bypassed by broad, unscoped database reads.

**Provider caveat:** `api.key_pool.acquire_key()` is the current shared Gemini key-selection primitive, aggregating configured Gemini keys and applying cooldowns. This is not evidence of a complete provider-neutral model gateway. The CEO chat route has a separate prompt/call path and should not be treated as the Chief Agent's canonical provider adapter without further reconciliation. The older `solspire/provider_manager.py` must be checked for current callers and consolidation status before use.

**Decision:** implement no new model client in Gate 1. First identify the canonical call adapter and its retry/error semantics; then expose it behind an Executive Office interface that is replaceable without changing identity, policy, memory, or records.

## 5. Approval, authorization and execution — critical distinctions

There are at least two related but distinct existing mechanisms:

1. **Tool-run approvals** in `api/approval_routes.py`: proposal canonicalization and SHA-256 digest bind a tool + payload + subject; approval decisions require Govern authority; approval is checked again at execution. The pending approval registry is process-local memory, so it is not a durable executive delegation ledger.
2. **SolSpire / ARK-WEAVER-01 authority chain**: a subject-owned proposal is accepted; a distinct human authorization action creates an enterprise Authorization with bounded scope and constraints; a governed execution attempt is dispatched; evidence is recorded; verification is a separate step. ACCEPTED ≠ AUTHORIZED.

**Decision:** the Executive Office should express work as a proposal and route human decisions through the canonical proposal/authority chain. Do not create an Executive Office approval queue. Do not treat a chat acknowledgement, proposal acceptance, approval record, authorization, execution, evidence, or verification as interchangeable.

**Execution boundaries**
- `weaver.console_adapter.WeaverConsoleAdapter` currently supports a narrow read-only tool set (filesystem read/list, git status/diff, constrained terminal read-only git commands). It enforces tool-in-scope, read_only and network restrictions.
- `solspire.execution_runtime.ExecutionRuntime` is in-process and explicitly rejects engineering mutation tools.
- Engineering repository mutation remains on the existing Weaver K15 → K3 path. Protected-branch merge and production deployment remain human-controlled.

## 6. Persistence and continuity

**Existing stores**
- Knowledge OS: vault Markdown + SQLite-backed note/chunk/embedding/graph/timeline structures.
- SolSpire/enterprise records: shared SQLite database at `data/solspire_projects.db`, configurable with `SOLSPIRE_PROJECTS_DB` / `SOLSPIRE_DATA_DIR`; workspaces, proposals, WorkEvents and ARK-WEAVER-01 records use this substrate.
- Some approval state remains in process memory (`PENDING_APPROVALS`).

**Gap — production durability is unverified.**
- Source defaults to local filesystem paths. The inspected root Dockerfile builds the canonical app but does not itself prove that the deployed service mounts a persistent disk at the database/vault paths.
- No root `render.yaml` was found in the inspected branch. Provider-side Render disk, backup, restart, region and instance configuration cannot be established from repository source alone.
- Do not add another database or LangGraph checkpointer until the deployment storage contract, backup/restore and transaction ownership are confirmed.

## 7. Runtime and deployment topology

**Source-confirmed**
- The root `Dockerfile` builds `web/arkadia_console` and runs the Python backend.
- `api/frontend_routes.py` serves the one canonical Console SPA and reserves backend prefixes including `/api`, `/solspire` and `/health`.
- `api/main.py` mounts the SolSpire router at `/solspire` through a guarded include; route composition is the existing extension seam.
- `GET /api/version` reports source revision using the revision identity helper; Render's `RENDER_GIT_COMMIT` is one revision source.
- `/health` and `/api/heartbeat` are the documented backend liveness contracts; `/api/health` is not the canonical backend health path.

**Not established**
- Current live Render service identity, paid/free plan, disk attachment, autoscaling/instance count, health-check configuration, deployed revision, uptime or alerting.
- Whether a persistent background worker is already provisioned for a new Executive Office workload.
- A free-tier runtime cannot be represented as guaranteed 24/7 service.

**Decision:** start with the existing API process and route composition for explicitly user-invoked, read-only operations only after Gate 1 identity is solved. Do not add a daemon, scheduler, or always-on worker in Gate 0/1. Durable scheduling requires a separate hosting and storage decision backed by provider-side evidence.

## 8. Console integration

The current product shell is `web/arkadia_console`; the older Prism and standalone console paths are not the canonical Docker build. The surface registry in `src/lib/surfaces.ts` defines stable IDs, paths, auth requirements and navigation grouping. The Executive Office should be a registered surface in that shell, with a read-only state/report view first.

The backend route should be composed as a child router under the existing `/solspire` namespace (for example, `/solspire/executive/*`) or another explicitly reserved prefix after route-collision review. Prefer the SolSpire router composition seam over adding inline logic to `api/main.py`, which has a strict line budget. Use the canonical API client and authenticated token provider.

## 9. Missing contracts / Gate 0 findings

These are real blockers or explicit unknowns, not assumed implementation details:

| Gap | Why it matters | Required resolution |
|---|---|---|
| Machine principal and founder subject binding | Prevents UID spoofing, founder impersonation and accidental cross-owner reads | Gate 1 identity ADR, least-privilege claims/grants, expiry/revocation and negative tests |
| Canonical provider-neutral call adapter | Avoids duplicate model paths and uncontrolled key selection | Trace current production callers and select a supported adapter; retain provider replaceability |
| Durable approval/delegation state | Process-local approval queue does not survive restart or scale-out | Reuse persistent authority records for delegation; define revocation and expiry semantics |
| Persistent volume / database backup | SQLite and vault paths may be ephemeral without provider disk configuration | Inspect Render service settings; prove mounted paths, backup and restore |
| Runtime topology and budget | No source evidence of a dedicated always-on worker or service objective | Confirm service plan, worker availability, budget owner and operational limits |
| Scheduler / trigger contract | Existing generic execution is in-process; no Chief Agent durable schedule contract established | Choose only after idempotency, dedupe, leases, retries, kill switch and restart recovery design |
| Current deployment parity | Historical docs are revision-bound and may be stale | Query live `/api/version`, health and provider deployment inventory before operational claims |
| Approval mechanism selection | Tool-run approvals and enterprise authorization are distinct mechanisms | Specify which actions use proposal→authorization→Weaver; do not unify by shortcut |
| Frontend route/API exact contract | Canonical shell is known, but no Executive Office UI or endpoint exists | Add route and API client adapter only after contracts are approved |

## 10. Recommended next implementation sequence

1. **Gate 1A — Identity ADR:** decide machine principal and subject/workspace grants; no code until security review of the chosen claims and token issuance.
2. **Gate 1B — Policy binding:** versioned policy digest, default-deny capability registry, expiry/revocation and founder-only authority actions.
3. **Gate 1C — Adapter contracts:** intelligence/provider adapter; owner-scoped Knowledge OS reads; proposal/authorization bridge; WorkEvent/evidence linkage.
4. **Gate 2 — Read-only report:** source-backed Arkadia state report using only approved read-only data paths; mark stale/unknown fields explicitly.
5. **Separate operations gate:** verify persistent storage and deployment topology before introducing checkpointing, scheduled jobs or a long-running worker.

## 11. Explicit non-decisions

- LangGraph is not selected or installed. Framework choice is deferred until state, checkpoint and recovery semantics are grounded in current storage and runtime constraints.
- LiteLLM is not selected.
- No new database is approved.
- No GitHub App or token is created by this map.
- No autonomous scheduler, worker, agent loop, or L3 delegation is active.
- No deployment, merge, runtime test, or production health claim is made.

## 12. Source index

The following source files were inspected on `main` for this pass:

- `api/auth.py`
- `api/oracle_spine.py`
- `api/key_pool.py`
- `api/approval_routes.py`
- `api/ceo_chat_routes.py`
- `api/main.py`
- `api/frontend_routes.py`
- `api/version_routes.py` (route contract cross-referenced)
- `knowledge/context_engine.py`
- `knowledge/db.py`
- `knowledge/vault.py`
- `knowledge/timeline.py`
- `solspire/console_router.py`
- `solspire/workspace_manager.py`
- `solspire/proposal_manager.py`
- `solspire/console_authority_router.py`
- `solspire/workevent_manager.py`
- `solspire/execution_runtime.py`
- `weaver/enterprise_orchestration.py`
- `weaver/console_adapter.py`
- `web/arkadia_console/src/lib/surfaces.ts`
- `Dockerfile`
- `requirements.txt`
- `DEPLOYMENT_GUIDE.md`
- `docs/recon/01_repository_map.md`
- `docs/recon/12_configuration_audit.md`
- `docs/recon/13_security_audit.md`
- `docs/voice/ARCHITECTURE_DISCOVERY.md`
- `docs/control-plane/evidence/gate2-public-runtime-integrity/EVIDENCE.md`

**Gate 0 exit:** source-level interfaces mapped; integration boundaries and unresolved contracts recorded. Runtime implementation remains blocked on Gate 1 identity/governance decisions and provider-side deployment/storage verification.
