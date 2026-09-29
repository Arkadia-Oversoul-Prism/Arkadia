# SOLSPIRE EXPERIENCE ARCHITECTURE v1

**Document type:** Mapping specification (not an implementation authorization)  
**Repository tip:** `3cc76afa198c868cba6fe4259a76a9d461ffddf1`  
**Trajectory:** ARKADIA-TRUTHFULNESS-01 **v7** (M01–M09 completed / accepted)  
**Parent law:** AEAS-v0.1.1 (FROZEN — Implementation NOT AUTHORIZED)  
**Worker law:** ARKADIA-WORKER-CONTRACT-v1 (merge/deploy human_only; TERMINATE at review)  
**Authority ceiling:** Level 2 — observe / map / propose  
**Status:** ARCHITECTURE RECORD ONLY  

> This document does **not** authorize M10, screen reconstruction, new APIs, schema migration, Weaver dispatch, AEAS activation, autonomous merge, or deploy.

---

## 0. Purpose and grammar

### Experience principle (freeze this, not a universal DB)

> Everything the human encounters in SolSpire should be addressable as contextual information with inspectable relationships and activity.

**One experience does not require one database.** Specialized substrates remain specialized.

### Conceptual grammar

```
SOLSPIRE
│
├── FIELD
│   ├── OBJECTS
│   ├── RELATIONSHIPS
│   └── ACTIVITY
│
├── LENSES
│
├── INTELLIGENCE
│   └── ARKANA
│
├── EXECUTION
│   └── WEAVER
│
└── GOVERNANCE
    ├── AUTHORITY
    ├── APPROVAL
    ├── VERIFICATION
    └── PROVENANCE
```

### Classification legend

| Label | Meaning |
|-------|---------|
| **EXISTS** | Directly represented in the repository at the tip SHA |
| **CONNECTED** | Exists with identifiable links to other substrate |
| **PARTIAL** | Substrate exists; proposed experience is not yet coherent |
| **LANDED** | In Git; may lack acceptance (N/A after v7 for M01–M09) |
| **ACCEPTED** | Trajectory completed + ACCEPT.json |
| **BOUNDARY** | Prohibited, subordinate, or human-gated |
| **MISSING** | No sufficient substrate found |
| **PROPOSED** | Experience concept only; needs future authorization |

### Epistemic columns (run through every map)

```
EXISTS → CONNECTED → EXPERIENCE GAP → PROPOSED
```

---

## MAP 01 · Object Ontology

