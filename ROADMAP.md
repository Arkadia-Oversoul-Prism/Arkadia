# Arkadia — Strategic Roadmap

> The bridge between the Engineering Constitution and day-to-day implementation.

This document is strategic. For tactical session state, read `docs/phase1/CONTINUATION_LEDGER.md`.  
For engineering philosophy, read `ENGINEERING_PRINCIPLES.md`.  
For architectural decisions, read `docs/adr/`.

*Last updated: ARK Y1 · D116 (2026-07-24)*

---

## Where We Are Now

### Current Phase: Phase 1 — Runtime Stabilization

**Analysis complete. Implementation not yet started.**

Phase 0 security hardening is constitutionally sealed (ADR-013). The Engineering Constitution is in place. Workstream B implementation begins at the next session.

### Current Maturity Level

| Dimension | State |
|---|---|
| Security boundary | ✅ Hardened (Phase 0 complete) |
| Governance model | ✅ Constitutional (ADRs, Fitness Tests, Phase Gates, Steward Charter) |
| Runtime durability | ❌ In-memory queue — jobs lost on crash |
| Kernel boundaries | ❌ Five layer violations (kernel → api) |
| Observability | ❌ In-process counters only; no request correlation |
| Plugin system | ❌ Hardcoded `ALLOWED_TYPES` frozenset |
| Corpus sync | ❌ Full-tree fetch on every run; no resumability |
| Domain model | ❌ Concepts scattered across modules |
| Knowledge Layer | ❌ Not yet canonicalized |

### Open Architectural Debt

1. **Runtime durability gap** — `kernel/jobs.py` uses `queue.Queue`; pending jobs are lost on process restart. (Workstream B)
2. **Layer violations** — five `kernel → api` imports invert the dependency direction. (Workstream A)
3. **Plugin inflexibility** — `ALLOWED_TYPES` frozenset requires code changes to add intent types. (Workstream E)
4. **Observability gap** — no structured logging, no request IDs, no timing correlation. (Workstream D)
5. **Corpus sync inefficiency** — full GitHub tree fetch on every run; no SHA comparison; not resumable. (Workstream C)
6. **`api/main.py` monolith** — 2500+ lines; decomposition deferred to Phase 2.
7. **Port interfaces undefined** — `StorageBackend`, `LLMProvider`, `KeyProvider` not yet abstracted (ADR-016, pending Phase 1 completion).

---

## Where We Are Going

### Phase 1 — Runtime Stabilization *(current)*

**Goal:** Make the runtime correct before making it capable.

A system cannot grow coherently if its runtime state is undurable, its boundaries are violated, and its behavior is invisible. Phase 1 closes those gaps before any new capability is added.

| Workstream | Objective | Priority |
|---|---|---|
| B — SQLite Job Runtime | Durable job and goal persistence | Highest |
| E — Plugin Registry | Replace hardcoded intent types | Second |
| D — Observability | Structured logging + request correlation | Third |
| A — Layer Violations | Eliminate all `kernel → api` imports | Fourth |
| C — Corpus Sync | Incremental SHA-comparison sync | Fifth |

**Exit criteria:** All seven Phase Gates (A–G) closed. See `docs/phase1/PHASE_GATES.md`.

---

### Phase 2 — Domain Canonicalization

**Goal:** One authoritative definition for every domain concept.

Phase 1 stabilizes the runtime. Phase 2 stabilizes the domain model. Currently, domain concepts like "job," "goal," "event," "transaction," and "knowledge" are defined implicitly by whatever data structure first happened to use them. Phase 2 gives each concept a single canonical home with an explicit interface.

**Anticipated workstreams:**
- Decompose `api/main.py` (2500+ lines) into bounded route modules
- Define `StorageBackend`, `LLMProvider`, `KeyProvider` port interfaces (ADR-016)
- Establish canonical domain types for Job, Goal, Event, Transaction, KnowledgeEntry
- Canonicalize oracle interaction model (request → context → response lifecycle)
- Migrate all implicit domain usage to canonical types

**Precondition:** Phase 1 complete. All layer violations resolved. Port interfaces cannot be defined until the kernel's outward-facing API is stable.

---

### Phase 3 — Unified Knowledge Layer

**Goal:** A coherent, queryable, authoritative Knowledge OS.

Phase 3 is the realization of Arkadia's core purpose. The Knowledge Layer becomes a first-class subsystem with a defined API, not an emergent property of how modules happen to call each other.

