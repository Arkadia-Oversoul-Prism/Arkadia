# SOLSPIRE GAP-PRIORITIZED EXPERIENCE PROPOSALS v1

**Document type:** Proposals only (not implementation authorization)  
**Parent map:** `docs/architecture/SOLSPIRE_EXPERIENCE_ARCHITECTURE_v1.md`  
**Mapped tip:** `3cc76afa198c868cba6fe4259a76a9d461ffddf1`  
**Architecture commit:** `1df152af59f508c06976a7c372f9a80512f1fdb7`  
**Trajectory:** ARKADIA-TRUTHFULNESS-01 v7 — **NO_LEGAL_MOVE**  
**AEAS:** FROZEN — Implementation NOT AUTHORIZED  
**Authority:** Architect — gap-prioritized proposals traced to EXISTS substrate  

> These proposals do **not** open M10, dispatch Weaver, activate AEAS, migrate schema, or deploy.  
> Each item must be separately authorized before any engineering trajectory is written.

---

## Prioritization method

| Rank driver | Rule |
|-------------|------|
| **P0** | High experience coherence gain using **only EXISTS** APIs/UI already on tip |
| **P1** | Coherence gain with **PARTIAL** substrate; thin composition, no new authority |
| **P2** | Valuable but needs new authorization surface or unclear substrate |
| **Reject** | Requires universal object DB, second graph authority, or UI-as-authorization |

Trace format for every proposal:

```
GAP → EXISTS substrate → CONNECTED pieces → EXPERIENCE CHANGE (proposed) → OUT OF SCOPE
```

---

## P0 — Compose what already exists

### P0.1 · Project Field Continuity

| Field | Content |
|-------|---------|
| **GAP** | Lenses (files, tasks, memory, conversations, events) feel like separate destinations; project interior is coherent but global lenses re-pick projects |
| **EXISTS** | `ProjectsWorkspace`, `ProjectDashboard` tabs, `FilesWorkspace` / `TasksWorkspace` / etc., `/solspire/projects/{id}/*` |
| **CONNECTED** | Same `project_id` children; `onOpenProject` / `onOpenProjectTab` already in `SolSpireExperience` |
| **PROPOSED EXPERIENCE** | When a project is selected, lens switches stay **inside** that project context (FIELD attention stays on one Project object) without new storage |
| **OUT OF SCOPE** | New project model, new DB, cross-user sharing |
| **Authority impact** | None — still owner CRUD |
| **Suggested future trajectory name** | *(not opened)* e.g. EXP-PROJECT-FIELD-CONTINUITY |

### P0.2 · Activity as Inspectable Feed (not proof)

| Field | Content |
|-------|---------|
| **GAP** | Observatory / events under-exposed relative to FILE/TASK mutations already logged |
| **EXISTS** | `project_events`, `GET .../events`, `log_event`, Events tab, Observatory lens |
| **CONNECTED** | Mutations on files/tasks already call `log_event` in store paths |
| **PROPOSED EXPERIENCE** | Single **Activity** presentation over existing events list: type, summary, time, subject id if present — labeled **activity, not provenance** |
| **OUT OF SCOPE** | WorkEvent merger, provenance engine, causal proof UI |
| **Authority impact** | None |
| **BOUNDARY preserved** | WorkEvent ≠ provenance |

### P0.3 · Governance Visibility in Weaver Surface

| Field | Content |
|-------|---------|
| **GAP** | PassSpec → PatchApproval → K15 → K3 is backend-real; UX may not make **locked vs ready** legible |
| **EXISTS** | `project_execution.py` readiness states, Weaver routes, ProjectDashboard weaver tab, worker contract TERMINATE |
| **CONNECTED** | Authorization state machine already returns lock reasons |
| **PROPOSED EXPERIENCE** | Display existing readiness/lock_reasons as explicit grammar: Proposal ≠ Approval ≠ Execution ≠ Verified |
| **OUT OF SCOPE** | Softening PassSpec, frontend-authored approval, auto-execute |
| **Authority impact** | **Display only** — no new authority |

### P0.4 · Public / Private Mode Clarity (NovaNet ↔ ReasoMate)

