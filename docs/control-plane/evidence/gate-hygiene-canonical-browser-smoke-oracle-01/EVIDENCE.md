# Canonical browser smoke — the oracle scored the wrong thing

Workstream: `gate-hygiene/canonical-browser-smoke-oracle-01`
Contract: ARK-OPS-CONTINUOUS-001 (revision 2026-11-22), cycle 16
Authority: implementation + evidence only. No merge, no deployment, no acceptance.

## 1. Reconstructed state at the start of the cycle

| Fact | Value | How measured |
| --- | --- | --- |
| `main` | `fd0a4fdc081064b2074aab9e17b4c7841736dd9f` | `git rev-parse HEAD` == `origin/main` |
| Open PRs | 49 (48 draft, 1 non-draft: #724) | `gh pr list --state open` |
| Full suite | 22 failed / 4251 passed / 22 skipped / 1 error (23 nodes) | `pytest tests/ -q -rEf --continue-on-collection-errors` |
| CP10 boundary | PASS | `scripts/cp10_mutation_boundary_policy.py --judge` |
| Production | `source_revision = fd0a4fdc…`, `/health` → `{"status":"radiant"}` | `GET /api/version`, `GET /health` |

Every red check across the 49 open PRs was inspected, not assumed. The recurring
`native-arkadia-golden-workflow` failure is the live external provider, measured in
run `45471798694`:

```
lab.engineering_lab.gateway.ModelUnavailable: N-ATLaS Gradio runtime error:
provider emitted error event with null/empty data (event_id=9429c2bd…, events=['error'])
FAILED tests/test_natlas_developer_lab.py::test_native_natlas_route_live_external_gradio
```

It is evidence about the provider, never about the tree. Nothing in the queue is
attributable to a branch this cycle.

## 2. The defect

`canonical-render-browser-smoke.yml` is the only UI/runtime observation surface in the
repository, and it has been `failure` on every push to `main` since 2026-11-05. The
cause is a test-side oracle defect, measured from the run's own artifact
(`gh run download 44663630718 -n canonical-render-browser-smoke`):

| route | status | body chars | console errors |
| --- | --- | --- | --- |
| `/` | 200 | 2366 | 2 × `status of 401` |
| `/solariun` | 200 | 577 | 2 × `status of 401` |
| `/oracle` | 200 | 1165 | 2 × `status of 401` |
| `/solariun/engineering-lab` | 200 | 577 | 2 × `status of 401` |
| `/operator` | 200 | 4211 | 2 × `status of 401` |
| `/n-atlas-lab` | 200 | 443 | 2 × `status of 401` |
| `/n-atlas-tester` | 200 | 443 | 2 × `status of 401` |

Every route rendered; the only console errors are the console's anonymous session
probe being refused with `401`. The gate failed the run for that, i.e. it asserted
"no unauthenticated surface may be refused a protected read" — which is the opposite
of the product's intended behaviour. A permanently red observation surface also trains
reviewers to ignore the check, so it cannot report a real regression.

Three further defects in the same step were measured while confirming the first:

1. **The artifact named the wrong revision.** `source_revision: process.env.GITHUB_SHA`
   labelled the observation with the *repository* SHA. On `workflow_dispatch` the
   readiness step does not require revision equality (`require_revision=0`), so the
   label could name a revision the deployment never ran. Run `44663630718` labelled
   the artifact `5f40e65c…` without ever reading the deployed revision into it.
2. **Readiness accepted a bare `200`.** The Render hibernation wake page is also a
   `200` HTML body and carries no revision. A run that started during a cold start
   could smoke the loader on every route, find no console errors, and report `PASS`
   without observing the application. Observed this cycle on the same origin:
   `x-render-routing: hibernate-pending-wake` then `200`.
3. **A fallback was indistinguishable from a resolved surface.** `resolvePath()`
   returns `{surface: "home", path: "/"}` for any path it does not know, so a drifted
   or invented route answers `200` with a full page. Measured in the browser at
   `fd0a4fdc`: `/definitely-not-a-route` → final URL `/`. The step recorded
   `final_url` but never compared it.

## 3. The repair

One file, four changes; no product code touched.

- Console errors are **classified, not silenced**: the anonymous `401` resource class
  is counted per route (`anonymous_401_count`); any other console error, any uncaught
  `pageerror`, any navigation error, any status ≥ 400 and any empty render still fail.
- Every row declares `resolvesTo`, and `fell_back` is **scored**. Legacy alias rows
  (`/oracle` → `/arkana`, `/n-atlas-tester` → `/n-atlas-lab`) keep their coverage while
  the expectation is the path the router actually normalises to.
- The report records `repository_sha` and `deployed_revision` separately, and fails on
  a mismatch when a revision is required. The readiness step exports the revision it
  observed instead of the artifact assuming the repository's.
- Readiness requires a readable 40-hex `source_revision`, so a wake page cannot be
  scored as a deployment.

The route table grew from 7 to 9 rows: `/arkana` and `/enterprise` are now driven
directly (previously reachable only through the `/oracle` alias, and not at all).

## 4. Guard

`tests/test_aeas05_canonical_frontend_acceptance.py` (executed by the
`prism-console-contract` gate, in its derived domain) gains 5 nodes, 11 → 16:

- `test_smoke_routes_are_bound_to_declared_surfaces` — every row must be a path
  `surfaces.ts` declares (or a lens of one), and an alias row must name the surface
  the router's `PATH_ALIASES` actually maps it to. Parsed from source, so the check
  cannot drift from the tables it judges.
- `test_smoke_route_detector_flags_the_pre_repair_shapes` — synthetic control: an
  undeclared path and a mis-targeted alias must both be reported.
- `test_smoke_scores_the_fallback_and_names_the_deployed_revision`,
  `test_smoke_readiness_requires_a_readable_deployment_revision` — the two evidence
  defects are pinned by their definitions, not by a mention.

`.github/workflows/prism-console-contract.yml` now selects the smoke workflow in both
filters, so an edit to the workflow re-runs the judge that judges it.

**Live negative control** against the real workflow file (not a fixture): rename
`/operator` to `/operator-console` →

```
FAILED tests/test_aeas05_canonical_frontend_acceptance.py::test_smoke_routes_are_bound_to_declared_surfaces
1 failed, 15 passed
```

Restored byte-identically → `16 passed`.

## 5. Verification

| Check | Result |
| --- | --- |
| `pytest tests/test_aeas05_canonical_frontend_acceptance.py` | 16 passed (was 11) |
| Workflow-scanning meta-guards (7 files, incl. trigger coverage, injection boundary, console wiring, verdict-step integrity) | 282 passed |
| Console contract domain (`scripts/console_contract_domain.py`) | 1276 passed, 12 failed — the same 12 nodes as `main` (10 `test_mission_lifecycle_adapter_contract.py` env-only, 2 `test_prism_w4_lab_pr_state.py` owned by #690) |
| `tests/architecture` | 11 passed |
| CP10 judge on the changed paths | PASS |
| Embedded JS | `node --check` OK |
| Workflow YAML | parses |

**Runtime verification (dispatched, not asserted).** `gh workflow run
canonical-render-browser-smoke.yml --ref gate-hygiene/canonical-browser-smoke-oracle-01`
→ run `45540290057`, `completed/success`, head `0ac47a74`. Readiness:
`Canonical Render is ready (HTTP 200, source revision fd0a4fdc081064b2074aab9e17b4c7841736dd9f; attempt 1)`.
Artifact:

```
result: PASS | repository_sha: 0ac47a74 | deployed_revision: fd0a4fdc | require_revision: 0
  /                          st=200 final=/                          fallback=False chars=2366 anon401=2 unexpected=0 pageerr=0 ok=True
  /arkana                    st=200 final=/arkana                    fallback=False chars=1165 anon401=2 unexpected=0 pageerr=0 ok=True
  /oracle                    st=200 final=/arkana                    fallback=False chars=1165 anon401=2 unexpected=0 pageerr=0 ok=True
  /solariun                  st=200 final=/solariun                  fallback=False chars= 577 anon401=2 unexpected=0 pageerr=0 ok=True
  /solariun/engineering-lab  st=200 final=/solariun/engineering-lab  fallback=False chars= 577 anon401=2 unexpected=0 pageerr=0 ok=True
  /operator                  st=200 final=/operator                  fallback=False chars=4211 anon401=2 unexpected=0 pageerr=0 ok=True
  /n-atlas-lab               st=200 final=/n-atlas-lab               fallback=False chars= 443 anon401=2 unexpected=0 pageerr=0 ok=True
  /n-atlas-tester            st=200 final=/n-atlas-lab               fallback=False chars= 443 anon401=2 unexpected=0 pageerr=0 ok=True
  /enterprise                st=200 final=/enterprise                fallback=False chars= 577 anon401=2 unexpected=0 pageerr=0 ok=True
```

This is the discriminating measurement: `repository_sha` (branch) and
`deployed_revision` (production) differ, and the artifact now states both. The
pre-repair code would have labelled this observation `0ac47a74` — a revision that was
never deployed. `/oracle` and `/n-atlas-tester` report `fallback=False` only because
their rows expect the router's real targets; with the requested path as the
expectation they would read `True`, which is the discrimination the fallback check
exists to make.

## 6. What this does not claim

- No merge, no deployment, no production acceptance. `main` and the deployed revision
  are unchanged (`fd0a4fdc`), and this change is not on `main`.
- The dispatched run observed the **production** deployment (`fd0a4fdc`) from the
  branch's workflow file. That is a verification of the *oracle*, not of the branch's
  source being deployed.
- A green `browser` job after merge means "the canonical origin served every declared
  route to an unauthenticated browser at the revision it reported". It does not mean
  the authenticated surfaces work, and it is not a parity or acceptance claim.
- The 401 refusals are recorded per route, not explained: this workstream did not
  identify which endpoints refuse the anonymous probe (candidates include
  `endpoints.me = /api/me`). A later change can pin the set and assert on it.
