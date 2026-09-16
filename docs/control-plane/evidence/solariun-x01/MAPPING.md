# SOLARIUN-X01-MAPPING — Canvas Foundation

## 1. Repository state
- HEAD baseline: `8136727c68892bf7beedf7c6a1d5a1b067819ec1` (origin/main)
- Branch: `solariun/x01-canvas-foundation`
- Mode: extension of canonical shell only

## 2. Existing routes
- App path router: `/solspire`, `/solspire/:section`
- Adapter: `web/public_prism/src/pages/SolSpireConsole.tsx`
- Lenses: overview, projects, commercial, knowledge, files, conversations, tasks, memory, weaver, observatory, engineering-lab, settings

## 3. Existing components (canonical)
- `SolSpireExperience.tsx` — sole mounted shell (V2 is re-export stub only)
- `SolariunHomeCockpit.tsx`, `ProjectsWorkspace`, `WorkspaceActionSurfaces`, `EngineeringLabLens`
- `solspire.css` + `solspire-canonical.css` visual layers
- GlobalDoors (Prism horizontal), Header, Sidebar, MobileNav, ContextBar

## 4–6. Data / API / auth
- Unchanged. Firebase → AuthContext → setApiAuthToken → apiClient → SolSpire APIs
- X01 does not add endpoints or persistence

## 7. Event sources
- Out of scope for X01 (Activity = X06)

## 8. Visual tokens (pre-existing)
- `--ss-gutter`, `--ss-panel`, `--ss-line`, gold/teal accents in canonical CSS
- Fixed header, sticky context bar, mobile bottom nav

## 9. Responsive behavior
- Sidebar desktop; mobile menu + bottom rail ≤700px
- Project interior object-sheet treatment ≤768px (P1.2)

## 10. Tests
- Frontend package scripts: `dev`, `build`, `preview` only (no dedicated unit suite for shell)

## 11. Existing capability
- Authenticated Solariun workspace loads with multi-lens navigation
- Arkana overlay + search overlay affordances
- Project field continuity (P0.1)

## 12. Missing substrate (X01)
- Explicit canvas foundation tokens (obsidian field, type scale, focus ring, reduced-motion)
- Landmark/skip structure for accessibility foundation
- Named field surface region for later object composition (X02+)

## 13. Proposed visual composition
- Keep single `.solspire-workspace` root
- Add `.solariun-canvas` foundation layer (CSS + landmarks only)
- No fake objects, metrics, or events

## 14. Files to modify
- `web/public_prism/src/components/solspire/solspire-canonical.css`
- `web/public_prism/src/components/solspire/SolSpireExperience.tsx`
- `docs/control-plane/evidence/solariun-x01/*`

## 15. Files not to modify
- Backend, K15, K3, WorkEvent, AEAS, auth, SolSpireExperienceV2 (stub only)
- Product lenses content (cockpit, files, knowledge) beyond shell chrome

## 16. Architectural risks
- Parallel shell regression (mitigated: V2 remains re-export; console stays on canonical)
- Visual noise / cyberpunk drift (mitigated: calm density tokens only)

## 17. Verification plan
- `npm run build` in `web/public_prism`
- Confirm single shell import path
- Confirm no backend file changes
- Manual route reachability: `/solspire`, `/solspire/files`

## 18. Explicit non-goals
- Object grammar (X02), field composition content (X03), sheets (X04), relationships (X05), activity (X06), Arkana expansion (X07), Weaver UI (X08), search (X09), mobile rewrite (X10), Observatory (X11), polish (X12)
