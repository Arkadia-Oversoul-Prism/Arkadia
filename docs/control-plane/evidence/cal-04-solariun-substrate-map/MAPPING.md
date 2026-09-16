# CAL-04 — Solariun Substrate Projection Map

**Move ID:** CAL-04  
**Title:** Solariun substrate projection map  
**Status:** IMPLEMENTED — MAPPING ONLY  
**Authority:** Human-authorized CAL-04  
**Branch:** `docs/cal-04-solariun-substrate-map`  
**Base:** `main` at `4d668dae851c18a2aafab74081a2630f9db13b6b`  
**Scope:** Repository archaeology and canonical substrate mapping only.  

## 1. Operating boundary

This record does not introduce a new UI surface, API, persistence layer, ontology, conversation system, database, execution path, authorization semantics, WorkEvent semantics, or K15/K3 change.

The purpose is to make the existing Solariun substrate explicit before any future projection change is implemented.

## 2. Current canonical experience shell

`web/public_prism/src/components/solspire/SolSpireExperience.tsx` is the canonical SolSpire experience shell. It owns the Solariun lens model and currently exposes:

- overview / Home
- projects
- commercial
- knowledge
- files
- conversations
- tasks
- memory
- weaver
- observatory / Activity
- engineering-lab
- settings

The shell also preserves project-context routing through `PROJECT_LENS_TO_TAB`, allowing an open project to remain the contextual owner for files, tasks, conversations, memory, knowledge, Weaver, events, and project overview.

## 3. Home projection: proven substrate

`web/public_prism/src/components/solspire/SolariunHomeCockpit.tsx` currently consumes these existing Solariun API functions:

- `getSolariunPulse()`
- `getSolariunWorkload()`
- `getSolariunWorkEvents()`
- `getSolariunSynthesis()`
- `getSolariunProposals()`

It uses `Promise.allSettled`, tracks live-surface failures, and renders truthful empty/failure states rather than substituting dummy data.

Current Home composition therefore has a verified code-level relationship to the Solariun status substrate, but not yet to every deeper SolSpire surface.

## 4. Existing object/lens matrix

| Surface | Existing UI | Existing API/substrate | Persistence / source | Current relationship to Home | Status |
|---|---|---|---|---|---|
| Pulse | `SolariunHomeCockpit` | Solariun pulse API | Solariun substrate | Direct | EXISTS / CONNECTED |
| Workload | `SolariunHomeCockpit` | Solariun workload API | Solariun workload substrate | Direct | EXISTS / CONNECTED |
| WorkEvents | `SolariunHomeCockpit`, Activity/Engineering surfaces | Solariun WorkEvent APIs | Control-plane spine | Direct, with boundary | EXISTS / BOUNDARY |
| Synthesis | `SolariunHomeCockpit` | Solariun synthesis API | Solariun synthesis substrate | Direct | EXISTS / CONNECTED |
| Proposals | `SolariunHomeCockpit` | proposal APIs | Solariun proposal substrate | Direct | EXISTS / CONNECTED |
| Projects | `ProjectsWorkspace`, `ProjectDashboard`, `ProjectOverview` | `/solspire/projects` and project routes | `project_store` / SQLite | Via project lens, not Home projection | EXISTS / ACCEPTED |
| Files | `FilesWorkspace`, ProjectDashboard Files | `/solspire/projects/{id}/files*` | project files | Project-scoped | EXISTS / ACCEPTED |
| Knowledge | `KnowledgeOSPage`, project Knowledge surface | Knowledge OS + project knowledge routes | Existing knowledge substrate | Separate lens | EXISTS / ACCEPTED |
| Tasks | `TasksWorkspace`, ProjectDashboard Tasks | `/solspire/projects/{id}/tasks*` | project store | Project-scoped | EXISTS / CONNECTED |
| Memory | workspace/project memory | `/solspire/projects/{id}/memory*` | project store / existing memory substrate | Project-scoped | EXISTS / CONNECTED |
| Conversations | `ConversationsWorkspace`, project conversation surface | `/solspire/projects/{id}/conversations*` | `project_conversations` | Project-scoped | EXISTS / CONNECTED |
| Activity / project events | Activity / Observatory surfaces | project events routes | `project_events` | Distinct from WorkEvent | EXISTS / BOUNDARY |
| Workflow | ProjectDashboard workflows | project workflow patterns | project substrate | Not mapped into Home | PARTIAL |
| Weaver | `WeaverSummary`, project Weaver surface, Engineering Lab | Weaver analysis/execution interfaces | governed evidence + git | Deep lens | EXISTS / BOUNDARY |
| Profile / identity | `AuthContext`, `PersonalCodex`, `PersonalEchofeild` | Firebase + `/api/me` / codex context | Firebase/profile + existing codex substrate | Identity context exists; Home binding not established | EXISTS / PARTIAL |
| Personal Codex | `PersonalCodex` | existing personal codex/profile path | existing personal codex substrate | Personal Echofeild identity layer | EXISTS / CONNECTED |
| Personal Echofeild | `PersonalEchofeild` | `/api/echoes` plus client-side Knowledge OS / SolSpire project data | existing Echo/Knowledge substrate | Separate personal-field surface | EXISTS / CONNECTED |
| Stellar / Interstellar Cartography | `StellarCartography` | `/api/stellar-cartography` | `kernel/stellar.py` | Existing NovaNet / Encyclopedia surface; no canonical Home binding established | EXISTS / SEPARATE |
| Oracle | `ArkanaCommune` | shared Oracle spine / `/api/commune/resonance` family | `api/oracle_spine.py` + existing memory/context engine | Must remain distinct from project conversation topology | EXISTS / BOUNDARY |
| Arcana Commune / ReasoMate | `ArkanaCommune`, `ReasoMatePage` | shared intelligence spine with interface-specific surfaces | existing conversational substrate | Existing intelligence interfaces; project-scoped conversation exists separately | EXISTS / BOUNDARY |
| Project ingestion | Project Files upload | `/solspire/projects/{id}/files/upload` | `project_files` + best-effort Knowledge OS ingestion | Project-scoped | EXISTS |

