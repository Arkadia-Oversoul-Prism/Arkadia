# WORKSTREAM STATE — gate-hygiene

Pass: `gate-hygiene/scheduler-trajectory-conformance-01`
Reconstructed: 2026-10-05 · BASE_MAIN `451e41a30fcbff4a65326e897a84818cc623b769`

## Current state

| item | evidence |
|---|---|
| canonical clone | `main`, ancestry intact, `origin/main` = `451e41a` (#317) |
| active workstream | gate-hygiene — hourly bounded-execution loop integrity |
| this pass | scheduler trajectory conformance fix + guard, and closure of the guard's CI-inert gap |
| PR | #319 (base `main`), OPEN, MERGEABLE |
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
| engineering-scheduler (`pull_request`) | **success** | run `37370596340`, `run_attempt` 3; step 6 guard ran+passed, step 7 session **skipped** — CI-live proof |
| Vercel – arkadia-prism | success | deployment completed on the branch head |
| Vercel – console | fail | provider build error ("Deployment has failed"); also fails on `main` (`451e41a`: "Deployment rate limited") — pre-existing, not attributable to this PR |
| Full-history secret scan | **success** | `pull_request` run at 20:34:35Z completed/success (same second as the scheduler run) |
| CP10 / sg-02-fe-2-v | not triggered | path filter did not match this diff |

**CI-live proof for the guard (OBSERVED, green):** on head `f179d2b` GitHub created a
`pull_request` run of `Arkadia Engineering Scheduler` (`run 37370596340`, event
`pull_request`, created `2026-10-05T20:34:35Z`). Before the follow-on this workflow had no
`pull_request` trigger, so that run could not exist. The `engineering-scheduler` job is
**completed/success** on `run_attempt` 3 (completed `2026-10-05T21:24:16Z): step 6,
*Trajectory-routing conformance guard*, ran and passed; step 7, *Session + Engineering
Runner*, was **skipped**, proving the PR never routes as a live session. An earlier attempt
was `cancelled` ("not acquired by Runner of type hosted") — a transient hosted-runner
acquisition failure, superseded by the success on attempt 3. Classification: **OBSERVED
(green)** for CI-liveness on this head; merge remains human-only.

## Next bounded task

Sovereign review of #319 (human-only merge). On merge, the next heartbeat
reconstructs `main` and the console frontier stays at G12-A acceptance — that
remains sovereign authority, not an engineering move.

## Proposed, not executed

- **Status-vocabulary divergence** — schema enumerates
  `{pending, revision_required, completed, accepted, blocked, failed, aborted}`;
  the console trajectory uses `merged_acceptance_pending` / `in_progress`, and
  `weaver/engineering_router.py::ACTIVE_STATUSES` accepts `in_progress`. Pre-existing;
  not the cause of the hourly failure; separate bounded workstream.
- **`attention-events.jsonl`** is generated at the repo root by
  `weaver/attention_bus.py` on every worker run and is **untracked/ungitignored**.
  Left uncommitted here; whether it should be gitignored is a separate proposal.