**Anticipated workstreams:**
- Unified Knowledge Vault API (graph + vector + relational, unified interface)
- Corpus ingestion pipeline (GitHub, documents, structured data) with deduplication
- Context retrieval engine (ranked, temporally-aware, source-attributed)
- Knowledge provenance — every retrieved fact traceable to its source
- Oracle knowledge grounding — Oracle responses cite vault entries, not hallucinations

**Precondition:** Phase 2 complete. Canonical domain types must exist before the Knowledge Layer can be typed against them.

---

### Phase 4 — Experience Projection

**Goal:** Project the Knowledge OS through every Arkadia experience coherently.

The Knowledge Layer exists. Phase 4 connects it to every surface: NovaNet, Oversoul Prism, Encyclopedia Galactica, the Discord bot, and any future public interface.

**Anticipated workstreams:**
- NovaNet knowledge integration
- Oversoul Prism — Oracle and Knowledge Layer as unified experience layer
- Encyclopedia Galactica — knowledge-backed chamber content
- Discord bot — vault-grounded responses
- Public API surface — authenticated, rate-limited knowledge queries
- Mobile (Sonata Android) — offline-first knowledge subset

**Precondition:** Phase 3 complete. Experience layers cannot reliably query knowledge that does not yet have a stable, bounded API.

---

### Phase 5 — Scale Without Compromise

**Goal:** Grow Arkadia's scope and contributor base without compromising architectural integrity.

Phase 5 is not a specific set of features. It is the proof that the Engineering Constitution works — that Arkadia can absorb new contributors, new capabilities, and new scale without the architectural debt that accumulates when platforms grow without governance.

**Anticipated workstreams:**
- CI pipeline — architecture fitness tests as required PR gate
- Contributor documentation — onboarding guide derived from Architecture Map and Engineering Principles
- Automated observability dashboards (structured logs → metrics → alerting)
- Horizontal scaling audit — identify what, if anything, requires infrastructure beyond SQLite
- Architecture Freeze v1.0 (see below)

**Precondition:** Phases 1–4 complete.

---

## Why This Order

The sequencing reflects a strict dependency structure.

```
Phase 0: Secure the platform
    ↓   (cannot build on an unsecured foundation)
Phase 1: Stabilize the runtime
    ↓   (cannot canonicalize a domain whose runtime is undurable)
Phase 2: Canonicalize the domain
    ↓   (cannot build a knowledge layer without stable domain types)
Phase 3: Unified Knowledge Layer
    ↓   (cannot project knowledge coherently without a stable knowledge API)
Phase 4: Experience Projection
    ↓   (cannot scale without established architectural integrity)
Phase 5: Scale Without Compromise
```

Each phase is a precondition for the next. Skipping or reordering phases produces the same outcome every time: the skipped work becomes technical debt that compounds until it is paid back — usually at the worst possible moment.

The instinct to jump to Phase 4 (visible, exciting user experiences) before Phase 1 (invisible, unglamorous runtime stability) is understandable. It is also how platforms become unmaintainable. The Knowledge OS must be correct before it becomes capable. It must be bounded before it becomes connected. It must be coherent before it becomes visible.

---

## Architecture Freeze v1.0

**Definition:** The milestone at which the foundational architecture is considered stable enough that feature development can accelerate without risk of structural regression.

This is not a freeze on features. It is a freeze on foundational architectural decisions — the layer map, the dependency direction, the kernel's scope, and the domain model. After this point, those things evolve only through a new ADR.

**Criteria:**

| Criterion | Status |
|---|---|
| No undocumented architectural decisions | 🚧 ADRs current through Phase 0–1 analysis |
| All layer rules enforced in CI | ❌ Tests exist; CI wire-up pending Phase 5 |
| Kernel responsibilities reduced to orchestration | ❌ Five violations remain (Phase 1, Workstream A) |
| Canonical domain model established | ❌ Phase 2 |
| SQLite runtime stable | ❌ Phase 1, Workstream B |
| Plugin system operational | ❌ Phase 1, Workstream E |
| Knowledge Layer interfaces defined | ❌ Phase 3 |

**Estimated:** After Phase 3 is complete.

---

## The CI Milestone

When architecture fitness tests become a required CI gate, architectural governance shifts from "best practice" to "enforced practice."

```
Engineering Principles
        ↓
ADRs
        ↓
Architecture Rules
        ↓
Fitness Tests
        ↓ ← you are here (tests exist; CI gate pending)
CI
        ↓
Pull Requests
        ↓
Main Branch
```

The fitness tests are pure AST-based Python — no secrets, no network, no running application. They can be wired to any CI provider without modification.

---

*This document is updated at the end of each phase, or whenever a strategic decision changes the sequencing or scope of a phase. Tactical changes belong in the Continuation Ledger, not here.*
