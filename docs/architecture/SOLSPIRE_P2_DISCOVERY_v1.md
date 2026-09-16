# SOLSPIRE P2 EXPERIENCE SUBSTRATE DISCOVERY v1

**Authorization:** SOLSPIRE-P2-DISCOVERY-01  
**Type:** Discovery report only — **not** implementation authorization  
**HEAD inspected:** `3a056da7109cf5aff7a64f8733f8b1cb5f4b6753`  
**Parent:** `SOLSPIRE_GAP_PROPOSALS_v1.md` §P2  
**AEAS:** FROZEN — Implementation NOT AUTHORIZED  

> No P2 implementation, schema migration, new graph DB, new authority layer, provenance/WorkEvent redefinition, K15/K3 changes, AEAS activation, or Weaver dispatch is authorized by this document.

---

## Method

For each P2 proposal:

`EXISTS → PARTIAL → MISSING → APIs → persistence → authority → verification → schema → security → dependencies → forbidden → future acceptance criteria`

---

## 1. Universal Search

### EXISTS
- **UI:** `SearchOverlay` in `SolSpireExperience.tsx` — labeled “Universal search” / “Search Solariun”
- **Client:** `web/public_prism/src/lib/knowledgeApi.ts` → `search()` against Knowledge OS groups: `semantic`, `fulltext`, `project`, `timeline`
- **API family:** `/api/knowledge/*` (Knowledge OS), not a unified Solariun object index
- **Project knowledge search:** `POST /solspire/projects/{id}/knowledge/search` (project-scoped keyword path)

### PARTIAL
- Overlay **placeholder** claims files, conversations, tasks, memory — implementation path is **Knowledge OS search**, not cross-object federation
- Semantic channel depends on embeddings status (often **NOT_AVAILABLE** / honest degradation)
- No single ranking across Project + File + Task + Conversation + Memory tables

### MISSING
- Unified search index over `project_files`, `project_tasks`, `project_conversations`, `project_memory`, `project_events`
- Cursor/pagination contract for mixed object types
- Permission-aware multi-project search beyond current Knowledge OS rules

### Required APIs (if ever authorized)
- Either: federated aggregator over existing list/search endpoints with explicit type tags  
- Or: new search service (would be **new substrate** — requires separate architecture auth)

### Required persistence
- **Prefer none new** — query existing stores  
- Full-text index table would be **schema migration** (forbidden under this discovery packet)

### Authority boundaries
- Knowledge OS auth + `require_auth` / project owner guards  
- Search results must not elevate to execution authority

### Verification path
- Source tests for overlay + knowledgeApi; runtime search depends on Knowledge OS availability  
- No ACCEPT path for “universal” behavior today (P2 not accepted)

### Schema implications
- **None required** for discovery  
- Implementation option A (federation): no schema  
- Option B (index): new tables/migrations — **out of scope unless authorized**

### Security implications
- Cross-object search can leak cross-project data if owner checks are weak  
- Must preserve `require_project_owner` per project corpus

### Architectural dependencies
- Knowledge OS + SolSpire project store duality (P1.3 library vs project corpus)

### Explicit forbidden changes
- Claiming SearchOverlay is already true universal object search  
- New graph DB for search  
- Silent embedding fabrication

### Recommended future acceptance criteria
1. Documented object types actually queried  
2. Per-type owner isolation tests  
3. Explicit degradation when semantic channel unavailable  
4. UI label matches real coverage (no false “universal”)

---

## 2. Intent Objects

### EXISTS
- **None** as a first-class `Intent` entity in SolSpire project store  
- Related **PARTIAL** concepts: trajectory **moves**, Lab **proposals** (`proposal_manager`), Weaver **objectives** (string on analyze/PassSpec), WorkEvent types list may include proposal-like vocabulary

### PARTIAL
- Human intent appears as free-text `objective` on Weaver flows  
- Control-plane moves are Architect intent at trajectory level — not user Intent objects in Solariun FIELD

### MISSING
- `intent` table / API CRUD  
- Linkage Intent → Project → Task → Evidence  
- UI object type “Intent” in field grammar

### Required APIs
- New CRUD + list-by-project (does not exist)

### Required persistence
- New store or extension of project DB — **schema change**

### Authority boundaries
- Intent must not authorize K15/PassSpec by existing  
- Architect trajectory intent ≠ user Intent object

### Verification path
- None for Intent objects (MISSING)

### Schema implications
- **High** — new entity

### Security implications
- Intent content may be sensitive; owner-scoped

### Architectural dependencies
- Object grammar in Experience Architecture v1 marks Intent as **PROPOSED**  
- Risk of collapsing into universal object ontology

### Explicit forbidden changes
- Treating PassSpec objective as Intent object store  
- Auto-executing intents via AEAS (freeze)

### Recommended future acceptance criteria
1. Explicit schema + owner scope  
2. Intent ≠ authorization  
3. No auto-execute  
4. Separate trajectory move authorization

---

