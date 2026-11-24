# ARK-OPS-CONTINUOUS-001 — cycle 07

_Recorded by an AI agent (OpenHands) on behalf of the repository sovereign. This cycle performs no
merge, no deployment and claims no acceptance. Merge execution is human-only under GOV-03._

Superseding contract: `docs/control-plane/openhands/hourly-weaver/2026-11-22-continuous-reconciliation-contract.md`
(open PR #705). This file is the resumption surface for the next cycle.

## 1. Reconstruction (live sources, 2026-11-24 ~04:05–04:20 UTC)

| fact | measured value |
|---|---|
| canonical `main` | `bb19aabda34d59594615b0279a45e9cbd3d8204d` (`git rev-parse origin/main` after `git fetch`) |
| production `GET /api/version` | `source_revision` = `bb19aabd…`, `revision_source` = `RENDER_GIT_COMMIT`, `revision_conflict: false` → source↔runtime consistent |
| open pull requests | **35**, all `isDraft: true` (`gh pr list --limit 100 --json isDraft`) |
| branch protection on `main` | `GET /branches/main/protection` → **404 "Branch not protected"** (recorded, not changed) |
| CI on `main` head | no non-`skipped` failing check-runs at `bb19aabd` |
| deployment shape | `entrypoint.sh` → `exec uvicorn api.main:app …` with **no `--workers`** → one process, one event loop |

The deployment shape matters for this cycle: on a single-worker process, an `async def` route that
blocks occupies the only loop, so it delays *every* concurrent request, including the liveness probe.

## 2. The gap that was measured

`solspire/console_router.py` is mounted into the canonical app (`api/main.py:330-331`, prefix
`/solspire`). Ten of its route handlers were declared `async def` while performing blocking work
directly or through a synchronous callee:

| handler | route | blocking work | worst case |
|---|---|---|---|
| `run_request` | `POST /solspire/run` | `_execute_run` → `time.sleep(0.25)` poll loop | **60 s** |
| `project_run` | `POST /solspire/projects/{id}/run` | same `_execute_run` | **60 s** |
| `github_repos` | `POST /solspire/tools/github/repos` | `tools_github.list_repos` → `httpx.get` | request timeout |
| `github_tree` | `POST /solspire/tools/github/tree` | `tools_github.get_tree` → `httpx.get` | request timeout |
| `github_read` | `POST /solspire/tools/github/read` | `tools_github.read_file` → `httpx.get` | request timeout |
| `create_project` | `POST /solspire/projects` | `subprocess.run` | unbounded |
| `instantiate_eden_project` | `POST /solspire/projects/instantiate-eden` | `subprocess.run` | unbounded |
| `project_integration_health_route` | `GET /solspire/projects/{id}/integration-health` | `subprocess.run` | unbounded |
| `project_weaver_bind_pass_spec` | Weaver bind-pass | `subprocess.run` | unbounded |
| `project_weaver_execute` | Weaver execute | `subprocess.run` | unbounded |

`github_commit` is **not** in the set: `tools_github.commit_file` is a pure refusal (`MUTATION_DISABLED`)
with no I/O, so it was left `async def` — the repair is bounded to measured offenders.

Measured detector output on the pre-repair blob (`git show main:solspire/console_router.py`):

```
PRE-REPAIR offenders: 10
   solspire/console_router.py:1122 project_run() -> ['time.sleep']
   solspire/console_router.py:1318 project_weaver_bind_pass_spec() -> ['subprocess.run']
   solspire/console_router.py:1348 project_weaver_execute() -> ['subprocess.run']
   solspire/console_router.py:194 run_request() -> ['time.sleep']
   solspire/console_router.py:233 create_project() -> ['subprocess.run']
   solspire/console_router.py:246 instantiate_eden_project() -> ['subprocess.run']
   solspire/console_router.py:442 github_repos() -> ['httpx.get']
   solspire/console_router.py:447 github_tree() -> ['httpx.get']
   solspire/console_router.py:452 github_read() -> ['httpx.get']
   solspire/console_router.py:681 project_integration_health_route() -> ['subprocess.run']
POST-REPAIR offenders: []
```

The class is wider than this one file. Measured over the whole tracked router corpus (36 modules that
construct an `APIRouter`), interprocedurally including imported sync helpers:

```
api/economic_seam_routes.py:23 scan() -> ['requests.get']
api/lab_routes.py:233 execute_bounded() -> ['subprocess.run']
api/lab_routes.py:636 pr_state() -> ['urlopen']            # repaired by open PR #712
api/lab_routes.py:736 run_agent_loop() -> ['subprocess.run']
api/plan_routes.py:23 run_plan() -> ['httpx.Client']
solspire/console_router.py (10 rows above)
```

Those five are **recorded, not repaired here** — see §7.

## 3. The repair

Ten `async def` → `def` in `solspire/console_router.py` (no behavioural change to any response
shape, status code or `Depends`): Starlette runs a `def` handler in the threadpool, so the blocking
work leaves the event loop. `require_auth` / `require_project_owner` are async dependencies and
FastAPI resolves them for sync and async handlers alike.

Two comments record *why* the handlers are sync, because "modernise" to `async def` would silently
restore a 60-second stall.

No authorization, response shape, key set or status code changed. `api/main.py` is untouched.

## 4. The guard

`tests/test_solspire_router_async_blocking_io_contract.py` (9 nodes). A class guard, not a pin on the
ten repaired lines:

- **Domain derived at test time** from `git ls-files -- 'solspire/*.py' 'solspire/**/*.py'`, filtered
  to modules that construct an `APIRouter` — a router added anywhere under `solspire/` is judged
  without editing the guard.
- **Interprocedural**: blocking work is followed through same-module sync callees *and*
  `from X import f` imports (`solspire.tools_github.get_tree` is reached cross-module), to depth 4.
- **Predicate**: `time.sleep`, `urllib` `urlopen`/`urlretrieve`, `requests.<verb>`, `httpx.<verb>`,
  `subprocess.<runner>`, `socket.create_connection`, and HTTP verbs on a sync client bound in the
  same function. Awaited calls and calls handed to `asyncio.to_thread` / `run_in_threadpool` /
  `run_in_executor` are excluded.
- **Both polarities proved by controls**: the pre-repair shape, a direct `requests.get`, a
  `requests.Session()` instance and the real cross-module `tools_github` helper must all be reported;
  the offloaded/awaited shape and the repaired `def` shape must be silent.
- **Domain-size assertion** (`≥5` router modules, `≥40` routes) so a broken derivation cannot make
  the invariant vacuous.
- A direct pin that `run_request` and `project_run` are `def` — the two 60-second offenders.

### Live negative control on the real file

```
$ # revert only the source line: `def run_request(` → `async def run_request(`
FAILED tests/test_solspire_router_async_blocking_io_contract.py::test_no_solspire_async_route_blocks_the_event_loop
FAILED tests/test_solspire_router_async_blocking_io_contract.py::test_the_run_pipeline_routes_are_synchronous
2 failed, 7 passed in 3.92s

$ # restore byte-identically
9 passed in 3.87s
```

## 5. The wiring (a guard no gate executes is decoration)

The guard's subject is `solspire/**`, so it is executed by the gate that already selects
`solspire/console_router.py`: `.github/workflows/solspire-project-execution.yml`.

- `pull_request.paths` gains `solspire/**` (the guard's whole domain, not one file) and the guard
  path; `solspire/console_router.py` was already selected.
- the `Unit and contract gates` step now runs the guard. The step was reformatted to one argument
  per line — same five files, plus the new one — so the next addition is not a 250-character edit.
- **Blast-radius control**: the five pre-existing files in that step are green on `main`
  (`28 passed, 3 skipped` in a clean `main` worktree) *before* widening the filter, so the newly
  selected paths cannot inherit a pre-existing red.

## 6. Verification (measured on this tree)

| check | result |
|---|---|
| `python -m py_compile solspire/console_router.py` + guard | PASS |
| guard alone | **9 passed** |
| gate step (6 files, as CI runs it) | **37 passed, 3 skipped** |
| `pytest tests/architecture -q` | **11 passed** |
| gate-domain guards (`m02a_ci_gate_integrity`, `ci_gate_trigger_coverage`, `prism_console_ci_wiring`, `economic_seam_ci_wiring`) | **230 passed** |
| `-k "solspire or opportunity or workevent or weaver_w4"` | `3 failed, 424 passed, 4 skipped, 1 error` — the 3 failures reproduce **identically on a clean `main` worktree** (`3 failed, 5 passed` in the two files), so they are pre-existing, not attributable |
| CP10 mutation boundary judge on all four changed paths | **PASS** |
| full suite `pytest tests/ -q -rEf --continue-on-collection-errors` | `19 failed, 4259 passed, 22 skipped, 1 error` in 289.54 s |
| canonical fingerprint (`scripts/baseline_fingerprint.py`) | **20 nodes**, outcomes `8d70e46e6f076049cacd8bdf16feeb42c6c078377d9d350e6bfbe1a8de4beceb`, ids `d6101722f624c0eedb48a957375f0b8abbef398f20e93e55e889dd8d9e0893ce` |

**Zero regression.** The 20-node failing/error set is byte-identical to the recorded `main`
baseline for cycles 01–06, and the `+9 passed` (4250 → 4259) is exactly the new guard file, measured
by `--collect-only` rather than inferred from the delta.

Note on convention: an earlier hand-rolled `grep`/`sed` extraction produced a 20-node hash of
`c2af8227…` because it kept pytest's truncated ` - TypeError: …` suffix on one node. The canonical
`scripts/baseline_fingerprint.py` strips that suffix and yields `8d70e46e…`. The tool's value is
exactly this: a fingerprint must be re-derivable by an independent operator.

Failing nodes are the same 20 attributed in cycles 05–06: CE-01 (`tests/test_autonomy.py`,
sovereign-reserved), FINDING F-01 (`test_ais_w2_living_gate_grove_handoff.py`, sovereign-reserved),
ten `test_mission_lifecycle_adapter_contract` nodes (environment-only: `web/arkadia_console/node_modules/typescript`
is absent in this sandbox and provisioned by CI), and eight owned by open PRs #700, #690, #693,
#691, #698.

## 7. Measured, not repaired — the rest of the class

The detector reports five further offenders outside this cycle's bounded slice. They are recorded
here rather than silently dropped, and rather than repaired opportunistically:

| offender | reason not repaired in this cycle |
|---|---|
| `api/lab_routes.py::pr_state` | already repaired by open PR #712 (with its own `api/`-only guard); touching the same function would compete with that PR |
| `api/lab_routes.py::execute_bounded`, `::run_agent_loop` | same file as #712 — composition hazard; `api/lab_routes.py` is an authority surface in `LAYER_MAP.py` |
| `api/economic_seam_routes.py::scan` | different lane; needs its own bounded change |
| `api/plan_routes.py::run_plan` | `await request.json()` in the body, so it needs an `asyncio.to_thread` repair around the `httpx.Client` call, not a sync conversion — a different repair shape and its own control |

A follow-on cycle can take these, one bounded slice at a time. Two guards now cover the class
partially (`api/` from #712, `solspire/` from this cycle); folding them into one whole-corpus guard
is proposed, not performed, because it would require editing a file #712 owns.

## 8. Next-action block

**Current state.** `main` = `bb19aabda34d59594615b0279a45e9cbd3d8204d`, production deployment
reports the same revision. 35 open PRs, all drafts. This cycle adds one branch on top of `main`:
ten behaviour-preserving handler conversions, one class guard, one gate wiring change, this record.
`main` is unmodified.

**Evidence.** §1–§7; every command above is reproducible as written.

**Blockers.** (a) Merge execution is human-only (GOV-03); the draft queue awaits human review.
(b) CE-01 and FINDING F-01 are sovereign-reserved. (c) The anonymous `/api/webhook/github` posture is
sovereign-gated. (d) The five remaining class offenders in §7 each need their own bounded change.

**Authorized next action.** A human reviews the queue for merge. A later cycle may re-measure the
baseline as the queue moves, take up one of the §7 slices, or take a newly measured, non-reserved
defect.

**Forbidden.** Merging; pushing to `main`; force-pushing; deploying; bypassing protection or required
checks (note `main` is *currently* unprotected — recording that is not authorization to exploit it);
weakening a guard to manufacture green; repairing CE-01 / F-01 / the webhook posture without a
sovereign decision; editing `api/lab_routes.py` while PR #712 owns it.

**Completion condition.** This cycle is complete when this record and its PR are reviewable, with
`main` unmodified and no merge, deployment or acceptance claimed.

## 9. Addendum — CI execution measured at the PR head (PR #713, draft)

Measured after the push, on head `17ddae2e60f700e4c685d40817ba595a483a03d5`.

| check | result |
|---|---|
| `boundary` (job in `solspire-project-execution.yml` — the gate that selects `solspire/console_router.py`) | **completed / success**, 44 s |
| its `Unit and contract gates` step log | names `tests/test_solspire_router_async_blocking_io_contract.py` and reports **`38 passed, 2 skipped`** — the guard is executed, not merely mentioned |
| `Full-history secret scan`, `boot-syntax`, `console-contract`, `router-composition`, `test` (economic-seam), `trigger-coverage`, `verdict-step-integrity`, `security-metadata`, `posture-currency`, `provider-forensics`, `mvp2-validation`, beta evidence jobs | **success** |
| `native-arkadia-golden-workflow` | **failure** — external provider, not the tree: `ModelUnavailable: N-ATLaS Gradio runtime …`, HTTP 503. Same intermittent class recorded on #700, #693, #696, #712; the job reads a live external model, so it is never evidence about this repository's tree, and this change touches no provider code. |

Convention note: the CI skip count (2) and the sandbox skip count (3) differ by one
docker-dependent test in `tests/solspire/test_live_container_execution.py`; passed totals move with
the environment, so the invariant is still the failing/error **node set**, not the totals.

PR state at this measurement: `draft: true`, `MERGEABLE` / `UNSTABLE` (the external-provider job),
head `17ddae2e`. `main` remains `bb19aabda34d59594615b0279a45e9cbd3d8204d` — unmodified. No merge, no
deployment, no acceptance claimed.
