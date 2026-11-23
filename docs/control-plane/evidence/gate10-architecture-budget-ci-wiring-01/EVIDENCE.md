# GATE-10 — execute the `api/main.py` line budget on the surface it constrains

**Contract:** ARK-OPS-CONTINUOUS-001 (reconciliation + gap closure)
**Branch:** `gate10/architecture-budget-ci-wiring-01`
**Base:** `main` @ `bb19aabda34d59594615b0279a45e9cbd3d8204d`
**Authority:** implementation, test, evidence, draft PR. **No merge, no deploy, no acceptance.**
**Status:** repository-source change VERIFIED locally; CI execution NOT CLAIMED until a run exists.

## 1. Defect (measured, not inferred)

`tests/architecture/test_layer_boundaries.py::test_api_main_line_count_within_budget`
holds `api/main.py` to **2600** lines.

```
$ wc -l api/main.py
2597 api/main.py
```

Three lines of headroom. The assertion is executed by exactly one workflow,
`provider-routing.yml`:

```
$ grep -n "architecture" .github/workflows/provider-routing.yml
12:      - "tests/architecture/**"
63:      - name: Relevant architecture regression
65:          python -m pytest tests/architecture -q
```

Its `pull_request` `paths` filter names `tests/architecture/**`, `weaver/**`,
`providers/**`, `scripts/provider_routing_gate.py` and a handful of test files. It does
**not** name `api/**`. So a commit that touches only `api/main.py` — the file the budget
constrains — runs the architecture suite **nowhere**. The next API change that adds four
lines breaches a stated architectural budget with no gate reporting it.

`tests/test_ci_gate_trigger_coverage.py` already records why this was left open:

> The architecture suite also asserts a line budget for `api/main.py`, so `api/**`
> arguably belongs in the filter of any workflow that runs it; `provider-routing.yml`
> also runs the full suite, which carries pre-existing `main` failures, so widening its
> filter to `api/**` would turn every API pull request red with debt it did not
> introduce. That widening is therefore recorded as proposed work, not performed here.

This change takes the **narrow** route that the deferral leaves open, rather than the
deferred one: a dedicated gate that selects `api/**` and runs the architecture suite
only. It runs no broad-suite step, so it cannot inherit debt it did not introduce.

## 2. Change

| Path | Change |
|---|---|
| `.github/workflows/architecture-budget.yml` | **new.** `pull_request` + `push(main)` selected by `api/**`, `tests/architecture/**`, the guard, and itself; `workflow_dispatch`; one step running `python -m pytest tests/architecture -q -rEf`. |
| `tests/test_architecture_budget_ci_wiring.py` | **new.** Derives every workflow that mentions the architecture suite, tokenises its `run` blocks, and judges execution, dispatchability, API selection, and exemption. |
| `tests/architecture/test_layer_boundaries.py` | docstring only: the stale `Current size: ~2506 lines` is replaced by a pointer that the size is measured live (2597 at `bb19aabd`). The assertion and budget are unchanged. |

The workflow's dependencies are `pytest` alone. `tests/architecture` imports only
`ast`, `sys`, `pathlib`, `typing` and `LAYER_MAP`, so a missing application dependency
cannot be misreported as an architecture breach.

## 3. Invariant and why it is stated generically

The guard is not written against `architecture-budget.yml`. It states four conditions
over **every** workflow that mentions the suite:

1. a mention must be an execution — a path in prose, or `echo pytest tests/architecture`,
   does not count;
2. some workflow must both execute the suite and be selected by `api/main.py`;
3. that workflow must be dispatchable;
4. an executing step must be able to fail the run (no step/job `continue-on-error`,
   no `if: false`).

Condition 2 is the load-bearing one: executing the suite in a gate that `api/**` does
not select leaves an API commit unjudged. A second workflow that runs the suite but
does not select `api/**` (today: `provider-routing.yml`) is therefore reported as a
candidate defect and tolerated, not required to change.

