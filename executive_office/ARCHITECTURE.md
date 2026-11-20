# Chief Agent — Hybrid Architecture Decision

**Decision record:** ARK-EXEC-ADR-001  
**Status:** Proposed; validate against live repository and deployment state before implementation.

## Context

Arkadia already has an intelligence spine, Knowledge OS, authorization and approval routes, Weaver/Engineering Lab execution surfaces, WorkEvent/Evidence concepts, a React/Vite console, and deployed backend infrastructure. A new executive agent must extend those systems without creating a competing source of truth or a parallel permission path.

The selected deployment direction is **hybrid**: a dedicated executive-office module and service boundary inside the canonical Arkadia repository, surfaced through the existing Arkadia Console and integrated through existing backend contracts.

## Proposed components

| Concern | Initial direction | Guardrail |
|---|---|---|
| Repository | Existing Arkadia repo | No separate competing product/repo |
| Service identity | Dedicated GitHub App | Least privilege; no personal PAT |
| Orchestration | LangGraph, subject to dependency and runtime review | Durable checkpoints; no implicit authority |
| API boundary | Existing FastAPI backend or separately deployed worker | Reuse auth, approval, audit and policy |
| Intelligence | Provider adapter over approved existing model routing | Model is replaceable; keys stay server-side |
| Memory | Existing Knowledge OS and approved durable stores first | Do not introduce duplicate memory/database |
| Execution | Existing Weaver / Engineering Lab interfaces | No direct bypass to tools or production |
| UI | Existing Arkadia Console | Executive view is a projection, not a new authority plane |
| Scheduling | Event/webhook triggers plus monitored scheduler | Jobs are idempotent, bounded, observable |
| Hosting | Existing deployment footprint for initial integration; paid persistent worker when funded | Free tiers may sleep, pause, or impose quotas |

## Important implementation sequence

1. Inventory current identity, auth, provider routing, knowledge persistence, tool approval, Weaver, WorkEvent, deployment and UI contracts.
2. Write adapters only where an existing contract does not already satisfy the need.
3. Start read-only: repository/project assessment and evidence-linked reporting.
4. Add explicit tool allowlists and policy checks at the execution boundary.
5. Add persistence/checkpointing only after identifying the canonical store and recovery semantics.
6. Add scheduled operation only after idempotency, rate limits, observability, failure handling and kill switch are tested.
7. Add scoped L3 capabilities only through a signed, versioned human delegation.

## Model and framework selection

LangGraph is the leading orchestration candidate because it supports stateful graph workflows and checkpointing. It is not itself the identity, authorization, memory source of truth, or hosting platform. The initial scaffold deliberately does not add it to global requirements or introduce a second dependency manager.

Use the existing provider routing where possible. A model gateway such as LiteLLM is optional and should be introduced only if current provider abstractions cannot meet the required routing, observability, and fallback behavior.

## Persistence decision

Do not create a new PostgreSQL or Supabase database by default. First inspect the existing Knowledge OS, Firestore, and deployment data contracts. If a separate LangGraph checkpointer is justified, document the data it stores, retention, backup, migration, encryption, and failure behavior.

## Uptime statement

"Permanent" means stable identity and recoverable institutional continuity, not guaranteed perpetual compute. A true always-on service requires a persistent worker, health monitoring, alerting, backups, tested restore, and budget. Free hosting is suitable for prototyping, not a 24/7 guarantee.

## Security and authority

- GitHub App installation limited to this repository and read-first permissions.
- No personal access token or user session token.
- Secrets are deployment secrets, never repository files or agent memory.
- Every tool call checks subject, capability, policy version, scope, approval, expiry and revocation.
- The agent cannot approve its own request or alter its own policy.
- Protected branch and production deployment controls remain external to the agent.
- All consequential activity is auditable and attributable.
