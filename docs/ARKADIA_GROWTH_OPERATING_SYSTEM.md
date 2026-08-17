# Arkadia Growth Operating System

**Status:** SPECIFICATION — Phase 4B
**Authority:** operating specification, not an implementation. This document
defines how we *use* the proven conversational spine to conduct growth. It
deliberately specifies more than is built, so real usage reveals which slice to
implement first. Per the Phase 4B directive: **build Arkadia by using Arkadia.**
Do not implement this spec wholesale — implement only the slice that the next
bottleneck demands.

---

## 0. The new north star

> **BUILD ARKADIA BY USING ARKADIA.**

Not: build Arkadia → eventually use Arkadia.

Every proposed capability must answer:

> Does this reduce the cognitive/operational cost of doing real work through Arkadia?

Real work = research, writing, publishing, distribution, audience development,
relationship building, lead generation, sales, product development, delivery,
customer feedback, analytics, strategic decision-making.

The target closed loop:

```
work → knowledge → reusable assets → distribution → relationships
   → revenue → feedback → knowledge
```

---

## 1. Purpose

Arkadia as a **Personal Growth Operating System**: a control plane that turns
real work into knowledge, knowledge into distribution-ready assets, assets into
relationships, relationships into opportunities, and outcomes back into
knowledge — with the human approving every consequential step.

The product metric is not "posts published." It is:

> **Founder Cognitive Load per Meaningful Outcome** — more meaningful outcomes
> (qualified leads, revenue, published authority, high-value relationships,
> partnerships, completed delivery) per unit of founder attention.

---

## 2. Architectural position

```
ONE INTELLIGENCE SPINE
        ↓
ONE KNOWLEDGE SUBSTRATE  (the proven Knowledge OS)
        ↓
ONE CANONICAL WORK / CONTENT MODEL  (Work Object + Content Object)
        ↓
MANY DISTRIBUTION SURFACES  (adapter pattern)
        ↓
ONE FEEDBACK LOOP  (signals → Knowledge OS → next action)
```

**Growth OS is not another brain.** It is an operational layer over the
Knowledge OS. A Lead is a Knowledge OS entity/view before it becomes a new
database. There is one substrate; Growth OS provides operational views onto it.

The control-plane diagram:

```
HUMAN
   │  intent / judgement
   ▼
┌─────────────────┐
│  ARKADIA PRISM   │
│  CONTROL PLANE   │
└────────┬────────┘
         │
   ┌─────┼─────┐
   ▼     ▼     ▼
COGNITION  KNOWLEDGE  GROWTH
(Oracle/   (memory,    (work, content,
 Arkana)   retrieval,  distribution,
           timeline,   audience, leads,
           graph)      offers, delivery,
                       analytics)
         │
         ▼
   PUBLIC WORLD
   (people, platforms, orgs)
         │
         ▼
      SIGNALS
         │
         ▼
   KNOWLEDGE OS ──► NEXT ACTION
```

---

## 3. Work Object

Not everything begins as content. A partner conversation, a customer objection,
a research question, a delivery issue — these are work, not content. The Work
Object is the broader abstraction; Content Object is a specialization.

### Schema (map, not MVP)

```
WORK_OBJECT
├── id
├── type            (see below)
├── source          (oracle conversation | manual | external signal)
├── project
├── owner
├── created_at
├── status
├── priority
├── context
├── relationships   (→ other work objects, notes, people)
├── next_action
├── outcomes
└── provenance      (linked back to the Knowledge OS note/thread that birthed it)
```

### Types

`idea`, `research`, `decision`, `question`, `content_opportunity`,
`relationship`, `lead`, `offer`, `sale`, `delivery`, `feedback`,
`experiment`, `open_loop`

```
WORK_OBJECT
   ├── research
   ├── relationship
   ├── lead
   ├── product
   └── content   ──► CONTENT_OBJECT
```

This prevents the classic mistake of turning a CMS into a pseudo-OS.

---

## 4. Content Object

A Content Object is a Work Object specialized for distribution. It carries one
canonical meaning and many distribution assets.

```
CONTENT_OBJECT
identity
├── id
├── source_work_id      (the Work Object it was derived from)
└── canonical_url

meaning
├── title
├── core_idea
├── thesis
├── audience
├── project
├── claim_type
└── evidence

assets
├── canonical           (the owned long-form)
├── article
├── newsletter
├── linkedin
├── x
├── facebook
├── video_script
├── visual
└── cta

campaign
├── objective
├── funnel_stage
├── offer
└── experiment

distribution
├── surface
├── status
├── scheduled_at
├── published_at
└── external_id

measurement
├── impressions
├── engagement
├── clicks
├── leads
├── conversions
└── revenue
```

