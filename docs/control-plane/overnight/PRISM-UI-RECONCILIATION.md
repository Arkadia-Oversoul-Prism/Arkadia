# Prism UI Reconciliation — Overnight Engineering Contract

**Status:** Active implementation directive; proposed through PR, not yet accepted into `main`.
**Prepared:** 2026-10-11
**Base revision:** `1fd96e767575ade56e953a02fcf8f1db46073336`
**Canonical production:** `https://arkadia-qzu4.onrender.com`
**Workstream:** Arkadia Console rebuild / reconciliation with archived Prism
**Consumers:** Upper Hands Engineering Lab, Weaver, and the Hourly Weaver Automation/pulse.
**Authority:** Human retains merge, production-deployment, and acceptance authority.

This document is the active work instruction for the overnight UI workstream. Every Engineering Lab / Weaver pulse must read it alongside `AGENTS.md`, the current `main` SHA, the live PR state, and the evidence files it cites. Do not depend on conversation memory or an old automation prompt.

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

On **each Hourly Weaver / OpenHands pulse**, the accepted contract at `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`, `AGENTS.md`, the four durable workstream instructions, current `main`, live PRs/branches/checks, and latest run evidence are mandatory inputs. The contract defines ownership; live GitHub state defines what is currently active.

1. **Prove the pulse source and outcome.** Identify the actual scheduler/run, trigger, timestamp, head SHA, dry-run setting, worker/agent dispatch evidence, and durable output. A green scheduler job is not proof that OpenHands agents were dispatched. If the run is only an orientation/dry-run or returns `NO_LEGAL_MOVE`, report that literally and do not claim source work advanced.
2. **Reconstruct from live state.** Fetch current `main` SHA; enumerate all four assigned branches and matching open PRs; inspect head/base SHAs, latest meaningful commits, check conclusions, and changed files. Treat closed/merged PRs as history, never as active work surfaces. Never copy an old branch map forward without measurement.
3. **Check contract freshness.** If the accepted shared contract's branch map contradicts live state, Workstream 1 must reconcile that coordinator-owned contract on its own branch/PR. Until merged, this directive's live reconstruction is authoritative for the current pulse; no stale PR number or branch may be resumed.
4. **Select one bounded task per lane.** Stay inside the lane's exclusive ownership. State the concrete user-visible or enabling outcome and why it outranks alternatives. If a lane has no authorized OpenHands worker/dispatch, record the exact dispatch/control-plane blocker rather than pretending to run an agent.
5. **Change and verify.** Edit only owned source/tests/evidence. Run narrow tests, typecheck/build, route checks and applicable security/architecture guards. Compare new failures with a fresh baseline by test-node identity.
6. **Record durable evidence.** For each lane, record full base/head SHAs, branch and PR URL, last meaningful commit, changed paths, commands and exact results, checks, unknowns/blockers, and next bounded move. A status summary without these artifacts is not a work result.
7. **Commit to the lane's long-lived PR.** Each lane uses one long-lived branch/PR at a time. After a human merge, that lane creates its next branch from freshly fetched `main` and opens its next draft PR. Never create a new PR for each pulse or resume a closed branch.
8. **Reconcile cross-lane state.** Re-read all four heads/checks and inspect file overlap. Workstream 1 owns shared shell, routes, endpoint/type registries and the shared branch map. Feature lanes must request shared-seam changes rather than edit them directly.
9. **Preserve human authority.** Agents may inspect, implement, test, commit and update draft PRs. They may not merge, deploy production, or declare acceptance. Production remains Render only.
10. **Report exact per-lane outcomes.** Use `IMPLEMENTED`, `TESTED`, `BLOCKED`, or `NOT DISPATCHED` with linked evidence. Do not infer concurrency, advancement, or success from workflow status alone.

A pulse with no safe, verified source change must produce a precise blocker and next action, not a speculative commit. Do not measure progress by file count, line count, percentage, or green scheduler status alone.

## 7. Four workstreams — live branch map, not permanent identifiers

The accepted parallel-work contract supersedes the former single-branch/single-PR rule. The shared contract defines exclusive ownership, but its branch/PR observations are snapshots, not durable identifiers. At the start of every pulse, reconstruct the live map from GitHub and reconcile it through Workstream 1.

**Last verified snapshot (2026-10-12, `main` `26521e246e575105ec9a42fec26dc66aeb4c98f4`):**

| Workstream | Last implementation PR | Verified disposition | Next required action |
|---|---|---|---|
| 1. Shell, navigation, design system, integration contracts | [#429](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/429) | Merged; old `feat/prism-next2-01-shell-contract-map` is history | Refresh shared contract branch map and select one fresh-base shell/integration task |
| 2. NovaNet and project Opportunity Radar | [#430](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/430) | Merged; old `feat/prism-next2-02-opportunity-entry-flow` is history | Select one fresh-base, feature-local opportunity improvement |
| 3. Solariun and Knowledge OS | [#431](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/431) | Merged; old `feat/prism-next2-03-knowledge-timeline` is history | Select one fresh-base, feature-local knowledge improvement |
| 4. Arkana, Weaver, Engineering Lab | [#432](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/432) closed unmerged; retained trace/model-gateway work merged via [#475](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/475) | #432 is history; #475 is merged history, not an active PR | Select one fresh-base, feature-local Arkana/Weaver/Lab improvement |

**Automation evidence boundary:** the latest successful GitHub scheduled Engineering Scheduler run found during this reconciliation is [#38165015207](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/38165015207), on 2026-10-11 at 18:43:34 UTC, at head `36df0ea8169087802e4fc34ae96496058a380d05`. Its actual log reports `status=NO_LEGAL_MOVE`, `next_move=NONE`, and `dry_run=true`. It proves the scheduler ran; it does **not** prove four OpenHands workstreams were dispatched or advanced. No newer scheduled run was found in the retrieved schedule-run history. Keep this limitation explicit until a real OpenHands dispatch and each lane's output are observed.

The first-wave PRs (#420–#423), next-wave PRs (#429–#432), and reconciliation PRs #471–#475 are history according to their live dispositions. Do not reopen or continue them as active work. Create fresh branches from the current `main` for the next bounded tasks; Workstream 1 updates the accepted contract's active branch map in its own PR. The human retains merge, production-deployment, and acceptance authority.

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