| Field | Content |
|-------|---------|
| **GAP** | Risk of residual confusion between public field and private conversation |
| **EXISTS** | M03 public markers, `ReasoMateSurface`, mode toggle patterns in social field |
| **CONNECTED** | Accepted M02/M03 boundaries |
| **PROPOSED EXPERIENCE** | Persistent mode chrome: **PUBLIC FIELD** vs **PRIVATE THREAD** using existing components only |
| **OUT OF SCOPE** | Merging social substrates, second messenger |

---

## P1 — Thin composition on PARTIAL substrate

### P1.1 · Arkana Context Pack (bounded)

| Field | Content |
|-------|---------|
| **GAP** | Arkana exists but “full context” is PARTIAL |
| **EXISTS** | Auth user, current project, `/files`, `/knowledge/search`, `/conversations`, `/tasks`, `/events`, ArkanaCommune UI |
| **CONNECTED** | Project-scoped APIs when project is open |
| **PROPOSED EXPERIENCE** | Optional **explicit** context checklist sent to Arkana: only fields the client already fetched — user-visible “what Arkana can see” |
| **OUT OF SCOPE** | Silent full-corpus embedding, sovereign bypass, fabricated memory |
| **Authority impact** | None — still not authorization |

### P1.2 · Object Sheet on Mobile

| Field | Content |
|-------|---------|
| **GAP** | MobileNav EXISTS; object-sheet grammar PARTIAL |
| **EXISTS** | MobileNav, ProjectDashboard sections, lens routes |
| **PROPOSED EXPERIENCE** | Opening a file/task/memory uses a sheet over FIELD without new routes ontology |
| **OUT OF SCOPE** | Desktop three-column redesign, new IA product roots |

### P1.3 · Knowledge Lens Alignment

| Field | Content |
|-------|---------|
| **GAP** | Global `KnowledgeOSPage` lens vs project `KnowledgePanel` can feel like two products |
| **EXISTS** | Both UIs; project knowledge APIs; M06 one-model banner |
| **PROPOSED EXPERIENCE** | When inside a project, knowledge lens **prefers** project panel/API; global OS remains explicit “library” mode |
| **OUT OF SCOPE** | Single knowledge database rewrite |

---

## P2 — Needs separate authorization (not EXISTS-complete)

| ID | Idea | Why not P0/P1 |
|----|------|----------------|
| P2.1 | Universal search across all object types | No unified search index EXISTS |
| P2.2 | Intent objects as first-class store | MISSING substrate |
| P2.3 | FOLLOW_UP_FOR relationship system | MISSING |
| P2.4 | Full provenance inspector | Would conflate activity with proof |
| P2.5 | Automation ontology / auto-build opportunities | AEAS freeze + possibility no-auto-build |

---

## Explicit rejects (BOUNDARY)

| Proposal | Reason |
|----------|--------|
| Universal object table for all types | Violates “one experience ≠ one DB” |
| UI state authorizes K15 | Violates PassSpec/PatchApproval |
| Worker auto-merge after gap fix | Worker contract TERMINATE |
| Second knowledge graph authority | Horizon II lesson |
| “Arkana understands everything” claim | False; PARTIAL only |

---

## Recommended Architect sequence (human only)

```
1. Merge PR #52 (Experience Architecture v1) if not already
2. Review this proposals doc
3. Select at most ONE P0 item
4. Write a narrow trajectory move (or explicit one-off authorization)
5. Implement → verify → ACCEPT — same Truthfulness discipline
```

**Do not** batch-implement P0–P2.

---

## Mapping back to architecture maps

| Proposal | Primary maps |
|----------|----------------|
| P0.1 | MAP 02 lenses, MAP 01 Project |
| P0.2 | MAP 06 activity |
| P0.3 | MAP 05 authority |
| P0.4 | MAP 08 NovaNet/ReasoMate |
| P1.1 | MAP 04 Arkana context |
| P1.2 | MAP 07 responsive |
| P1.3 | MAP 02 knowledge lens |

---

## Status

| Item | State |
|------|--------|
| Proposals v1 | **DELIVERED** (this file) |
| Implementation | **NOT AUTHORIZED** |
| M10 | **Not opened** |
| AEAS activation | **Not authorized** |
| Weaver dispatch | **Not authorized** |

*End of SolSpire Gap-Prioritized Experience Proposals v1.*
