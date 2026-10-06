# GATE-07 · CI suite continuation — the judging broad-suite step executed zero tests

**Workstream:** GATE-07 durable weaver loop / hourly scheduler (chain PRs #319–#324)
**Branch:** `gate07/ci-suite-collection-continuation-01`
**Base main:** `451e41a30fcbff4a65326e897a84818cc623b769`
**Classification:** IMPLEMENTED (repository source + local measurement); CI verification
requires this PR's own runs.
**Authority boundary:** no merge, no push to `main`. Human sovereign merges.

## 1. Observation that motivated this pass

Reviewing the GATE-07 chain (#319–#324) required deciding whether the red
"Provider Routing Verification" runs on `gate07/attention-truthfulness` were caused by the
chain or were pre-existing. Live evidence, run `37395288765` @ `cd749ea` (PR #323 head):

```
6  Targeted K2 and key-pool regressions      success   23 passed in 0.37s
7  Relevant architecture regression          success   11 passed in 1.56s
8  Broader test suite                        failure
     $ python -m pytest tests/ -q
     ERROR collecting tests/test_autonomy.py
     E  ImportError: cannot import name 'load_autonomy_config' from 'weaver.autonomy'
     !!! Interrupted: 1 error during collection !!!
     1 skipped, 1 warning, 1 error in 4.99s
     ##[error]Process completed with exit code 2.
```

`tests/test_attention_truthfulness.py` — the guard PR #323 adds — is collected by that
step and **executed zero times**. It passes locally (9 passed) and in no CI job. A
regression the guard was written to catch would have reached `main` unjudged, because the
session aborted on an unrelated module-vs-package collision (CE-01,
`weaver/autonomy/__init__.py` vs `weaver/autonomy.py`, reserved to the sovereign).

This is the known gate-hygiene class: *a red job is not evidence that the suite ran.*

## 2. Attribution — the chain did not cause it

| Fact | Evidence |
| --- | --- |
| The step failed at **collection**, before any test ran | run `37395288765` step 8 log |
| The collision is CE-01, pre-existing on `main`, unrelated to `weaver/attention_bus.py` | `weaver/autonomy/__init__.py` + `weaver/autonomy.py` both tracked |
| None of #319–#324 touch `provider-routing.yml` | `GET /pulls/{n}/files` for n=319..324 |
| The two targeted steps passed on the same head | steps 6 and 7 above |

The chain's own guards are green where they run. The red job is a pre-existing structural
defect in how the workflow invokes the suite.

## 3. Bounded change

1. `.github/workflows/provider-routing.yml`
   - `Broader test suite` now runs
     `python -m pytest tests/ -q -rEf --continue-on-collection-errors`.
     The session no longer aborts at the CE-01 error, so the suite — including the
     `weaver/**` guards this workflow is the only CI surface for — actually executes and
     is judged. Debt is still reported; it is no longer *silent*.
   - The trigger `paths` gain `tests/test_ci_suite_collection_continuation.py` so the new
     guard is executed by the workflow it audits.
2. `tests/test_ci_suite_collection_continuation.py` (new, 28 tests)
   - parametrized over **every** `.github/workflows/*.yml`: a broad-suite step that can
     fail the job must carry the continuation flag;
   - asserts a *judging* broad-suite surface still exists (not only `continue-on-error`
     reporters);
   - asserts `provider-routing.yml` stays selected by `weaver/**` and stays judging;
   - asserts a `weaver/**`-selected workflow reaches a whole-suite run;
   - asserts the guard is itself selected by that workflow;
   - three negative controls: the detector flags the exact pre-fix line, ignores
     file-targeted invocations, and treats a `continue-on-error` step as a non-judging
     surface.

Scope discipline: `sg-02-fe-2-v.yml`'s broad-suite step carries `continue-on-error: true`.
It does not gate anything, so it is deliberately **out of scope** — the rule applies only
to steps that can fail the job. Widening to it would change a workflow unrelated to this
defect.

`api/main.py` is untouched (boot-code safety and the 2600-line budget are not engaged).

## 4. Verification measured in this environment

```
python -m pytest tests/test_ci_suite_collection_continuation.py -q   -> 27 passed
   negative control (workflow fix stashed):                            3 failed, 24 passed
python -m pytest tests/architecture -q                                -> 11 passed
python -m pytest tests/test_ci_suite_collection_continuation.py \
    tests/test_m02a_ci_gate_integrity.py tests/test_workflow_injection_boundary.py -q
                                                                      -> 116 passed
git diff --name-only | python scripts/cp10_mutation_boundary_policy.py --judge
                                                                      -> PASS (exit 0)
```

Full suite, baseline `main` `451e41a` vs this branch, both
`python -m pytest tests/ -q -rEf --continue-on-collection-errors`:

| | baseline `451e41a` | branch |
| --- | --- | --- |
| summary | 54 failed, 1203 passed, 18 skipped, 28 errors | 54 failed, 1231 passed, 18 skipped, 28 errors |
| failing/error **node set** | 82 nodes, sha256 `72994ba2003979a4…` | 82 nodes, sha256 `72994ba2003979a4…` |

The node sets are **identical** (`delta: []`). The `+28 passed` is exactly the new guard
file. The 28 errors are environmental here (`starlette.testclient requires httpx`, absent
locally); CI installs `httpx` from `requirements.txt`, so CI does not see them.

**Regression:** unchanged.

## 5. Remaining uncertainty

- CI confirmation is this PR's own runs; local measurement cannot substitute for it.
- The CE-01 collision itself is **not** fixed here. It is reserved to the sovereign and
  this change deliberately works around its symptom at the CI boundary only.
- The GATE-07 composed-integration review (#319–#324) continues on the PR #324 evidence
  branch; this pass resolves only the CI-attribution question and the guard-reachability
  defect it exposed.

## 6. Authorization required

Sovereign review and merge of this bounded PR. No consequential follow-on work is included.