| Object | Source | Backend | Persistence | Identity | Relationships | Activity | UI | Status |
|--------|--------|---------|-------------|----------|---------------|----------|-----|--------|
| **Project** | `project_store` / `project_manager` | `GET/POST /solspire/projects` | SQLite `projects` + durable mirror | Owner-scoped | Children: files, tasks, memory, conv, events | `log_event` on mutations | ProjectsWorkspace, ProjectDashboard | **ACCEPTED** (M01/M04) |
| **File** | `project_files` | `/projects/{id}/files*` + upload/copy | SQLite `project_files` | Belongs to project | Project BELONGS_TO | file_created etc. | Files tab, FilesWorkspace | **ACCEPTED** (M05) |
| **Conversation** | `project_conversations` | `/conversations*` | SQLite | Project-scoped | Messages under conv | Events | Conversations tab/lens | **EXISTS** / **CONNECTED** |
| **Task** | `project_tasks` | `/tasks*` | SQLite | Project-scoped | Project | Task events | Tasks tab/lens | **EXISTS** / **CONNECTED** |
| **Memory** | `project_memory` | `/memory*` | SQLite | Project-scoped | Project | Memory events | Memory tab/lens | **EXISTS** / **CONNECTED** |
| **Knowledge (project view)** | knowledge routes + corpus | `/knowledge`, `/search`, `/graph`, `/embeddings` | Existing knowledge + files | Project context | Sources listed; graph PARTIAL | Search hits | KnowledgePanel | **ACCEPTED** (M06) as binding |
| **Knowledge OS (global)** | `pages/knowledge/*` | Knowledge OS pages | Separate from project store | Global learner/builder surfaces | Graph views | — | KnowledgeOSPage lens | **EXISTS**; audience/IA debt possible |
| **Event (project)** | `project_events` + `log_event` | `GET .../events` | SQLite `project_events` | Project-scoped | Summary string + optional data | Itself is activity | Events tab / Observatory | **EXISTS** — **≠ provenance** |
| **WorkEvent** | Control-plane / Lab docs | Lab/CP routes | Separate spine (CP-MOVE3) | Lab vocabulary | **BOUNDARY:** WorkEvent ≠ provenance proof | Lab activity | Engineering Lab lens | **EXISTS** / **BOUNDARY** |
| **Repository (project link)** | `project_repositories` | `/repositories*` | SQLite | Project-scoped | Project | — | Repos tab | **EXISTS** |
| **Workflow** | ProjectDashboard workflows tab | project routes | Project store patterns | Project-scoped | — | — | workflows tab | **PARTIAL** |
| **Weaver session / plan** | `weaver/*`, `project_execution` | weaver analyze/context/capabilities; execute via PassSpec path | Evidence folders + git | Human-gated | Trajectory move | Evidence | Weaver tab / Engineering Lab | **EXISTS** / **BOUNDARY** |
| **PassSpec / PatchApproval** | `weaver/pass_spec`, execution | readiness → K15 | In-request / governed path | **Not** UI authority | Hash-bound | Execution evidence | Project execution UI | **EXISTS** / **BOUNDARY** |
| **Opportunity** | `lab/possibility` (if present on tip) | Lab possibility | Lab | Recognition-only | **BOUNDARY:** no auto_build | — | — | **PARTIAL** / Lab |
| **Transmission / public post** | social / NovaNet | transmissions API | Social substrate | Public field | Public ≠ private | Feed activity | NovaNet public field | **ACCEPTED** (M03) |
| **ReasoMate thread** | ReasoMateSurface | private conversational | Private substrate | Authenticated | **BOUNDARY:** not public field | — | ReasoMate mode | **ACCEPTED** (M02) |
| **Identity / User** | AuthContext, Firebase | `require_auth` | Firebase + profile | Session | Gates Solariun | — | Login / gate | **EXISTS** |
| **Trace / Release** | — | — | — | — | — | — | — | **MISSING** / **PROPOSED** as unified objects |
| **Intent object** | — | — | — | — | — | — | — | **PROPOSED** |

**No invented relationships.** Children of Project are table FKs / `project_id`, not a universal graph DB.

---

## MAP 02 · Surface / Lens Matrix

Lenses from `SolSpireExperience` (`LensContent`):

| Lens | Existing surface | Backend | Objects | Acceptance | Gap |
|------|------------------|---------|---------|------------|-----|
| **overview** | SolariunHomeCockpit | workspace/status patterns | summary | PARTIAL coherence | Not a full FIELD canvas |
| **projects** | ProjectsWorkspace | `/solspire/projects` | Project | **ACCEPTED** M04 | — |
| **commercial** | CommercialPanel | commercial APIs if any | offers | PARTIAL | Product depth unclear |
| **knowledge** | KnowledgeOSPage | Knowledge OS | global knowledge | EXISTS | ≠ project KnowledgePanel only |
| **files** | FilesWorkspace | upload + open project | File via projects | **ACCEPTED** M05 path | Cross-project Move deferred |
| **conversations** | ConversationsWorkspace | project conversations | Conversation | EXISTS | Continuity UX PARTIAL |
| **tasks** | TasksWorkspace | project tasks | Task | EXISTS | — |
| **memory** | WorkspaceCollection memory | project memory | Memory | EXISTS | — |
| **weaver** | WeaverSummary → project weaver | weaver + execution | Plan/PassSpec | EXISTS / BOUNDARY | Not primary nav hero |
| **observatory** | WorkspaceCollection events | project events | Event | EXISTS | Activity ≠ proof |
| **engineering-lab** | EngineeringLabLens | `/api/lab` + require_auth | Lab objects | EXISTS / BOUNDARY | Authenticated browser lens deferred historically |
| **settings** | SettingsPage + SourceSync | settings | — | EXISTS | — |
| **Project interior** | ProjectDashboard | all project routes | all project children | **ACCEPTED** M04 | Inspector sheet **PROPOSED** |

---

## MAP 03 · Relationship Grammar

