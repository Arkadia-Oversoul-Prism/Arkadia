# SPIRAL GROVE — WAVE 01
## Architecture Specification & Repository Mapping

**Repository:** `Arkadia-Oversoul-Prism/Arkadia`
**Branch:** `main`
**Status:** Architecture specification / implementation boundary
**Wave:** 01 — Capability Foundation
**Date:** 2026-08-30

---

## 0. PURPOSE

Spiral Grove is the human-capability environment of Arkadia Prism.

It is not a second Knowledge OS, a course catalogue, an autonomous agent, or a replacement for existing Prism/Weaver infrastructure.

Its purpose is to coordinate a human's progression from intent to demonstrated capability:

```text
Intent
  ↓
Calibration
  ↓
Learning Path
  ↓
Practice
  ↓
Project
  ↓
Evidence
  ↓
Reflection
  ↓
Next Capability
```

Wave 01 establishes the canonical domain model, repository boundaries, persistence strategy, API seams, and trust/authority rules required to implement this loop without duplicating existing Arkadia authorities.

---

## 1. ARCHITECTURAL THESIS

Arkadia Prism is the human-directed intelligence environment.

Spiral Grove is the capability-growth environment inside Prism.

Weaver remains the engineering/project execution workbench.

Knowledge OS remains the canonical knowledge substrate.

Provider adapters remain interchangeable reasoning/tool interfaces.

Therefore:

```text
                         ARKADIA PRISM
                              │
              ┌───────────────┴───────────────┐
              │                               │
        SPIRAL GROVE                         WEAVER
       Human Capability                  Engineering Work
              │                               │
       Learning / Practice              Project / Execution
       Evidence / Progress              Code / Patches
              │                               │
              └──────────────┬────────────────┘
                             │
                       KNOWLEDGE OS
                             │
                   Sources / Memory / Graph
                             │
                      PROVIDER ROUTER
                             │
                   Human Authority Boundary
```

### Core rule

**Spiral Grove composes existing authorities. It does not create parallel authorities.**

In particular, Wave 01 must not introduce:

- a second memory store
- a second knowledge graph
- a second vector/embedding authority
- a second project authorization system
- a second provider router
- an unrestricted autonomous agent

---

## 2. PRODUCT OBJECTIVE

The first product expression of Spiral Grove is the A.I.S Living University.

A.I.S can expose multiple programs over the same capability engine:

| Audience | Program | Primary outcome |
|---|---|---|
| Secondary students | A.I.S Learning Lab | Future-skill foundations |
| Young adults | A.I.S Future Builder | Capability + portfolio + market readiness |
| Professionals | A.I.S Professional Intelligence | Applied AI/workflow capability |
| Organizations | A.I.S Workforce Intelligence | Human-centered capability development |
| Agriculture/community | A.I.S Ground Intelligence | Applied ecological/agricultural capability |

The software should not hard-code these commercial programs into the core domain. Programs should reference reusable capabilities, learning resources, exercises, challenges, projects, and assessment definitions.

---

## 3. WAVE 01 SCOPE

### In scope

1. Capability Registry
2. Skill levels and prerequisites
3. Learning Resource registry
4. Exercise / Challenge definitions
5. Learning Path composition
6. Learner enrollment/progress state
7. Evidence/artifact references
8. Calibration result envelope
9. Progression recommendation envelope
10. Basic cohort/community references
11. Tool registry metadata
12. Trust/consent classifications
13. Read-only integration with Knowledge OS
14. API contracts and tests

### Explicitly out of scope

- full autonomous agent execution
- payments/subscriptions
- employer marketplace
- commercial sale of learner data
- child profiling for advertising
- biometric inference
- hidden child research collection
- new vector database
- new graph database
- replacement LMS
- replacement project authorization
- automatic publishing/submission of consequential work
- automatic enrollment into paid services

---

## 4. CANONICAL DOMAIN MODEL

### 4.1 Capability

A capability is the canonical unit of human development.

```text
Capability
- id
- slug
- name
- description
- domain
- level
- prerequisites[]
- outcomes[]
- status
- version
```

