# Agent 01 — Shell, Navigation, Design System & Integration

**Branch:** `feat/prism-parallel-01-shell-contracts`  
**PR:** #419 (draft bootstrap)  
**Owns:** `App.tsx`, `lib/router.ts`, `lib/surfaces.ts`, `components/SurfaceLenses.tsx`, shared shell/tokens, shared shell/navigation contract tests, and integration of shared endpoint/type registries.  
**Contract:** read `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` first.

## Mission
Reconcile archived Prism shell/navigation/visual primitives with the active `web/arkadia_console/` without rebuilding feature pages or introducing a second route model. Preserve current route and serving-path constraints.

## First tasks
1. Reconstruct current `main`, PR #418, the archive shell files, current shared components/tokens, and route guards. Record exact SHAs and overlapping paths.
2. Produce a compact shared-interface contract: route declaration shape, navigation callback shape, design-token usage, API registry/type contribution protocol, and responsive/accessibility rules.
3. Compare the existing #418 shell changes against main and archive. Do not duplicate them blindly; #418 remains an open draft until human/coordinator decides whether to retain or re-home its implementation.
4. Implement only shared-shell/integration improvements that are independently bounded and tested. Coordinate API constants/types through reviewed patches from feature owners.
5. Keep `tests/test_console_shell_nav_contract.py` non-vacuous with positive and negative controls. Check actual FastAPI route collisions, not only Vite catch-all behavior.

## Hard boundaries
- Do not implement NovaNet page internals, Opportunity Radar, Solariun/Knowledge pages, Arkana/Weaver/Engineering Lab feature internals.
- Do not change backend authority/runtime contracts or deployment configuration.
- Do not merge, deploy, or mark accepted.
- Stop if route ownership, global shell ownership, or API contract is ambiguous; document the exact blocker.

## Required PR evidence
Archive/source paths; route map; files changed; targeted test commands/results; typecheck/build; negative controls; mobile/keyboard observations; baseline failure-node comparison; exact branch SHA; next bounded move.
