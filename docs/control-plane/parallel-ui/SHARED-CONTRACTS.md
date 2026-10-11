# Prism Parallel UI Work — Shared Contracts

**Status:** ACCEPTED — merged via PR #419 at `a29a9b8f18ada55cb9457ea3cdab98414522a4e8`.
**Baseline observed:** `main` at PR #418 base `d2670ce8b41c500df5cf475f7c6526016c7bd3aa`. Re-fetch `main` before every change; this SHA is not a permanent pin.
**Canonical production:** https://arkadia-qzu4.onrender.com (ADR-016). No deployment is authorized.
**Authority:** agents may inspect, implement, test, commit to their assigned branch, and update their PR. Human retains merge, production deployment, and acceptance.

## 1. Four workstreams and exclusive file ownership

| Workstream | Branch | Exclusive source ownership | Must not edit |
|---|---|---|---|
| 1. Shell, navigation, design system, integration contracts | `feat/prism-parallel-01-shell-contracts` | `web/arkadia_console/src/App.tsx`; `src/lib/router.ts`; `src/lib/surfaces.ts`; `src/components/SurfaceLenses.tsx`; shared shell/navigation primitives and tokens; `tests/test_console_shell_nav_contract.py`; this contract and shell instruction | Feature page internals owned by workstreams 2–4 |
| 2. NovaNet and project Opportunity Radar | `feat/prism-parallel-02-novanet-opportunity` | `src/pages/NovaNetPage.tsx`; NovaNet-only components under `src/components/novanet/`; opportunity UI modules under `src/components/opportunities/` or a page-local feature folder approved by workstream 1; NovaNet/opportunity-specific tests and evidence | App/router/surfaces registry, global navigation, shared tokens, shared shell tests |
| 3. Solariun and Knowledge OS | `feat/prism-parallel-03-solariun-knowledge` | Solariun/Knowledge OS page modules and feature-local components/tests/evidence, after exact existing paths are discovered from current tree/archive and recorded in its PR | App/router/surfaces registry, global navigation, shared tokens, shared shell tests, NovaNet files |
| 4. Arkana, Weaver, Engineering Lab | `feat/prism-parallel-04-arkana-weaver-lab` | Arkana/Oracle, Weaver, Engineering Lab feature-local page modules/components/tests/evidence, after exact paths/contracts are discovered and recorded in its PR | App/router/surfaces registry, global navigation, shared tokens, shared shell tests, NovaNet/Solariun files, runtime/authority model |

**Important:** these are ownership boundaries, not proof that every proposed directory already exists. Inspect the live tree first. Do not create duplicate abstractions just to match a suggested path. If an existing file spans two owners, the shell/integration owner owns the seam; feature agents submit a narrow proposal instead of editing it.

## 2. PR #418 — measured patch map and disposition

PR #418 is open, draft, and not merged at the last observed read. Its head was `56ca23b8431ca6b628894bdf5eb1ff0d08e39c1d`; re-fetch live state before acting.

| Existing PR #418 path | Current content / ownership disposition |
|---|---|
| `AGENTS.md` | Global agent instructions/amendment. **Do not duplicate or rewrite from feature PRs.** Workstream 1 proposes any future global changes separately; preserve the active canonical Render and human-approval rules. |
| `docs/control-plane/overnight/PRISM-UI-RECONCILIATION.md` | Current workstream-wide directive and pulse loop. **Coordinator-owned governance**, not page-feature ownership. Update only with explicit evidence and preserve one source of truth. |
| `docs/control-plane/overnight/PRISM-UI-INVENTORY.md` | Cross-product route/capability inventory. **Coordinator-owned integration artifact**; feature agents submit evidence/row changes to the coordinator rather than competing edits. |
| `docs/control-plane/overnight/PRISM-UI-SLICE-A-SHELL-INVENTORY.md` | Shell/navigation archive comparison. Workstream 1 owns updates. |
| `docs/control-plane/evidence/prism-ui-reconciliation-slice-a-novanet-01/EVIDENCE.md` | Evidence for NovaNet slice. Workstream 2 owns feature evidence; coordinator validates it against tests and exact SHAs. |
| `tests/test_console_shell_nav_contract.py` | Shared route/alias/lens contracts. Workstream 1 owns; feature-specific tests live separately. |
| `web/arkadia_console/src/App.tsx` | Route composition seam; workstream 1 owns. Feature agents request a small integration change through a PR comment/contract update. |
| `web/arkadia_console/src/lib/router.ts` | Canonical router and alias resolution; workstream 1 owns. |
| `web/arkadia_console/src/lib/surfaces.ts` | Canonical surface registry; workstream 1 owns. |
| `web/arkadia_console/src/components/SurfaceLenses.tsx` | Shared navigation control; workstream 1 owns. |
| `web/arkadia_console/src/lib/endpoints.ts` | Shared endpoint registry. Existing NovaNet additions came from #418; future additions require owner coordination. Workstream 1 owns file-level integration; feature agents provide verified endpoint names/paths and evidence. |
| `web/arkadia_console/src/lib/types.ts` | Shared API types. Existing NovaNet types came from #418; future additions require coordination. Workstream 1 owns file-level integration; feature agents submit exact handler-derived shapes. |
| `web/arkadia_console/src/pages/NovaNetPage.tsx` | NovaNet feature implementation; workstream 2 owns. |
| `docs/control-plane/evidence/console-complete-build/OVERNIGHT-BUILD.md` | Historical/parallel workstream handoff with supersession note; coordinator-owned continuity record. Do not revive its superseded baseline or Vercel assumptions. |