## 4. Verification (measured in this environment)

```
$ python -m pytest tests/test_architecture_budget_ci_wiring.py -q
11 passed in 0.57s

$ python -m pytest tests/architecture tests/test_architecture_budget_ci_wiring.py \
    tests/test_ci_gate_trigger_coverage.py tests/test_m02a_ci_gate_integrity.py \
    tests/test_ci_suite_collection_continuation.py tests/test_workflow_injection_boundary.py -q
354 passed in 4.85s

$ printf '%s\n' ".github/workflows/architecture-budget.yml" \
    "tests/test_architecture_budget_ci_wiring.py" \
    "docs/control-plane/evidence/gate10-architecture-budget-ci-wiring-01/EVIDENCE.md" \
    "tests/architecture/test_layer_boundaries.py" \
  | python scripts/cp10_mutation_boundary_policy.py --judge
Mutation boundary PASS (M02A legitimate-surface + constitutional denylist)
```

### Live negative control (the detector bites on the real file)

Removing the two `- "api/**"` lines from the **real** workflow and re-running the guard:

```
FAILED tests/test_architecture_budget_ci_wiring.py::test_a_gate_selects_api_changes_and_executes_the_suite
E  AssertionError: no workflow both executes the architecture suite and is selected by
   api/main.py; defects per candidate: architecture-budget.yml: ['paths filter does not
   select api/main.py']; provider-routing.yml: ['paths filter does not select api/main.py']
1 failed, 10 passed in 0.84s
```

Restored byte-identically (`sha256 8c74e081…f8008` before and after) → `11 passed`.
Exactly one node reddens, and it is the load-bearing one.

### Detector controls (all in the new file)

| Control | Asserts |
|---|---|
| `test_detector_is_silent_on_the_correct_shape` | positive: the invariant's own shape audits clean |
| `test_detector_flags_a_gate_that_does_not_select_api_changes` | the measured pre-repair shape is reported |
| `test_detector_does_not_count_a_mention_as_an_execution` | `echo pytest …` is not an execution |
| `test_detector_flags_an_exempted_executing_step` | `continue-on-error` disarms a gate |
| `test_detector_flags_an_undispatchable_gate` | no `workflow_dispatch` |
| `test_detector_flags_a_gate_that_does_not_select_the_budget_assertion` | the assertion itself must be selected |
| `test_glob_matching_covers_the_concrete_paths_the_invariant_names` | `api/**` selects `api/main.py`, not `apis/main.py` |

## 5. Baseline comparison

Attributed by failing/error **node identity**, never by count. Baseline measured on
`main` `bb19aabd` in this environment with the same dependency set; the branch delta is
recorded in the PR body. The change adds only: one workflow file (which the generic
workflow-scanning suites iterate, so they gain passing nodes by construction), one test
file, and a docstring.

## 6. Limitations (stated, not hidden)

- **CI execution is NOT CLAIMED.** No workflow run exists at this revision yet. The
  local runs above are evidence about this tree only.
- **The budget is a repository convention, not a platform-enforced rule.** Branch
  protection is absent (`GET /branches/main/protection` → `404 Branch not protected`)
  and the repository has **0** rulesets, so nothing prevents a direct push that bypasses
  this gate. Making the budget unbypassable is a platform/configuration change and is
  therefore reserved to the human.
- **`api/main.py` is 3 lines from the budget.** This gate makes a breach visible; it
  does not create headroom. Decomposition is Phase 2 work and is not attempted here.
- `provider-routing.yml` is intentionally unchanged, so this change touches no workflow
  an open PR owns (`sg-02-fe-2-v.yml` → #695, `canonical-render-browser-smoke.yml`
  → #689, `gate2-production-observation.yml` → #681/#687, `lab-security-contract.yml`
  → #686, `solspire-r3-validation.yml` → #691).

## 7. Next authorized action

Human review of this draft PR. Merge execution is human-only (GOV-03); no agent may
merge, deploy, or accept this change.
