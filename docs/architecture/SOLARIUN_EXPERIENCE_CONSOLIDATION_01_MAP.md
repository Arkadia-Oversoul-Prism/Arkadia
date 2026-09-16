# SOLARIUN EXPERIENCE CONSOLIDATION 01 — BOUNDED MAP

**Authorization:** `SOLARIUN-EXPERIENCE-CONSOLIDATION-01`
**Base:** `8136727c68892bf7beedf7c6a1d5a1b067819ec1`
**Branch:** `exp/solariun-experience-consolidation-01`
**Mode:** existing substrate only
**Merge:** human_only
**Deploy:** human_only

## Purpose

Align the four named experience surfaces through a thin shared experience grammar without creating a new persistence authority, object model, intent schema, automation ontology, or authority path.

## Boundary ledger

| Forbidden | Treatment |
|---|---|
| New graph DB | Not used |
| New object DB | Not used |
| New Intent schema | Not used |
| Automation ontology / AEAS activation | Not used |
| K15/K3 changes | None |
| WorkEvent redefinition | None; activity remains distinct from provenance |
| Provenance redefinition | None |
| Second project model | None |
| Second Knowledge model | None |
| Second memory system | None |
| Autonomous merge/deploy | Not performed |
| Scope expansion | Four surfaces only |

## Recursive endpoint/component/data mapping

### Bounded Area A — NovaNet

**Components**
- `web/public_prism/src/pages/NovaNetPage.tsx`
- `web/public_prism/src/pages/SocialFieldVerified.tsx` (NovaNet implementation surface)
- `web/public_prism/src/components/ArkadiaNavigation.tsx`

**Existing data/runtime**
- NovaNet/social field routes and existing public-field markers.
- Shared Arkana runtime remains the existing Oracle spine; no new intelligence surface.

**Experience alignment**
- Naming: `NovaNet` remains the public field; navigation exposes `Solariun` and `Spiral Command` as adjacent system surfaces.
- Context: explicit `PUBLIC FIELD` indicator; no private project data implied.
- Inspector/activity: links to existing Solariun activity surface; activity is not provenance.
- Governance/Weaver: descriptive links only; no authority transfer.
- Responsive: shared shell adapts the top context rail to compact controls.

**Out of scope**
- social backend rewrite, new public/private storage, new graph, new message system.

### Bounded Area B — Solariun Workspace

**Components**
- `web/public_prism/src/pages/SolSpireConsole.tsx`
- `web/public_prism/src/components/solspire/SolSpireExperience.tsx`
- `web/public_prism/src/pages/ProjectDashboard.tsx`
- `web/public_prism/src/pages/SolSpireWorkspacePanels.tsx`

**Existing endpoints/substrate**
- `/solspire/projects`
- `/solspire/projects/{id}/files*`
- `/solspire/projects/{id}/tasks*`
- `/solspire/projects/{id}/memory*`
- `/solspire/projects/{id}/conversations*`
- `/solspire/projects/{id}/events*`
- existing Knowledge OS/search routes
- existing Weaver routes under project scope

**Experience alignment**
- Naming: one `Solariun` workspace surface; existing lens labels remain canonical.
- Object grammar: Project remains the parent object; children remain project-scoped.
- Contextual field: current project/lens remains the context carrier.
- Inspector: use existing object/project surfaces only; no universal object store.
- Activity: existing project events remain activity, explicitly not provenance.
- Arkana: link to existing Arkana surface; do not claim full-corpus understanding.
- Weaver: existing project Weaver remains the governed work surface.
- Search: existing Knowledge OS search remains the search substrate; no universal index.

**Out of scope**
- replacing ProjectDashboard, new object persistence, new project/knowledge/memory models.

### Bounded Area C — SolSpire substrate

**Components**
- `web/public_prism/src/components/solspire/SolSpireExperience.tsx`
- `web/public_prism/src/components/solspire/solspire.css`
- `web/public_prism/src/components/solspire/solspire-canonical.css`
- existing `knowledgeApi.ts` and `apiClient.ts`

**Existing data/runtime**
- `searchKnowledge()` over Knowledge OS groups.
- Project-scoped files/tasks/memory federation when a project is open.
- Existing Arkana context pack UI.
- Existing project event/activity and Weaver bindings.

**Experience alignment**
- Shared system rail becomes the outer grammar; SolSpire keeps ownership of project context.
- Search coverage remains honest: no universal object index claim.
- Relationship language uses existing `BELONGS TO`, `REFERENCES`, `DERIVED FROM`, `CONNECTED TO` semantics only where substrate supports them.
- Governance labels remain display-only.

**Out of scope**
- second graph authority, second search index, causal provenance engine, WorkEvent changes.

### Bounded Area D — Spiral Command

**Components**
- `web/public_prism/src/pages/SpiralCommandInterface.tsx`
- `web/public_prism/src/lib/sciCommandRegistry.ts`

**Existing runtime**
- Registry metadata and bound navigation routes.
- SCI explicitly does not own PassSpec, PatchApproval, K15, K3, or mutation.

**Experience alignment**
- Naming: `Spiral Command` remains the operator/discovery shell.
- Navigation: shared rail makes SCI adjacent to Solariun rather than a hidden authority plane.
- Governance: existing descriptive lifecycle remains visible; authority stays backend/human-gated.
- Weaver visibility: route to the existing SolSpire project Weaver surface.
- Responsive: command rail collapses into the shared compact shell.

**Out of scope**
- SCI authorization, execution, K15/K3 calls, new command ontology.

## Cross-surface grammar

```text
ARKADIA PRISM
  ├─ NovaNet       → PUBLIC FIELD
  ├─ Solariun      → PRIVATE WORKSPACE
  │    └─ SolSpire → project/context substrate
  └─ Spiral Command → DISCOVERY / GOVERNANCE VISIBILITY

Human authority remains above all display/navigation surfaces.
Activity ≠ provenance.
Discovery ≠ authorization.
Weaver visibility ≠ Weaver execution.
```

## Implementation gate

This map is the pre-implementation record for the four bounded areas. Implementation may only add shared composition and truthful visibility over the mapped existing substrate.
