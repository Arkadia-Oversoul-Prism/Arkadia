# Agent 01 — Shell, Navigation, Design System & Integration

**Active branch:** `feat/prism-next2-01-shell-contract-map`
**Base revision:** `f390526ab14e122fef358ef9b9e1cd438509463c`
**Task:** refresh the shared branch map and finish verified endpoint-registry seams needed by Workstream 4.
**Owns:** shared app shell, `App.tsx`, router/surface registry, global navigation/lenses/tokens, shared shell/endpoint contract tests, `lib/endpoints.ts`, `lib/types.ts`, and integration seams.
**Contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`.

## Start now — no new prompt required

1. Verify current `main` is descended from the stated base, then refresh the four active branch/PR/head entries in `SHARED-CONTRACTS.md` after the four next-wave PRs exist. Keep the merged #425–#428 wave as history, not active work.
2. Re-verify the actual served handler and URL encoding for Workstream 4's recorded requests. Add `labAutomations: "/api/lab/engineering/automations"` to the canonical registry and add a typed, encoded `labCanvas(id)` path builder derived from `endpoints.labArtifacts`. `labSession(id)` already exists; verify it remains correct. Do not add paths that are not served.
3. Add focused positive/negative contract tests for those builders and their served routes. Run endpoint-registry guards, TypeScript/build, and route-table checks.
4. Review the merged Opportunity Radar Projects mount against the actual board handler; make a shared integration change only if evidence proves one is needed. Do not take over the feature-local implementation.
5. Continue with the highest-value remaining shell/navigation gap in the live inventory. Work in bounded commits and keep the PR updated.

## Hard boundaries

- Do not implement NovaNet/Opportunity, Knowledge OS, Arkana/Weaver/Lab feature internals.
- Do not change backend authority/runtime contracts or deployment configuration.
- Do not merge, deploy, or mark accepted.
- Continue automatically after each merge. Escalate only a concrete security/privacy issue, explicit human authority decision, destructive/data-loss risk without a safe path, or genuine cross-workstream contract conflict. Record exact evidence in the PR thread and continue with a safe non-overlapping task where possible.

## Required evidence

Exact base/head SHAs; route/OpenAPI verification; ownership/overlap check; targeted tests and negative controls; typecheck/build; baseline failure-node comparison; current branch map; one next bounded task.
