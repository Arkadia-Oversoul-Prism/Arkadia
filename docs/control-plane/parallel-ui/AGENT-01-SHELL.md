# Agent 01 — Shell, Navigation, Design System & Integration

**Active branch:** `feat/prism-next2-01-shell-contract-map`
**Active PR:** [#429](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/429) — draft, implementation in progress.
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

## Measured contract facts (do not re-derive from memory)

- **`useRouter` normalises the address bar on load** (`lib/router.ts`, this branch). It resolves the inbound pathname and `replaceState`s the canonical path when they differ, so `/nexus`, a trailing slash, or an unrouted path does not leave the address bar holding a path no surface declares. Reconciled from the archived Prism (`archive/frontend/arkadia-prism/web/public_prism/src/App.tsx:102 history.replaceState`). `tests/test_console_shell_nav_contract.py` evaluates the real router in Node rather than pinning its text.
- The canvas route is a **sibling** of artifacts, not a sub-resource. Served: `/api/lab/engineering/artifacts` (GET), `/api/lab/engineering/canvas/{artifact_id}` (GET). **Not** served: `/api/lab/engineering/artifacts/{artifact_id}`, and `/api/lab/engineering/canvas` alone is not a route. This is why `labCanvas` derives its base by substitution and why a `labCanvasRoot` registry entry would fail the served-path guard.
- `/api/commune/resonance` and `/api/knowledge/search` are **POST-only**; a GET probe returning 405/404 is not a defect.
- Workstream 2's merged evidence explicitly requests **no** shared endpoint constant for `/solspire/buyer-recon`; that path is handler-derived in its own contract module. Do not add it to the registry. Its served shapes are `/solspire/buyer-recon/projects/{project_id}` and `/…/entries` (verified against `app.openapi()`), and the Projects mount is `SolSpirePage.tsx:33` → `OpportunityRadarSection` → `ProjectOpportunityRadar` (reviewed this pass; no shared change needed).
- `knowledgeSearch` was already added by `67696372`; do not re-add it.
- **A concurrent commit on this branch may land the same work.** Two landed while this pass's copies were uncommitted or in flight: `9b1b3ef1` ("reconcile shared endpoint contract against merged feature slices") added `labAutomations` + `labCanvas`, and `e8b0b77a` ("widen the one-registry guard to apiRequest literals") took the detector-widening that this pass had recorded as its own next move. `git fetch` + compare against `origin/<branch>` **before** committing and again before pushing; drop a duplicate rather than re-landing it, rebase the non-overlapping work onto the remote head, and keep **both** sides of a documentation conflict rather than picking one.

## Hard boundaries

- Do not implement NovaNet/Opportunity, Knowledge OS, Arkana/Weaver/Lab feature internals.
- Do not change backend authority/runtime contracts or deployment configuration.
- Do not merge, deploy, or mark accepted.
- Continue automatically after each merge. Escalate only a concrete security/privacy issue, explicit human authority decision, destructive/data-loss risk without a safe path, or genuine cross-workstream contract conflict. Record exact evidence in the PR thread and continue with a safe non-overlapping task where possible.

## Required evidence

Exact base/head SHAs; route/OpenAPI verification; ownership/overlap check; targeted tests and negative controls; typecheck/build; baseline failure-node comparison; current branch map; one next bounded task.
