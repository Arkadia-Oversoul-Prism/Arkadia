# Gate-2 served-artifact app identity

**Date:** 2026-11-22
**Base main:** `034d8879d68ecf8ed4c291eb0ab07432657a06a1`
**Branch:** `gate2/served-artifact-app-identity-01`
**Authority:** none requested — no merge, no deployment, no acceptance.

## 1. Defect (measured)

Running the harness against the canonical origin at base main:

```
ALIAS OBSERVATION
  https://arkadia-qzu4.onrender.com/ -> HTTP 200
  manifest: assets/index-BJojPKi_.css, assets/index-CYGHeCpJ.js

MARKER-SET LINEAGE
  artifact app: UNDETERMINED   scoring against: no declared marker list
  no artifact fetched -> no marker set read (NOT OBSERVED);
  !! STALE marker list -- literals gone from source: [7 Prism literals]
...
  marker-set oracle   NOT OBSERVED (served app undetermined; markers describe 'arkadia-prism')
```

The alias was reachable and served a real bundle, yet nothing scored it. Cause,
read from the source:

```python
deployed_app = frontend_of(prod[0]["environment"]) if prod else None
```

App identity had exactly one source: the project suffix on a GitHub deployment
label. The canonical runtime is Render (`ADR-016`), which publishes no GitHub
deployment record, so `prod == []`, `deployed_app is None`, and every downstream
classifier was forced to the "undetermined" branch — the marker oracle could never
score the artifact it had already fetched.

Consequence in the other direction: `app_for_closure = deployed_app or MARKER_APP`
fell back to `arkadia-prism`, an **archived** application, so the source-lineage
and SG-04 verdicts were scoped to the wrong app and the marker list reported as
stale on every run.

## 2. Repair

App identity now has a second, build-invariant source: the application's declared
`<title>` in its own `index.html`, served verbatim by the SPA shell.

- `MARKER_APPS[app]["html_root"]` names each app's shell.
- `served_identity(app)` reads the `<title>` from that shell (not restated in code).
- `detect_served_app(html)` returns the single app whose declared title is present.
- The assignment prefers a naming deployment record and falls back to detection:

```python
deployed_app = (frontend_of(prod[0]["environment"]) if prod else None) or detect_served_app(html)
```

Soundness properties, each pinned by a test:

| Property | Behaviour | Test |
|---|---|---|
| Fail closed on a non-app page | Render's cold-start holding page (`<title>Render - Application loading</title>`) matches nothing -> `None` | `test_detection_is_undetermined_for_a_non_application_page` |
| Fail closed on ambiguity | two declared titles in one shell -> `None` | `test_detection_refuses_an_ambiguous_shell` |
| Aliases are not ambiguity | `MARKER_APPS["console"] is MARKER_APPS["arkadia-console"]`; without the `id()` dedupe the console would match twice and detection would return `None` | `test_a_shared_marker_list_does_not_make_one_app_ambiguous` |
| A record still wins | `frontend_of(...)` is evaluated first in the assignment | `test_a_deployment_label_still_wins_over_the_served_shell` |
| Identity is per app | the three declared titles are distinct | `test_served_identity_is_the_declared_title_of_each_app` |

Identity is a property of the shell, not of the bundle: it survives minification
and does not depend on the emitted asset hash, which the repository already records
as env-dependent and therefore not a parity oracle.

## 3. Measured result after the repair (same run, same SHA)

```
ALIAS OBSERVATION
  https://arkadia-qzu4.onrender.com/ -> HTTP 200
  manifest: assets/index-BJojPKi_.css, assets/index-CYGHeCpJ.js
  bundle  : assets/index-CYGHeCpJ.js (426232 bytes)

MARKER-SET LINEAGE
  artifact app: arkadia-console   scoring against: arkadia-console
  Protected surface                              1  (expect>0)
  Sign in to continue                            1  (expect>0)
  Go to sign in                                  1  (expect>0)
  Reading canonical contract                     1  (expect>0)
  Human authority remains the decision boundary  3  (expect>0)
  Arkadia is temporarily unreachable             2  (expect>0)
  Enter the enterprise layer.                    0  (expect 0)

SG-04 REGRESSION
  in source: False   NOT EVALUABLE: score against the 'arkadia-console' app,
                     which has no SG-04 surface.

BOUNDARY CLASSIFICATION
  current main resolved                      VERIFIED
  main -> deployment identity                UNKNOWN
  deployment build output observed           UNKNOWN
  alias reachable                            VERIFIED
  alias -> deployment SHA binding            UNKNOWN
  build <-> source lineage                   UNKNOWN
  marker-set oracle                          VERIFIED (marker set observed in served artifact)
  browser-rendered UI correctness            UNKNOWN
  production acceptance                      NOT CLAIMED (human authority)
```

