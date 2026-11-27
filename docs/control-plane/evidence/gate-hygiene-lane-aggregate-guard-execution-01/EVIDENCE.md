# Evidence — the aggregate-PR classification guard is executed by the lane gate

**Workstream:** `gate-hygiene/lane-aggregate-guard-execution-01`
**Base:** `main` @ `bb19aabda34d59594615b0279a45e9cbd3d8204d` (2026-11-22T18:23:48+01:00)
**Observed:** 2026-11-23T04:09Z
**Authority:** repository-source repair only. No merge, no deployment, no production claim.

## 1. Defect (measured, not inferred)

`tests/test_lane_aggregate_pr_classification.py` (15 tests) judges the lane
ownership classifier. It executes the **real** classifier from
`scripts/lane_state_refresh.py` against the **real** declaration
`docs/control-plane/parallel-ui/aggregate-prs.json`.

`.github/workflows/lane-doc-currency.yml` selects both of those inputs:

```
$ git grep -l "lane_state_refresh" bb19aabd -- .github/workflows/
bb19aabd:.github/workflows/lane-doc-currency.yml
```

and its filters also select the whole snapshot tree
(`docs/control-plane/parallel-ui/**`). So a commit that changes what the
classifier does, or what it is told to treat as aggregate, **executes the lane
gate** — and the gate runs everything except the guard that judges it:

```
$ git grep -l "test_lane_aggregate_pr_classification" bb19aabd -- .github/
0
```

