# WORKSTREAM STATE — gate-hygiene

Pass: `gate-hygiene/scheduler-trajectory-conformance-01`
Reconstructed: 2026-10-05 · BASE_MAIN `451e41a30fcbff4a65326e897a84818cc623b769`

## Current state

| item | evidence |
|---|---|
| canonical clone | `main`, ancestry intact, `origin/main` = `451e41a` (#317) |
| active workstream | gate-hygiene — hourly bounded-execution loop integrity |
| this pass | scheduler trajectory conformance fix + guard, and closure of the guard's CI-inert gap |
| PR | #319 (base `main`), OPEN, MERGEABLE, head `5fee1bc`, CLEAN |
| frontier | G12-A `merged_acceptance_pending` → worker returns `NO_LEGAL_MOVE` (truthful) |

## Defect and fix (measured)

| | pre-fix | post-fix |
|---|---|---|
| trajectory structure | `moves` nested under `trajectory:` | `moves` top-level |
| router result | `ValueError: invalid trajectory structure` | routing decision |
| worker status / exit | `FAILED` / 1 | `NO_LEGAL_MOVE` / 0 |
| guard tests | 4 failed / 12 passed | **16 passed** |
| guard reachability | no workflow executed it (CI-inert) | `pull_request` trigger + step on every event |

## Guard reachability (follow-on, measured)

The §3 guard was CI-inert: a grep of `.github/workflows/` found no `pytest` invocation of
`tests/test_scheduler_trajectory_conformance.py`, and the scheduler workflow had no
`pull_request` trigger. Fixed by adding a path-filtered `pull_request` trigger plus a guard
step that runs on every event, plus two self-selection assertions. Negative control: removing
the trigger makes `test_scheduler_workflow_selects_this_guard` FAIL; restoring it gives 16
passed. The runner step is gated to `github.event_name != 'pull_request'`, so a PR is never
routed as a session.

## Test / baseline fingerprint at this pass

- `tests/test_scheduler_trajectory_conformance.py` — **16 passed** (negative control 4F pre-fix)
- `tests/test_ci_gate_trigger_coverage.py` — **42 passed** on branch (39 on `main`; +3 new
  parametrizations for this workflow, all pass)
- `tests/architecture` — **11 passed** (main's own baseline)
- `python -m py_compile api/main.py` — OK; `api/main.py` untouched (2432 lines)
- CP10 boundary judge on changed paths — **PASS** (exit 0)
- full suite — main `451e41a`: 1005P/69F/48E/20S, 117 nodes, fp `f33d69df…`/`6dde9f16…`
- branch `f179d2b`: 1024P/69F/48E/20S, 117 nodes, same fp; collected 1093→1112 (+19)
- node-set delta `only in main: []`, `only in branch: []` → zero regression

## Environment note

`fastapi` / `pydantic` are **not installed** in this sandbox, so a local full-suite
run cannot exercise the API surface. Recorded, not worked around. CI (with the
installed environment) is the authority for those nodes.

## CI state on #319 (measured)

| check | result | attribution |
|---|---|---|
| engineering-scheduler (`pull_request`) | **success** | run `37379373120` on head `5fee1bc`, **attempt 1**; step 6 guard ran+passed, step 7 session **skipped** — CI-live proof |
| Vercel – arkadia-prism | success | deployment completed on the branch head |
| Vercel – console | fail | provider build error ("Deployment has failed"); also fails on `main` (`451e41a`: "Deployment rate limited") — pre-existing, not attributable to this PR |
| Full-history secret scan | **success** | run `37379373062` on head `5fee1bc`, attempt 1 |
| CP10 / sg-02-fe-2-v | not triggered | path filter did not match this diff |

**CI-live proof for the guard (OBSERVED, green):** on head `5fee1bc` GitHub created a
`pull_request` run of `Arkadia Engineering Scheduler` (`run 37379373120`, attempt 1) that is
**completed/success**: step 6 *Trajectory-routing conformance guard* ran and passed, step 7
*Session + Engineering Runner* was **skipped**, proving a PR is never routed as a live
session. `security-secret-scan` (`37379373062`) is also completed/success on the same head.
Before the follow-on the workflow had no `pull_request` trigger, so no such run could exist.
An earlier `cancelled` attempt belongs to `f179d2b` (`run 37370596340`, *"not acquired by
Runner of type hosted"*) and was a transient hosted-runner acquisition failure; it was
superseded by that run's attempt-3 success and is not a property of the guard or workflow.
Classification: **OBSERVED (green)** for CI-liveness on this head; merge remains human-only.

**Scope of this observation — it binds to head `5fee1bc`, and that is sufficient here.**
The scheduler workflow's `pull_request` path filter covers the workflow file,
`weaver/engineering_router.py`, `weaver/engineering_worker.py`, `docs/control-plane/trajectory.schema.json`,
`docs/control-plane/TRAJECTORY-*.yaml`, and `tests/test_scheduler_trajectory_conformance.py` — **not**
`docs/control-plane/evidence/**`. The commit that adds this paragraph touches only evidence docs,
so it creates no new scheduler run; `security-secret-scan` runs on every `pull_request` and does.

This does **not** make the observation stale, and the reason is checkable rather than assumed:
the guard judges a specific set of surfaces, and the follow-up diff changes none of them.
Verify with

```
git diff --name-only 5fee1bc..<tip>          # only docs/control-plane/evidence/... paths
git diff --stat 5fee1bc..<tip> -- \
  .github/workflows/arkadia-engineering-scheduler.yml \
  weaver/engineering_router.py weaver/engineering_worker.py \
  docs/control-plane/trajectory.schema.json 'docs/control-plane/TRAJECTORY-*.yaml' \
  tests/test_scheduler_trajectory_conformance.py   # empty
```

An empty second diff means the tree the guard judged at `5fee1bc` is byte-identical at the tip,
so the green run remains the governing evidence for the PR. If a future commit touches any of
those surfaces, the `5fee1bc` run becomes `STALE` for it and a fresh run is required.

## Next bounded task

#319 is **READY FOR SOVEREIGN MERGE**: both triggered checks green on head `5fee1bc`,
mergeable/CLEAN, evidence corrected to measured reality, zero regression. The only permitted
next action is human review + merge; no agent merges. On merge, the next heartbeat reconstructs
`main` and the console frontier stays at G12-A acceptance (sovereign authority).

## Proposed, not executed

- **Status-vocabulary divergence** — schema enumerates
  `{pending, revision_required, completed, accepted, blocked, failed, aborted}`;
  the console trajectory uses `merged_acceptance_pending` / `in_progress`, and
  `weaver/engineering_router.py::ACTIVE_STATUSES` accepts `in_progress`. Pre-existing;
  not the cause of the hourly failure; separate bounded workstream.
- **`attention-events.jsonl`** is generated at the repo root by
  `weaver/attention_bus.py` on every worker run and is **untracked/ungitignored**.
  Left uncommitted here; whether it should be gitignored is a separate proposal.
