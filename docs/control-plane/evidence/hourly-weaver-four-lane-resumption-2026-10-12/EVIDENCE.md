# Evidence — OpenHands hourly automation and four-lane recovery

**Observed:** 2026-10-12  
**Repository:** `Arkadia-Oversoul-Prism/Arkadia`  
**Current main at checkpoint:** `49809f45274f2f81b24e01fefdfb3009e8717495`  
**Purpose:** reconcile live scheduler output, four lane PRs, and the portfolio evidence boundary. This record is not an OpenHands dispatch claim.

## 1. Scheduler source of truth

- Workflow: [Arkadia Engineering Scheduler](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/workflows/arkadia-engineering-scheduler.yml)
- Latest successful scheduled run identified: [#38165015207](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/38165015207)
- Event/time/head: scheduled, `2026-10-11T18:43:34Z`, `36df0ea8169087802e4fc34ae96496058a380d05`
- Actual output: `status=NO_LEGAL_MOVE`, `next_move=NONE`, `dry_run=true`
- Interpretation: scheduler job succeeded, but selected no move and did not prove four OpenHands dispatches.
- Pull-request-triggered scheduler run [#38294936054](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/38294936054) passed the conformance guards; its runner step was skipped because the event was `pull_request`. It is not a scheduled execution.
- The connected tool surface exposes GitHub repository/PR operations but no callable OpenHands dispatch-and-run-inspection action. Actual lane outputs below establish useful work products; they do not retroactively prove the hourly scheduler dispatched those workers.

## 2. Four live workstreams

| Lane | Active PR / head | Base relationship to current main | Durable output / next action |
|---|---|---|---|
| W1 — Shell/navigation/integration | [#489](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/489), `8fff6eef4f6224236da5ae2f685e1f5d3f1774f5` | Base `ee684fff...`; current-main comparison: ahead 1, behind 2, diverged | Legacy `/nexus/<sub>` deep-link resolution. Recorded 32 focused shell-contract tests and broader checks on that head. Reconcile onto current main, rerun checks. |
| W2 — NovaNet/Opportunity Radar | [#492](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/492), `2c24adb516f10c5491de0be50a1b732156598f62` | Fresh base `49809f45274f2f81b24e01fefdfb3009e8717495`; ahead 1, behind 0 | Per-status opportunity pipeline strip; off-vocabulary statuses counted instead of dropped. PR records 55 focused tests, 408 derived-domain tests, 11 architecture tests and frontend build. |
| W3 — Solariun/Knowledge OS | [#491](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/491), `c2427815b4dd0bd7e1c1a3f003e39bad3d4edf97` | Base `ee684fff...`; current-main comparison: ahead 1, behind 2, diverged | “Load older events” paging. PR records 52 paging/window/boundary tests, 136 sibling contracts, 11 architecture tests and frontend build. Reconcile onto current main, rerun checks. |
| W4 — Arkana/Weaver/Engineering Lab | [#493](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/493), `d3e978d13d5a5f4bbb41776e46e8ef8bcb6ad619` | Fresh base `49809f45274f2f81b24e01fefdfb3009e8717495`; ahead 1, behind 0 | Read-only Lab automation grammar projection. PR records 49 focused tests, 450 derived-domain/wiring tests, 11 architecture tests and frontend build. Write-path remains intentionally unwired. |

Check conclusions observed for lane heads: all nine reported workflow runs on each of #489, #491, #492 and #493 completed successfully. For #489/#491, these checks apply to their old heads, not to a reconciled head on current main. PR bodies contain the detailed command-level evidence; do not promote PR-reported tests to independently re-executed tests in this checkpoint.

## 3. Control-plane router defect

- Draft repair: [PR #495](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/495), branch `fix/weaver-acceptance-pending-router-current-main`, head `763af66386384e0b92e485e7ad91213313e43b4e`.
- It recognizes `merged_acceptance_pending`, `blocked`, `failed`, and `aborted` as valid but non-routable states; requires human acceptance evidence after merge; and distinguishes a true clean stop from a blocked frontier.
- PR checks observed: scheduler conformance job succeeded; Weaver MVP2 validation failed at `Engineering-router status truthfulness guard`; provider routing verification was still in progress at last observation.
- The new regression test has not been independently executed in this session. **Do not merge or claim the fix verified until the failing guard is diagnosed and the complete relevant checks pass.**

## 4. Portfolio boundary

- Draft portfolio PRs #480 and #455 overlap on `docs/portfolio/BOUNDED_TECHNICAL_PORTFOLIO.md`; neither is a second independent portfolio deliverable.
- Existing bounded authenticated Engineering Lab acceptance: [run #38159464567](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/38159464567), source/live SHA `36df0ea8169087802e4fc34ae96496058a380d05`, deployment `dep-db5s9i0u01pc73evsrjg`. Valid for that exact revision and bounded journey only.
- Current main `49809f45274f2f81b24e01fefdfb3009e8717495` does not inherit that acceptance. Current route reconciliation, OpenAPI authorization coverage, additional authenticated UI journeys, and authoritative integration cleanup remain unestablished by this record.

## 5. Governance and next gates

- No PR merged, no production deployment triggered, and no acceptance declared in this recovery.
- Render remains the only canonical production origin.
- Human retains merge, production-deployment, and acceptance authority.
- Next: diagnose #495's failing router-status-truthfulness guard; reconcile W1 #489 and W3 #491 against current main and rerun checks; preserve W2 #492 and W4 #493 as fresh-base independent drafts; update the portfolio only with exact-SHA evidence.
