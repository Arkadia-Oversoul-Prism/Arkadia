# Route-Composition Acceptance — 01

**Observer:** OpenHands agent (weaver role), on behalf of the human sovereign.
**Observation window:** 2026-10-10T18:17Z – 18:42Z.
**Verdict:** **ACCEPTED (repository + runtime observation)**. One boundary stays
`BLOCKED` and one trust property stays `NOT TESTED`; neither is claimed as verified.

> **Deployment drift detected and re-measured.** The examination began at `main`
> `3b74c19d`. While it ran, PR #405 merged, advancing `main` to `c8abb28e`
> (2026-10-10) and moving production with it. Nothing here restates the earlier
> reading: every measurement was **re-derived at `c8abb28e`** (Section 12). The
> `3b74c19d` readings are retained as a superseded first pass.

## 1. Exact revision under examination

| Quantity | First pass | Current (binding) |
| --- | --- | --- |
| canonical source revision (`main`) | `3b74c19d…` | **`c8abb28e4ac0fda5eb6b0117aa0ff979d93e5853`** |
| local `main` == `origin/main` | yes | yes |
| runtime origin | `https://arkadia-qzu4.onrender.com` | same |
| runtime `source_revision` (`/api/version`) | `3b74c19d…` | **`c8abb28e…`** |

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

Because the dedicated gate was not dispatchable, the contract was executed in CI through
a workflow that **does** run it. Both revisions were measured; the binding measurement is
at the current revision `c8abb28e`.

| Run | Workflow | Head SHA | Event | Result |
| --- | --- | --- | --- | --- |
| `38076487397` | Provider Routing Verification (`provider-routing.yml`) | **`c8abb28e…`** | `workflow_dispatch` | completed / **failure** (pre-existing debt) |
| `38076486048` | Canonical Render Runtime Probe | **`c8abb28e…`** | `workflow_dispatch` | completed / **success** |
| `38075478690` | Provider Routing Verification (superseded) | `3b74c19d…` | `workflow_dispatch` | completed / failure |
| `38075479966` | Canonical Render Runtime Probe (superseded) | `3b74c19d…` | `workflow_dispatch` | completed / success |

The Provider Routing broad-suite step runs
`python -m pytest tests/ -q -rEf --continue-on-collection-errors`, which includes the
composition contract. At `c8abb28e`: **22 failed, 2047 passed, 21 skipped, 1 error**
(2m25s), and `tests/test_solspire_route_composition.py` is **absent from the
FAILED/ERROR node list** → the contract **executed and passed in CI at the exact
revision**. The 23-node failing/error set is pre-existing debt, not this contract.
(The `3b74c19d` run reported the same shape: 22 failed, 2047 passed, 21 skipped, 1 error,
contract absent from the failing set.)

Local corroboration at the same revision: `python -m pytest
tests/test_solspire_route_composition.py -q` → **1 passed**.

Source-equivalence note (necessary, not sufficient): the three gate inputs
(`solspire/console_router.py` `3a1bc916`, `tests/test_solspire_route_composition.py`
`86e71b1e`, `scripts/production_runtime_probe.py`) are **byte-identical** between
`73fbb51a` and `3b74c19d` — but the execution recorded here is at the revision
actually dispatched, and the probe script changed in `c8abb28e` (Section 12).

## 4. The route inventory (drives Sections 4–5)

Source: artifact `canonical-render-runtime-probe` (id `11679036146`) from run
`38076486048` at `c8abb28e`, produced by `scripts/production_runtime_probe.py` in
read-only mode (`mode: read_only_get_probes; no mutation verbs invoked`).
Artifact `production-route-inventory.json` sha256
`36937cb55b75672cc4c3bc0ac15e67d04af28549d397840d2726c5a07764b4fb`.
(First pass at `3b74c19d`: artifact id `11678234179`, sha256 `5c43c591…`; the
measured counts below are identical on both.)

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
   material is **not established here** and is proposed as follow-up (Section 10).

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

New guard `tests/test_solspire_route_composition_ci_wiring.py` (14 tests) is stated over
every workflow that **mentions** the contract. Its four conditions are load-bearing:

1. some workflow **executes** it — a step whose command is a pytest invocation whose
   arguments contain the contract file or its containing directory (`pytest tests/ -q`
   counts). A step that only *prints* or *comments* the path is a mention, not an
   execution and does not satisfy this. The command is tokenised (`shlex`, comments
   dropped) so prose cannot masquerade as an invocation.
2. such a workflow is dispatchable (`workflow_dispatch`);
3. its `paths` filter names the contract file **and** `solspire/**`;
4. the executing step can actually fail the run — it is not exempted by step- or
   job-level `continue-on-error`, nor by step- or job-level `if: false`.

Negative controls cover each defect form: mention-without-execution (`echo` of the path),
comment-only mention, a non-pytest command naming the path (`cat`), missing
`workflow_dispatch`, an incomplete `paths` filter, `continue-on-error` at step and at job
level, and `if: false` at step and at job level. Positive controls cover the wired shape
and a directory invocation (`pytest tests/ -q`).

**Live controls on the real workflow** (not synthetic dicts): replacing the executing
step's `run` with `echo tests/test_solspire_route_composition.py` → **2 failed** (the
loose predecessor detector passed this form); adding job-level `continue-on-error: true`
→ **2 failed**. The workflow file was restored byte-identically after each control.

**Runtime-proven:** dispatching the gate on the branch head
(`ref=acceptance/route-composition-01`) produced run `38075821913` at `a6f4f260`, job
`router-composition` → **completed / success**, steps 7 (`Verify composed EDEN-OPS-02
routes`) and 8 (`Route-composition CI-wiring guard`) both **success**. Check-runs on
`a6f4f260` include `router-composition` = **success**.

## 7. Guard-and-record correction (review findings, 2026-10-10)

The record above and the guard shipped in the first pass were reviewed against the live
branch. Three narrow defects were found in the **self-checking guard**, not in the route
inventory or the runtime observations. They are corrected here; the corrected guard is a
separate claim from the runtime observations and should be read as such.

| # | Defect (pre-correction) | Consequence | Correction |
| --- | --- | --- | --- |
| 1 | `_runs_contract` matched the contract path **anywhere** in a step's `run` string | a step that merely `echo`ed or commented the path satisfied the "runs the contract" condition | the detector now tokenises each command and requires an actual **pytest invocation** whose arguments target the contract file or a directory containing it |
| 2 | only step-level `continue-on-error` was inspected | a job-level `continue-on-error: true` left the contract step unable to fail the run, yet the guard passed | the whole execution path is inspected: step and job `continue-on-error`, and step and job `if: false` |
| 3 | the guard was documented but the underlying execution-on-demand guarantee was not proven at the gate | — | the guard is run **inside** the gate (pre-existing) and is proven end-to-end by the CI run on this PR's head (see PR checks) |

Measured before the correction: `_runs_contract("echo tests/test_solspire_route_composition.py")`
→ `True` and `_runs_contract("# run tests/test_solspire_route_composition.py")` →
`True` — both forms passed the pre-correction detector. After the correction, both are
reported as `no effective step executes the contract`, and the live controls in Section 6
confirm the bite on the real workflow file.

Scope: this correction changes only the guard and this record. No change to
`solspire/console_router.py`, the route inventory, the runtime observations, or the
authorization findings. The pre-existing 22-failure / 1-error broad-suite result is
unchanged debt and is not repaired here.

## 8. Regression evidence (no new failure introduced)

Full suite, branch vs `main`, **same environment** (`pytest tests/ -q -rEf
--continue-on-collection-errors`), at the rebased current base:

| Tree | Result |
| --- | --- |
| `main` `c8abb28e` | 86 failed, 1822 passed, 31 skipped, 19 errors |
| branch (guard-and-record correction) | 86 failed, 1836 passed, 31 skipped, 19 errors |
| branch `bbe54278` (first corrected pass, guard = 7 tests) | 86 failed, 1829 passed, 31 skipped, 19 errors |
| `main` `3b74c19d` (first pass) | 86 failed, 1822 passed, 31 skipped, 19 errors |
| branch `a6f4f260` (first pass) | 86 failed, 1829 passed, 31 skipped, 19 errors |