Examples:

- `ai-literacy`
- `prompt-engineering`
- `research-systems`
- `workflow-design`
- `visual-design`
- `communication`
- `farm-operations`

### 4.2 Learning Resource

A learning resource points to material that supports a capability.

```text
LearningResource
- id
- title
- resource_type
- source_ref
- capability_ids[]
- difficulty
- estimated_minutes
- provenance
- status
```

`source_ref` should reference an existing Arkadia knowledge/file/source object where possible rather than copying content into a new Grove store.

### 4.3 Exercise

A bounded practice activity.

```text
Exercise
- id
- capability_id
- prompt
- expected_output
- evaluation_mode
- difficulty
- timebox
```

### 4.4 Challenge

A structured EduLeague activity.

```text
Challenge
- id
- capability_ids[]
- title
- objective
- rules
- constraints
- submission_type
- evaluation_rubric
```

### 4.5 Learning Path

A directed sequence of capability-building activities.

```text
LearningPath
- id
- name
- audience
- capability_ids[]
- resource_ids[]
- exercise_ids[]
- challenge_ids[]
- project_template_ids[]
- progression_rules
- version
```

### 4.6 Learner State

The learner state records progression, not an absolute judgment of the human.

```text
LearnerCapabilityState
- learner_id
- capability_id
- status
- demonstrated_level
- confidence
- evidence_refs[]
- last_assessed_at
- next_recommended_action
```

Important: `demonstrated_level` means demonstrated within defined evidence, not a claim about the person's intrinsic intelligence or worth.

### 4.7 Evidence

Evidence is a reference to a learner artifact, submission, observation, assessment, or reflection.

```text
Evidence
- id
- learner_id
- capability_id
- evidence_type
- source_ref
- provenance
- created_at
- consent_scope
- visibility
```

Evidence must remain traceable to its source.

### 4.8 Cohort

```text
Cohort
- id
- program_id
- facilitator_ids[]
- learner_ids[]
- schedule
- status
```

### 4.9 Tool

A structured description of a tool that may assist a capability path.

```text
Tool
- id
- name
- category
- capability_ids[]
- input_types[]
- output_types[]
- provider_ref
- cost_class
- risk_class
- permission_class
```

A Tool record describes routing metadata. It does not grant execution authority.

---

## 5. CALIBRATION PROTOCOL

Calibration is the first operational intelligence capability.

The system presents bounded tasks and records evidence of performance.

```text
Learner Intent
    ↓
Calibration Task
    ↓
Submission
    ↓
Evaluation
    ↓
Evidence Record
    ↓
Capability State
    ↓
Recommended Path
```

Calibration must be:

- task-based
- transparent
- reversible
- explainable
- scoped to the capability being assessed
- contestable by the learner/facilitator

The system must not infer sensitive traits or make consequential decisions from calibration results.

---

## 6. LEARNING LOOP

The canonical Spiral Grove loop is:

```text
CALIBRATE
    ↓
LEARN
    ↓
PRACTICE
    ↓
BUILD
    ↓
PROVE
    ↓
REFLECT
    ↓
ADAPT
```

Each stage produces an explicit state transition or artifact.

### Example

```text
Capability: Research Systems

Calibration → weak source verification
Learning    → verification module
Practice    → source comparison exercise
Build       → research brief
Prove       → evidence-backed presentation
Reflect     → learner reflection
Adapt       → next capability: evidence synthesis
```

---

## 7. KNOWLEDGE OS INTEGRATION

Existing Knowledge OS architecture establishes that knowledge is the canonical source of truth, AI providers are reasoning adapters, and derived project knowledge must not become a second graph/memory authority.

Spiral Grove therefore consumes Knowledge OS through read-oriented references and context assembly.

Existing implementation:

- `knowledge/` — canonical Knowledge OS
- `knowledge/schema.sql` — canonical persistence schema
- `knowledge/pipeline.py` — ingestion
- `knowledge/context_engine.py` — context assembly
- `knowledge/search.py` — retrieval
- `knowledge/graph.py` — graph operations
- `knowledge/timeline.py` — immutable events
- `providers/router.py` — provider abstraction
- `solspire/project_knowledge.py` — derived project knowledge views

