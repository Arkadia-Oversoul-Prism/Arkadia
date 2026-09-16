# SOLARIUN-X01 → X12 — CANONICAL RECOVERY MAP

**Arc:** SOLARIUN-X01 → SOLARIUN-X12
**Base under repair:** `482e4f0697a5625ff91d56797989aeab30d29b4f`
**Repair branch:** `repair/solariun-x01-x12-canonical-recovery`
**Mode:** existing substrate only
**Merge:** human-only
**Deploy:** human-only

## 1. Audit finding

PR #59 added a cross-surface wrapper with a second header/rail/search/inspector system. PR #60 then added visual grammar components and a single-pass CSS layer, but the evidence itself states that object sheets are only a composition API, relationship chips only render when callers supply evidence, and Weaver lifecycle is visibility-only.

The resulting implementation therefore did not satisfy the intended X01-X12 experience contract. The repair must consolidate back onto the canonical `SolSpireExperience` rather than stack another application shell above it.

## 2. Canonical ownership

- `SolSpireExperience.tsx` owns Solariun navigation, field/project state, search, Arkana, project continuity and lens composition.
- `ProjectDashboard.tsx` remains the existing project object/context interior.
- `ProjectsWorkspace.tsx` remains the existing project list/create surface.
- `knowledgeApi.ts` remains the existing Knowledge OS search client.
- Existing project APIs remain the source for files/tasks/memory/events/Weaver.
- Existing Arkana context pack remains bounded and explicit.
- Existing WorkEvent/provenance semantics remain unchanged.

## 3. X01-X12 recovery map

| Move | Repository truth | Recovery target |
|---|---|---|
| X01 | Canonical SolSpire shell exists; field markers exist | One atmospheric field, quiet header, spatial depth |
| X02 | Existing project/file/task/conversation/knowledge/memory shapes exist | Shared object visual grammar through existing renderers |
| X03 | Home cockpit already reads live endpoints | Field-first composition, not dashboard decoration |
| X04 | Project object sheet/mobile sheet substrate exists | Inspector/sheet without leaving field |
| X05 | Relationship evidence is partial | Show only supplied relationships; no inference |
| X06 | Project events/activity exist | One temporal activity grammar without provenance claims |
| X07 | Arkana context pack exists | Contextual lens over current field |
| X08 | Weaver lifecycle visibility exists | Distinct authority/lifecycle states, no execution authority |
| X09 | P2 federated search exists | Reuse existing search and honest coverage labels |
| X10 | Existing responsive/mobile rail exists | Desktop spine, mobile bottom instrument, same data |
| X11 | Existing Observatory/events lens exists | Temporal inspection over existing activity |
| X12 | Focus/reduced-motion primitives exist | Calm motion, accessibility, visual consistency |

## 4. Repair scope

1. Remove the duplicate outer navigation/search/inspector shell introduced by PR #59.
2. Restore the canonical Solariun shell as the only workspace shell.
3. Replace the forced desktop bottom-nav treatment with a quiet desktop constellation spine and retain one mobile bottom rail.
4. Restore the field/project surfaces to an editorial spatial composition instead of stacked SaaS cards.
5. Strengthen project-world visual hierarchy so the project interior is legible and not an undifferentiated dark slab.
6. Preserve all existing backend/data/identity/governance boundaries.

## 5. Explicit non-goals

No new database, graph store, universal object persistence, Intent Object schema, Automation Ontology, AEAS activation, K15/K3 change, WorkEvent redefinition, provenance engine, second project model, second Knowledge model, second memory system, autonomous merge, or autonomous deployment.

## 6. Verification plan

- static repository tests
- Vite production build on the repair branch
- inspect DOM ownership for exactly one Solariun workspace shell
- inspect desktop navigation ownership
- inspect mobile navigation ownership
- exercise `/solspire/projects` and project opening
- verify existing API calls remain unchanged
- verify no forbidden architecture files/routes are introduced
