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
| branch | 1015 | 69 | 20 | 48 | 117 | `f33d69df…` | `6dde9f16…` |

- **Zero regression:** identical outcomes fingerprint and identical failure-node *set*
  (`only in main: []`, `only in branch: []`). The `+10 passed` is exactly the new guard.
- `tests/architecture`: **11 passed** (main's own baseline).
- `python -m py_compile api/main.py`: **OK**; `api/main.py` **untouched** (budget unchanged).
- Baseline debt (69F / 48E) is **pre-existing main debt, recorded not fixed** — it is not
  attributable to this change (fingerprint unchanged).

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