Wave 01 must reference these systems rather than replicate them.

The existing project knowledge layer explicitly classifies its graph as derived/source-backed and keeps project knowledge separate from authorization. This boundary remains intact.

---

## 8. REPOSITORY MAPPING

### Existing canonical homes

| Concern | Existing home | Wave 01 action |
|---|---|---|
| Knowledge persistence | `knowledge/` | Reuse |
| Knowledge ingestion | `knowledge/pipeline.py` | Reuse |
| Search | `knowledge/search.py` | Reuse |
| Context | `knowledge/context_engine.py` | Reuse |
| Graph | `knowledge/graph.py` | Reuse |
| Timeline | `knowledge/timeline.py` | Reuse |
| Provider abstraction | `providers/` | Reuse |
| Project knowledge | `solspire/project_knowledge.py` | Consume, do not duplicate |
| Project authorization | existing SolSpire authorization seams | Do not bypass |
| Web Prism | `web/public_prism/` | Add Grove UI incrementally |
| API | `api/` | Thin Grove routes only |
| Tests | `tests/` | Add domain + architecture tests |
| Documentation | `docs/architecture/` | Canonical Grove architecture docs |

### Proposed Wave 01 homes

```text
spiral_grove/
├── __init__.py
├── models.py              # Domain types / schemas
├── capabilities.py        # Capability registry and lookup
├── paths.py               # Learning path composition
├── calibration.py         # Calibration contracts + evaluation envelope
├── progression.py         # Learner state + next-action recommendations
├── evidence.py            # Evidence references and provenance
├── challenges.py          # EduLeague challenge definitions
├── cohorts.py             # Cohort membership / state
├── tools.py               # Tool metadata registry, no execution authority
├── consent.py             # Consent scope / data-use policy primitives
└── repository.py           # Persistence adapter; no duplicated Knowledge OS authority
```

API surface should initially be thin:

```text
api/spiral_grove_routes.py
```

Frontend should initially be composed into the existing Prism application rather than creating a separate application:

```text
web/public_prism/
├── components/spiral_grove/
└── pages/SpiralGrovePage.tsx
```

Exact frontend locations must be reconciled against the current navigation and route architecture before implementation.

---

## 9. PERSISTENCE STRATEGY

Wave 01 should use a dedicated Grove domain schema only for Grove-native state.

It must not duplicate:

- notes
- source documents
- graph edges
- embeddings
- project records
- provider records
- authorization records

Recommended Grove-native records:

```text
capabilities
learning_paths
learning_path_items
exercises
challenges
learner_capabilities
learner_enrollments
learner_evidence
cohorts
cohort_members
tools
consent_records
```

Where a record points to knowledge, files, projects, or artifacts, use stable references to the canonical source.

---

## 10. API CONTRACT

Initial read/write surface:

```text
GET  /api/spiral-grove/capabilities
GET  /api/spiral-grove/capabilities/{id}
GET  /api/spiral-grove/paths
GET  /api/spiral-grove/paths/{id}
POST /api/spiral-grove/calibrate
GET  /api/spiral-grove/learners/me/progress
GET  /api/spiral-grove/learners/me/recommendations
POST /api/spiral-grove/evidence
GET  /api/spiral-grove/challenges
GET  /api/spiral-grove/cohorts/{id}
GET  /api/spiral-grove/tools
```

No Wave 01 route may silently mutate external systems or submit consequential actions.

---

## 11. COMPANION ROUTER

The first companion capability is recommendation and orchestration, not unrestricted execution.

```text
Human Intent
     ↓
Context Assembly
     ↓
Capability State
     ↓
Available Resources
     ↓
Tool Metadata
     ↓
Recommendation
     ↓
Human Confirmation where required
     ↓
Bounded Action
     ↓
Evidence / Timeline
```

Autonomy classes:

