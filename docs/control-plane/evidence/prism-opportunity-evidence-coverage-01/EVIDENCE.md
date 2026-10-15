# Opportunity Radar — evidence-coverage metric (display-only)

Workstream 2 (NovaNet & project Opportunity Radar), durable instruction
`docs/control-plane/parallel-ui/AGENT-02-NOVANET-OPPORTUNITY.md`, contract
`docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`, governing directive
`docs/control-plane/overnight/PRISM-UI-RECONCILIATION.md`.

Bounded objective: surface the **evidence-coverage** count the contract already
computes (`opportunityRadarContract.ts::summarize` → `withEvidence`) but no
surface rendered. This is the third metric the radar summary carries
(`byStatus`, `offVocabulary`, `withEvidence`); the first two were reconciled by
`prism-opportunity-pipeline-strip-01`. `withEvidence` remained dead data.

Authority: human retains merge, production deployment, and acceptance. Nothing
here claims any of the three. This slice adds **no transport, no route, no write
control, and no authority**.

## Revision binding

- Work branch: `feat/prism-next7-02-pipeline-strip` (draft PR #492, continued —
  not reopened).
- `origin/main` at the start of this pass:
  `49809f45274f2f81b24e01fefdfb3009e8717495` (`Merge pull request #490 ...`).

## 1. The reconciliation gap (measured, not assumed)

`summarize()` returns `withEvidence` = the count of entries whose
`evidence_status` is not the backend's `NONE` sentinel
(`solspire/buyer_recon.py`). The landed `ProjectOpportunityRadar` rendered
`total`, `actionable`, the per-status columns, and the off-vocabulary note — but
never `withEvidence`. The structure was computed on every render and discarded.

## 2. Why display-only, and why not the capture path

The durable instruction names the *evidence capture path* as the successor task,
**"only if such a handler is verified"**. It is not: `evidence_status` / `evidence`
have **no verified owner- and board-scoped write path** (AGENT-02, recorded
limitation). Adding a write control without one would invent a mutation path — a
hard boundary. The metric is therefore display-only: it reports what the board
already carries and asserts **nothing** about the evidence itself.

## 3. What changed

| File | Change |
|---|---|
| `web/arkadia_console/src/components/opportunities/ProjectOpportunityRadar.tsx` | renders the evidence-coverage line (`data-testid="opportunity-evidence-metric"`), derived from `summary.withEvidence`; names the backend `NONE` sentinel from the imported `NO_EVIDENCE` constant |
| `tests/test_prism_opportunity_entry_flow.py` | +3 tests; Node probe extended with `summary_evidence`, `summary_evidence_none_only`, `no_evidence_sentinel` |

The copy states the metric plainly (`N of M recorded prospect(s) carry an
evidence status other than the backend's NONE sentinel`) and makes no claim that
the evidence is sufficient, current, or accepted.

## 4. Proof (run in this environment)

- `python -m pytest tests/test_prism_opportunity_entry_flow.py -q -rEf`
  → **72 passed** (was 69; +3 this pass).
- `python -m pytest -q $(python scripts/console_contract_domain.py)` — the derived
  CI domain the gate executes (21 files) → **425 passed**.
- `python -m pytest tests/test_prism_opportunity_radar_module.py tests/test_prism_console_ci_wiring.py tests/test_buyer_recon_router_board_scope.py -q -rEf`
  → **62 passed** (adjacent Lane 2 guards unchanged).
- `python -m pytest tests/architecture -q` → **11 passed**.
- Frontend: `corepack pnpm install --frozen-lockfile && corepack pnpm build`
  (`tsc --noEmit && vite build`) → `✓ built` (the build is load-bearing here:
  `noUnusedLocals` rejects an unimported/unused symbol).
- Full suite ONCE: `python -m pytest tests/ -q -rEf --continue-on-collection-errors`
  → **8 failed, 2984 passed, 20 skipped, 1 error** (222 s).

### Failing/error node set (baseline debt — none attributable)

```
ERROR  tests/test_autonomy.py                                                      (CE-01 module-vs-package collision, sovereign-reserved)
FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
FAILED tests/test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated
FAILED tests/test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set
FAILED tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
FAILED tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
```

**Attribution:** every failing/error node is a governance/authority/Lab pin. None
of the source files these nodes exercise (`api/lab_routes.py`, the Lab router,
`weaver/autonomy*`, identity spine, solspire governance) is touched by this
branch — `git diff --name-only origin/main HEAD` intersects the failing-test set
in **0** files. This branch touches only two frontend files + one test + evidence,
so none of these nodes can be branch-caused. Baseline, not attributed.

## 5. Remaining uncertainty / not claimed

- No production deployment, no merge, no acceptance — human authority.
- The `evidence_status` / `evidence` capture path stays **not wired**; adding it
  requires a verified owner- and board-scoped handler. Not claimed.
- MEASURED DEFECT 3 (backend `update_entry` does not normalize status) remains
  pinned, not repaired.
- `web/arkadia_console/dist/` is untracked; nothing was staged from it.