## 5. Identity and personal field findings

The repository's current architecture record states that Personal Echofeild is not a second Personal Codex. `PersonalEchofeild` renders `PersonalCodex` as its identity layer and then adds the living project / knowledge-graph / Crystal Matrix aggregation. The same record identifies `/api/echoes` as the shared public/personal echo pipe, with personal entries injected client-side from authenticated Knowledge OS and SolSpire project data.

Therefore CAL-04 does **not** authorize creation of a separate personal-memory or personal-codex system.

## 6. Cartography findings

`kernel/stellar.py` is an existing pure-Python Stellar Cartography engine. `api/main.py` exposes `/api/stellar-cartography`, and `StellarCartography.tsx` consumes the readout. Current repository documentation places this surface in NovaNet and Encyclopedia Galactica rather than Solariun Home.

The requested phrase “Interstellar Cartography” is therefore mapped to an existing Stellar Cartography substrate, but no evidence was found in this cycle establishing a canonical Solariun Home binding. That remains an EXPERIENCE GAP, not a missing backend.

## 7. Conversation topology findings

The current architecture already has two important boundaries:

1. Oracle / Arkana intelligence interfaces use the shared `api/oracle_spine.py` intelligence spine.
2. Project conversations use project-scoped conversation routes and project identifiers.

The project dashboard can load conversations for the current project and send messages against a selected project thread. This supports multiple persistent project-scoped threads without requiring a second conversation backend.

No CAL-04 implementation should introduce a parallel thread store. Any future Arcana Commune multi-chat UX should reuse the existing conversation identifiers and project relationships.

## 8. Ingestion findings

The repository's canonical shared extractor is `kernel/doc_extract.py` and the architecture record identifies support for PDF, DOCX, TXT, Markdown, HTML and JSON in the shared extraction helper.

The SolSpire project attachment UI currently advertises PDF/DOCX/TXT/MD. Therefore:

- shared extraction capability is broader than the currently advertised project upload control;
- HTML/JSON project UI support is not established by the current project attachment surface;
- multimedia support was not established as an existing project ingestion capability in this cycle;
- no new ingestion system is justified by CAL-04.

## 9. Home composition grammar

The current Home already follows the intended truthful field grammar in a narrow form:

```text
FIELD
├── Attention
├── Active world
├── Current signal
├── Continuity
├── Synthesis
└── Decisions
```

