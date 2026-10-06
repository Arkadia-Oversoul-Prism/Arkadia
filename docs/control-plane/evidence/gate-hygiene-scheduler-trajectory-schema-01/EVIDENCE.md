# EVIDENCE — gate-hygiene/scheduler-trajectory-schema-01

Bounded objective: make the scheduler's trajectory conformance guard **CI-live and
non-skippable**, and reconcile the frozen trajectory schema with the status
vocabulary the router and the live trajectories actually use.

Reconstructed: 2026-10-05 · BASE_MAIN `451e41a30fcbff4a65326e897a84818cc623b769`
Stacked on PR #319 head `3d1829db87ee2e436354002842c9586e7bd58350`.

## 1. Defect (measured, not inferred)

Three surfaces must agree on a move's `status` vocabulary. They did not:

| surface | statuses |
|---|---|
| `docs/control-plane/trajectory.schema.json` (frozen contract) | `pending, revision_required, completed, accepted, blocked, failed, aborted` |
| `weaver/engineering_router.py` `ACTIVE_STATUSES` | `pending, revision_required, **in_progress**` |
| `weaver/engineering_router.py` `TERMINAL_DONE` | `completed, accepted, **merged**` |
| live `TRAJECTORY-CONSOLE-COMPLETION-01.yaml` | `merged_acceptance_pending`, `in_progress`, `merged_acceptance_pending` |

`merged_acceptance_pending` and `in_progress` were both **outside** the schema enum,
and `merged` was a router terminal status the schema did not admit. The router's own
vocabulary was therefore not schema-legal.

Measured with the new guard's reader against the **original** enum (negative control):

```
TRAJECTORY-ARKADIA-TRUTHFULNESS-01.yaml:  10 moves; 0 violations
TRAJECTORY-CONSOLE-COMPLETION-01.yaml:     6 moves; 3 violations
    -> G12-A merged_acceptance_pending
    -> G12-B in_progress
    -> G12-C merged_acceptance_pending
```

## 2. Why the divergence reached `main`

The only test that validated a trajectory against the schema,
`tests/test_m08_trajectory_schema.py`, is gated on `jsonschema`, which is **absent**
from `requirements.txt` and from the environment (`ModuleNotFoundError: No module
named 'jsonschema'`). The test therefore *skips*, and the schema was never enforced.
A conformance check that can be skipped for a missing install is decoration.

The sibling guard added by PR #319 (`tests/test_scheduler_trajectory_conformance.py`)
proves *structure* (the `moves` list is top-level and router-loadable) but never reads
the schema enum, so a structurally valid trajectory with an out-of-enum status passed.

## 3. Fix

1. `docs/control-plane/trajectory.schema.json` — extend the move `status` enum with
   `in_progress`, `merged_acceptance_pending`, and `merged`. The enum now covers the
   union of the router vocabulary and the statuses the live trajectories use. No status
   was removed; this is a superset of the previous enum.

2. `tests/test_trajectory_schema_conformance.py` (new) — a **stdlib-only** guard. It
   reads the JSON schema with `json` and extracts move statuses with a small YAML
   reader, so it needs neither `jsonschema` nor `pyyaml` and runs under
   `pip install pytest` alone. It asserts two invariants:
   - the router's `ACTIVE_STATUSES | TERMINAL_DONE` is a subset of the schema enum;
   - every move `status` in every `docs/control-plane/TRAJECTORY-*.yaml` is in the enum.

   Three negative controls prove the reader detects the defect it claims to detect:
   an out-of-enum status is surfaced; multiple moves are read; a `moves` list nested
   under `trajectory:` is **not** mistaken for the canonical top-level list.

3. `.github/workflows/arkadia-engineering-scheduler.yml` — add the new guard to the
   `pull_request` path filter and execute it in a step on every event, beside the
   PR #319 guard. The scheduler's own bootstrap guard
   (`tests/test_ci_gate_trigger_coverage.py`) then requires the workflow to be
   selected by the surfaces it judges — including the schema the guard reads.

## 4. Verification

| check | result |
|---|---|
| `pytest tests/test_trajectory_schema_conformance.py` | **6 passed** |
| `pytest tests/test_trajectory_schema_conformance.py tests/test_scheduler_trajectory_conformance.py tests/test_ci_gate_trigger_coverage.py tests/test_engineering_scheduler_bootstrap.py tests/test_m08_trajectory_schema.py tests/test_m02a_ci_gate_integrity.py` | **144 passed, 1 skipped** (the skip is the `jsonschema`-gated M08 test — the gap this guard closes) |
| `pytest tests/architecture -q` | **11 passed** |
| `scripts/cp10_mutation_boundary_policy.py --judge` on the changed paths | **PASS** |
| guard vs **original** enum (negative control) | 3 violations detected — the guard has teeth |

### Regression boundary (node-set, not counts)

Full suite on the branch vs its base `3d1829d`, both with
`pytest tests/ -q --continue-on-collection-errors -rEf`:

```
base   (3d1829d): 117 nodes  outcomes f33d69dfbc1d91761e94fe469ea0da02565d9670222989aaec97457d634f2169
branch (this PR): 117 nodes  outcomes f33d69dfbc1d91761e94fe469ea0da02565d9670222989aaec97457d634f2169
NEW: none    FIXED: none
```

The failure/error **node set is byte-identical**; zero regression. The 117 nodes are
pre-existing environmental debt (no `jsonschema`; the CE-01 `weaver.autonomy`
module-vs-package collision), not attributable to this change.

## 5. Uncertainty / not claimed

- No runtime or production claim. This is a repository-source + local-test claim.
- `tests/test_m08_trajectory_schema.py` still skips without `jsonschema`. The new
  guard covers its invariant for the move-status enum; a full `jsonschema` structural
  validation remains skipped. Installing `jsonschema` is a separate dependency
  decision, not taken here.
