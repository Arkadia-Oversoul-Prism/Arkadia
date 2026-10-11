# Agent 01 — Shell, Navigation, Design System & Integration

**Current slice:** PR #425 — shell accessibility, endpoint-registry guard, verified `labSession(id)` builder, and cross-workstream contract reconciliation.
**After merge:** create the next branch from freshly fetched `main`, open a new draft PR, update the active branch map in `SHARED-CONTRACTS.md`, and begin immediately.
**Owns:** shared app shell, `App.tsx`, router/surface registry, global navigation/lenses/tokens, shared shell/endpoint contract tests, `lib/endpoints.ts`, `lib/types.ts`, and integration seams.
**Contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`.

## Immediate continuation task

1. Re-fetch `main` and reconcile the merged shell/endpoint work with the other three merged feature slices. Bind every observation to the exact main SHA.
2. Verify the Opportunity Radar integration on the Projects surface after Workstream 2's PR merges. Review the actual project list and project-board contracts, confirm route ownership and failure states, and make only the shared integration changes proven necessary. Do not duplicate Workstream 2's feature-local implementation.
3. Refresh the shared active branch/PR map once all four next-wave branches are replaced by fresh branches from current `main`.
4. Continue the highest-value remaining shell/navigation gap from the live inventory/archive comparison. Prefer one bounded, testable improvement over a broad redesign.
5. Run the endpoint-registry and shell/navigation guards, TypeScript/build, and actual route-collision checks. Keep negative controls non-vacuous and compare failure nodes against the current baseline.

## Hard boundaries

- Do not implement NovaNet/Opportunity, Knowledge OS, Arkana/Weaver/Lab feature internals.
- Do not change backend authority/runtime contracts or deployment configuration.
- Do not merge, deploy, or mark accepted.
- Do not wait for another conversational prompt. Continue on the next non-overlapping task after each merge.
- Escalate only a concrete security/privacy issue, explicit human authority decision, destructive/data-loss risk without a safe path, or genuine cross-workstream contract conflict. Record exact evidence in the PR thread; otherwise keep working.

## Required PR evidence

Exact base/head SHAs; changed paths and ownership check; API/route contract evidence; targeted tests and negative controls; typecheck/build; keyboard/mobile observations; baseline failure-node comparison; production observations separately from code-level evidence; one next bounded move.
