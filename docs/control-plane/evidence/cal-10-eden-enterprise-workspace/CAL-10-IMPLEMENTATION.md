# CAL-10 — Eden Enterprise Workspace + Master Dashboard

**Status:** IMPLEMENTED ON BRANCH · VERIFICATION IN PROGRESS · HUMAN MERGE GATE  
**Branch:** `cal-10-eden-enterprise-workspace`

## 10.1 Repository substrate audit

| Eden requirement | Existing substrate | Decision |
|---|---|---|
| Canonical authenticated subject | `api.auth.require_auth` / `require_sovereign` | Reuse |
| Canonical SolSpire workspace | `solspire/workspace_manager.py` | Reuse |
| Canonical workload | `solspire/workload_manager.py` | Reuse; existing Barnabas workload is the continuity seed |
| WorkEvent continuity | `solspire/workevent_manager.py` / router | Reuse; no semantic change |
| Daily Pulse | `solspire/pulse_manager.py` / router | Reuse |
| Weekly Synthesis | `solspire/synthesis_manager.py` / router | Reuse |
| Project/workspace UI grammar | `SolSpireExperience`, ProjectDashboard, object sheets | Reuse |
| Enterprise tenant + eight workstreams | No bounded multi-desk enterprise object found | Genuine gap; add bounded enterprise tables |
| Week-1 task/workstream seed | No Eden enterprise seed object found | Genuine gap; add bounded enterprise task seed |
| Master dashboard projection | Existing overview/project dashboards are not Eden's cross-workstream control projection | Genuine gap; add projection endpoint |
| Premium enterprise product role | Existing sovereign access is authorization above Firebase; exclusive Architect entitlement is not established by repository evidence | Product metadata only; never authorization |
| UNKNOWN epistemic state | Existing control-plane design and bounded object statuses | Preserve |

## 10.2 Eden domain mapping

```
CANONICAL HUMAN SUBJECT
        ↓
SOLSPIRE WORKSPACE
        ↓
EDEN ENTERPRISE TENANT
        ↓
8 WORKSTREAMS / DESKS
        ↓
WEEK-1 TASKS
        ↓
EXISTING WORKLOAD / WORKEVENT / PULSE / SYNTHESIS
        ↓
MASTER DASHBOARD PROJECTION
```

The dashboard is a projection. It is not a second source of truth.

## 10.3 Enterprise workspace contract

The implementation introduces `enterprise_workspaces`, `enterprise_workstreams`, and `enterprise_tasks` inside the existing SolSpire SQLite persistence boundary.

The Eden enterprise record carries:

- tenant identity;
- existing SolSpire workspace reference;
- product tier = `ENTERPRISE`;
- product role = `SOVEREIGN_ACCESS_PRODUCT_ROLE`;
- explicit boundary: `DESCRIPTIVE_ONLY__DOES_NOT_AUTHORIZE_MUTATION`;
- pilot budget = ₦1,000,000.

No new authentication universe, sovereign identity namespace, provenance authority, execution boundary, or K15/K3 path is introduced.

## 10.4 Master dashboard projection contract

The dashboard endpoint exposes:

- commercial confirmation;
- money;
- eight operating desks;
- Week-1 task seed;
- transaction state;
- critical path;
- evidence references/state;
- truthfulness boundary.

Every unavailable commercial, financial, or transaction fact is emitted as `UNKNOWN` rather than inferred.

Known seed values are explicitly sourced. The ₦1,000,000 opening capital is a pilot control input, not evidence that funds have been deposited or spent.

## 10.5 Week-1 task/workstream seed

Eight desks are seeded with the approved pilot budget:

- Procurement & Commodity Operations — ₦500,000
- Logistics & Distribution — ₦120,000
- Packaging, Quality & Handling — ₦45,000
- Marketing & Customer Acquisition — ₦75,000
- Brand, Content & Customer Experience — ₦35,000
- Digital Operations & Communications — ₦25,000
- Operations Management & Finance — ₦130,000
- Contingency / Reserve — ₦70,000

Seventeen Week-1 tasks are seeded from Monday through Sunday. All begin `NOT_STARTED`.

## 10.6 UI implementation

A new `Eden Enterprise` lens is exposed inside the existing SolSpire field. It uses the existing navigation/context grammar and the existing authenticated `apiFetch` boundary.

The surface provides:

- enterprise header;
- budget cards;
- commercial confirmation;
- eight operating desks;
- Week-1 operating seed;
- transaction state;
- truthfulness boundary.

No separate enterprise application shell is created.

## 10.7 Runtime verification

Required checks:

1. Backend import and route registration.
2. Eden bootstrap idempotence.
3. Eight workstreams and 17 Week-1 tasks.
4. Dashboard preserves `UNKNOWN` for unrecorded facts.
5. Enterprise role metadata cannot authorize mutation.
6. Frontend builds cleanly.
7. Authenticated sovereign-access gate rejects unauthenticated/non-sovereign access.
8. Existing SolSpire routes remain mounted.

A successful build or endpoint response does not establish production deployment.

## 10.8 Human review / merge gate

Merge remains a human decision.

The implementation must not be described as production-live merely because the PR exists or CI passes.

### Invariants

- Human sovereignty remains upstream.
- Identity ≠ authority event.
- Product entitlement ≠ authorization.
- Dashboard ≠ mutation authority.
- Projection ≠ provenance.
- `UNKNOWN` ≠ zero.
- Existing WorkEvent semantics remain unchanged.
- K15 remains the protected preflight boundary.
- K3 remains the mutation boundary.