**Do not implement every field immediately.** The schema is the map. The MVP is
much smaller — see §8.

---

## 5. Distribution model (adapter pattern)

```
ARKADIA CORE
     │
 Content Object
     │
 Distribution API
     │
 ┌───┼───┐
 ▼   ▼   ▼
LinkedIn  Substack  (other)
Adapter   Adapter   Adapter
   │       │
   ▼       ▼
Platform  Platform
```

The core never knows a platform's API peculiarities. Arkadia knows only:
"publish this canonical asset." The adapter knows the platform.

### Adapter contract (tiny)

```
publish(content_object)  → external_id
status(content_object)   → published | failed
metrics(external_id)     → available metrics
ingest_event(...)        → Knowledge OS
```

No platform-specific intelligence inside the core.

### Adapter must be replaceable

A platform can be swapped by replacing its adapter. The core's Content Object
and Distribution API are stable; adapters are the volatile edge.

---

## 6. Channel roles (model by function, not by API)

| Channel | Function |
|---|---|
| **Substack** | Authority — long-form thinking, research, essays, intellectual positioning |
| **LinkedIn** | Professional credibility + relationships — research, founder perspective, partnerships, high-value connections |
| **X** | Discovery / public conversation — ideas, threads, live thinking, network discovery |
| **Facebook** | Community / broader public reach — accessible explanations, announcements, stories |
| **Arkadia website / canonical repository** | Owned canonical layer — the place that ultimately belongs to us |

One idea → canonical asset → {Substack, LinkedIn, X, Facebook} → owned home → lead.

---

## 7. Relationship model

A relationship is a Work Object of type `relationship`, linked to Knowledge OS
notes (the conversations that formed it) and to leads/offers downstream.

Minimum representable facts per relationship:
- who (person/org, linked to source signal)
- origin (which surface / conversation / content they engaged with)
- expressed problem / interest
- last touch + next action
- status (cold / warm / active / committed / delivered)

---

## 8. Lead model + the first operational loop

The canonical funnel (representable, not all built):

```
ATTENTION → INTEREST → TRUST → RELATIONSHIP → LEAD → QUALIFICATION
   → OFFER → SALE → DELIVERY → RESULT → PROOF → AUTHORITY → ATTENTION
```

The system must eventually answer:
- Where did this lead come from?
- What did they engage with?
- What problem did they express?
- Which offer is relevant?
- What conversation happened?
- What is the next action?
- Did they convert?
- What did we learn?

### The first Growth OS loop (MVP)

```
REAL WORK
   ↓
ARKADIA CAPTURE  (via the proven Oracle Chat spine)
   ↓
KNOWLEDGE OS  (archived, retrievable across surfaces — proven)
   ↓
CONTENT OPPORTUNITY  (Arkana derives from real work)
   ↓
CANONICAL CONTENT  (drafted)
   ↓
HUMAN APPROVAL
   ↓
DISTRIBUTION  (manual first; adapter later)
   ↓
RESPONSE  (captured)
   ↓
KNOWLEDGE OS
```

Not "can we auto-post to 12 platforms?" — but "can Arkana take something we
genuinely produced, transform it into a distribution-ready asset, help us
publish it, and remember what happened?"

---

## 9. Offer / revenue model

Revenue is a first-class loop, not vanity metrics. Every meaningful funnel
transition should eventually become representable in the Knowledge OS. A Lead,
Offer, Sale, Delivery, and Result are all Work Objects (§3) linked through the
provenance chain back to the originating content/relationship.

Growth OS must not become a vanity-metrics engine. The through-line is:
attention → trust → relationship → qualified lead → offer → sale → delivery →
proof → authority → attention.

---

## 10. Metrics

| Metric | Definition |
|---|---|
| Growth Efficiency | Meaningful outcomes / founder hours |
| Meaningful outcomes | qualified leads, revenue, published authority, high-value relationships, partnerships, completed delivery |
| Founder cognitive load | founder hours consumed per meaningful outcome |

The product metric for Growth OS is **more meaningful outcomes per unit of
founder attention** — over time.

---

## 11. Human approval boundary (governance feature)

```
ARKADIA
   ├── captures
   ├── analyses
   ├── drafts
   ├── repurposes
   ├── recommends
   └── prepares
          │
          ▼
       HUMAN APPROVES
          │
          ▼
     AUTOMATION EXECUTES
```

Human approval is required for: public claims, research, reputational
statements, sales offers, relationship communication, publishing, and any
consequential external action. This is not friction; it is the operational
embodiment of the research principles Arkadia is built around.

---

## 12. Daily operating loop

Every operating day, Arkadia should be able to answer:

