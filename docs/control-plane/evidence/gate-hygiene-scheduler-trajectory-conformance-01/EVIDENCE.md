# EVIDENCE — scheduler ↔ trajectory conformance (gate-hygiene)

**Gate / workstream:** gate-hygiene (hourly bounded-execution loop integrity)
**Branch:** `gate-hygiene/scheduler-trajectory-conformance-01`
**Base main:** `451e41a30fcbff4a65326e897a84818cc623b769`
**Classification:** VERIFIED (repository-source), regression boundary unchanged

## 1. Defect (evidence-backed)

The hourly scheduler `.github/workflows/arkadia-engineering-scheduler.yml` runs the
`EngineeringWorker` against the trajectory named by
`ARKADIA_ENGINEERING_TRAJECTORY` (`docs/control-plane/TRAJECTORY-CONSOLE-COMPLETION-01.yaml`)
and fails the job (`exit 1`) when the worker result status is `FAILED`.

At base main the trajectory nested `moves` and `routing_invariants` **two spaces under the
`trajectory:` block**. `weaver/engineering_router.py::_load_yaml` requires top-level
`trajectory` + `moves` and raises `ValueError("invalid trajectory structure")` otherwise.
The router therefore never returned a routing decision; the worker returned `FAILED` and the
hourly session failed closed on every wake — a false red, not a truthful clean stop.

Observed at base main:

```
status=FAILED   exit=1
```

## 2. Change

`docs/control-plane/TRAJECTORY-CONSOLE-COMPLETION-01.yaml` — `moves` and
`routing_invariants` dedented from under `trajectory:` to the document top level. Pure
structural correction: **no move status, dependency, spec, or ordering was altered.** The
file now conforms to `docs/control-plane/trajectory.schema.json` (top-level required
`trajectory` + `moves`), matching the canonical `TRAJECTORY-ARKADIA-TRUTHFULNESS-01.yaml`.

After the fix the router returns a **decision**, not a failure:

```
status=NO_LEGAL_MOVE  exit=0  trajectory_id=ARKADIA-CONSOLE-COMPLETION-01
```

`NO_LEGAL_MOVE` is the *correct* frontier result: G12-A is `merged_acceptance_pending`
(merge alone is not acceptance — routing invariant), so dependent G12-B is correctly not
selected. This change does **not** attempt to unblock the frontier; see §5.

## 3. Regression guard (with negative control)

`tests/test_scheduler_trajectory_conformance.py` (10 tests). It reads the trajectory path
**from the workflow itself** (not a hardcoded name) and loads every
`docs/control-plane/TRAJECTORY-*.yaml` through the router's own `_load_yaml` /
`select_next_move`, so a structural slip fails CI rather than the scheduler.

Falsifiability — negative control against the pre-fix artifact
(`git show HEAD:docs/control-plane/TRAJECTORY-CONSOLE-COMPLETION-01.yaml`):

| artifact | result |
|---|---|
| pre-fix (nested `moves`) | **4 failed**, 6 passed |
| post-fix (top-level `moves`) | **10 passed** |

`test_negative_control_nested_moves_is_rejected` additionally feeds a nested structure to
the loader and asserts `ValueError("invalid trajectory structure")`, so the detector cannot
be disarmed by editing the fixture without reddening the control.

## 4. Measured result

Full suite, `-q -rEf --continue-on-collection-errors`, this environment:

| tree | passed | failed | skipped | errors | failing/error nodes | outcomes fp | ids fp |
|---|---|---|---|---|---|---|---|
| main `451e41a` | 1005 | 69 | 20 | 48 | 117 | `f33d69df…` | `6dde9f16…` |
| branch `f179d2b` | 1024 | 69 | 20 | 48 | 117 | `f33d69df…` | `6dde9f16…` |

Both trees were measured **in this same environment** (base main in a detached worktree at
`451e41a`), so the delta is attributable to the branch, not to a dependency difference.

- **Zero regression:** identical failure/error-node **set** on both trees
  (`only in main: []`, `only in branch: []`; `sha256` of the sorted node list =
  `f33d69df…` on both). Baseline debt (69F / 48E) is **pre-existing main debt, recorded not
  fixed** — it is not attributable to this change.
- **The `+19 passed` is explained, not assumed.** Collected nodes: `main` 1093, branch
  1112. The 19 new nodes are the 16 guard nodes **plus 3** parametrizations of the
  pre-existing `tests/test_ci_gate_trigger_coverage.py` that the new `pull_request` trigger
  now selects for this workflow — all 3 pass (VERIFICATION.md item 9). Earlier `+10` / `+15`
  figures (recorded before later follow-ons) are superseded by this measurement.
- `tests/architecture`: **11 passed** (main's own baseline; this workflow does not run it —
  `provider-routing.yml` does).
- `python -m py_compile api/main.py`: **OK**; `api/main.py` **untouched** (2432 lines, within
  the 2600 budget).

## 5. Non-goals / proposed (NOT executed)

- **Frontier semantics.** G12-B remains correctly blocked by G12-A's
  `merged_acceptance_pending`. Unblocking requires human acceptance of G12-A — sovereign
  authority, not an engineering change. `NO_LEGAL_MOVE` is truthful.
