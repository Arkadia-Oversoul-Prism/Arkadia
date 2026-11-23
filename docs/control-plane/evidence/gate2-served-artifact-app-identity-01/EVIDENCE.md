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

---

## 8. Addendum — the runtime revision link (§7's first open item, closed)

**Measured:** 2026-11-23 at `main` `bb19aabda34d59594615b0279a45e9cbd3d8204d`.
**Scope:** `scripts/gate2_production_observation.py`, its fitness tests, its wiring
guard, and this gate's `paths` filters. No product code, no route, no authority,
no deployment, no acceptance.

### 8.1 The defect this closes

§7 recorded that `main -> deployment identity` stays `UNKNOWN` because the
canonical runtime publishes no GitHub deployment record, and that binding
`/api/version` `source_revision` "is a separate bounded change". That change is
this addendum.

The evidence was one unauthenticated GET away the whole time:

```
$ curl -s https://arkadia-qzu4.onrender.com/api/version
{"schema":"arkadia.version/v1", ..., "source_revision":"bb19aabda34d59594615b0279a45e9cbd3d8204d",
 "revision_source":"RENDER_GIT_COMMIT","revision_conflict":false, ...}
```

`grep -n "api/version" scripts/gate2_production_observation.py` returned **0**
matches before this change, so the first unresolved link of the chain
`main SHA -> deployment SHA -> production response -> observation` was reported
unproven while a matching runtime revision was readable.

### 8.2 Why this is a *separate* boundary, not a rewrite of the record one

ADR-016 keeps the six concepts apart. The GitHub `/deployments` record describes
the retired Vercel project; the running Render process is the canonical
deployment. They are different systems, and one verdict for both is exactly how a
stale record and a current runtime come to look identical. So
`classify_deployment_identity` is **unchanged**, and a new boundary is added:

```
main -> deployment identity                UNKNOWN      (GitHub record; no Render record exists)
main -> canonical runtime revision         VERIFIED (source_revision == main)
```

The record row staying `UNKNOWN` is correct, not a regression.

### 8.3 Reuse, not a second copy of the rules

The revision semantics already exist and are already tested:
`scripts/version_reconciliation.py` (`fetch_reported_evidence`, `compare`,
`invalid_reported_sources`) over `kernel/revision_identity.py`. The harness now
imports them, and `classify_runtime_revision` mirrors that module's precedence
exactly rather than restating it:

| Observation | Verdict |
|---|---|
| `GET /api/version` unreadable / non-JSON / non-object | `BLOCKED` |
| `revision_conflict: true` (two valid sources disagree) | `UNKNOWN` — fail closed |
| a reported source carries an unusable value | `UNKNOWN` |
| `source_revision == main`, both valid | `VERIFIED` |
| both valid and different | `DRIFT`, naming both SHAs |
| absent / placeholder / invalid `source_revision` | `UNKNOWN` |

`compare` already returns `UNKNOWN` for `compare("UNKNOWN", "UNKNOWN")`, so two
identical placeholders can never read as a match.

Because the harness now depends on those two files, both are added to this gate's
`paths` filters **and** to `_REQUIRED_SELECTORS` in the wiring guard — the
repository's rule that a filter must name every input its guard reads.

### 8.4 Live observation (same machine, same minute)

```
CANONICAL RUNTIME REVISION (ADR-016: Render is the reconciled deployment)
  https://arkadia-qzu4.onrender.com/api/version -> OK
  reported source_revision: bb19aabda34d59594615b0279a45e9cbd3d8204d
  main -> canonical runtime revision: VERIFIED (source_revision == main)
  note: a matching revision is necessary evidence of source<->runtime
        consistency -- not proof the application works, not acceptance.

BOUNDARY CLASSIFICATION
  main -> deployment identity                UNKNOWN
  main -> canonical runtime revision         VERIFIED (source_revision == main)
  alias reachable                            VERIFIED
  marker-set oracle                          VERIFIED (marker set observed in served artifact)
  deployment build output observed           UNKNOWN
  production acceptance                      NOT CLAIMED (human authority)
```

This is source<->runtime **consistency**. It is not proof the application works,
not deployment-identity evidence for the retired provider, and not acceptance.

### 8.5 Tests and negative controls

`tests/test_gate2_production_observation.py`: **48 -> 57** nodes; with the wiring
guard, **56 -> 65 passed**. Nine new nodes: match, drift-naming-both,
not-a-constant, conflict, blocked-vs-unknown, invalid-source, absent-value,
no-evidence, and wiring.

Two **live** controls on the real files, each restored byte-identically
(`sha256 85829a5cf4ee2e56c8d5adc47c198b1ab431f82a0a5258fbe472222195b0c564`):

1. Boundary assignment replaced with a literal `"UNKNOWN"` -> **1 failed**
   (`test_the_boundary_is_wired_to_its_classifier`), restored -> 57 passed.
   This proves the classifier is executed, not merely defined.
2. `classify_runtime_revision` made to return a constant `VERIFIED` -> **7 failed**,
   including `test_the_classifier_reads_the_expected_revision_and_is_not_a_constant`
   (matching evidence scored against a *different* main). Restored -> 57 passed.
   This is the control that stops the positive cases from being satisfiable by a
   classifier that ignores its input.

Cross-suite: `tests/test_version_reconciliation.py` + both gate-2 files **101
passed**; the three generic workflow-scanning suites **256 passed**;
`python scripts/cp10_mutation_boundary_policy.py --judge` **PASS**.

### 8.6 Non-effects

No merge, no push to `main`, no deployment, no production acceptance, no
ruleset or branch-protection change, no product or route change. The record-based
`main -> deployment identity` row is unchanged and still `UNKNOWN`;
`deployment build output observed`, `build <-> source lineage`, and
`browser-rendered UI correctness` remain `UNKNOWN`.