```
ARKADIA — TODAY
🔥 ONE PRIORITY
📚 KNOWLEDGE       — what did we learn?
✍️ CREATION        — what should we create?
📣 DISTRIBUTION    — what is ready to publish?
🤝 RELATIONSHIPS   — who needs attention?
💰 REVENUE         — which opportunities need action?
📦 DELIVERY        — what commitments are due?
🔁 OPEN LOOPS      — what remains unresolved?
📈 SIGNALS         — what changed?
🎯 ONE HIGH-LEVERAGE ACTION — greatest expected value today
```

The purpose is to reduce decision fatigue, not to generate a giant dashboard.

---

## 13. Content queue

```
IDEA → CAPTURED → SELECTED → DRAFTING → READY → APPROVED → PUBLISHED → MEASURED → REPURPOSE
```

Every real piece of published work passes through this queue. This gives Arkadia
operational memory of the publishing life — something it currently lacks.

---

## 14. Content opportunity derivation

Arkadia should derive public work from actual work, not generate generic posts:

| Real-work signal | Derived content |
|---|---|
| Research finding | Content opportunity |
| Repeated question | Explainer |
| Objection | Sales content |
| Customer result | Case study |
| Strong public response | Repurpose |
| New connection | Relationship action |
| Unanswered question | Research task |
| Product demand | Offer opportunity |

---

## 15. Weekly review

- What did we create?
- What did we publish?
- What generated attention? conversations? leads? revenue?
- What consumed time?
- What repeated?
- What should be automated?
- What should be deleted?

---

## 16. Automation rules + decision filter

Every proposed feature must pass A–F or be deferred:

- **A.** Does it use the existing spine? (no → reject/defer)
- **B.** Does it reduce real operational friction? (no → defer)
- **C.** Can we accomplish it with an existing external service? (yes → orchestrate before rebuilding)
- **D.** Does it create reusable operational knowledge? (no → question its value)
- **E.** Does it preserve human approval where consequences matter? (no → redesign)
- **F.** Does it produce measurable growth or learning? (no → deprioritize)

---

## 17. 30-day operational experiment

Do not build a 90-day software roadmap. Run a 30-day Arkadia-as-OS experiment.

**Every day:** use Arkadia for capture, research, decisions, content,
publishing preparation, relationships, leads, offers, open loops.

**Every week:** run §15 review.

**Day 30 — ask:** where is the human repeatedly doing work that Arkadia now
understands well enough to orchestrate? That becomes the next automation target.
Not the other way around.

---

## 18. Do NOT build (yet)

- CS2 / UI redesign
- A separate CRM
- A separate analytics platform
- Ten integrations
- Autonomous publishing
- A duplicate memory system
- A duplicate context engine
- A broad refactor

Use first. Build only the smallest slice that removes the next observed
bottleneck.

---

## 19. Future adapter architecture (reference, not now)

When §17 reveals the first bottleneck (default hypothesis: LinkedIn, because it
simultaneously tests content distribution, professional credibility,
relationship discovery, inbound opportunity, and lead generation), build exactly
one adapter against the §5 contract. The core stays platform-agnostic; the
adapter is the only place that knows LinkedIn.

---

## 20. Invariants

```
ONE INTELLIGENCE SPINE
ONE KNOWLEDGE SUBSTRATE
ONE CANONICAL WORK / CONTENT MODEL
MANY DISTRIBUTION SURFACES
ONE FEEDBACK LOOP
CONTESTABLE MEMORY            (human-owned, retrievable, correctable)
HUMAN AGENCY ABSOLUTE          (AI prepares; human approves; automation executes)
WARMTH WITHOUT DEPENDENCY      (attention without attachment)
CONTINUITY WITHOUT FABRICATION (empty retrieval = no continuity claim)
```

---

## 21. The phase transition this spec encodes

```
PHASE 1  Architecture
PHASE 2  Construction
PHASE 3  Agent Governance
PHASE 4  Operational Proof        ← Gate A PASSED (commit 0242b79)
████████████████████████████████
          WE ARE HERE
████████████████████████████████
PHASE 4B Contract Freeze          ← this doc + the Runtime Contract
PHASE 4C Daily Operational Use    ← starts now, manual
PHASE 4D Growth OS MVP            ← the first slice §17 exposes
PHASE 4E Distribution Adapter     ← one adapter, LinkedIn default
PHASE 4F Feedback + Analytics
PHASE 5  Product / Surface Expansion
```

The new invariant:

> **One spine. Many surfaces. One operating loop.**
>
> Think → Capture → Remember → Create → Approve → Distribute → Connect →
> Convert → Deliver → Learn → Remember.

The next proof is not another technical demo. It is:

> Can a real week of our life run through Arkadia and come out the other side
> with more published work, more relationships, more opportunities, less
> cognitive load, and better knowledge than went in?
