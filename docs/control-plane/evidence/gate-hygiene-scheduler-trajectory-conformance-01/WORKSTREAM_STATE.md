# WORKSTREAM STATE — gate-hygiene

Pass: `gate-hygiene/scheduler-trajectory-conformance-01`
Reconstructed: 2026-10-05 · BASE_MAIN `451e41a30fcbff4a65326e897a84818cc623b769`

## Current state

| item | evidence |
|---|---|
| canonical clone | `main`, ancestry intact, `origin/main` = `451e41a` (#317) |
| active workstream | gate-hygiene — hourly bounded-execution loop integrity |
| this pass | scheduler trajectory conformance fix + guard, and closure of the guard's CI-inert gap |
| PR | #319 (base `main`), OPEN, MERGEABLE, CLEAN; head moves with each push |
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
| engineering-scheduler (`pull_request`) | **success** | attempt 1 on every head so far (`37379373120`@`5fee1bc`, `37379631218`@`ac5e4d5`); step 6 guard ran+passed, step 7 session **skipped** — CI-live proof |
| Vercel – arkadia-prism | success | deployment completed on the branch head |
| Vercel – console | fail | provider build error ("Deployment has failed"); also fails on `main` (`451e41a`: "Deployment rate limited") — pre-existing, not attributable to this PR |
| Full-history secret scan | **success** | attempt 1 on every head (`37379373062`@`5fee1bc`, `37379631232`@`ac5e4d5`) |
| CP10 / sg-02-fe-2-v | not triggered | path filter did not match this diff |

**CI-live proof for the guard (OBSERVED, green).** Before the follow-on, the scheduler
workflow had no `pull_request` trigger, so no such run could exist. It now fires on every push
to this branch and has been green on each head observed:

| head | scheduler run | guard step 6 | session step 7 |
|---|---|---|---|
| `f179d2b` | `37370596340` success (attempt 3) | success | skipped |
| `5fee1bc` | `37379373120` success (attempt 1) | success | skipped |
| `ac5e4d5` | `37379631218` success (attempt 1) | success | skipped |

Step 7 *Session + Engineering Runner* being `skipped` on every run is what proves a PR is never
routed as a live session. `security-secret-scan` is also success on every head
(`37370596359`, `37379373062`, `37379631232`). On `f179d2b` an earlier attempt was `cancelled`
(*"not acquired by Runner of type hosted"*) — a transient hosted-runner acquisition failure,
superseded by that run's attempt-3 success and not a property of the guard or workflow.

**Correction — the trigger fires on every push, including docs-only.** An earlier version of
this section reasoned that a docs-only follow-up would not re-trigger the scheduler, because
`docs/control-plane/evidence/**` is absent from the workflow's `pull_request` path filter.
**Measured, that is false:** the docs-only commit `ac5e4d5` produced run `37379631218`. A
`pull_request` path filter is evaluated against the **whole PR diff**, not the single pushed
commit. The governing evidence is therefore the run for the *current* head, re-read each pass —
never an earlier head's green carried forward.

Classification: **OBSERVED (green)** for CI-liveness; merge remains human-only.

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
