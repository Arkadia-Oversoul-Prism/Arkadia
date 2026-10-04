# gate-hygiene/nodes-configure-routers-idempotency-01 — SH-09

**BASE_MAIN**: `1b7c089f237a1a8ea11791ab060525b0e36e2029` (merge of PR #261, SH-08)
**Branch**: `gate-hygiene/nodes-configure-routers-idempotency-01`
**Workstream**: `gate-hygiene` -> composition-seam test-isolation hardening
**Origin**: the explicitly-deferred follow-on recorded in PR #262 (pass 3), which
characterized the defect but did not execute the fix ("a **separate** bounded
workstream, not executed here").
**Scope**: one production seam function (`api/nodes.py`) + one test file
(`tests/test_nodes_composition_seam.py`). No `api/main.py`, no governance surface,
no authority path, no workflow, no policy module.

## Objective (bounded)

Make `api.nodes.configure_routers()` idempotent so re-entry does not double-include the
injected sub-routers, removing the order-dependent duplicate-OpenAPI-operation-ID
warnings at their root cause rather than masking them in the test.

## Defect (root cause, not the symptom)

`api.nodes.router` is a **module-level `APIRouter` singleton**. `configure_routers()`
calls `router.include_router(...)`, which **mutates** that singleton. The composition
root (`api/main.py:294`) calls it **once**, so production is correct. The seam test
(`tests/test_nodes_composition_seam.py`) calls it a **second** time on the already-wired
singleton, appending the injected sub-routers again. A later `app.openapi()` walk then
expands them twice and FastAPI emits one duplicate-operation-ID warning per injected
operation: **5** (`api/ais_profile.py`) + **24** (`api/lab_routes.py`) = **29**.

Measured growth of the singleton (this environment, python 3.13):

```
nodes.router.routes = 11  (fresh)
                    = 13  (after composition-root wiring: +2 _IncludedRouter markers)
                    = 15  (after the seam test's 2nd configure_routers call)
                    = 17  (3rd call)
```

`app.routes` stays **55** because `_IncludedRouter` is a lazy marker, so **route serving
is unaffected** (`/api/lab/overview` -> 401, mounted once). The defect is confined to
OpenAPI schema generation, which is why it appeared as warnings, not failures.

## Change

`api/nodes.py` — a re-entry guard (module-level `_routers_configured`), so a second call
after a successful wiring is a no-op. The ADR-014 Decision 4 composition pattern is
unchanged: `api/nodes.py` still does not import the layer-1 surface, and the two literal
`router.include_router(...)` lines that `tests/test_ais_w8_canonical_identity.py` asserts
are preserved.

`tests/test_nodes_composition_seam.py` — new regression test
`test_configure_routers_is_idempotent`, asserting the singleton route count is stable
across repeat calls and that exactly **2** injected sub-router markers exist.

## Negative control (the test detects the defect it claims)

`test_configure_routers_is_idempotent` was run against the **unfixed** `api/nodes.py`
(change stashed):

```
FAILED tests/test_nodes_composition_seam.py::test_configure_routers_is_idempotent
1 failed  — assert 17 == 15   (3rd call grew the singleton by 2)
```

On the fixed tree the same test passes. The test cannot be disarmed by reverting the
source without failing.

## Verification (this environment, python 3.13, `PYTHONPATH=<repo>/archive/legacy_python`)

| command | result |
|---|---|
| `python -m py_compile api/main.py api/nodes.py` | OK |
| `api/main.py` line budget | **2582 / 2600** (untouched) |
| `pytest tests/architecture -q` | **11 passed** |
| `pytest tests/test_nodes_composition_seam.py -q` | **4 passed** (was 3) |
| `pytest tests/test_production_health_route.py -q` | **5 passed** |
| `pytest tests/test_ais_w8_canonical_identity.py -q` | **5 passed** (ADR-014 literals intact) |
| duplicate warnings, seam→health order | **29 → 0** |
| duplicate warnings, seam→health→w8 order | **0** |
| full suite `--continue-on-collection-errors` | **9 failed / 1415 passed / 20 skipped / 1 error** |
| CP10 mutation boundary over changed paths | **PASS (RC 0)** |

## Node-set delta (attribution is by node set, never by count)

Failure/error node list is **byte-identical** between base `1b7c089` and this head:

```
sha256(base nodes)  = 33ff748dea76dcd193713a7df9ac03b531cdfd77ff333891f3b94da94fa0fe68
sha256(fixed nodes) = 33ff748dea76dcd193713a7df9ac03b531cdfd77ff333891f3b94da94fa0fe68
diff                = (empty)
```

```
ERROR tests/test_autonomy.py
FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
FAILED tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
FAILED tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
FAILED tests/test_steward_filter.py::test_allows_mythic_with_action
FAILED tests/test_steward_filter.py::test_blocks_identity_claims
FAILED tests/test_steward_filter.py::test_compress_to_choices
```

Delta: **−0 / +0 nodes**; `+2 passed` is exactly the two new assertions. None of the 9
residual failures is a safe test-side repair (each needs a product/architectural
decision — see the classification ledger); none is touched here.

## Regression boundary

- Directly affected: `tests/test_nodes_composition_seam.py` (grows by one test),
  `tests/test_ais_w8_canonical_identity.py` (literal pin, unchanged and passing),
  `tests/test_production_health_route.py` (unchanged and passing).
- Protected surface: `tests/architecture` — **11 passed**.
- Full-suite node set unchanged.

## Remaining uncertainty

- The guard is process-local, as is the singleton it protects. It makes the seam safe to
  invoke more than once **within a process**; it does not create a second router or a new
  composition path.
- The 9 residual baseline failures are unchanged and remain a **separate** workstream;
  this PR does not begin them.

## Authority boundary

- No merge, no push to `main`, no force-push.
- No production boot code (`api/main.py` untouched), no governance/authority path, no
  constitutional surface, no workflow, no policy module.
- No product decision required: the seam contract ("called once by the composition root")
  is made structurally true instead of merely documented.
- Merge is the sovereign's act.
