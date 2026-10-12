# Prism UI Reconciliation — Overnight Engineering Contract

**Status:** Active implementation directive; proposed through PR, not yet accepted into `main`.
**Prepared:** 2026-10-11
**Base revision:** `1fd96e767575ade56e953a02fcf8f1db46073336`
**Canonical production:** `https://arkadia-qzu4.onrender.com`
**Workstream:** Arkadia Console rebuild / reconciliation with archived Prism
**Consumers:** Upper Hands Engineering Lab, Weaver, and the Hourly Weaver Automation/pulse.
**Authority:** Human retains merge, production-deployment, and acceptance authority.

This document is the active work instruction for the overnight UI workstream. Every Engineering Lab / Weaver pulse must read it alongside `AGENTS.md`, the current `main` SHA, the live PR state, and the evidence files it cites. Do not depend on conversation memory or an old automation prompt.


## Live recovery checkpoint — 2026-10-12

**Observed current main:** `49809f45274f2f81b24e01fefdfb3009e8717495`. This checkpoint supersedes older branch-map snapshots below; historical snapshots remain provenance, not current assignments.

- W1 shell/navigation: [PR #489](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/489), head `8fff6eef4f6224236da5ae2f685e1f5d3f1774f5`, is 2 commits behind/diverged from current main. Its checks passed on its old head; reconcile the patch and rerun checks against a fresh base.
- W2 Opportunity Radar: [PR #492](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/492), head `2c24adb516f10c5491de0be50a1b732156598f62`, is 1 commit ahead of current main. Focused tests/build evidence are recorded in the PR; verify the live check set before any readiness claim.
- W3 Knowledge OS: [PR #491](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/491), head `c2427815b4dd0bd7e1c1a3f003e39bad3d4edf97`, is 2 commits behind/diverged from current main. Its checks passed on its old head; reconcile the patch and rerun checks against a fresh base.
- W4 Engineering Lab: [PR #493](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/493), head `d3e978d13d5a5f4bbb41776e46e8ef8bcb6ad619`, is 1 commit ahead of current main. Focused tests/build evidence are recorded in the PR; write-path remains unwired.
- Control plane: proposed router PR [#495](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/495) is closed without merge. Its first patch violated the pinned vocabulary decision; its second patch broke the worker→attention composition guard, which expects `NO_LEGAL_MOVE` plus explicit blocker details. Preserve the current router/worker contract; fix coordinator interpretation and dispatch proof first.
- Scheduler truth: scheduled run [#38165015207](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/38165015207) reported `NO_LEGAL_MOVE`, `next_move=NONE`, `dry_run=true`. Pull-request-triggered scheduler run [#38294936054](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/38294936054) passed its conformance steps but skipped the runner. Neither event alone proves an OpenHands hourly dispatch.
- Authority: no merge, production deployment, or acceptance is performed by this checkpoint. Render remains the sole canonical production origin.
## 1. Objective

The current `web/arkadia_console/` UI is a **thin scaffold**, not feature parity with the retired Prism product. The archived Prism frontend contains roughly 30k lines across 135 source files and must be treated as a valuable, recoverable implementation and product-history source—not discarded, not blindly restored, and not assumed to be compatible with today's backend contracts.

Reconcile the product deliberately:

- Recover the useful interaction patterns, information architecture, product identity, visual language, and workflows already built in Prism.
- Map each useful legacy capability to the current canonical backend/API and current Arkadia architecture.
- Implement the highest-value slices in the new console incrementally, reusing the current identity, authorization, workspace, project, evidence, and execution substrate.
- Retain the archived source and its Git history. Do not delete the archive or make a production cutover.
- Make each pulse leave a tested, reviewable improvement within the **four-workstream parallel plan** governed by `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`. Each workstream owns one branch/PR; shared files have exactly one owner.

The target is not a cosmetic shell, a second application, or a large unreviewed rewrite. The target is a coherent product UI that regains Prism's depth while preserving the newer backend's stronger governed capabilities.

## 2. Canonical source map

Read these before selecting work:

- `AGENTS.md` — governing agent and repository contract.
- `docs/adr/ADR-016-single-canonical-deployment.md` — one canonical deployment.
- `docs/control-plane/evidence/frontend-arkadia-console-01/EVIDENCE.md` — console cutover, current scaffold inventory, and baseline claims.
- `docs/control-plane/evidence/aeas05-console-route-contract-01/EVIDENCE.md` — route-contract and production acceptance history; check later entries and current SHAs before relying on older claims.
- `archive/frontend/arkadia-prism/README.md` — archive contents and recovery procedure.
- `archive/frontend/arkadia-prism/web/public_prism/` — legacy UI, components, pages, assets, routes, and feature behavior.
- `web/arkadia_console/` — active frontend being reconciled.
- `web/arkadia_console/src/lib/surfaces.ts`, `router.ts`, `apiConfig.ts`, `apiClient.ts`, `endpoints.ts` — active route/API boundary.
- `api/`, `solspire/`, `weaver/`, `lab/engineering_lab/`, and `knowledge/` — implementation and contracts to reuse, not duplicate.
- `tests/test_frontend_arkadia_console_rebuild_01.py`, `tests/test_canonical_frontend_routing.py`, and `tests/test_aeas05_canonical_frontend_acceptance.py` — route, archive, and serving regression guards (verify exact paths on current main).

The archive is evidence of prior product work, **not proof that every old endpoint, assumption, suffix, or route remains valid**. Current backend contracts and explicit governance outrank legacy frontend assumptions.

## 3. First pulse: inventory before redesign

The first pulse must produce a compact, checked-in feature/route reconciliation matrix before a broad implementation pass. Include at least:

| Field | Required content |
|---|---|
| Legacy capability | Named page, component, interaction, or workflow; cite source path |
| Legacy route / suffix | Exact observed path(s), including aliases and suffix variants |
| Current surface | New-console route/component or `MISSING` |
| Backend contract | Exact existing endpoint/module and auth requirement, or `UNKNOWN` |
| State and persistence | Real source of data; loading, empty, auth, error, success states |
| Decision | Reuse, adapt, replace, defer, or retire with evidence |
| Test | Existing test or a concrete new regression check |
| Status | `VERIFIED`, `IMPLEMENTED`, `BLOCKED`, `UNKNOWN`, or `DEFERRED` |

Inventory navigation, page families, modals, global controls, audio/voice, uploads, personal/public content boundaries, projects, knowledge surfaces, Oracle/Arkana, and mobile layouts. Search the archive and Git history instead of guessing from the visible shell. Record duplicate suffixes and conflicting route declarations explicitly; do not silently choose one.

Run both frontend builds and the relevant existing tests at baseline, where the environment permits. Record the exact SHA, commands, results, and pre-existing failures. Do not use baseline failures as a reason to skip new targeted tests.

## 4. Implementation order

After the inventory, choose **one bounded vertical slice per pulse**, based on user-visible value, backend readiness, and risk. Suggested order; revise only with recorded evidence.

### Slice A — Product shell and design-system reconciliation
- Compare archived Prism's actual shell, navigation, page hierarchy, responsive behavior, typography, color, spacing, and interaction affordances with the new console.
- Establish reusable console primitives rather than page-local styling drift.
- Keep one global navigation model and one router/surface declaration. Eliminate duplicate aliases only after proving inbound links and route contracts.
- Preserve visible auth, loading, unavailable, empty, and error states. No decorative controls that do nothing.

### Slice B — Solariun / personal field
- Reconcile home, personal workspace, personal Codex/Echofeild, capture, and knowledge entry points against the real personal-data contracts.
- Keep personal data behind the authenticated identity boundary; never route personal uploads into the public corpus.
- Reuse existing audio/read-aloud infrastructure where the backend and UI contracts support it.

### Slice C — Arkana / Oracle experience
- Recover the legacy conversation canvas and useful message interactions (Markdown, source/reference presentation, voice controls, history where truly supported).
- Use the canonical Arkana/Oracle endpoint and current response shape; do not invent streaming, memory, citations, or provider behavior absent from the live contract.
- Render backend failure honestly. No mock replies, fabricated evidence, or “success” inferred from an empty state.

### Slice D — SolSpire Projects and Opportunity Radar
- Make project navigation and project detail feel like a usable operational workspace, not a placeholder.
- Surface the Opportunity Radar within each project / Weaver project workflow, reusing the existing opportunity capture and project substrate instead of creating a parallel store.
- Keep buyer, contract, budget, and outreach claims tied to their evidence state; `UNKNOWN` remains visible when facts are not established.

### Slice E — Knowledge OS
- Reconcile files, captures, graph/timeline/search surfaces against actual APIs and authorization boundaries.
- Keep public corpus and private vault clearly separate in copy, controls, endpoint selection, and tests.
- Avoid adding a second memory database or duplicate source of truth.

### Slice F — Weaver and Engineering Lab
- Make project/workstream state, run history, authorization thresholds, execution outcomes, evidence, and verification legible.
- Preserve the governing distinction: proposal ≠ approval ≠ execution ≠ evidence ≠ verification ≠ acceptance.
- The UI may expose a capability only when the real backend contract exists and the required human authorization is present. Read-only Engineering Lab capabilities must not silently become repository mutation capabilities.

This order is a prioritization guide, not permission to implement every slice overnight. The inventory and evidence decide the next bounded move.

## 5. Route and suffix reconciliation rules

The prior UI accumulated route suffixes, aliases, and overlapping page structures. Prevent recurrence:

1. Establish one canonical route per user-facing surface in `src/lib/surfaces.ts`; use the shared router rather than page-specific path parsing.
2. Before renaming a route, enumerate references in the archive, current source, tests, deep links, and backend router table. Document compatibility/redirect decisions.
3. Never mount an SPA on a path owned by a real backend handler or reserved API prefix. Check the real FastAPI route table, not only the Vite dev server.
4. Do not create another API prefix, frontend suffix, router, persistence store, or authority path to work around a mismatch.
5. Keep `lib/apiConfig.ts` as the canonical API base. No hardcoded fallback hostname, no Vercel origin, and no second production API base.
6. Add a regression test for every resolved collision/alias family, including a negative control where practical.

## 6. Per-pulse execution loop — four-workstream governance

On **each Hourly Weaver pulse**, perform these steps in order. The accepted shared contract at `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` and the four durable agent instructions are mandatory inputs.

1. **Reconstruct:** fetch current `main` SHA; PR #418 state/head/diff/checks; PRs #419–#422 state/head/checks; all four assigned branches; relevant files and current evidence. Do not assume a PR is merged or a branch is current from memory.
2. **Select:** select one bounded task within the active workstream's ownership. State why it outranks alternatives.
3. **Check ownership:** compare every intended path against the shared contract. If another workstream owns it, do not edit it; create a precise interface request/blocker for the owner.
4. **Change:** edit only owned source/tests/evidence. No opportunistic refactors or duplicate implementations.
5. **Verify:** run narrow tests, typecheck/build, route checks and applicable security/architecture guards. Compare new failures to a fresh baseline by node identity.
6. **Record:** update feature matrix/work log with full SHA, paths, commands, exact results, failures, unknowns and next move.
7. **Commit:** commit verified progress only to the workstream's assigned branch and update its existing PR. Never create a new PR for each pulse.
8. **Reconcile:** reread branch/PR heads, checks and changed-file overlap across all four PRs. Stop if another actor moved a branch or semantic integration is unclear.
9. **Integrate:** continuously identify dependency order and overlap; do not merge one PR into another or main automatically. Shared contract/interface changes go through Workstream 1 and require explicit human review.
10. **Report:** end with exact state per workstream: IMPLEMENTED, BUILD/TEST PASSED, PREVIEW READY, PREVIEW VERIFIED, BLOCKED, or UNKNOWN. No inferred progress.

1. **Reconstruct:** fetch current `main`, this branch, the existing PR, relevant open PRs, current CI/check-runs, and the latest evidence. Confirm the branch/PR is still the one authorized work surface. If `main` moved, inspect the delta before continuing.
2. **Select:** choose one bounded, user-visible slice or one enabling inventory/test task. State why it outranks alternatives.
3. **Change:** edit only the required source, tests, and evidence. No opportunistic refactors.
4. **Verify:** run the narrow tests, TypeScript/build checks, route checks, and any applicable security/architecture guards. Compare new failures with a fresh baseline by test-node identity.
5. **Record:** update the feature matrix and work log with full SHA, paths, commands, exact results, failures, unknowns, and next move.
6. **Commit:** commit only verified progress to this same branch and update this same PR. Each of the four accepted workstreams also maintains its own durable branch/PR; do not create a new PR per pulse.
7. **Reconcile:** reread `main`, this PR, PRs #420–#423, changed-file overlap and checks before the next pulse. PR #419 is the merged governance contract; #420–#423 are the four implementation workstreams. Stop only for a real ownership, safety, authority, or integration blocker—not because another workstream exists.

A pulse with no safe, verified source change must produce a precise blocker/next-action record rather than a speculative commit. Do not measure progress by number of files changed, lines written, or a claimed percentage.

## 7. Four branches, four PRs, human merge and acceptance

The former single-branch/single-PR rule is superseded by the explicitly accepted parallel-work governance contract in `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`.

- **Governance contract:** PR #419 is merged into main. **Workstream 1 implementation:** `feat/prism-parallel-01-shell-implementation` / PR #423 — shared shell, navigation, route/surface registry, shared tests and integration contracts.
- **Workstream 2:** `feat/prism-parallel-02-novanet-opportunity` / PR #420 — NovaNet page-local work and project Opportunity Radar feature modules.
- **Workstream 3:** `feat/prism-parallel-03-solariun-knowledge` / PR #421 — Solariun and Knowledge OS feature-local modules.
- **Workstream 4:** `feat/prism-parallel-04-arkana-weaver-lab` / PR #422 — Arkana, Weaver and Engineering Lab feature-local modules.
- Every pulse must read the shared contract and the relevant durable instruction under `docs/control-plane/parallel-ui/`.
- The single-owner table in the shared contract is binding. Shared route/API registry/type files are integrated by Workstream 1; feature agents submit exact contract changes rather than editing shared files directly.
- Keep feature PRs draft while work is in progress. Do not mark a PR ready solely because an agent finished a turn.
- **PR #418 disposition:** preserve it intact as the current existing shell + NovaNet implementation/evidence slice. Do not copy its changes into each new branch, rewrite its history, cherry-pick blindly, or close it automatically. Workstreams 1 and 2 must treat the paths already changed by #418 as existing implementation to reconcile, not recreate. Until #418 is merged or explicitly superseded by a human decision, avoid conflicting source edits to its owned files; Workstreams 1 and 2 may work on non-overlapping tests, inventory, evidence, and feature-local new modules while recording integration requests. Workstreams 3 and 4 may proceed in their isolated feature-owned paths.
- Agents may inspect, implement, test, document, commit to their assigned branch, and update their PR. They may not merge any PR, deploy production, or declare product acceptance.
- Integration means continuous overlap/dependency review and shared-contract reconciliation—not automatic merging. The human retains merge, production-deployment, and acceptance authority.
- Do not force-push, bypass required checks, weaken tests, delete archive history, or change provider settings.

## 8. Deployment boundary — explicit current rule

The only canonical production origin is **`https://arkadia-qzu4.onrender.com`**, governed by ADR-016. The Vercel Git integration was disconnected by the human and the post-disconnect branch-push / draft-PR event class was observed three times without a Vercel status or deployment, with a positive control proving the detector can observe the old behavior.

Treat that result as **VERIFIED for the tested event class**, not as proof about every conceivable provider trigger. Provider settings remain reported rather than directly inspected.

**Do not deploy to Vercel, do not reconnect Vercel, and do not treat any Vercel URL/status/preview as production or acceptance evidence.** If a Vercel deployment unexpectedly reappears, record it as a boundary regression and stop to report it; do not promote it or try to repair it through an alternate deployment. Render preview environments are not canonical production. No production deployment is authorized by this document.

## 9. Acceptance gates for a slice

A slice is complete only when its evidence demonstrates:

- route and suffix decision is explicit and regression-protected;
- UI reads the real backend contract and preserves authentication/authorization;
- loading, empty, error, unavailable, and success states are honest;
- core interaction works with real data or is visibly marked blocked/not wired;
- keyboard/mobile behavior and layout have been checked where the slice changes them;
- targeted tests pass, build/TypeScript passes, and new failures are separated from baseline debt;
- feature matrix and work log bind to the exact commit;
- no duplicate authority, database, endpoint, or deployment path was introduced.

Build success alone is not UI acceptance. Local browser success is not production acceptance. Production acceptance requires a separate human-authorized deployment and live verification.

## 10. Overnight exit condition

At the end of this workstream window, leave its PR in a truthful state and a deterministic handoff containing:

- starting and ending `main` SHA and branch head SHA;
- the feature/route reconciliation matrix;
- slices implemented and slices not started;
- tests/build/browser checks actually run, with exact results and baseline comparison;
- screenshots or visual evidence for changed surfaces when browser tooling is available;
- known gaps, blockers, route/suffix conflicts, and `UNKNOWN` items;
- next single bounded move;
- explicit statement that no merge, production deployment, or acceptance was performed.

**North star:** recover Prism's depth by reconciling its proven product work with the stronger current Arkadia substrate—not by throwing away the old work, and not by mistaking today's scaffold for the finished product.