| Class | Meaning |
|---|---|
| A0 | Observe / explain |
| A1 | Recommend / prepare |
| A2 | Execute reversible low-risk action |
| A3 | Execute inside explicitly approved workflow |
| A4 | Human approval required |
| A5 | Human-only authority |

Wave 01 primarily operates at A0–A1. Any A2 behavior must be explicit, reversible, logged, and tested.

---

## 12. TRUST & DATA GOVERNANCE

Spiral Grove is designed around capability development, not extraction of people.

### Principles

1. Learner data has a defined purpose.
2. Consent is explicit where required.
3. Participation is not conditional on unrelated data collection.
4. Learners can inspect meaningful records about themselves.
5. Evidence provenance is retained.
6. Research use is separate from operational learning use.
7. Child data receives stronger safeguards.
8. No advertising profiling from learner records.
9. No sale of identifiable learner records as a default business model.
10. Aggregation/anonymization must not be represented as automatically risk-free.
11. Consequential decisions require human review.
12. Memory/context remains contestable.

### Child Listening boundary

The Child Listening Project may inform curriculum design, but it is not silently embedded into ordinary student activity.

Any child research protocol must have its own consent/assent, purpose, retention, access, withdrawal, and publication rules.

---

## 13. A.I.S PROGRAM MAPPING

Programs are compositions over the same Grove capability graph.

### A.I.S Learning Lab

Primary capabilities:

- AI literacy
- critical thinking
- communication
- collaboration
- research
- creativity
- problem solving

### A.I.S Future Builder

Primary capabilities:

- AI/digital intelligence
- research systems
- systems thinking
- creative technology
- communication
- market/project execution

### A.I.S Professional Intelligence

Primary capabilities:

- AI workflows
- research
- operations
- automation
- decision architecture
- professional communication

### A.I.S Workforce Intelligence

Primary capabilities:

- role-specific capability mapping
- workforce upskilling
- workflow transformation
- human-AI collaboration
- organizational learning

### A.I.S Ground Intelligence

Primary capabilities:

- soil systems
- farm operations
- water systems
- food systems
- resource management
- sustainable agriculture

---

## 14. LEARNING INTELLIGENCE

Learning Intelligence is a derived analytical layer, not a new authority.

It should answer questions such as:

- Which capabilities are most requested?
- Where do learners commonly struggle?
- Which resources correlate with successful completion?
- Which exercises produce stronger evidence?
- Which learning paths have high abandonment?
- What improvements should be tested in the curriculum?

It must distinguish:

```text
OBSERVED
DERIVED
RECOMMENDED
INFERRED
UNKNOWN
```

No model-generated inference should be silently promoted to fact.

---

## 15. MEASUREMENT

Wave 01 should measure:

### Learner

- participation
- completion
- demonstrated capability
- evidence quality
- confidence/self-report
- project completion
- reflection

### Program

- enrollment → completion
- activity completion
- challenge participation
- facilitator workload
- learner satisfaction
- capability progression

### System

- recommendation acceptance
- recommendation correction rate
- provenance completeness
- failed tool calls
- unauthorized action attempts
- context retrieval quality

Measurement is for improvement, not automated ranking of human worth.

---

## 16. ARCHITECTURAL INVARIANTS

Wave 01 implementation must preserve these invariants:

### I1 — One canonical knowledge authority

Grove does not create a second Knowledge OS.

### I2 — One canonical provider abstraction

Grove does not call provider SDKs directly when the existing provider abstraction applies.

### I3 — Learning state is not authorization

A capability level, course completion, or recommendation never grants project or system authority.

### I4 — Evidence is source-backed

No fabricated evidence, achievement, or learner history.

### I5 — Recommendations are not commands

A recommendation does not execute by implication.

### I6 — Human authority remains explicit

Consequential actions require the appropriate human authorization path.

### I7 — Child research is separate

Educational delivery and research participation are distinct scopes.

### I8 — Derived intelligence remains derived

Aggregated or inferred learning insights must retain classification and provenance.

### I9 — Offline/local-first compatibility is preserved

