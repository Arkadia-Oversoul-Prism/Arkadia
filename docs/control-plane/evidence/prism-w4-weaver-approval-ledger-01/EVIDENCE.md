# Lane 4 — Weaver approval ledger (read-only) — EVIDENCE

- **Workstream:** Prism UI reconciliation, Lane 4 (Arkana + Weaver + Engineering Lab)
- **Branch:** `gate10/prism-lane4-weaver-approval-ledger-01`
- **Base:** `main` @ `49809f45274f2f81b24e01fefdfb3009e8717495` (merge of #490)
- **Mode:** inspection / composition / test only — no merge, no deployment, no acceptance
- **Canonical production:** `https://arkadia-qzu4.onrender.com` (ADR-016)

## Objective

Advance Lane 4 with one bounded, user-visible, tested slice: replace the Weaver page's
inline, type-blind approvals list with a truthful **read-only approval ledger** that renders
the distinction the substrate enforces — an approval is an authorization, not the execution
it authorizes.

## Defect (evidence-backed, source-level)

`web/arkadia_console/src/pages/WeaverPage.tsx` rendered `GET /api/approvals`
(`api/approval_routes.py::api_list_approvals`) as `{id} · {status}` and nothing else. Measured
against the handler, the served record carries and the handler enforces:

- `status` vocabulary `pending | approved | rejected` (written by `queue_approval`,
  `api_approve`, `api_reject`);
- `subject_ref` / `decided_by` — and `api_approve` **refuses self-approval** with `403`
  ("a principal may not approve its own request");
- `consumed_at` — set only when the approval is actually spent at the tool-run boundary;
  a decision **does not** imply execution (the handler docstring: "Does NOT execute the tool").

The inline view erased all three: a decision and an execution were the same string, a
backend-refused self-decision would have rendered as ordinary state, and the record's own
subjects were dropped.

## Change (files)

| File | Change |
|---|---|
| `web/arkadia_console/src/components/weaver/approvalLedger.ts` | **new** — pure projection: record → ordered ledger with a phase ceiling (`REQUESTED → DECIDED → CONSUMED`), status vocabulary pinned to the handler, boundary-violation detection. No network, no React, node-executable. |
| `web/arkadia_console/src/components/weaver/ApprovalLedger.tsx` | **new** — feature-local surface; renders the projection via `endpoints.approvals` + `useHydration`. Read-only (GET only). |
| `web/arkadia_console/src/pages/WeaverPage.tsx` | inline approvals panel replaced by `<ApprovalLedger />`; `LabSessionList` and the `NotYetWired` execute-boundary note retained. |
| `tests/test_prism_w4_weaver_approval_ledger.py` | **new** — 13 guards (see below). |
| `docs/control-plane/evidence/prism-w4-weaver-approval-ledger-01/EVIDENCE.md` | this record. |

## Load-bearing property, and its negative control

The projection derives the phase from the **facts** (`consumed_at`), never from the `status`
string, so `approved` can never read as `CONSUMED`.

- `test_a_decision_is_not_an_execution` — an `approved` record with `consumed_at: null` reads
  `DECIDED`, `consumed: false`.
- `test_negative_control_approved_without_consumption_is_not_consumed` — two records compared
  in one payload (one with a real `consumed_at`, one without); only the first may read
  `CONSUMED`. The control fails if consumption is ever inferred from `approved`.
- `test_self_decision_is_a_boundary_violation` — `subject_ref == decided_by` is flagged, and
  appears in `ledger.violations`.
- `test_contradictory_record_is_flagged_not_advanced` — `consumed_at` present while `pending`
  is flagged, not shown as an ordinary request.
- `test_unknown_status_is_reported_not_coerced` — a status outside the handler vocabulary
  reads `UNKNOWN`, not a coerced known phase.
- Shape pins: the handler's `approvals` key, its status vocabulary, and the record fields the
  projection reads are read from `api/approval_routes.py`, so a rename reddens the guard.

## Verification (measured this pass)

| Command | Result |
|---|---|
| `python -m pytest tests/test_prism_w4_weaver_approval_ledger.py -q -rEf` | **13 passed** |
| `python -m pytest tests/test_prism_w4_lab_read_model.py tests/test_console_shell_nav_contract.py tests/test_console_endpoint_registry_contract.py tests/test_prism_console_ci_wiring.py tests/test_m02a_ci_gate_integrity.py -q` | **176 passed** |
| `python -m pytest tests/architecture -q` | **11 passed** |
| `python scripts/console_contract_domain.py \| wc -l` | **22** (domain grew 21 → 22; the new guard is in the derived domain) |
| `corepack pnpm build` (`tsc --noEmit && vite build`) | **built** (83 modules; `index-C95PYtEO.js`) |

## Boundaries respected

- **No shared-file edits.** `App.tsx`, `router.ts`, `surfaces.ts`, `endpoints.ts`, `types.ts`,
  `SurfaceLenses.tsx` are untouched — `endpoints.approvals` already exists, so no Lane-1
  interface request is needed. This keeps the change clear of the Lane-4 composition hazard
  (two open PRs editing `EngineeringLabPage.tsx`), which this slice does not touch.
- **Read-only.** No mutating route is referenced or issued; the approve/reject/request acts
  stay unwired.
- **No merge, no deployment, no acceptance.** Draft PR only; production is not claimed.

## Remaining uncertainty

- `test_surface_reads_only_a_served_contract` asserts the Weaver page's advertised `contract=`
  path is served by `api/main.py`; it is a source-level (non-runtime) assertion, consistent
  with the repository's console-guard convention.
- Production parity remains **NOT CLAIMED** (per ADR-016 and the deployment boundary).