## 3. Provenance Inspector

### EXISTS
- **Project activity:** `project_events` + `log_event` + Events UI / P0.2 activity feed (activity **≠** provenance)  
- **WorkEvent spine:** `solspire/workevent_manager.py`, `workevent_router.py` — continuity records, authenticated  
- **Control-plane evidence:** EVIDENCE / VERIFICATION / ACCEPT files (human process provenance)  
- **Governance hashes:** pass_spec_hash / patch_hash on execution path

### PARTIAL
- WorkEvent is **continuity**, documented as **not** full causal provenance proof  
- Experience Architecture hard rule: **WorkEvent ≠ provenance**  
- No single inspector UI that chains file→task→knowledge→patch→verify as proof

### MISSING
- Provenance graph store  
- Cryptographic or append-only proof chain for arbitrary field objects  
- Inspector that **correctly** labels activity vs WorkEvent vs ACCEPT evidence vs patch hashes

### Required APIs
- Prefer **composition** of existing: events, workevents, evidence paths, execution result hashes  
- New provenance API only if composition insufficient (separate auth)

### Required persistence
- Prefer existing tables + evidence files  
- New provenance tables = schema + semantic risk

### Authority boundaries
- Inspector is **read-only** observation  
- Must not upgrade activity to legal/causal proof  
- Must not bypass PassSpec

### Verification path
- Architecture tests / boundary docs; WorkEvent tests if present  
- UI must carry explicit epistemic labels

### Schema implications
- Composition: **none**  
- New provenance model: **major** + forbidden redefinition under this packet

### Security implications
- Over-claiming proof can mislead operators  
- WorkEvent access already auth-bound

### Architectural dependencies
- P0.2 activity feed, M09 worker evidence, M07 AEAS freeze (no silent autonomy proof)

### Explicit forbidden changes
- Redefining WorkEvent as provenance  
- Provenance semantic rewrite  
- Laundering `log_event` into proof

### Recommended future acceptance criteria
1. Epistemic labels mandatory (ACTIVITY / CONTINUITY / EVIDENCE / HASH)  
2. No single “proven” badge without criteria  
3. Read-only  
4. Tests that refuse WorkEvent≡provenance

---

## 4. Automation Ontology

### EXISTS
- **AEAS-v0.1.1** frozen specification (hands **not** authorized)  
- **Worker contract** — subordinate, TERMINATE at review, merge/deploy human_only  
- **Lab possibility** / Opportunity recognition paths (where present) — **no auto_build** posture in Phase 8 design  
- **Trajectory / scheduler** — cadence, not autonomous product automation ontology for Solariun users

### PARTIAL
- Opportunity / proposal vocabulary in Lab  
- Weaver bounded execution under PassSpec (governed, not automation ontology for end-users)

### MISSING
- User-facing automation ontology (triggers, rules, agents-as-objects) in Solariun FIELD  
- Safe automation catalog bound to AEAS levels

### Required APIs
- Would require AEAS implementation authorization (currently **NOT AUTHORIZED**)

### Required persistence
- Policy/rules store — new substrate under AEAS-shaped auth

### Authority boundaries
- **AEAS freeze** is controlling  
- Worker must not gain auto-merge  
- UI automation must not become K15 authority

### Verification path
- AEAS + worker contract tests; Lab possibility no-auto-build tests if present

### Schema implications
- High if implementing; **blocked** by AEAS freeze for activation

### Security implications
- Automation is highest risk surface for authority creep

### Architectural dependencies
- M07 ACCEPT freeze, M09 worker contract, PassSpec/K15 stack

### Explicit forbidden changes
- AEAS activation via “ontology” packaging  
- auto_build / autonomous deployment  
- Reinterpreting freeze as soft guidance

### Recommended future acceptance criteria
1. Explicit Architect revocation/amendment of AEAS freeze or scoped exception  
2. Level-gated capabilities  
3. No merge/deploy autonomy  
4. Human review termination preserved

---

## Summary matrix

| P2 proposal | EXISTS | PARTIAL | MISSING | Implementable without new architecture? |
|-------------|--------|---------|---------|----------------------------------------|
| Universal Search | Knowledge OS search + overlay | Label vs coverage gap | Federated project-object index | **Only** as honest federation + label fix — still needs auth |
| Intent Objects | — | objective strings / proposals | Entity + API + UI | **No** — needs schema + move |
| Provenance Inspector | events, WorkEvent, evidence, hashes | Continuity ≠ proof | Proof model + honest UI | **Partial** composition possible **with** strict labels; full provenance **No** |
| Automation Ontology | AEAS text, worker, Lab opportunity | Recognition-only | Runtime automation | **No** — AEAS freeze |

---

## Packet completion

| Deliverable | Status |
|-------------|--------|
| Discovery report | **THIS FILE** |
| Implementation | **NOT PERFORMED** |
| Schema migration | **NONE** |
| Merge | human_only |
| Deploy | human_only |
| Continuation | **No P2 implementation implied** |