- **Status vocabulary divergence (PROPOSED, separate workstream).** The canonical schema
  `docs/control-plane/trajectory.schema.json` enumerates move statuses
  `{pending, revision_required, completed, accepted, blocked, failed, aborted}`, while the
  console trajectory uses `merged_acceptance_pending` and `in_progress`, and the router's
  `ACTIVE_STATUSES` accepts `{pending, revision_required, in_progress}`. Neither
  `in_progress` nor `merged_acceptance_pending` is schema-valid. This is **pre-existing and
  does not cause the hourly failure** (jsonschema validation is not run by the scheduler and
  `jsonschema` is not installed in this environment). It is recorded here as a bounded
  proposal; **not fixed in this workstream** to avoid scope expansion.

## 6. Authorization boundary

Human-only merge and human-only deploy. No production-parity claim is made: this is a
repository-source fix plus a regression guard, not a runtime observation.

## 7. Follow-on within this workstream: the guard was CI-inert (measured, then fixed)

The guard added in §3 stated the invariant but **no workflow executed it**. Measured on the
PR head before this follow-on:

- `grep -rn "test_scheduler_trajectory_conformance" .github/workflows/` → only the
  `ARKADIA_ENGINEERING_TRAJECTORY` line matched (a substring coincidence); no `pytest`
  invocation. The guard ran nowhere.
- `.github/workflows/arkadia-engineering-scheduler.yml` had **no `pull_request` trigger**
  (only `workflow_dispatch` + `schedule`), so a PR that introduced the structural slip
  would merge with the guard unexecuted and the hourly session would fail closed again.
- The pre-existing generalised guard `tests/test_ci_gate_trigger_coverage.py` (39 passed on
  `main`) does **not** catch this class: it only judges workflows that *already run pytest*,
  and the scheduler is selected by `schedule`/`workflow_dispatch`, not by path filters.

A guard no workflow executes is decoration. This is the same defect class the workstream
exists to close — the invariant was asserted but not enforced.

### Fix

1. Added a path-filtered `pull_request` trigger to the scheduler workflow selecting the
   surfaces the guard judges: the workflow itself, `weaver/engineering_router.py`,
   `weaver/engineering_worker.py`, `docs/control-plane/trajectory.schema.json`,
   `docs/control-plane/TRAJECTORY-*.yaml`, and the guard test.
2. Added a `Trajectory-routing conformance guard` step that runs the guard on **every**
   event. On `pull_request` it judges before merge; on the hourly `schedule` it also proves
   the workflow still selects the guard. The runner step is now gated to
   `github.event_name != 'pull_request'` so a PR is never routed as a session.
3. Added two self-selection assertions to the guard:
   `test_scheduler_workflow_selects_this_guard` (the `pull_request` paths filter names the
   test file) and `test_scheduler_workflow_executes_the_guard` (a step actually runs it).
   Because the guard step runs on the schedule too, **removing the trigger fails the next
   hourly session** instead of silently disabling the guard.

The workflow remains `permissions: contents: read` / `actions: read`; no merge, push, or
deploy path is added.

### Measured

- Guard suite: **16 passed** (10 before the CI-live follow-on; 12 after the trigger/step
  addition, before the two PR-safety invariant tests).
- Negative control: stripping the `pull_request` block from the workflow →
  `test_scheduler_workflow_selects_this_guard` **FAILS** with the "runs nowhere" message;
  restoring it → **16 passed**. The detector detects the defect it claims to detect.
- `tests/test_ci_gate_trigger_coverage.py` 42 passed; `tests/test_engineering_scheduler_bootstrap.py`
  and `tests/test_m08_trajectory_schema.py` unchanged and passing.

### CI-live proof (OBSERVED — green on the branch head)

The claim "the guard is CI-live" is a claim about *trigger selection*, and it is now proved by
a **passing job**, not by intent:

- On the branch head `f179d2b`, GitHub created a **`pull_request` run of
  `Arkadia Engineering Scheduler`** (`run 37370596340`, event `pull_request`, created
  `2026-10-05T20:34:35Z`). Before the follow-on this workflow had no `pull_request` trigger,
  so no such run could exist. The trigger selects the workflow.
- The `engineering-scheduler` job is **`completed` / `success`** (`run_attempt` 3, completed
  `2026-10-05T21:24:16Z`). Step 6, *Trajectory-routing conformance guard*, ran and passed —
  the guard is executed in CI, not merely present in the tree. Step 7, *Session + Engineering
  Runner*, was **`skipped`**, proving the `github.event_name != 'pull_request'` gate holds: a
  PR is never routed as a live engineering session.
- The `security-secret-scan` `pull_request` run created at the same second
  (`run 37370596359`) is also `completed` / `success`.
- An **earlier attempt** of the scheduler run was `cancelled` with the annotation *"The job was
  not acquired by Runner of type hosted even after multiple attempts"*. That was a transient
  GitHub-hosted **runner-acquisition** failure, now superseded: the same run object reached
  `success` on attempt 3. It is recorded here so a future pass does not re-derive a
  contradicted "BLOCKED on runner outage" classification from the cancelled attempt alone.

Classification: **OBSERVED (green)** for the guard's CI-liveness on this branch head. This is
a CI observation, not a production-parity or acceptance claim — merge and deploy remain
human-only.

### Blast-radius note (PROPOSED, not executed)

Generalising `tests/test_ci_gate_trigger_coverage.py` to "a workflow that runs pytest must
name every test file it runs in its own path filter" is **not** safe today. Measured:
`sg-02-fe-2-v.yml` names 9 test files absent from its filter and
`prism-execution-workevent-governance.yml` names 4 — but `sg-02-fe-2-v.yml`'s backend step
is `continue-on-error: true` and both workflows currently fail or never run on `main`. The
documented rule is that a gate must stop being baseline-red before its blast radius is
expanded. Recorded as a separate bounded workstream; **not** performed here.
