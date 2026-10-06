# EVIDENCE — gate07/router-schema-vocabulary-closure-01

Trajectory: `ARKADIA-CONSOLE-COMPLETION-01` (in progress)
Move class: bounded engineering guard (no gate promotion, no authority change)
Branch: `gate07/router-schema-vocabulary-closure`
Base: `main` @ `17e626cd27f8ea1e31f711fb787e6c7e5027ec70`
Head: `4b04c4c5605e42d182e49ade0d3100b30e08c36f` (pre-evidence commit)

## Defect

`tests/test_trajectory_schema_conformance.py` guards the seam in one direction
only: `router ⊆ schema` (every status the router acts on is schema-legal). The
reverse direction — `schema ⊆ router` — is asserted nowhere, so the frozen
contract can admit a status the router has no behaviour for and **nothing fails**.

That gap is live. `docs/control-plane/trajectory.schema.json` was refreshed at
`e611edd` ("refresh trajectory status enum + add CI-live schema guard"), adding
`merged_acceptance_pending`, `in_progress` and `merged` to the enum. Four
schema-legal statuses remain absent from the router vocabulary
(`ACTIVE_STATUSES ∪ TERMINAL_DONE`):

| Schema enum (10) | Router vocabulary (6) |
|---|---|
| `pending, revision_required, in_progress, merged_acceptance_pending, completed, accepted, merged, blocked, failed, aborted` | active: `in_progress, pending, revision_required` · terminal: `accepted, completed, merged` |

Unroutable but schema-legal: **`aborted`, `blocked`, `failed`,
`merged_acceptance_pending`**.

This supersedes the predecessor note (`gate07-router-status-truthfulness-01`,
base `451e41a`) which recorded `merged_acceptance_pending` as absent from the
schema enum — true at `451e41a`, false after `e611edd`. The frontier is now
doubly live: `TRAJECTORY-CONSOLE-COMPLETION-01.yaml` carries moves `G12-A` and
`G12-C` at `merged_acceptance_pending` and `G12-B` at `in_progress`.

## Scope — what the guard does and does not demand

The guard pins the **classification** half of the seam, which is what the router
can honestly promise: a status outside the vocabulary is **reported**, not
silently skipped. It does **not** demand the vocabulary be closed — closing it,
or teaching the router these four states, is a sovereign decision. The
truthfulness repair (PR #322) made the skip nameable; this guard keeps it named.

## Non-vacuity (negative control)

Against the pre-fix silent-skip router, **7** guard assertions fail:

```
FAILED ...test_every_schema_legal_status_is_routable_or_named_unroutable[aborted]
FAILED ...test_every_schema_legal_status_is_routable_or_named_unroutable[blocked]
FAILED ...test_every_schema_legal_status_is_routable_or_named_unroutable[failed]
FAILED ...test_every_schema_legal_status_is_routable_or_named_unroutable[merged_acceptance_pending]
FAILED ...test_live_trajectory_frontier_is_unroutable_and_named
FAILED ...test_negative_control_pre_fix_router_would_have_skipped_silently
FAILED ...test_negative_control_future_status_outside_the_schema_is_still_named
7 failed, 10 passed
```

The pre-fix router was reproduced by restoring the silent `continue` and removing
the naming block, then reverting: `weaver/engineering_router.py` is byte-identical
to its committed form (`c355b387c2f3b315cd0564357f4f097da3861043d8f92d34c6bfa7b4be94ac1d`).
Both negative controls are in the failing set, so the guard cannot be satisfied by
reverting to the silent skip nor by hard-coding the four known statuses.

## Test results

| Suite | Result |
|---|---|
| `tests/test_router_schema_vocabulary_closure.py` | **17 passed** |
| Wired CI step command (3 files) | **39 passed** |
| `tests/architecture` | **11 passed** |
| CP10 mutation boundary judge (both new paths) | **PASS** |
| `python -m py_compile api/main.py` | n/a — boot code untouched |

## Baseline comparison (node-set identity, not counts)

Full suite `-rEf --continue-on-collection-errors`, branch vs `main` @ `17e626c` in
a detached worktree:

- failing/error **node sets identical** — 11 nodes, `diff` empty
- node-set `sha256` = `fdc792071b6b4af45ea91782de08992605a04b40ed62ce9d00b771cdf2843cb1`
  on **both** sides
- passed 1601 (branch) vs 1585 (`main`) — **+16 = exactly the new file**
- 10 failed / 1 error is pre-existing environment debt, not attributable to this change

## CI liveness (the point of this move)

Three workflows reach `weaver/engineering_router.py`; only one is a viable host.

- **`weaver-mvp2-validation.yml` — chosen host.** Reaches the router through the
  `weaver/**` glob, so the guard is selected on a router change as well as on its
  own file. The guard is now in **both** the `push` and `pull_request` filters
  (identical sets) and named in the existing router-truthfulness `run:` step.
  Its own `test_guard_is_selected_and_executed_by_a_workflow` asserts trigger
  **and** execution, so the wiring cannot silently rot.
- **`arkadia-engineering-scheduler.yml` — also references the router** (path
  filter + hourly `schedule` + `pull_request`), but hosts only
  `test_scheduler_trajectory_conformance.py` and
  `test_trajectory_schema_conformance.py`. It is a second router-touching
  workflow, not a host for these guards.
- **`provider-routing.yml` — rejected as host.** Reaches the router through
  `weaver/**`, but its path filter does not include the guard file, and its
  full-suite step (`pytest tests/ -q -rEf --continue-on-collection-errors`) is
  pre-existing red at 11-node baseline debt for every PR. A guard hosted there
  could never produce a clean signal.

The first draft of this section claimed the router was "path-filtered out of
every other workflow". That was false and is corrected above — the router is
reached by three workflows, two of them by glob.

## Authorization boundary

Review-gated. No merge, no deploy, no self-authorization, no gate promotion.
Human sovereign merges.
