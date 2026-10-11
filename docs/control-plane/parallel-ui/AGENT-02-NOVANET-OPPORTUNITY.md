# Agent 02 — NovaNet & Project Opportunity Radar

**Branch:** `feat/prism-parallel-02-novanet-opportunity`  
**PR:** #420 (draft bootstrap)  
**Owns:** `src/pages/NovaNetPage.tsx`, NovaNet-only components, opportunity-radar feature modules and their tests/evidence. Shared registries and global shell are not owned here.  
**Shared contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` in PR #419; fetch/review it before edits.

## Mission
Recover the useful NovaNet hub and project-level Opportunity Radar workflows from archived Prism and the current opportunity/project substrate. Each project should eventually expose its opportunity layer in the Projects/Weaver experience without creating a second store or pretending prospects are verified buyers.

## First tasks
1. Reconstruct live `main`, PR #418, and archive sources. Specifically map #418's existing `NovaNetPage.tsx`, NovaNet additions in `endpoints.ts`/`types.ts`, and evidence file. Do not duplicate the existing slice.
2. **PR #418 overlap gate:** until #418 is merged or a human explicitly chooses a split, do not edit `NovaNetPage.tsx`, `endpoints.ts`, `types.ts`, `App.tsx`, `lib/router.ts`, `lib/surfaces.ts`, or shared navigation/tests. Start with verified API discovery, feature matrix, and new opportunity-only modules/tests under a feature-local path. If a NovaNet page integration is required, record a precise patch request for Workstream 1 and wait.
2. Verify `/api/transmissions` and `/api/echoes` against current backend route table and handlers before relying on PR #418's evidence; re-check auth and response shapes.
3. Discover the actual project/opportunity APIs and storage before implementing project radar. Record exact method/path/auth/schema/source; if unknown, keep the UI blocked and report the gap.
4. Write a capability matrix for NovaNet hub, IMS, Grove, Larder, Distribution, and project Opportunity Radar. Do not invent routes for unverified subviews. Existing note: `/api/ims/inquiries` was reported as sovereign-key gated while the browser client sends bearer auth only; re-measure before proposing access.
5. Implement page-local UI and tests only. For route/surface registration, shared endpoint/type registry changes, or navigation, send workstream 1 a narrow integration request with evidence rather than editing shared files.

## Hard boundaries
- No edits to `App.tsx`, `lib/router.ts`, `lib/surfaces.ts`, global nav/lenses, shared shell tests, or global token files.
- No mock buyers, invented budget/contract claims, invented endpoints, duplicate persistence, or silent auth bypass.
- No merge/deploy/acceptance.

## Acceptance
Real-contract data flow or honest not-wired state; distinct loading/empty/error/auth states; interaction tests and negative controls where practical; typecheck/build; exact evidence/commit SHA; explicit unknowns and next move.