The guard was written after the gate's step inventory was, and the inventory was
a fixed list. This is the class already recorded for the console-contract gate
(PR #435/#439) and the economic-seam gate: **a fixed inventory of a
content-derived domain drifts, and the drift is silent.** No individual PR can
observe it — the branch that adds a guard is green against the gate it inherited.

## 2. Repair (2 files, bounded)

1. `.github/workflows/lane-doc-currency.yml` (+9 lines)
   - `tests/test_lane_aggregate_pr_classification.py` added to the
     `pull_request` **and** `push` filters, so editing the guard itself selects
     the gate that runs it;
   - a step that **executes** it (`python -m pytest -q tests/...`), so the guard
     is not merely selected.
2. `tests/test_lane_currency_ci_wiring.py` (+8 nodes, 12 → 20)
   - `_lane_domain()` derives the guard set at test time from
     `git ls-files -- tests/` plus needles (`lane_state`, `lane-state.json`,
     `lane-doc-currency`, `aggregate-prs`) — the same derivation convention as
     `scripts/console_contract_domain.py`;
   - `test_workflow_executes_every_lane_guard[...]` and
     `test_trigger_filters_name_every_lane_guard[...]` are parametrized over that
     domain, so a guard added to the corpus reddens this judge until the gate
     executes it — the omission cannot recur silently;
   - `test_domain_derivation_finds_the_known_lane_guards` is the **positive
     control**: an empty domain would make both parametrized tests vacuously
     true (a judge that derives nothing always passes);
   - `test_domain_judge_bites_when_a_guard_step_is_missing` is the **negative
     control**: fed the real workflow text with the executing step removed, no
     pytest invocation names the guard.

`parallel-ui` alone was rejected as a needle: it over-matches
`tests/test_weaver_merge_authority_contract.py`, which reads
`SHARED-CONTRACTS.md` and guards merge authority, not the lane snapshot.

## 3. Verification (commands and measured results)

| Command | Result |
| --- | --- |
| `pytest tests/test_lane_currency_ci_wiring.py -q` (pre-repair) | 12 collected |
| `pytest tests/test_lane_currency_ci_wiring.py -q` (post-repair) | **20 passed** (+8 = 3 execution + 3 filter + 1 positive control + 1 negative control) |
| `pytest tests/test_lane_currency_ci_wiring.py tests/test_lane_instruction_doc_currency.py tests/test_lane_aggregate_pr_classification.py -q` | **101 passed** |
| `python scripts/lane_state.py --check` | exit 0 — `lane instruction docs consistent with snapshot (4 guarded lanes)` |
| `pytest tests/test_ci_gate_trigger_coverage.py tests/test_gate_filter_selection.py tests/test_ci_suite_collection_continuation.py tests/test_workflow_injection_boundary.py tests/test_m02a_ci_gate_integrity.py tests/test_ci_verdict_step_integrity.py tests/architecture -q` | **417 passed** |
| `cp10_mutation_boundary_policy.py --judge` on the three changed paths | `PASS`, exit 0 |

**Live negative control** (on the real workflow file, not a synthetic fixture):
the executing step was removed from `.github/workflows/lane-doc-currency.yml`
and the judge re-run → `2 failed, 18 passed`, failing exactly
`test_workflow_executes_every_lane_guard[tests/test_lane_aggregate_pr_classification.py]`
plus the control's own staleness assertion. The file was then restored
byte-identically (`git diff --stat` → only the intended +9 lines) and the judge
returned `20 passed`.

## 4. Not claimed

- No merge, no deployment, no production observation. The gate's behaviour under
  CI is asserted from source and from local execution only; the first
  `pull_request` run of this branch is the runtime proof and is reported on the
  PR, not here.
- `api/main.py` untouched (budget 2600).
- The workflow still enumerates its steps one per guard. Executing the derived
  domain directly (`pytest $(python scripts/lane_contract_domain.py)`) would
  remove the last hand-maintained list, but that widens an execution surface and
  is a separate bounded change for sovereign review.

## 5. Runtime observation (branch, not acceptance)

Run `45110213175` (`Lane Doc Currency`, `event=pull_request`) at head
`2f4f727f023e6451085ac3fc27c2867b11233d3d` → **success**, and the *step log*
(not the job conclusion) shows the guard executing:

```
Execute lane instruction-doc currency guard      66 passed in 2.24s
Execute the aggregate-PR classification guard    15 passed in 0.07s   <-- newly executed
Execute the wiring guard (judges this workflow)  20 passed in 0.16s
lane_state.py --check                            lane instruction docs consistent with snapshot (4 guarded lanes)
```

Of the 10 workflow runs at that head, 9 are `success`. The single `failure`
(`N-ATLAS external beta validation`, run `45110213166`) is
`ModelUnavailable: N-ATLaS Gradio runtime error` — the live external provider,
never evidence about the repository tree, and recorded as intermittent.

## 6. Adjacent gap observed, deliberately NOT repaired

No workflow whose `paths` filter includes `tests/**` executes the whole suite.
`economic-seam-engine.yml`, `prism-console-contract.yml` and
`operator-console-posture.yml` all select `tests/**`, and each runs a **narrow**
inventory (`pytest -q <8 files>`, `pytest -q $(console_contract_domain.py)`, two
named files). `provider-routing.yml` is the only whole-suite surface
(`python -m pytest tests/ -q -rEf --continue-on-collection-errors`) and its
filter is `weaver/**`, `providers/**`, `tests/architecture/**` and four named
files. Measured consequence: a commit that edits, say,
`tests/test_weaver_sci_boundary_01.py` executes three gates and **none of them
runs that file** — no workflow names it (`grep -rl` over `.github/workflows/`
→ 0, and it is not in the console-contract domain either).

Scale, measured at `bb19aabd` over `git ls-files -- tests/`: of **341**
`test_*.py` files, **112** are named by some workflow, **74** are in the
console-contract domain, and the `tests/architecture/` tree is covered by
`provider-routing.yml`'s whole-suite step — **178** covered in total, so **163**
test files are executed by no gate that a change to them would trigger.

Two guards that *look* unwired are not: `tests/test_prism_w4_lab_pr_state.py`
and `tests/test_prism_solspire_control_plane.py` are members of the
console-contract domain (74 files), so `prism-console-contract.yml` executes
them. Check the derived domain before declaring a guard unwired.

That is the same class as §1 at repository scale, and it is **not** repaired
here: making a `tests/**`-selected gate run the whole suite widens an execution
surface (runtime cost, dependency set, and the sovereign's gate budget). It is
recorded as a separate proposed workstream for sovereign review. Discovery does
not authorize execution.

## 7. Next authorized action

- **This PR:** human review of a draft. Merge execution is human-only (GOV-03);
  nothing here is a merge, deployment, or acceptance claim.
- **After a human merge:** re-run `lane-doc-currency` on the resulting `main` and
  confirm the step log still shows `15 passed` for the aggregate guard.
- **Separate, not started:** the §6 whole-suite execution-surface decision is a
  sovereign question (which gate runs the full suite, on which filter, with
  which dependency set). Do not open a competing PR on
  `.github/workflows/lane-doc-currency.yml`; compose any further lane-gate change
  into this branch.
