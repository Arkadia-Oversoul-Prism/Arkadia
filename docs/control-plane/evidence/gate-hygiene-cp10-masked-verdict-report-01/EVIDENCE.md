# CP10 reported a masked step as a verdict

Contract: `ARK-OPS-CONTINUOUS-001`. This is a bounded engineering correction to a
CI evidence artifact. **No merge, no deployment, and no production acceptance is
claimed.** Human authority remains final; merge execution is human-only (GOV-03).

- Starting `main`: `bb19aabda34d59594615b0279a45e9cbd3d8204d`
- Branch: `gate-hygiene/cp10-masked-verdict-report-01`
- Files changed: 2 — `.github/workflows/sg-02-fe-2-v.yml`,
  `tests/test_ci_verdict_step_integrity.py`
- Gating behaviour: **unchanged**. No assertion was added to or removed from the
  terminal enforcement step.

## 1. The defect, observed at runtime

Run [`45044373044`](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/45044373044)
(`event=pull_request`, head `6964abb6d`, job `validate`, `conclusion=success`).

The step `CP10-B broader backend regression` (`id: backend`) ran:

```yaml
run: python -m pytest tests/ -q --continue-on-collection-errors 2>&1 | tee cp10-backend.log
```

and reported:

```
9 failed, 4267 passed, 21 skipped, 6 warnings, 1 error in 269.67s (0:04:29)
```

The CP10 evidence summary for that same run recorded:

```
Broader backend regression: success
```

and the terminal enforcement printed `test 'success' = success` for all 17 of its
assertions, then `Executable CP10 gates: PASS (browser step outcome success).`

The step's `outcome` is `success` for **every** pytest result. The command pipes
into `tee` and the step declares no `set -o pipefail`, so the pipeline's exit
status is `tee`'s and is `0`. GitHub's default shell is `bash -e {0}`, which does
not imply `pipefail`.

The guard `tests/test_ci_verdict_step_integrity.py` already knows this and records
it:

```python
REGISTERED_MASKED_VERDICT_STEPS = {
    ("sg-02-fe-2-v.yml", "backend"),
}
```

That register stops the guard reddening. Nothing stopped the workflow from
*printing* the masked value as a result, so a human reading the step summary — or
the uploaded `cp10-*.log` artifact — was told the broader regression passed in a
run where it reported 9 failures and a collection error.

This is the same failure mode the guard's own docstring names ("a guard that
cannot fail"), one layer further out: the *artifact* claimed a verdict that was
never measured.

## 2. The repair

**`.github/workflows/sg-02-fe-2-v.yml`** — the summary reports the log's own
summary line instead of the masked outcome, and labels the step for what it is:

```yaml
# `steps.backend.outcome` is `success` for every pytest result: the step
# pipes into `tee` without `pipefail`, so the pipeline reports tee's exit
# status (registered in tests/test_ci_verdict_step_integrity.py). Printing
# it here stated a pass that was never measured — run 45044373044 recorded
# `9 failed, 4267 passed, 1 error` while this line read `success`. Report
# the log's own summary line instead.
backend_result=$(tail -n 1 cp10-backend.log 2>/dev/null || true)
echo "Broader backend regression (non-gating diagnostic): ${backend_result:-no log}"
```

Rendered against the measured log content and against an absent log:

```
Broader backend regression (non-gating diagnostic): 9 failed, 4267 passed, 21 skipped, 1 error in 269.67s
Broader backend regression (non-gating diagnostic): no log
```

**`tests/test_ci_verdict_step_integrity.py`** — detector 5
(`masked_outcomes_reported`), stated over the whole tracked workflow corpus:

> A masked step's `outcome` must not be printed as a result anywhere outside the
> terminal enforcement step.

The enforcement step is exempt because it *is* the gating surface, and the mask it
inherits is the register's business — that separation is deliberate and is not
changed here.

Whole-line `#` comments are stripped before the scan (`_without_shell_comments`),
so the repair can describe itself: the workflow's own explanatory comment names
`steps.backend.outcome`, and flagging documentation would make the fix
unwritable.

## 3. Blast radius, measured before the change

The detector was run over `git ls-files .github/workflows/*.yml` **before** the
repair. Exactly one offender exists in the corpus:

```
sg-02-fe-2-v.yml masked: ['backend'] reported_outside_enforcement: [('backend', 'CP10 evidence summary')]
```

The two sibling `| tee` steps are *not* masked, because they declare
`set -o pipefail` (`Grove contracts`, `CP10-A Lab tests`). No other workflow masks
a verdict command.

## 4. Verification

