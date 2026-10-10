# Route-Composition Acceptance — 01

**Observer:** OpenHands agent (weaver role), on behalf of the human sovereign.
**Observation window:** 2026-10-10T18:17Z – 18:32Z.
**Verdict:** **ACCEPTED (repository + runtime observation)**. One boundary stays
`BLOCKED` and one trust property stays `NOT TESTED`; neither is claimed as verified.

## 1. Exact revision under examination

| Quantity | Value |
| --- | --- |
| canonical source revision (`main`) | `3b74c19d4000b25dfecb9bfc3ef50684d9fa54ec` |
| local `main` == `origin/main` | yes (measured) |
| runtime under examination | canonical Render origin `https://arkadia-qzu4.onrender.com` |
| runtime `source_revision` (`/api/version`) | `3b74c19d4000b25dfecb9bfc3ef50684d9fa54ec` |

`/api/version` reports `revision_source = RENDER_GIT_COMMIT` and
`revision_conflict = false`. The canonical deployment is at the exact current revision.

## 2. What "the route-composition tests" are, and their execution state

- Contract: `tests/test_solspire_route_composition.py` — asserts the EDEN-OPS-02 routes
  are present in the composed OpenAPI schema. Blob `86e71b1e…`.
- Router under test: `solspire/console_router.py`. Blob `3a1bc916…`.

**Finding (defect, closed by this PR).** The contract is executed only by
`.github/workflows/solspire-route-composition.yml`, which is path-filtered to
`solspire/**` and carried **no** `workflow_dispatch`. Measured at `main` `3b74c19d`:

- runs of that workflow on `main`: **1** — run `38066134354` at `73fbb51a`
  (the PR #404 merge), not at the current revision.
- revisions between `73fbb51a` and `3b74c19d`: `d9da03f4` (`api/main.py`, a test),
  `8e160603`/`4d75fa16` (merges), `3b74c19d` (one new workflow file) — none touches
  `solspire/**`, so none triggered the gate and none has a route-composition execution.
- `grep -rn test_solspire_route_composition .github/` → only that one workflow.

The gate could not be executed against an exact revision on demand. This is the
repository's named defect class — *a guard that only runs on one path filter* — and is
repaired here (Section 6).

## 3. Execution against the exact revision (obtained via GitHub)

Because the dedicated gate was not dispatchable, the contract was executed in CI at
`3b74c19d` through a workflow that **does** run it:

| Run | Workflow | Head SHA | Event | Result |
| --- | --- | --- | --- | --- |
| `38075478690` | Provider Routing Verification (`provider-routing.yml`) | `3b74c19d…` | `workflow_dispatch` | completed / **failure** (pre-existing debt) |
| `38075479966` | Canonical Render Runtime Probe | `3b74c19d…` | `workflow_dispatch` | completed / **success** |

The Provider Routing broad-suite step runs
`python -m pytest tests/ -q -rEf --continue-on-collection-errors`, which includes the
composition contract. In that run: **22 failed, 2047 passed, 21 skipped, 1 error**
(2m35s), and `tests/test_solspire_route_composition.py` is **absent from the
FAILED/ERROR node list** → the contract **executed and passed in CI at the exact
revision**. The 23-node failing/error set is pre-existing debt, not this contract.

Local corroboration at the same revision: `python -m pytest
tests/test_solspire_route_composition.py -q` → **1 passed**.

Source-equivalence note (necessary, not sufficient): the three gate inputs
(`solspire/console_router.py` `3a1bc916`, `tests/test_solspire_route_composition.py`
`86e71b1e`, `scripts/production_runtime_probe.py` `271f67a1`) are **byte-identical**
between `73fbb51a` and `3b74c19d`, so the earlier execution and this one exercise the
same blobs — but the execution recorded here is the one at `3b74c19d` itself.

## 4. The route inventory (drives Sections 4–5)

Source: artifact `canonical-render-runtime-probe` (id `11678234179`) from run
`38075479966`, produced by `scripts/production_runtime_probe.py` in read-only mode
(`mode: read_only_get_probes; no mutation verbs invoked`).
Artifact `production-route-inventory.json` sha256
`5c43c59198314d508e2afe8821af1a2348ec11610f062a5359ff3c427b590e37`.

| Quantity | Measured |
| --- | --- |
| OpenAPI title / version | `Arkadia Mind — Cycle 11` / `0.1.0` |
| deployed OpenAPI paths | **288** |
| deployed OpenAPI operations | **331** |
| static source route declarations | 331 |
| exact source↔runtime method+path matches | **331 / 331** |
| runtime ops without a source match | **0** |
| source decls without a runtime match | **0** |

The deployed surface reconciles **exactly** with the source at `3b74c19d`: no route is
served that the source does not declare, and no declared route is missing at runtime.
Composition status: `router_aware_nested_and_dynamic_registration_composition`.

Independent composition cross-check: composing `solspire.console_router` locally at the
revision yields 112 paths / 133 operations, and **all 133 are present** in the deployed
inventory (strict subset — 0 missing).

**EDEN-OPS-02 composed routes in the deployed OpenAPI (the contract's own set):**

| Route | Deployed | Runtime probe |
| --- | --- | --- |
| `POST /solspire/enterprise/workspaces/{enterprise_id}/members` | PRESENT | not probed (non-GET) |
| `DELETE …/members/{handle}/desks/{desk}` | PRESENT | not probed (non-GET) |
| `GET …/{enterprise_id}/tasks` | PRESENT | protected (401/403) |
| `PATCH …/tasks/{task_id}` | PRESENT | not probed (non-GET) |
| `GET …/{enterprise_id}/control-room` | PRESENT | protected (401/403) |

## 5. Security and functional checks driven by the inventory

### 5.1 Authorization boundary (security)

Read-only GET probes were issued for **153** of the 331 operations. Classification:

| Classification | Count | Meaning |
| --- | --- | --- |
| `protected` (401/403) | **98** | reachable but requires authorization |
| `reachable` (2xx) | **40** | served anonymously |
| `route_reachable_request_shape_rejected` (400/405/422) | 9 | registered, request shape rejected by design |
| `resource_not_found_route_present` (404 + "not found") | 6 | registered; sentinel record absent (not route absence) |
| non-GET (not probed) | 178 | OpenAPI proves registration; no mutation verb sent |

Authorization probes against `/api/operator/security-verification`:

| Identity | HTTP | Classification |
| --- | --- | --- |
| anonymous (no header) | 401 | protected |
| malformed bearer | 401 | protected |
| valid low-privilege identity | — | **NOT TESTED** (`ARKADIA_PROBE_LOW_PRIVILEGE_BEARER` unset) |

All 5 EDEN-OPS-02 workspaces sub-resources that are GET-addressable are `protected`;
the mutating members/tasks routes are auth-gated at runtime (OpenAPI-registered, and
the GET siblings return 401).

**Functional (authorization) result:** the boundary **rejects** anonymous and malformed
credentials on operator and SolSpire workspaces routes. Disambiguation of *unauthenticated
(401)* from *unauthorized (403)* for a valid but insufficiently-privileged identity is
**NOT TESTED** — a limitation of the available authorization matrix, recorded, not claimed.

### 5.2 Anonymously reachable surface (security observation)

40 GET routes answer without credentials. They are read-only status/catalog surfaces
(`/health`, `/api/version`, `/api/codex`, `/api/stellar-cartography`, the
`/api/knowledge/*` read views, `/api/keys`, `/api/provider-keys`, `/api/tts/keys`, …).

**Finding — `security_declared: 0`.** The deployed OpenAPI declares **no**
`components.securitySchemes` and **no** operation-level `security`, across all 331
operations, while 98 operations enforce 401/403 at runtime. Two consequences:

1. The OpenAPI document is **not** a reliable authorization oracle — a consumer reading
   it cannot tell a protected route from an open one. This is why Section 5.1 uses
   **live probes**, not the schema, to establish the boundary.
2. The anonymously-reachable list must be read as *observed reachability*, not as a
   declared public contract. In particular `/api/keys`, `/api/provider-keys` and
   `/api/tts/keys` return metadata/previews anonymously; whether that leaks any secret
   material is **not established here** and is proposed as follow-up (Section 8).

### 5.3 Functional route-availability result

Every one of the 331 deployed operations maps to a source declaration (Section 4), and
the contract's 5 composed routes are all present. Functional composition is **PASS** at
`3b74c19d`; the deployed runtime is the same revision.

## 6. Repair included in this acceptance (narrow, wiring only)

`.github/workflows/solspire-route-composition.yml`:

- added `workflow_dispatch` — the composed-route contract is now executable against an
  exact revision on demand;
- added `tests/test_solspire_route_composition_ci_wiring.py` to both `paths` filters;
- added a step running that guard, so a rewrite of the gate is judged by itself.

New guard `tests/test_solspire_route_composition_ci_wiring.py` (7 tests) states, over
every workflow that runs the contract: (1) some workflow runs it; (2) such a workflow is
dispatchable; (3) its `paths` filter names the contract file and `solspire/**`; (4) its
contract step can fail the job. It carries negative controls for each defect form
(missing dispatch, incomplete filter, `continue-on-error`) and a positive control.

**Runtime-proven:** dispatching the gate on the branch head
(`ref=acceptance/route-composition-01`) produced run `38075821913` at `a6f4f260`, job
`router-composition` → **completed / success**, steps 7 (`Verify composed EDEN-OPS-02
routes`) and 8 (`Route-composition CI-wiring guard`) both **success**. Check-runs on
`a6f4f260` include `router-composition` = **success**.

## 7. Regression evidence (no new failure introduced)

Full suite, branch vs `main`, **same environment** (`pytest tests/ -q -rEf
--continue-on-collection-errors`):

| Tree | Result |
| --- | --- |
| `main` `3b74c19d` | 86 failed, 1822 passed, 31 skipped, 19 errors |
| branch `a6f4f260` | 86 failed, 1829 passed, 31 skipped, 19 errors |

- sorted failing/error **node set**: **identical** on both trees
  (`comm -3` empty); digest `be6bd2372e9a651f45f4e0089903a0317ba5140dc9f3349954a91dc283672da0`, 105 nodes.
- `+7 passed` is exactly the 7 new guard tests (`--collect-only` → 7 collected).

The absolute 105-node local debt is an **environment delta** from the 23 nodes CI
reported at the same revision (dependency set), not a regression; the load-bearing
invariant is node-set identity across trees, which holds.

Supporting suites, all green: `tests/architecture` + `test_ci_gate_trigger_coverage.py`
+ `test_ci_suite_collection_continuation.py` + `test_workflow_injection_boundary.py` →
**147 passed**; `tests/test_m02a_ci_gate_integrity.py` → **64 passed**; CP10
`--judge` on the branch diff → **PASS**.

## 8. Boundaries explicitly not claimed

| Boundary | State | Why |
| --- | --- | --- |
| Application behaviour correctness beyond route composition | **NOT CLAIMED** | composition + availability observed; semantics not exercised |
| Unauthorized (valid low-privilege identity) rejection | **NOT TESTED** | no low-privilege bearer configured |
| Secrets not exposed via `/api/keys`, `/api/provider-keys`, `/api/tts/keys` | **UNKNOWN** | anonymous reachability observed; payload sensitivity not adjudicated |
| OpenAPI as authorization oracle | **FAILED as an oracle** | 0 of 331 operations declare security; use live probes |
| Production acceptance / deployment *identity* beyond revision metadata | **NOT CLAIMED** | `/api/version` matching revision is necessary, not sufficient (its own note says so) |
| Pre-existing 23-node CI debt and 105-node local debt | **NOT REPAIRED** | out of scope; recorded, not silently resolved |

## 9. Proposed follow-ups (not executed)

1. Declare a `securitySchemes` entry (and per-operation `security`) so the OpenAPI
   document stops being a misleading authorization oracle.
2. Adjudicate whether the anonymously reachable key endpoints expose secret material.
3. Configure `ARKADIA_PROBE_LOW_PRIVILEGE_BEARER` so 401 (unauthenticated) and 403
   (unauthorized) can be distinguished.

## 10. Reproduction commands

```bash
# exact revision
git rev-parse HEAD                                  # 3b74c19d…
curl -s https://arkadia-qzu4.onrender.com/api/version | python -m json.tool
# run-state of the dedicated gate
gh api repos/Arkadia-Oversoul-Prism/Arkadia/actions/workflows/solspire-route-composition.yml/runs?branch=main
# execute the contract + wiring guard
python -m pytest tests/test_solspire_route_composition.py tests/test_solspire_route_composition_ci_wiring.py -q
# node-set regression (same environment)
python -m pytest tests/ -q -rEf --continue-on-collection-errors
```