Where the existing Knowledge OS contract requires local-first operation, Grove must not make cloud availability a hidden prerequisite.

### I10 — Existing architecture boundaries are strengthened, not bypassed

No new cross-layer imports may be introduced merely for implementation convenience.

---

## 17. TEST PLAN

Wave 01 requires tests for:

### Domain

- capability creation/lookup
- prerequisite resolution
- path ordering
- enrollment state
- evidence provenance
- challenge definitions

### Calibration

- bounded input
- deterministic envelope shape
- evidence creation
- no sensitive inference
- contestable recommendation

### Authorization

- learner state cannot grant execution authority
- recommendation cannot mutate external systems
- tool metadata cannot execute tools

### Architecture

- no Grove → provider SDK direct imports
- no Grove → second graph/vector authority
- no Grove → unauthorized project mutation
- no new kernel → api dependency without explicit architectural registration
- API routes remain thin

### Data governance

- consent scope required for research-classified records
- child research records cannot be implicitly created by ordinary learning telemetry
- visibility boundaries are enforced

---

## 18. IMPLEMENTATION SEQUENCE

### Pass SG-01 — Domain Foundation

Create the Grove domain package and canonical models.

No UI. No autonomous execution.

### Pass SG-02 — Capability Registry

Create capability definitions and prerequisite resolution.

### Pass SG-03 — Learning Path Engine

Compose capabilities, resources, exercises, and challenges.

### Pass SG-04 — Learner Progression

Persist learner capability state and evidence references.

### Pass SG-05 — Calibration

Implement bounded calibration and recommendation envelopes.

### Pass SG-06 — API Skin

Expose read/write contracts through thin FastAPI routes.

### Pass SG-07 — Prism Surface

Introduce the first Spiral Grove learner view inside existing Prism navigation.

### Pass SG-08 — EduLeague Integration

Connect challenge definitions to cohort activity.

### Pass SG-09 — Companion Routing

Add bounded recommendation/orchestration using existing Knowledge OS + provider infrastructure.

### Pass SG-10 — Pilot Instrumentation

Add measurement and ethically scoped learning analytics for the A.I.S pilot.

Each pass remains independently testable and reviewable.

---

## 19. FIRST VERTICAL SLICE

The first production slice should be deliberately small:

```text
User
 ↓
Select capability: AI Literacy
 ↓
Calibration
 ↓
Capability state
 ↓
Recommended 3-step path
 ↓
Learning resource
 ↓
Exercise
 ↓
Evidence submission
 ↓
Progress update
 ↓
Next recommendation
```

If this works cleanly, the same machinery can support Research Systems, Creative Technology, Systems Thinking, Communication, and Ground Intelligence without creating new product-specific engines.

---

## 20. DEFINITION OF DONE — WAVE 01

Wave 01 is complete when:

- [ ] canonical Grove domain exists
- [ ] capabilities can be registered and queried
- [ ] learning paths can be composed
- [ ] learner progression can be stored
- [ ] evidence is source-backed
- [ ] calibration can produce a bounded recommendation
- [ ] Knowledge OS is consumed rather than duplicated
- [ ] provider routing uses existing abstraction
- [ ] authorization boundaries are preserved
- [ ] child research is isolated from ordinary learning telemetry
- [ ] API contracts have tests
- [ ] architecture tests prevent forbidden dependencies
- [ ] a learner can complete the first vertical slice through Prism

---

## 21. FINAL ARCHITECTURAL STATEMENT

Spiral Grove is the capability-growth substrate of Arkadia Prism.

It turns the Prism from a place where a human can access intelligence into a place where a human can **develop, demonstrate, organize, and apply capability over time**.

The system's job is not to replace human cognition.

Its job is to reduce unnecessary cognitive overhead while preserving human intent, judgment, consent, and authority.

The governing loop is:

> **Human Intent → Arkadia Intelligence → Bounded Action → Evidence → Learning → Better Next Action.**

That is the Wave 01 foundation for A.I.S as a Living University and for Arkadia as a general-purpose human capability environment.