| Check | Command | Result |
|---|---|---|
| Guard + its CI wiring | `pytest tests/test_ci_verdict_step_integrity.py tests/test_ci_verdict_step_integrity_ci_wiring.py -q` | **47 passed** (was 41; `+6` = the new controls) |
| Workflow-scanning suites | `pytest tests/test_ci_gate_trigger_coverage.py tests/test_workflow_injection_boundary.py tests/test_ci_suite_collection_continuation.py tests/test_m02a_ci_gate_integrity.py tests/test_gate_filter_selection.py -q` | **377 passed** |
| Workflow YAML + shell syntax | `yaml.safe_load` + `bash -n` on the summary step's `run` | parse OK, `returncode=0` |
| CP10 mutation boundary | `printf '<path>\n' \| python scripts/cp10_mutation_boundary_policy.py --judge` | `Mutation boundary PASS`, exit 0 |

### Live negative control (the real workflow file, not a fixture)

The repaired workflow was copied aside, the pre-repair file restored from the
index, and the guard re-run:

```
=== NEGATIVE CONTROL: pre-repair workflow ===
FAILED tests/test_ci_verdict_step_integrity.py::test_a_masked_step_is_not_reported_as_a_verdict
FAILED tests/test_ci_verdict_step_integrity.py::test_the_corpus_summary_is_reported_when_it_prints_a_masked_outcome
2 failed, 33 passed

=== RESTORED: post-repair workflow ===
35 passed
```

Exactly the two new corpus nodes redden; nothing else moves. A guard that is
silent on both the defect and its absence is not a guard.

### Controls that keep the detector honest

- `test_masked_outcome_is_reported_when_a_summary_prints_it` — the measured
  pre-repair shape (masked step + summary echo) is reported.
- `test_detector_is_silent_when_the_summary_reports_the_log` — the repaired form is
  silent.
- `test_detector_is_silent_when_the_step_keeps_its_exit_status` — with `pipefail`
  the outcome is a real verdict, so printing it is honest and not reported.
- `test_detector_does_not_exempt_the_enforcement_step_from_masking` — the
  enforcement exemption is asserted, not assumed.

### Full-suite node set — unchanged

Measured in this sandbox with `PYTHONPATH=<repo>/archive/legacy_python`, both trees
in the same environment:

| tree | failed | passed | skipped | collection errors |
|---|---|---|---|---|
| `main` `bb19aabd` (worktree) | 19 | 4234 | 38 | 1 |
| branch (this change) | 9 | 4250 | 38 | 1 |

The raw counts differ, and the difference is **not** the change. `git worktree`
does not carry `web/arkadia_console/node_modules`, so the ten
`tests/test_mission_lifecycle_adapter_contract.py` nodes — which transpile the real
adapter with the repository TypeScript compiler — fail on the worktree only.
Symlinking `node_modules` into the worktree and re-running that file:

```
10 passed in 3.19s
```

Node-set comparison after that attribution:

```
=== nodes only on main ===   (the 10 mission-lifecycle nodes above)
=== nodes only on branch === (empty)
```

Zero nodes are introduced by this change; the ten main-only nodes are a
worktree-environment artifact, proven by re-running them with the dependency
present.

The residual set on both trees is pre-existing and owned or deferred elsewhere:
`test_solspire_r1_governance_convergence.py` (2, PR #693),
`test_solspire_r3_execution_runtime.py` (1, PR #691), `test_m01_persistence.py` /
`test_m05_files.py` (2, PR #690), `test_ais_w2_living_gate_grove_handoff.py` /
`test_identity_spine_w1.py` / `test_m02_reasomate_truth.py` (3, recorded product
presentation deferrals), `test_static_ingestion_idempotency.py` (order-dependent
shared-runtime class), and the CE-01 `weaver.autonomy` collection error
(sovereign-reserved).

## 5. Deliberate non-changes (accountability, not oversight)

- **The terminal enforcement assertion was not touched.** Removing
  `test '${{ steps.backend.outcome }}' = success` would change what the gate
  asserts, and it would also require deleting the `REGISTERED_MASKED_VERDICT_STEPS`
  entry (`test_registered_masked_steps_are_still_masked` pins the inventory).
  Making a gate honest by deleting an assertion is a governance decision for the
  sovereign, not a test-hygiene edit. It is recorded here as proposed work, not
  performed.
- **`set -o pipefail` was not added to the backend step.** It would make the gate
  red on the broader corpus's pre-existing failures, including the CE-01
  `weaver.autonomy` module-vs-package collision that is reserved to the sovereign.
- **No other surface was widened.** `api/main.py` was not touched and stays inside
  its 2600-line budget.

## 6. Observed, not repaired here

Running the suite in this sandbox left an untracked
`data/engineering_lab/agent_events.jsonl`. It is the class PR #688
(`gate-hygiene/engineering-lab-event-log-sandbox-01`) repairs; it is not this
change's to fix, and it was deleted from the working tree rather than committed.

## 7. Authority

Repository-source claim only. Production `GET /api/version` reported
`source_revision == bb19aabda34d59594615b0279a45e9cbd3d8204d` at the start of this
pass — necessary evidence of source↔runtime consistency, and **not** proof that
the application works, that this change is deployed, or that anything is accepted.