- sorted failing/error **node set**: **identical** on both trees
  (`comm -3` empty); digest `be6bd2372e9a651f45f4e0089903a0317ba5140dc9f3349954a91dc283672da0`, 105 nodes.
- `+14 passed` over `main` is exactly the 14 corrected guard tests
  (`--collect-only` → 14 collected); the earlier pass reported `+7` for the 7-test guard.

The absolute 105-node local debt is an **environment delta** from the 23 nodes CI
reported at the same revision (dependency set), not a regression; the load-bearing
invariant is node-set identity across trees, which holds.

Supporting suites, all green: `tests/architecture` + `test_ci_gate_trigger_coverage.py`
+ `test_ci_suite_collection_continuation.py` + `test_workflow_injection_boundary.py` →
**147 passed**; `tests/test_m02a_ci_gate_integrity.py` → **64 passed**; CP10
`--judge` on the branch diff → **PASS**.

## 9. Boundaries explicitly not claimed

| Boundary | State | Why |
| --- | --- | --- |
| Application behaviour correctness beyond route composition | **NOT CLAIMED** | composition + availability observed; semantics not exercised |
| Unauthorized (valid low-privilege identity) rejection | **NOT TESTED** | no low-privilege bearer configured |
| Secrets not exposed via `/api/keys`, `/api/provider-keys`, `/api/tts/keys` | **UNKNOWN** | anonymous reachability observed; payload sensitivity not adjudicated |
| OpenAPI as authorization oracle | **FAILED as an oracle** | 0 of 331 operations declare security; use live probes |
| Production acceptance / deployment *identity* beyond revision metadata | **NOT CLAIMED** | `/api/version` matching revision is necessary, not sufficient (its own note says so) |
| Pre-existing 23-node CI debt and 105-node local debt | **NOT REPAIRED** | out of scope; recorded, not silently resolved |

## 10. Proposed follow-ups (not executed)

1. Declare a `securitySchemes` entry (and per-operation `security`) so the OpenAPI
   document stops being a misleading authorization oracle.
2. Adjudicate whether the anonymously reachable key endpoints expose secret material.
3. Configure `ARKADIA_PROBE_LOW_PRIVILEGE_BEARER` so 401 (unauthenticated) and 403
   (unauthorized) can be distinguished.

## 11. Reproduction commands

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

## 12. Deployment drift re-measurement (binding)

Between the first and second passes, `main` advanced `3b74c19d` → `c8abb28e`
(PR #405, "Preserve codex response headers on body read timeout"), and production moved
with it: `/api/version` reported `3b74c19d…` during the first pass and `c8abb28e…`
during the second. The drift was **re-measured, not reconciled by argument**.

What PR #405 changed: `scripts/production_runtime_probe.py` only — `request_without_redirects`
(used solely by the focused anomaly sub-probe) now records response headers before reading
the body, so a body-read timeout keeps the HTTP status/Location instead of erasing it.
The OpenAPI route inventory, source-inventory composition, and authorization-matrix code
were **not** changed.

Re-measured at `c8abb28e` (run `38076486048`, artifact id `11679036146`):

| Quantity | `3b74c19d` | `c8abb28e` |
| --- | --- | --- |
| deployed OpenAPI paths / operations | 288 / 331 | **288 / 331** |
| source↔runtime exact matches | 331 / 331 | **331 / 331** |
| runtime-only / source-only | 0 / 0 | **0 / 0** |
| classifications (reachable/protected/shape-rejected/resource-404) | 40 / 98 / 9 / 6 | **40 / 98 / 9 / 6** |
| auth matrix | anon 401, malformed 401, valid-low-priv NOT TESTED | **identical** |
| EDEN-OPS-02 routes present in deployed OpenAPI | 5 / 5 | **5 / 5** |
| contract node in CI failing set | absent (pass) | **absent (pass)** |
| branch-vs-main failing/error node set | identical (105) | **identical (105)** |

Drift classification: **the observed surface did not drift** despite the deployment
moving. The inventory and the security/functional conclusions are therefore re-derived
at the current revision rather than restated from the superseded pass. The artifact
sha256 differs between passes (`5c43c591…` → `36937cb5…`) because the harness's
anomaly-probe payload changed; the route inventory itself is unchanged.
