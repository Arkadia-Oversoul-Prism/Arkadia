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
| W1 — Shell/navigation/integration | [#497](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/497), `b63b641800ccd10aa316f4be443a8ccc60b1615c` | Fresh base `49809f45274f2f81b24e01fefdfb3009e8717495`; ahead 5, behind 0 | Fresh-base replay of legacy `/nexus/<sub>` deep-link resolution. The original PR recorded 32 focused shell-contract tests; current-head CI is in progress, so no current-head test pass is claimed. |
| W2 — NovaNet/Opportunity Radar | [#492](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/492), `2c24adb516f10c5491de0be50a1b732156598f62` | Fresh base `49809f45274f2f81b24e01fefdfb3009e8717495`; ahead 1, behind 0 | Per-status opportunity pipeline strip; off-vocabulary statuses counted instead of dropped. PR records 55 focused tests, 408 derived-domain tests, 11 architecture tests and frontend build. |
| W3 — Solariun/Knowledge OS | [#498](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/498), `7ca474846bc994b4e609bcdfeca1b88a1279fde6` | Fresh base `49809f45274f2f81b24e01fefdfb3009e8717495`; ahead 4, behind 0 | Fresh-base replay of “Load older events” paging. Original PR recorded 52 paging/window/boundary tests; current-head CI is in progress, so no current-head test pass is claimed. |
| W4 — Arkana/Weaver/Engineering Lab | [#493](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/493), `d3e978d13d5a5f4bbb41776e46e8ef8bcb6ad619` | Fresh base `49809f45274f2f81b24e01fefdfb3009e8717495`; ahead 1, behind 0 | Read-only Lab automation grammar projection. PR records 49 focused tests, 450 derived-domain/wiring tests, 11 architecture tests and frontend build. Write-path remains intentionally unwired. |

Check conclusions: old PRs #489 and #491 had nine successful workflow runs each on their old heads. Their fresh-main successors #497 and #498 now have current-head CI in progress. PRs #492 and #493 each have nine successful workflow runs on their fresh-base heads. PR bodies contain command-level evidence; do not promote PR-reported tests to independently re-executed tests in this checkpoint.

## 3. Control-plane router defect

- Proposed router PR [#495](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/495) is **closed without merge**.
- The first patch violated the pinned vocabulary decision (8 failures / 36 passes). The revised patch preserved the vocabulary but changed `NO_LEGAL_MOVE` to `BLOCKED`; the worker→attention composition guard then failed 2 tests because it explicitly expects `NO_LEGAL_MOVE` with blocker details carried separately.
- The source of truth is therefore the existing behavior: schema-only statuses remain named as unroutable, dependency blockers are recorded, and the worker/attention contract expects `NO_LEGAL_MOVE`. Do not change router semantics without revisiting the worker→attention contract and its governance decision together.
- No router fix is accepted or claimed. The control-plane correction belongs first in coordinator interpretation and dispatch proof, not in a speculative router status rewrite.

## 4. Portfolio boundary

- Draft portfolio PRs #480 and #455 overlap on `docs/portfolio/BOUNDED_TECHNICAL_PORTFOLIO.md`; neither is a second independent portfolio deliverable.
- Existing bounded authenticated Engineering Lab acceptance: [run #38159464567](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/38159464567), source/live SHA `36df0ea8169087802e4fc34ae96496058a380d05`, deployment `dep-db5s9i0u01pc73evsrjg`. Valid for that exact revision and bounded journey only.
- Current main `49809f45274f2f81b24e01fefdfb3009e8717495` does not inherit that acceptance. Current route reconciliation, OpenAPI authorization coverage, additional authenticated UI journeys, and authoritative integration cleanup remain unestablished by this record.

## 5. Governance and next gates

- No PR merged, no production deployment triggered, and no acceptance declared in this recovery.
- Render remains the only canonical production origin.
- Human retains merge, production-deployment, and acceptance authority.
- Next: wait for and inspect current-head CI on #497/#498; keep #492/#493 as fresh-base independent drafts; use the corrected evidence/contract PR #496 to consolidate the live state; do not merge or claim acceptance.