Do not copy the entire PR #418 branch into every new branch: that would make four duplicate full-surface diffs. These four PRs begin as **parallel execution-plan/agent bootstrap PRs**. Existing functional code in #418 remains there until a human/coordinator explicitly chooses a migration strategy. Do not cherry-pick, split, close, or rewrite #418 automatically.

## 3. Shared frontend and API contract

1. **One route registry:** `src/lib/surfaces.ts` is the canonical surface declaration; `src/lib/router.ts` resolves paths and compatibility aliases; `App.tsx` composes surfaces. No page-local router, duplicate surface registry, or route suffix guessing.
2. **One shell:** shared navigation, lenses, tokens, responsive primitives and shared shell tests belong to workstream 1. Feature modules expose page content; they do not recreate the global shell.
3. **API evidence before UI claims:** inspect current backend route/OpenAPI and handler implementation; record method, exact path, auth requirements, request/response shape, errors and persistence. A source constant or archive usage is not proof of a live contract. Never invent an endpoint.
4. **Use canonical client:** use existing `apiConfig.ts` and `apiClient.ts`; no hardcoded hostname, second API base, or alternate production origin. Preserve bearer/auth semantics and private/public data boundaries.
5. **Honest states:** loading, success, empty, unavailable/not wired, authorization failure, and transport/server error must be distinct where relevant. Do not fake data or infer success from an empty response.
6. **Real controls only:** interactive elements must have working behavior, keyboard access and accessible state. If the required backend contract or authority is absent, render a non-interactive, clearly marked blocked state.
7. **Evidence chain:** proposal ≠ approval ≠ execution ≠ work event ≠ evidence ≠ verification ≠ review/acceptance. UI may not imply a later state from an earlier one.
8. **Preserve history:** archive is source evidence, not code to delete or blindly restore. Reconcile each capability to current contracts and record adapt/defer/block decisions.
9. **Deployment invariant:** Render at `https://arkadia-qzu4.onrender.com` is the sole canonical production origin under ADR-016. No Vercel deployment, provider mutation, production deployment, merge, or acceptance is authorized by these instructions.

## 4. Parallel coordination protocol

- Each agent reads `AGENTS.md`, ADR-016, the current reconciliation directive, this contract, its own instruction file, live `main`, PR #418, and current checks before editing.
- Each agent edits only its owned files. Shared-file changes are proposed as a small interface request to workstream 1; no direct drive-by edits.
- Before implementation, each feature agent writes a short capability matrix: legacy source, current route, exact backend contract/auth, data states, tests, status and unknowns.
- Keep PRs draft until their bounded slice has targeted tests, build/typecheck where applicable, evidence bound to exact commit, and baseline-failure comparison.
- No agent merges another PR or rebases/force-pushes another agent's branch. If a contract change is needed, pause that dependent slice and record the blocker.
- Integrator checks changed-file overlap, dependency direction, combined build/test behavior, route collision and authorization boundaries. Do not merge merely because individual PRs pass.
- Branches start from the observed main for clean ownership. Because their bootstrap PRs are siblings, shared source integration is coordinated via PR #419's contract and review comments; after bootstrap, feature implementation PRs may depend on an explicit integration PR rather than duplicate shell changes.
- Every handoff records starting `main` SHA, branch SHA, paths, commands/results, pre-existing failures by node identity, blockers, and exactly one next move.
- Human acceptance is explicit. A green build, PR creation, or preview is not merge, production verification, or acceptance.

## 5. Exit criteria for each feature PR

- Exact, evidence-backed route and backend contract; no invented route/API.
- Functional core interaction or visibly blocked/not-wired state.
- Auth and personal/public data boundaries preserved.
- Targeted tests include a negative control for the primary regression detector where practical.
- Typecheck/build and relevant architecture/route checks pass; full-suite deltas compared to a fresh baseline.
- Keyboard/mobile checks recorded when affected.
- Evidence and feature matrix bind to exact commit; uncertainty is explicit.
- No merge/deploy/acceptance claim unless independently performed and authorized.


## 6. Explicit supersession of the single-PR rule

The current directive in `docs/control-plane/overnight/PRISM-UI-RECONCILIATION.md` §7 originally requires one long-lived branch/PR and prohibits parallel UI rebuild PRs. The user has since explicitly directed a four-PR parallel execution plan. This proposed contract supersedes **only that one-branch/one-PR constraint for the four named workstreams**, subject to human review/merge of this contract. All other governance remains in force: no duplicate ownership, no merge/deploy/acceptance by agents, no Vercel, evidence before claims, and no production change without explicit authorization.

Until this contract is reviewed and accepted, treat the four new PRs as draft bootstrap artifacts only. Do not launch source-editing agents on the assumption that the governance conflict is already resolved. Once accepted, the coordinator should amend the overnight directive so Hourly Weaver and OpenHands consume this four-workstream contract rather than the old single-PR instruction.