| Relation | Exists? | Storage | Creator | Authoritative? | Inferred? | User-inspectable? | WorkEvent? | Knowledge OS? | Provenance? |
|----------|---------|---------|---------|----------------|-----------|-------------------|"|-----------|---------------|-------------|
| **BELONGS_TO** (child → project) | **YES** | `project_id` columns | API on create | **YES** (store) | No | Via project UI | Project events only | No | No |
| **REFERENCES** (knowledge → sources) | **PARTIAL** | knowledge sources payload | Knowledge routes | Partial | Possible | Panel shows sources | No | Yes (global) | **BOUNDARY** |
| **DERIVED_FROM** | **PARTIAL** | embeddings/status notes | System | No (honest NOT_AVAILABLE often) | Yes risk | Status strings | No | Partial | **BOUNDARY** |
| **CONNECTED_TO** (graph edges) | **PARTIAL** | knowledge graph endpoint | Graph builder | Unknown quality | Often | Graph UI | No | Yes | No |
| **GENERATED_BY** (Weaver/agent) | **PARTIAL** | evidence markdown, execution results | Worker/Lab | Evidence files | — | Evidence docs | Lab | No | Separate |
| **FOLLOW_UP_FOR** | **MISSING** | — | — | — | — | — | — | — | — |

**Lesson from Horizon II:** Do not implement a second hidden graph authority to make the experience pretty.

---

## MAP 04 · Context Propagation (Arkana)

Desired chain:

```
USER → SURFACE → OBJECT → PROJECT → FILES → KNOWLEDGE → CONVERSATION → TASKS → ACTIVITY → ARKANA
```

| Context element | Available today? | Mechanism |
|-----------------|------------------|-----------|
| Auth user | **EXISTS** | AuthContext / Firebase |
| Current lens/section | **EXISTS** | SolSpireExperience state |
| Current project | **EXISTS** when interior open | `project` state + ProjectDashboard |
| Files list | **EXISTS** | `/files` |
| Knowledge search | **EXISTS** | `/knowledge/search` |
| Conversations | **EXISTS** | `/conversations` |
| Tasks | **EXISTS** | `/tasks` |
| Events | **EXISTS** | `/events` |
| Unified Arkana context pack | **PARTIAL** | ArkanaCommune / overlays exist; not one governed context API |
| “Arkana understands everything” | **PROPOSED** / false | Must not claim |

**Arkana status:** **PARTIAL** intelligence surface; **BOUNDARY** — not an authorization authority.

---

## MAP 05 · Action / Authority Graph

```
OBSERVE → INTERPRET → PROPOSE → HUMAN DECISION → AUTHORIZE
    → WEAVER → EXECUTE → VERIFY → EVIDENCE → HUMAN REVIEW
```

| Action | Initiate | Authorize | Execute | Verify | Merge | Deploy |
|--------|----------|-----------|---------|--------|-------|--------|
| Browse Solariun | User (auth) | Session | Client | — | — | — |
| CRUD project children | User (owner) | `require_project_owner` | API/store | — | — | — |
| Public NovaNet read | User/public rules | Route policy | API | — | — | — |
| ReasoMate private | Authenticated user | Auth | Private surface | — | — | — |
| Weaver propose/analyze | User in project | Project access ≠ PassSpec | Analyze routes | — | — | — |
| Governed patch execute | Human | **PassSpec + PatchApproval** | **K15 → K3** | Tests/evidence | **Human** | **Human** |
| Trajectory advance | Architect | ACCEPT.json | Router read | Verification | Human | Human |
| Worker session | Scheduler/manual | Trajectory + dry_run | NullAdapter default | Report | **false** | **false** |

**Worker contract (ACCEPTED M09):** `merge: false`, `deploy: false`, `continues_to_next_move: false` at TERMINATE.

**AEAS (ACCEPTED freeze M07):** Implementation **NOT AUTHORIZED**.

---

## MAP 06 · Activity Grammar

