# GATE-10 — execute the `api/main.py` line budget on the surface it constrains

**Contract:** ARK-OPS-CONTINUOUS-001 (reconciliation + gap closure)
**Branch:** `gate10/architecture-budget-ci-wiring-01`
**Base:** `main` @ `bb19aabda34d59594615b0279a45e9cbd3d8204d`
**Authority:** implementation, test, evidence, draft PR. **No merge, no deploy, no acceptance.**
**Status:** VERIFIED locally and in CI at `f6e7cb5d` (14/14 check-runs `success`, including the new
`architecture-budget` gate). Merge, deployment and acceptance remain NOT CLAIMED and human-only.

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

## 5. Full-suite baseline comparison (measured, same command on both trees)

Both trees run in this environment with the identical dependency set and the identical
command:

```
python -m pytest tests/ -q -rEf --continue-on-collection-errors -m "not live_container"
```

| Tree | Result | Failing/error node set |
|---|---|---|
| `main` @ `bb19aabd` (detached worktree) | `26 failed, 4230 passed, 33 skipped, 1 error in 290.74s` | **27 nodes**, `sha256 a6da301439f00753431bea519c9a586ed1ae6ba7192b6b80838706eccb712002` |
| branch @ `f6e7cb5d` | `26 failed, 4248 passed, 33 skipped, 1 error in 285.12s` | **27 nodes**, `sha256 a6da3014…2002` |

`comm -3` on the two sorted node lists is **empty**: zero new, zero fixed. Attributed by
node identity, not by count — the passed totals differ only because the branch carries
more nodes.

The `+18 passed` is attributed by `--collect-only` across the two trees (4290 → 4308
collected ids), not inferred from the delta:

```
 11  tests/test_architecture_budget_ci_wiring.py      (the new guard)
  3  tests/test_ci_gate_trigger_coverage.py           (parametrized over workflows)
  2  tests/test_ci_suite_collection_continuation.py   (parametrized over workflows)
  1  tests/test_gate_filter_selection.py              (parametrized over workflows)
  1  tests/test_workflow_injection_boundary.py        (parametrized over workflows)
```

The seven non-new nodes are the generic workflow-scanning suites gaining a member by
construction from one added workflow file — the recorded pattern, not a behaviour change.

## 6. CI execution (this revision, observed)

All **14** check-runs on `f6e7cb5d` are `completed/success`, including:

- `architecture-budget` — **pass, 12s**: the new gate executes and is green in CI, so the
  wiring is runtime-proven rather than source-asserted.
- `provider-routing` — pass, 7m59s: the independent full-suite/baseline comparison gate
  agrees there is no regression.
- `test` (economic-seam-engine / CP10 integrity), `console-contract` (3m6s),
  `posture-currency`, `trigger-coverage`, `verdict-step-integrity`, `boot-syntax`,
  `Full-history secret scan`.

One transient: `beta-beta-01-english` failed on the first run of
`n-atlas-external-beta.yml` while `beta-beta-02-hausa` **passed in the same run**, and
`bundle-beta-evidence` then failed because it read the stale FAILED artifact. This is the
recorded live external-provider flake (`ModelUnavailable: N-ATLaS Gradio runtime error`),
not evidence about this tree: the workflow was re-run and `beta-01`, `beta-02`, `bundle`
and `native-arkadia-golden-workflow` are all `pass`. This diff touches no `lab/`,
`providers/` or N-ATLaS code.

## 7. Limitations (stated, not hidden)

- **CI execution is now claimed for `f6e7cb5d` only.** A later push needs its own run.
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

## 8. Next authorized action

Human review of this draft PR. Merge execution is human-only (GOV-03); no agent may
merge, deploy, or accept this change.
