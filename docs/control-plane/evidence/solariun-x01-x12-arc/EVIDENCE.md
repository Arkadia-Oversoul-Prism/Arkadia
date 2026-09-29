# SOLARIUN-X01 → X12 — SINGLE-PASS ARC EVIDENCE

**Authorization:** Architect single-pass execution; one PR for human verify + merge.  
**Base:** `5750148` (main) + X01 commit lineage on `solariun/x01-canvas-foundation-v2`.  
**Mode:** In-place composition over canonical `SolSpireExperience`. No parallel shell.

## Move matrix

| Move | Objective | Implementation | Substrate |
|------|-----------|----------------|-----------|
| X01 Canvas foundation | Field shell, depth, type scale | `solariun-canvas` markers + CSS tokens | Existing shell |
| X02 Object grammar | Shared object visual contract | `SolariunGrammar.tsx` object views | Existing object shapes |
| X03 Field composition | “What matters now?” | Existing `SolariunHomeCockpit` + field markers | Live endpoints only |
| X04 Object sheets | Inspector structure | `SolariunObjectSheet` + existing project `solspire-object-sheet` | Composition only |
| X05 Relationship grammar | CONNECTED TO / … | `RelationChip` / relation row | Labels only when evidence provided |
| X06 Activity grammar | Unified activity items | `SolariunActivityStream` + existing ActivityItem | Existing events/WorkEvents |
| X07 Arkana lens | Contextual intelligence | Existing `ArkanaOverlay` context pack | No fabricated context |
| X08 Weaver state surface | Lifecycle visibility | `WeaverLifecycleLegend` in Weaver lens | Display ≠ authorization |
| X09 Semantic search | One field search | Existing federated `SearchOverlay` | Knowledge OS + project corpus |
| X10 Mobile spatial | Native mobile composition | Scrollable `solariun-bottom-rail` + sheet CSS | Same objects, different layout |
| X11 Observatory | Temporal inspection | Existing Observatory / events collection | Activity ≠ provenance |
| X12 Polish / a11y | Motion + focus | reveal keyframes, focus-visible, reduced-motion | Additive CSS |

## Boundaries preserved

- No K15 / K3 / WorkEvent / provenance semantic changes
- No AEAS activation, autonomous merge/deploy
- No second project / knowledge / memory / files system
- No fake metrics, events, relationships, or Weaver run state
- No SolSpireExperience V2/V3 parallel shell

## Files touched (arc)

- `web/public_prism/src/components/solspire/SolSpireExperience.tsx`
- `web/public_prism/src/components/solspire/solspire-canonical.css`
- `web/public_prism/src/components/solspire/SolariunGrammar.tsx` (new)
- `web/public_prism/src/components/solspire/SolariunHomeCockpit.tsx`
- `web/public_prism/src/pages/SolSpireWorkspacePanels.tsx`
- `docs/control-plane/evidence/solariun-x01-canvas-foundation/*`
- `docs/control-plane/evidence/solariun-x01-x12-arc/EVIDENCE.md`

## Honest limitations

- Object sheets are a **composition API**; not every lens auto-opens a sheet for every row yet.
- Weaver lifecycle steps are **visibility grammar**; live step highlighting requires a `current` status from backend when available.
- Relationship chips render only when callers supply supported relation evidence — no inference engine.
- Frontend production build / visual QA is for human verify on preview after PR deploy.

## Human gate

Verify → merge **one PR**. Deploy remains human-controlled.
