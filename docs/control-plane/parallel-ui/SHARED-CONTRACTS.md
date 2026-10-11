# Prism Parallel UI Work — Shared Contracts

**Status:** ACCEPTED — merged via PR #419 at `a29a9b8f18ada55cb9457ea3cdab98414522a4e8`.
**Baseline observed:** `main` after the next-wave bootstrap: `962434bed1bccb11fbf5edfcb0299317b12a8915` (PR #424 merge; first wave merged as #423 `972c3423`, #420 `55b27d10`, #421 `22941cc5`, #422 `e924aec1`). Re-fetch `main` before every change; this SHA is not a permanent pin. The branch map in §1 was last refreshed 2026-10-11 (Workstream 1) against the four next-wave branches below.
**Canonical production:** https://arkadia-qzu4.onrender.com (ADR-016). No deployment is authorized.
**Authority:** agents may inspect, implement, test, commit to their assigned branch, and update their PR. Human retains merge, production deployment, and acceptance.

## 1. Four workstreams and exclusive file ownership

Active branch map, re-measured 2026-10-11 at `main` `962434be`. Each next-wave branch starts from that revision; the heads below are observations, not pins.

| Workstream | Branch | PR (draft) | Head observed | Exclusive source ownership | Must not edit |
|---|---|---|---|---|---|
| 1. Shell, navigation, design system, integration contracts | `feat/prism-next-01-shell-integration` | #425 | `e82f7465` | `web/arkadia_console/src/App.tsx`; `src/lib/router.ts`; `src/lib/surfaces.ts`; `src/components/SurfaceLenses.tsx`; shared shell/navigation primitives and tokens; `src/lib/endpoints.ts`; `src/lib/types.ts`; shared shell/endpoint contract tests; this contract and shell instruction | Feature page internals owned by workstreams 2–4 |
| 2. NovaNet and project Opportunity Radar | `feat/prism-next-02-opportunity-backend` | #426 | `d3ef3729` | `src/pages/NovaNetPage.tsx`; NovaNet-only components under `src/components/novanet/`; opportunity UI modules under `src/components/opportunities/`; **scoped backend repair ownership for `solspire/buyer_recon.py` and `solspire/buyer_recon_router.py` limited to the measured project/workspace board uniqueness and entry-create arity defects**; NovaNet/opportunity-specific tests and evidence | App/router/surfaces registry, global navigation, shared tokens, shared shell tests, unrelated SolSpire authority/authentication behavior |
| 3. Solariun and Knowledge OS | `feat/prism-next-03-knowledge-search` | #427 | `7b5b71c5` | Solariun/Knowledge OS page modules and feature-local components/tests/evidence, after exact existing paths are discovered from current tree/archive and recorded in its PR | App/router/surfaces registry, global navigation, shared tokens, shared shell tests, NovaNet files |
| 4. Arkana, Weaver, Engineering Lab | `feat/prism-next-04-arkana-threads` | #428 | `91cac4bf` | Arkana/Oracle, Weaver, Engineering Lab feature-local page modules/components/tests/evidence, after exact paths/contracts are discovered and recorded in its PR | App/router/surfaces registry, global navigation, shared tokens, shared shell tests, NovaNet/Solariun files, runtime/authority model |

The first-wave branches (`feat/prism-parallel-01-…` through `-04-…`) are closed history; do not reopen or continue them. The four next-wave branches above are the active threads, and all four agents continue automatically after each merge.

**Important:** these are ownership boundaries, not proof that every proposed directory already exists. Inspect the live tree first. Do not create duplicate abstractions just to match a suggested path. If an existing file spans two owners, the shell/integration owner owns the seam; feature agents submit a narrow proposal instead of editing it.

## 2. PR #418 — measured patch map and disposition

PR #418 was merged via squash as `49de33d4ebaee7f73cd914182c430cc2fb523b4e`. Its NovaNet route alias, page, shell lens, endpoint/type entries, reconciliation inventory, and updated hourly governance instructions are now part of `main`. The four feature PRs were then merged: #423 `972c342380e718153fe7a3c20f0f63684f2dec82`, #420 `55b27d10ae61cef4d33c2b9d80c355bd64d8f481`, #421 `22941cc510747378992b7ac3b3df8e20ce26f8ae`, and #422 `e924aec17ff2a68f3bce0ca61a183ca306416e3f`.

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

The initial reconciliation and four workstream PRs are merged into `main`; do not cherry-pick or copy them into new branches. The next wave starts from fresh `main` with new PRs, not by reopening or duplicating the closed PRs. Historical evidence below remains useful for provenance, but PR #418 is no longer an active ownership blocker.

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

- Each agent reads `AGENTS.md`, ADR-016, the current reconciliation directive, this contract, its own instruction file, live `main`, the latest merged workstream evidence, and current checks before editing. PR #418 is historical context, not an active blocker.
- Each agent edits only its owned files. Shared frontend endpoint/type/route changes are integrated by Workstream 1. Workstream 2's backend ownership is the narrow exception explicitly listed in §1: only the two measured buyer-recon defects and regression tests; no unrelated auth/authority refactor.
- Before implementation, each feature agent writes a short capability matrix: legacy source, current route, exact backend contract/auth, data states, tests, status and unknowns.
- Keep PRs draft until their bounded slice has targeted tests, build/typecheck where applicable, evidence bound to exact commit, and baseline-failure comparison.
- No agent merges another PR or rebases/force-pushes another agent's branch. If a contract change is needed, pause that dependent slice and record the blocker.
- Integrator checks changed-file overlap, dependency direction, combined build/test behavior, route collision and authorization boundaries. Do not merge merely because individual PRs pass.
- Every next-wave branch starts from the observed current `main` for clean ownership. Keep four long-running source-editing threads active. When one PR merges, the agent immediately opens its next bounded PR from the new `main`; do not wait for the user to say 'continue'. If blocked on another workstream, keep progressing on a non-overlapping task and report the dependency.
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


## 7.1 Next-wave scope assignment — 2026-10-11

The first-wave PRs are merged. The next work begins immediately on fresh branches/PRs:

- **Workstream 1:** own the shared integration seam. First resolve the Lab `labSession(id)` helper request and any verified Opportunity Radar endpoint/type request; then continue the next archived shell/navigation gap.
- **Workstream 2:** explicitly owns the narrowly scoped backend repair in `solspire/buyer_recon.py` and `solspire/buyer_recon_router.py` for the two defects measured in its merged evidence: create-entry column/value arity mismatch and inability for one subject to hold both workspace and project boards. Add regression tests and a safe migration for existing data. No broader auth, execution, budget, or authority changes.
- **Workstream 3:** mount the verified multi-mode Knowledge OS search panel into `KnowledgePage.tsx`, using only the handler-verified `POST /api/knowledge/search` contract and the shared endpoint registry; continue personal/public boundary tests.
- **Workstream 4:** implement Arkana thread history against the verified `/api/commune/threads` handler, preserving truthful state and human-approval boundaries.

All four agents should continue automatically after each merge. Human attention is required only for an explicit authority decision, a security/privacy risk, a destructive or data-loss migration decision that cannot be made safely, or a genuinely unresolved cross-workstream contract. An external provider failure must be reported with exact evidence but must not block unrelated UI work.
