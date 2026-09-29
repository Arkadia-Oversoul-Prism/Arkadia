# ARKADIA

## Sovereign intelligence architecture

Arkadia is a working architecture for **human cognitive sovereignty, continuity, and coherence in a distributed AI era**.

It is not presented here as a finished product. The repository is the primary public engineering record: architecture, implementation, evidence, experiments, and the boundaries between them.

> **Human authority remains the decision boundary.**
>
> **DON'T KNOW IS ALLOWED. Evidence decides what we can claim.**

## What exists

The current system composes:

- **Identity** → canonical subject and workspace boundaries
- **Workspace / SolSpire** → organizational operating substrate
- **Workload / Workstream** → bounded units of work
- **Authorization** → explicit human-governed decision boundary
- **Execution / Weaver / Engineering Lab** → governed execution substrate
- **WorkEvent / Evidence** → observable provenance and state transitions
- **Knowledge OS** → graph, retrieval, embeddings, timeline, and contextual memory
- **Solariun** → personal intelligence workspace and experience layer
- **Enterprise projections** → governed operational views, including the Eden pilot
- **Opportunity Radar** → economic opportunity capture projected from canonical repository state

The architecture is intentionally compositional. A new interface should expose the existing substrate rather than create a second memory system, second database, or parallel authority path.

## The canonical chain

```
Identity
   ↓
Workspace
   ↓
Workload
   ↓
Workstream
   ↓
Authorization
   ↓
Execution
   ↓
WorkEvent
   ↓
Evidence
   ↓
Knowledge
   ↓
Verification
   ↓
Operational projection
```

The important boundaries are equally important:

**Specification ≠ implementation**

**Authorization ≠ execution**

**Execution ≠ completion**

**Completion ≠ approval**

**Approval ≠ merge**

**Merge ≠ deployment**

**Deployment ≠ acceptance**

## Public / private boundary

The repository is intentionally public, but **public does not mean everything belongs in Git**.

### Public by design

- architecture and ADR evidence
- non-sensitive implementation
- tests and verification contracts
- public pilots and public opportunity intelligence
- interface contracts
- governance boundaries
- reproducible technical evidence
- honest records of known gaps

### Never commit

- credentials, API keys, tokens, private keys
- private Knowledge OS vault contents
- client-confidential material
- unpublished personal data
- authentication artifacts
- private negotiation or financial records

See [PUBLIC_SURFACE.md](PUBLIC_SURFACE.md) for the current public-surface contract.

## Evidence state

Arkadia uses explicit epistemic states rather than treating every document or generated result as truth.

Typical states include:

- **VERIFIED**
- **SUPPORTED**
- **LEAD**
- **UNKNOWN**
- **EXPIRED**
- **REJECTED**
- **PROPOSED / EXPERIMENTAL**

A public claim should be traceable to implementation, evidence, or an explicitly attributed external source.

## Current experience

The main experience is the **Solariun / SolSpire** interface.

The live application is linked from the repository's GitHub metadata and deployment configuration. Some surfaces are experimental or environment-dependent. The repository is the authoritative place to inspect what has actually been implemented.

### Opportunity Radar

Opportunity Radar is a thin lens over the existing substrate, not a second application.

Its current SAPZ capture state lives at:

[opportunity_radar/SAPZ_CAPTURE_STATE.md](opportunity_radar/SAPZ_CAPTURE_STATE.md)

The current capture includes Wave 1 outreach to Sydani Group and Agroxchange Technology Services, with Wave 2 targets queued. Bidder/incumbent status remains explicitly **UNKNOWN** where it has not been independently established.

## How to inspect Arkadia

Start with:

1. [PUBLIC_SURFACE.md](PUBLIC_SURFACE.md) — what is safe and meaningful to inspect publicly
2. [CURRENT_STATE.md](CURRENT_STATE.md) — historical checkpoint record; not a live status oracle
3. [AGENTS.md](AGENTS.md) — engineering conventions and hard boundaries
4. [ENGINEERING_PRINCIPLES.md](ENGINEERING_PRINCIPLES.md) — engineering principles
5. [opportunity_radar/SAPZ_CAPTURE_STATE.md](opportunity_radar/SAPZ_CAPTURE_STATE.md) — current opportunity-capture state
6. [web/public_prism/](web/public_prism/) — current frontend
7. [api/](api/) and [solspire/](solspire/) — backend and operating substrate
8. [weaver/](weaver/) and [lab/engineering_lab/](lab/engineering_lab/) — governed execution surfaces
9. [knowledge/](knowledge/) — Knowledge OS implementation
10. [docs/control-plane/evidence/](docs/control-plane/evidence/) — evidence records

## Verification honesty

The repository may contain historical records whose status has since changed. **Do not infer current runtime health from a prose checkpoint alone.**

When a claim matters, inspect the current tree, current commit, current workflow result, or run the relevant test.

That distinction is part of the architecture.

## Mission

Arkadia is being built as an architecture for:

**human cognitive sovereignty, continuity, and coherence in the distributed AI era.**

The goal is not to make AI the authority.

The goal is to make intelligence more inspectable, more executable, and more useful **without transferring the final human decision boundary to the machine.**