**Scope of the claim.** `marker-set oracle` moves `NOT OBSERVED` -> `VERIFIED`
because the literals were read from the served bundle, including a control literal
that is correctly absent. `main -> deployment identity`, `build <-> source
lineage`, and `browser-rendered UI correctness` remain `UNKNOWN` — Render
publishes no deployment record and this harness reads no browser. Production
acceptance remains `NOT CLAIMED`; the human remains the acceptence boundary.

## 4. A transient state that must not be read as an outage

The first probe of this pass returned **HTTP 503** with
`<title>Render - Application loading</title>` and 258,535 bytes on `/`, `/health`,
`/api/version` and `/api/stellar-cartography`. A second attempt 8 s later returned
`200` with `source_revision = 034d8879...` = main. This is Render's cold-start
holding page, not a service failure, and it is why detection must fail closed
rather than guess an app from any response body.

`/api/version` `source_revision == main` is recorded here as observed
source<->runtime revision consistency. It is **not** production acceptence and does
not by itself prove the application works.

## 5. CI wiring (the gate that was absent)

`grep -rn test_gate2_production_observation .github/` -> **0** at base main. The
suite ran only when a human invoked pytest, so the oracle could regress silently —
the same class already closed for the baseline-fingerprint and boot-sintax guards.

`.github/workflows/gate2-production-observation.yml` executes the fitness tests and
the wiring guard, is `workflow_dispatch`-able, and selects every input the tests
read (the script, both test files, and both `index.html` shells whose `<title>` is
the identity under test). The generic workflow-scanning suites
(`test_ci_gate_trigger_coverage.py`, `test_workflow_injection_boundary.py`) judge
the new file automatically and pass.

`tests/test_gate2_production_observation_ci_wiring.py` (8 tests) states the
invariant generically over every workflow that executes the suite, with negative
controls for mention-without-execution (`echo pytest <target>`), each exemption
form (`continue-on-error` and `if: false`, step and job), a missing input selector,
and a missing `workflow_dispatch`.

## 6. Verification performed

| Command | Result |
|---|---|
| `pytest tests/test_gate2_production_observation.py` | **48 passed** (41 before, +7 new) |
| `pytest tests/test_gate2_production_observation_ci_wiring.py` | **8 passed** |
| `pytest tests/test_gate2_alias_app_binding.py tests/test_aeas05_canonical_frontend_acceptance.py` + the two above | **80 passed** |
| `pytest tests/test_ci_gate_trigger_coverage.py tests/test_workflow_injection_boundary.py` + the two above | **209 passed** |
| `pytest tests/test_m02a_ci_gate_integrity.py` | **76 passed** |
| `python scripts/cp10_mutation_boundary_policy.py --judge` on all four paths | **PASS** (exit 0) |
| `python -m py_compile scripts/gate2_production_observation.py` | ok |

### Live negative controls (on the real files, restored byte-identically)

1. Dedupe disabled (`if id(entry) in seen` -> `if False`): **2 failed**
   (`test_detection_identifies_the_console_shell`,
   `test_a_shared_marker_list_does_not_make_one_app_ambiguous`), restored -> 48 passed.
2. The gate's executing step downgraded to `echo pytest -q <target>`: **2 failed**
   (`test_some_workflow_executes_the_gate2_observation_suite`,
   `test_every_executing_workflow_satisfies_the_invariant`), restored -> 8 passed.

## 7. Non-goals and open items

- No merge, no deployment, no production acceptence, no ruleset or protection change.
- `main -> deployment identity` stays `UNKNOWN`: the canonical runtime is Render and
  the GitHub deployments API has no record for it. Binding the runtime revision is
  what `/api/version` `source_revision` offers, and wiring that into the harness is a
  separate bounded change — it would add a claim this pass did not measure end to end.
- `browser-rendered UI correctness` stays `UNKNOWN`: no browser observation was made
  in this pass.
- The Render cold-start 503 is recorded as an operational characteristic. Whether the
  service should be kept warm is a human/provider decision, not a repository change.
