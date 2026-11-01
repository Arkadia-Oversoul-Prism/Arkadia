# OpenAPI security-metadata inventory — ARKANA A2 SSE stream (gate-hygiene)

Measured 2026-11-01 at `main` `d14c2598b5b5e9016703b6a834fd44b8def1e5a1`.

Authority for this pass: inspection/measurement only (SHARED-CONTRACTS.md). No merge, no
deployment, no acceptance. The change below is test-side, on a file no lane owns.

## 1. Defect

`tests/test_openapi_security_production_contract.py` pins the composed operation inventory at
**332**, with a comment recording the 331 -> 332 bump as a deliberate, reviewable act
(AEAS-01 P0.3, issue #590 — the Engineering Lab's read-only repository observation
`GET /api/lab/engineering/repository`).

The live composition root now serves **333** operations. The extra operation is the ARKANA A2
SSE resonance stream, `POST /api/commune/resonance/stream` — additive, it does **not** replace
`POST /api/commune/resonance`. Its boundary was adjudicated in the prior pass and is correct:

| property | value |
|---|---|
| `x-arkadia-auth-boundary.classification` | `optional_firebase_bearer` |
| runtime guard | `inline_get_current_user` |
| `security` | `[{"FirebaseBearer": []}, {}]` |

So the operation is sound and the **pin** is stale. This is the "a count moved and nobody named
what moved it" class: the assertion fails on a correct tree, which is the direction that trains
operators to bump a number without looking.

## 2. Repair

One file, `tests/test_openapi_security_production_contract.py`, +9 / -1. The count moves
332 -> 333 **and** the operation is named, mirroring the convention the file already
established for the 331 -> 332 bump:

```python
stream_op = schema["paths"].get("/api/commune/resonance/stream", {}).get("post", {})
assert stream_op, "the A2 SSE resonance stream is no longer served"
assert stream_op.get("x-arkadia-auth-boundary", {}).get("classification") == "optional_firebase_bearer"
assert stream_op.get("security") == [{"FirebaseBearer": []}, {}]
assert len(operations) == 333, f"Expected captured 333-operation inventory; got {len(operations)}"
```

The number can therefore only move when the operation it accounts for is present *and*
adjudicated. A bare count bump would have been the defect this repair is meant to avoid.

## 3. Proof

- Repaired test: `1 passed`.
- Related security tests (`+ test_forge_openapi_security_boundary.py`): `2 passed`.
- `python -m py_compile api/main.py` -> OK; `api/main.py` = 2586 lines (budget 2600).
- `python -m pytest tests/architecture -q` -> **11 passed**.
- No other `332` pin exists: `grep -rn "\b332\b" tests/ --include=*.py` -> none.

### Negative controls (live, on the real file)

Both were run by mutating the real test file, then the file was restored byte-identically
(`git diff --stat` afterwards = the single intended change).

| control | mutation | result |
|---|---|---|
| A — naming bites | point `stream_op` at `/api/commune/resonance/nonexistent` | **1 failed** |
| B — classification bites | expect `firebase_bearer` instead of `optional_firebase_bearer` | **1 failed** |

A control that reddens on both proves the named assertions are load-bearing, not decoration
alongside the count.

## 4. Findings recorded, not repaired

Two further observations from this pass. Both are outside this repair's scope and are recorded
here rather than acted on.

### 4.1 The gate is red in CI on `main`, and `main` cannot re-run it

`.github/workflows/openapi-security-metadata.yml` is **path-filtered**. Its `push` filter names
`api/**`, `solspire/**`, the two security test files and itself — but **not** `web/**`. Every
run on record is `failure`, the newest at 2026-10-30T08:34:10Z (`93385990`).

At `d14c2598` the newest commit is `fix(arkana): repair A2.2 console break … (#604)`, which
touches exactly one file, `web/arkadia_console/src/pages/ArkanaPage.tsx`. No gate trigger path
moved, so no run fires and the red gate leaves no observation at the current revision. This is
the "a path-filtered gate has no execution at a revision that does not touch its paths" class
already recorded for the route-composition gate; the workflow carries no `workflow_dispatch`,
so the contract cannot be re-run against an exact revision on demand.

The repair above touches `tests/test_openapi_security_*.py`, which **is** a trigger path — so
this change does cause the gate to execute, which is how the repair gets runtime proof.

### 4.2 The recorded baseline fixture and live debt have both moved

`tests/fixtures/baseline_node_set.txt` holds **10** nodes; the live full suite reports **10**
nodes — but they are not the same ten.

```
NEW (live, not fixture):
  + tests/test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set
  + tests/test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated
  + tests/test_openapi_security_production_contract.py::test_all_composed_operations_have_adjudicated_security_boundaries

RESOLVED (fixture, not live):
  - tests/test_steward_filter.py::test_allows_mythic_with_action
  - tests/test_steward_filter.py::test_blocks_identity_claims
  - tests/test_steward_filter.py::test_compress_to_choices
```

Equal counts, three-node substitution. A count-based baseline comparison would have called this
"unchanged" and missed all six movements — which is exactly why the standing rule is to compare
the sorted FAILED/ERROR **node set**, never the counts. `tests/test_steward_filter.py` is now
`12 passed` in isolation.

The two `test_engineering_lab_api.py` nodes are **pre-existing on `main`** and unowned drift:

- `test_lab_router_is_read_only_and_authenticated` — asserts `"require_auth" in dependency_names`;
  the router now exposes `{'require_lab_auth'}` (`f96d5fd2`).
- `test_lab_mutation_endpoints_are_exactly_the_lab_state_set` — two extra mutating endpoints,
  `/api/lab/engineering/n-atlas/test-session` and `/api/lab/engineering/n-atlas/run` (`72432353`).

`api/lab_routes.py` is an authority surface carrying the Lab mutation boundary, so repairing
those pins is an authority-boundary change: **sovereign-only**. Proposed, not executed.

### 4.3 Lane snapshot currency

`docs/control-plane/parallel-ui/lane-state.json` (`observed_at` 2026-10-31T23:25:40Z,
`base_main` `6776ee10`) lists `unassigned_open_prs: [603]`. PR #603 is **closed and merged**
(2026-11-01T04:09:19Z, head `b67681a5`) — a merged PR cannot be "unassigned open". The snapshot
also shows all four lanes at `open_prs: []`, while the live inventory holds draft PR **#605**
(`feat/prism-w4-model-gateway-dispatchability`, created 2026-11-01T09:16:02Z, base `d14c2598`,
head `560805e9`), which is lane 4: it touches
`web/arkadia_console/src/components/lab/LabModelGateway.tsx` and `.../lab/labGateway.ts`, both
inside lane 4's exclusive ownership. #605 was opened *after* the snapshot was observed.

`scripts/lane_state.py --check` exits **0** here, and that is **correct by its own criterion**:
freshness is scoped to the guarded lane docs, and `git log 6776ee10..d14c2598 --
docs/control-plane/parallel-ui/` contains only the two lane-currency commits (#602, #603) that
wrote them. The snapshot is stale against *live PR state*, not against its guarded docs — the
residue `_freshness_findings` explicitly delegates to `_pr_state_findings`. Recorded; the
snapshot refresh is a lane-currency workstream action, not part of this repair.

## 5. Boundaries preserved

No production code changed. No authority, identity, K15/K3 governance, approval enforcement,
constitutional architecture or deployment configuration touched. No merge, no deployment, no
acceptance claimed. `api/main.py` untouched.
