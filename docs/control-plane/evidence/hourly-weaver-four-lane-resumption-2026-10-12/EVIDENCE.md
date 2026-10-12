# Evidence — OpenHands hourly automation and four-lane recovery

**Observed:** 2026-10-12  
**Repository:** `Arkadia-Oversoul-Prism/Arkadia`  
**Current main at checkpoint:** `49809f45274f2f81b24e01fefdfb3009e8717495`  
**Purpose:** reconcile live scheduler output, four lane PRs, and the portfolio evidence boundary. This record is not an OpenHands dispatch claim.

## 1. Scheduler source of truth

- Workflow: [Arkadia Engineering Scheduler](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/workflows/arkadia-engineering-scheduler.yml)
- Latest successful scheduled run identified: [#38165015207](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/38165015207)
- Event/time/head: scheduled, `2026-10-11T18:43:34Z`, `36df0ea8169087802e4fc34ae96496058a380d05`
- Actual output: `status=NO_LEGAL_MOVE`, `next_move=NONE`, `dry_run=true`.
- Exact blockers: `G12-A` and `G12-C` have `merged_acceptance_pending`, which the pinned router vocabulary intentionally reports as unrecognized; `G12-B` depends on `G12-A`; `G14` depends on `G12-C`; `G15` depends on `G14`; `G16` depends on `G15`.
- The runner recorded an attention outbox event. Delivery status was `NOT_CONFIGURED`, with reason `ARKADIA_ATTENTION_DELIVERY_URL/SOVEREIGN_KEY/ARKADIA_ATTENTION_OWNER_UID not configured`; the run therefore had durable blocker evidence but no configured attention delivery.
- Interpretation: the job did not silently skip the frontier—the artifact names the vocabulary and dependency blockers. `NO_LEGAL_MOVE` is the worker's current contract and is expected by the worker→attention composition tests; do not rename it without a coupled contract change. The scheduler still did not prove four OpenHands dispatches.
- Pull-request-triggered scheduler run [#38294936054](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/38294936054) passed the conformance guards; its runner step was skipped because the event was `pull_request`. It is not a scheduled execution.
- The connected tool surface exposes GitHub repository/PR operations but no callable OpenHands dispatch-and-run-inspection action. Actual lane outputs below establish useful work products; they do not retroactively prove the hourly scheduler dispatched those workers.

## 2. Four live workstreams

| Lane | Active PR / head | Base relationship to current main | Durable output / next action |
|---|---|---|---|
| W1 — Shell/navigation/integration | [#497](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/497), `cc1e8f7cb4f0047e208dd9e014a9b5166051face` | Fresh base `49809f45274f2f81b24e01fefdfb3009e8717495`; ahead 6, behind 0 | Fresh-base replay of legacy `/nexus/<sub>` deep-link resolution. All nine reported workflow runs on this exact head completed successfully. The 32 focused shell-contract test count is historical predecessor evidence; no independent local test execution is claimed. |
| W2 — NovaNet/Opportunity Radar | [#492](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/492), `2c24adb516f10c5491de0be50a1b732156598f62` | Fresh base `49809f45274f2f81b24e01fefdfb3009e8717495`; ahead 1, behind 0 | Per-status opportunity pipeline strip; off-vocabulary statuses counted instead of dropped. PR records 55 focused tests, 408 derived-domain tests, 11 architecture tests and frontend build. |
| W3 — Solariun/Knowledge OS | [#498](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/498), `e7086afd0420f847cab6b9364857998db77b24e9` | Fresh base `49809f45274f2f81b24e01fefdfb3009e8717495`; ahead 5, behind 0 | Fresh-base replay of “Load older events” paging. All nine reported workflow runs on this exact head completed successfully. The 52 paging/window/boundary test count is historical predecessor evidence; no independent local test execution is claimed. |
| W4 — Arkana/Weaver/Engineering Lab | [#493](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/493), `d3e978d13d5a5f4bbb41776e46e8ef8bcb6ad619` | Fresh base `49809f45274f2f81b24e01fefdfb3009e8717495`; ahead 1, behind 0 | Read-only Lab automation grammar projection. PR records 49 focused tests, 450 derived-domain/wiring tests, 11 architecture tests and frontend build. Write-path remains intentionally unwired. |

Check conclusions: PRs #497, #492, #498, and #493 each have nine successful workflow runs on their recorded fresh-base heads. PR bodies contain command-level evidence; predecessor test counts remain historical and are not represented as independently re-executed in this checkpoint.

## 3. Control-plane router defect and proposed repair

- Proposed router PR [#495](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/495) is **closed without merge** after two contract-conflicting approaches.
- Fresh-main [PR #499](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/499), head `c1e7718b084f35a47322256f7f4ef58b8e34b31c`, proposes explicit non-routable gates for `merged`, `merged_acceptance_pending`, `blocked`, `failed`, and `aborted`; only `completed`/`accepted` remain terminal. It preserves the worker result `NO_LEGAL_MOVE` and projects the acceptance gate into the existing high-priority attention path.
- This specifically avoids both unsafe alternatives: routing an already-merged move as active, or treating a merge as acceptance. Schema/router/worker-composition CI is still running; no fix is accepted or verified yet.

## 4. Portfolio boundary

- Draft portfolio PRs #480 and #455 overlap on `docs/portfolio/BOUNDED_TECHNICAL_PORTFOLIO.md`; neither is a second independent portfolio deliverable.
- Existing bounded authenticated Engineering Lab acceptance: [run #38159464567](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/38159464567), source/live SHA `36df0ea8169087802e4fc34ae96496058a380d05`, deployment `dep-db5s9i0u01pc73evsrjg`. Valid for that exact revision and bounded journey only.
- Current main `49809f45274f2f81b24e01fefdfb3009e8717495` does not inherit that acceptance. Current route reconciliation, OpenAPI authorization coverage, additional authenticated UI journeys, and authoritative integration cleanup remain unestablished by this record.

## 5. Governance and next gates

- No PR merged, no production deployment triggered, and no acceptance declared in this recovery.
- Render remains the only canonical production origin.
- Human retains merge, production-deployment, and acceptance authority.
- Next: inspect current-head CI on #499; retain #497/#492/#498/#493 as independent drafts (all nine reported workflows passed on each current head); recover the missing callable OpenHands dispatch/inspection interface; do not merge or claim acceptance.