| Event class | Exists today? | Source |
|-------------|---------------|--------|
| FILE_* | **YES** | `log_event` / file routes |
| TASK_* | **YES** | task routes + events |
| CONVERSATION_* | **PARTIAL** | conv routes; event coverage varies |
| MEMORY_* | **PARTIAL** | memory routes |
| KNOWLEDGE_CONNECTED | **PARTIAL** | knowledge panel / graph |
| ARKANA_INVOKED | **PARTIAL** | client-side commune |
| WEAVER_* | **PARTIAL** | evidence + execution results |
| VERIFICATION_COMPLETED | **YES** (control plane) | VERIFICATION.md / CP10 history |
| MEMORY_CONFIRMED | **PROPOSED** as first-class UX | — |

**Event shape (project_events):** id, project_id, type, summary, data?, timestamps — **not** full causal provenance.

**Hard rule:** **WorkEvent ≠ provenance.** Activity UI must not launder events into proof.

---

## MAP 07 · Responsive Composition

| Viewport | Pattern | Status |
|----------|---------|--------|
| Desktop | FIELD + optional inspector | FIELD **PARTIAL**; inspector **PROPOSED** |
| Tablet | FIELD + sheet | **PROPOSED** composition |
| Mobile | Bottom nav + sheets | MobileNav **EXISTS**; object sheet grammar **PARTIAL** |

**Attention states (not three permanent columns):**

```
FIELD → OBJECT → INTELLIGENCE (Arkana)
```

---

## MAP 08 · Repository Reality Matrix

| Concept | UI | API | Persistence | Relationship | Evidence | Authority | Status |
|---------|----|-----|-------------|--------------|----------|-----------|--------|
| Project | ✓ | ✓ | ✓ | BELONGS_TO children | M01/M04 ACCEPT | Human + owner | **ACCEPTED** |
| File | ✓ | ✓ | ✓ | project_id | M05 ACCEPT | Owner | **ACCEPTED** |
| Knowledge (project) | ✓ | ✓ | existing | PARTIAL | M06 ACCEPT | Owner | **ACCEPTED** |
| Conversation | ✓ | ✓ | ✓ | project_id | — | Owner | **EXISTS** |
| Task | ✓ | ✓ | ✓ | project_id | — | Owner | **EXISTS** |
| Memory | ✓ | ✓ | ✓ | project_id | — | Owner | **EXISTS** |
| Project Event | ✓ | ✓ | ✓ | project_id | — | Owner | **EXISTS** / ≠ provenance |
| NovaNet public | ✓ | ✓ | social | public field | M03 ACCEPT | Public rules | **ACCEPTED** |
| ReasoMate | ✓ | ✓ | private | private | M02 ACCEPT | Auth | **ACCEPTED** |
| PassSpec path | ✓/partial | ✓ | governed | hash binding | Weaver tests | **BOUNDARY** | **EXISTS** |
| Arkana full context | PARTIAL | PARTIAL | — | — | — | Human | **PARTIAL** |
| Object inspector | — | — | — | — | — | Human | **PROPOSED** |
| Universal search | — | — | — | — | — | Human | **PROPOSED** |
| Intent objects | — | — | — | — | — | Human | **PROPOSED** |
| Automation ontology | — | — | — | — | — | Human | **PROPOSED** |
| Universal object DB | — | — | — | — | — | — | **BOUNDARY** (do not build) |

---

## AEAS alignment (why this is memory, not hands)

| AEAS principle | This document |
|----------------|---------------|
| Authority ceiling Level 2 | Mapping only |
| Implementation NOT AUTHORIZED | No code activation |
| Human authorization required for execution | Explicit |
| Worker subordinate | Referenced, not expanded |
| No autonomous merge/deploy | Restated |
| Lab records / does not redefine authority | Cartography only |

**Storage for memory:** `docs/architecture/SOLSPIRE_EXPERIENCE_ARCHITECTURE_v1.md`  
**Companion binary:** `docs/architecture/SOLSPIRE_EXPERIENCE_ARCHITECTURE_v1.docx`

---

## Explicit non-goals of v1

- No M10  
- No pixel redesign  
- No new graph database  
- No AEAS activation  
- No Weaver dispatch from this doc  
- No schema migration  
- No Horizon III declaration  

---

## Next authorized uses (when Architect chooses)

1. Gap-prioritized experience proposals **traced to EXISTS substrate**  
2. Verification of any future UI change against MAP 02 / MAP 08  
3. Refusal of “universal object store” proposals as **BOUNDARY**  

---

*End of SolSpire Experience Architecture v1 — repository-grounded @ 3cc76afa.*