The repository's X01-X12 evidence record identifies `SolariunHomeCockpit` as the existing field composition over live endpoints and the shared `SolariunGrammar.tsx` as the object visual contract.

The next experience change, if authorized separately, should extend this grammar through composition/lenses rather than flattening every subsystem into permanent cards.

## 10. Projection candidates and current evidence

### PRIMARY — already supported

- current attention/open loops
- active workload
- current signal
- recent continuity/activity
- current synthesis
- decisions/proposals

### SECONDARY — existing substrate, not yet Home-projected

- project context
- project activity
- project conversations
- project files
- project tasks
- project memory

### CONTEXTUAL — existing substrate, separate surface

- Personal Codex / Personal Echofeild
- Knowledge OS
- Stellar Cartography
- Profile / identity

### DEEP — existing substrate, should remain lens/object-sheet accessible

- RQA / reasoning-analysis surfaces where present
- Cartography atlas detail
- Echo Field graph/detail
- Codex detail
- Knowledge graph
- Weaver / engineering evidence

The labels above are compositional classifications for this map, not new ontology types.

## 11. Protected boundaries confirmed

No evidence in CAL-04 justifies changing:

- K15/K3 semantics
- authorization semantics
- provenance semantics
- WorkEvent semantics
- persistence architecture
- conversation persistence architecture
- project persistence architecture
- Knowledge OS architecture
- Oracle authority boundaries
- execution / autonomous-worker behavior

In particular, project events and WorkEvents must remain distinguishable; activity must not be represented as provenance proof.

## 12. Regression observations from recent history

The immediately preceding calibration sequence addressed concrete project-surface failures:

- Calibration-01 isolated project dashboard failures and persisted the Arcana doorway.
- Calibration-02 exposed the isolated project client exception.
- Calibration-03 restored the existing Project Overview binding after preview evidence identified `ReferenceError: Overview is not defined`.

PR #64 was merged into `main` as commit `4d668dae851c18a2aafab74081a2630f9db13b6b`.

This sequence reinforces the CAL-04 rule: trace an actual failure boundary before making a broad composition change.

## 13. CAL-04 verdict

**VERDICT: MAPPING COMPLETE.**

The repository contains sufficient existing substrate to support a future narrow Home projection improvement without creating new storage, APIs, conversation infrastructure, or ontology.

However, this mapping does not itself establish which deep surface should be projected first. The exact next UI binding remains a human-review decision.

**No speculative implementation was performed.**

## 14. Next action

Human review should select exactly one bounded implementation target from the mapped gaps, for example:

- one existing deep SolSpire surface made surfaceable through the Home field grammar; or
- one proven information-density calibration on an existing Arcana surface.

Do not combine broad Home federation, conversation topology changes, ingestion expansion, and typography calibration into one move.

## 15. Evidence references

- Current `main`: `4d668dae851c18a2aafab74081a2630f9db13b6b`
- Canonical shell: `web/public_prism/src/components/solspire/SolSpireExperience.tsx`
- Home field: `web/public_prism/src/components/solspire/SolariunHomeCockpit.tsx`
- Project surface: `web/public_prism/src/components/solspire/ResilientProjectDashboard.tsx`, `web/public_prism/src/pages/ProjectDashboard.tsx`, `web/public_prism/src/pages/ProjectOverview.tsx`
- Shared Markdown: `web/public_prism/src/components/MarkdownViewer.tsx`
- Arcana: `web/public_prism/src/components/ArkanaCommune.tsx`
- Personal field: `web/public_prism/src/pages/PersonalEchofeild.tsx`, `web/public_prism/src/pages/PersonalCodex.tsx`
- Cartography: `web/public_prism/src/components/StellarCartography.tsx`, `kernel/stellar.py`, `/api/stellar-cartography`
- Architecture map: `docs/architecture/SOLSPIRE_EXPERIENCE_ARCHITECTURE_v1.md`
- Experience evidence: `docs/control-plane/evidence/solariun-x01-x12-arc/EVIDENCE.md`
- Canonical recovery evidence: `docs/control-plane/evidence/solariun-x01-x12-canonical-recovery/IMPLEMENTATION.md`
- Repository agent memory / source-of-truth notes: `AGENTS.md`
