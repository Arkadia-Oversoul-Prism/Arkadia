# SOLARIUN-X01 — IMPLEMENTATION

**Move:** Canvas Foundation  
**Base HEAD at start:** `575014840c2ead75f460b38de06b04e99d6993f7`  
**Mode:** in-place extension of canonical shell only  

## What changed

1. `SolSpireExperience.tsx`
   - Root workspace receives `solariun-canvas` plus `data-solariun-zoom` (`field` | `deep` when a project is open).
   - `role="application"` and `aria-label` on the canvas roots.
   - Field content region labeled with `data-solariun-region="field"`.

2. `solspire-canonical.css`
   - Additive SOLARIUN-X01 block: canvas depth background, ENVIRONMENT / OBJECT / METADATA type tokens, calm focus-within, reduced-motion respect.
   - Scoped under `.solspire-workspace.solariun-canvas` so legacy rules remain intact.

## What was reused

- Canonical `SolSpireExperience` (post dual-shell recovery)
- Existing `--ss-*` layout tokens and mobile/desktop composition
- Existing Auth → Console → Experience mount path
- `SolSpireExperienceV2` left as re-export only

## What was not implemented (deferred)

- Object grammar (X02)
- Overview field “what matters” composition beyond existing cockpit (X03)
- Object sheets (X04)
- Relationship / activity / Arkana / Weaver / search / observatory surfaces (X05–X11)
- Motion polish (X12)
- Any backend, K15, K3, WorkEvent, or provenance change
- Parallel shell or second navigation system

## Architectural boundaries preserved

- SolSpire = substrate; Solariun = inhabitable surface labels on the same shell
- No fake objects, metrics, events, or relationships
- No second persistence layer
