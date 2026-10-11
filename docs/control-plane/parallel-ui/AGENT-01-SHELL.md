# Agent 01 — Shell, Navigation, Design System & Integration

**Branch:** `feat/prism-parallel-01-shell-implementation`  
**PR:** #423 (implementation workstream; governance contract is merged in main)  
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


## Next wave — continue immediately after this PR closes

Coordinator direction (2026-10-11): do not wait for another conversational prompt. After the current PR is merged, fetch fresh `main` and start a new branch/PR from it. First, resolve the integration requests already recorded by feature owners: (1) add a typed `labSession(id)` path helper to the shared endpoint registry only after re-verifying the actual GET handler and URL encoding; (2) integrate Workstream 2's project Opportunity Radar only after its backend contract and ownership checks are verified. Keep endpoint/type registry edits here; do not take over feature-local implementation. Run the endpoint-registry guard, shell/route tests, TypeScript/build, and route-table collision checks. Continue into the next highest-value archived shell/navigation gap when no shared-interface request is pending. Stop only for an actual authority, security, or unresolved contract conflict; record exact evidence and continue on a non-conflicting task where possible.
