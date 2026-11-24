# ARK-OPS-CONTINUOUS-001 — cycle 06

**Contract:** `ARK-OPS-CONTINUOUS-001`, rev 2026-11-22.
**Authority:** human-governed, evidence-bounded, fail-closed. `MERGE_AUTHORITY := NONE`,
`DEPLOY_AUTHORITY := NONE`. This cycle contains no merge, no push to `main`, no deployment,
and claims no acceptance.
**Observation window:** 2026-11-24T03:06Z onward.

---

## 1. Reconstructed state (live, at cycle start)

| item | measured | source |
|---|---|---|
| canonical `main` | `bb19aabda34d59594615b0279a45e9cbd3d8204d` | `GET /git/ref/heads/main` |
| local checkout | `bb19aabd…`, `main`, clean, **not** shallow | `git rev-parse`, `git status` |
| local vs remote | `0` ahead / `0` behind | `git rev-list --count` both directions |
| open PRs | **34**, every one a draft, every one `base: main`, `MERGEABLE` | `gh pr list --state open` |
| obsolete open PRs | **0** | per-PR file inventory + prior-cycle classification |
| production revision | `source_revision` = `bb19aabd…`, `revision_conflict: false` | `GET /api/version` (HTTP 200) |

Production source-to-runtime consistency is **VERIFIED** (necessary evidence, not sufficiency —
the endpoint says so itself).

`main` is therefore unchanged since cycles 01–05. No merge has been executed by an agent.

## 2. New verified negative: the console's endpoint registry is fully served

Not measured by any prior cycle. The console's `src/lib/endpoints.ts` is the single API surface
map; its own header claims the paths are read from the deployed application.

```
served OpenAPI paths (production)                : 300
declared endpoints in endpoints.ts               : 45
declared endpoints absent from served OpenAPI    : 0
```

Inline path literals outside the registry: **27**, of which **1** is not served —
`/api/codex/categories`. That one is not a drift defect: the console carries a *positive control*
asserting it is **not** served (`tests/test_console_spiral_codex_contract.py`), which flips if the
route is ever implemented. Classified: documented absence, not a gap.

## 3. Gap found and closed: an async route blocking the single event loop

The canonical runtime serves the whole application from **one** Uvicorn worker, so every
`async def` handler shares one event-loop thread. A synchronous HTTP client called inside an
`async def` route blocks that thread for the whole request.

Discovery, two independent oracles agreeing:

```
$ ruff check --select ASYNC --output-format concise api lab weaver
api/lab_routes.py:648:14: ASYNC210 Async functions should not call blocking HTTP methods

$ <AST scan: every async route handler x every blocking client call>
api/lab_routes.py:648  async route pr_state() calls blocking urlopen()
total: 1
```

Exactly one offender across the tracked `api/` corpus: `api/lab_routes.py::pr_state`
(`GET /api/lab/engineering/pr/{number}`, EL-10) called
`urllib.request.urlopen(..., timeout=10)` directly inside `async def`. One operator opening the
Lab PR-state panel could stall the entire deployment — liveness probe and every page load — for up
to ten seconds. Ruff flagged the same line, but **no CI gate runs ruff**, so nothing prevented the
next instance.

### Repair (behaviour-preserving)

The blocking GET moved to a module-level sync helper and is offloaded with `asyncio.to_thread`:

```python
def _read_json_url(req: urllib.request.Request, timeout: float) -> dict:
    """Blocking GET. Callers must offload it — the server runs one event loop."""
    import json
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())
...
        data = await asyncio.to_thread(_read_json_url, req, 10)
```

`asyncio.to_thread` was chosen over converting the handler to `def` because the route's projection
tests drive it as a coroutine (`asyncio.run(lab_routes.pr_state(623))`). Converting the handler
would have required editing `tests/test_prism_w4_lab_pr_state.py`, which open PR #683 owns;
offloading keeps every existing pin intact (`25 passed`, §5).

No authorization, response shape, key set, or status code changed. `api/main.py` was not touched
(budget unaffected).

## 4. The guard is a class guard, not a literal pin

`tests/test_async_route_blocking_io_contract.py` (7 tests) derives its subject from
`git ls-files -- api/**/*.py` **at test time**, parses each module with `ast`, and reports every
`AsyncFunctionDef` carrying a route decorator whose body calls `urllib.request.urlopen` /
`urlretrieve` or `requests.<verb>` without an offload wrapper.

It does **not** flag: a plain `def` helper (already off the loop), an `await`ed async client, or
anything inside `asyncio.to_thread` / `run_in_executor`. Both polarities are controls:

| control | asserts |
|---|---|
| `test_detector_flags_the_repaired_shape` | the pre-repair handler, verbatim, is reported as `("pr_state", 5, "urlopen")` |
| `test_detector_flags_a_synchronous_requests_client` | `requests.post` in an async route is reported |
| `test_detector_is_silent_on_offloaded_and_awaited_calls` | the repair shape and an awaited `httpx.AsyncClient` pass |
| `test_detector_ignores_a_synchronous_helper_outside_a_route` | a `def` helper is not flagged |
| `test_the_tracked_corpus_is_what_the_guard_believes_it_is` | the derived domain is non-trivial (a guard over an empty domain would pass for the wrong reason) |

### Live negative control (the real file, not a fixture)

```
$ # revert the source line only, on the working tree
  pytest tests/test_async_route_blocking_io_contract.py -q
E  AssertionError: api/lab_routes.py:657 async route pr_state() calls blocking urlopen();
                   offload it with asyncio.to_thread
E  assert 'await asyncio.to_thread(_read_json_url' in source
FAILED ...::test_api_async_routes_do_not_block_the_event_loop
FAILED ...::test_the_guarded_handler_is_offloaded_where_it_runs

$ # restore byte-identically
  pytest tests/test_async_route_blocking_io_contract.py -q
7 passed in 0.21s
```

Execution in CI: this change touches `api/lab_routes.py`, a named trigger path of
`.github/workflows/sg-02-fe-2-v.yml`, whose CP10-B step runs
`pytest tests/ -q --continue-on-collection-errors`; the guard is therefore executed by that gate
for this revision. (For a future `tests/`-only change, the broader "177 files reached only through
a broad-suite step" limitation stands as already recorded — unchanged by this cycle.)

## 5. Verification (measured, this tree)

| check | result |
|---|---|
| `python -m py_compile api/lab_routes.py` | PASS |
| `pytest tests/architecture -q` | **11 passed** |
| `pytest tests/test_prism_w4_lab_pr_state.py tests/test_engineering_lab_api.py -q` | **25 passed** |
| `pytest tests/test_console_endpoint_registry_contract.py` + lab pr-state + engineering-lab api/substrate | **84 passed** |
| `pytest tests/test_async_route_blocking_io_contract.py -q` | **7 passed** |
| mutation boundary (`cp10_mutation_boundary_policy.py --judge` on both changed paths) | **PASS** |
| full suite `pytest tests/ -q -rEf --continue-on-collection-errors` | `19 failed, 4250 passed, 22 skipped, 1 error` in 289.93 s |

**Failing/error node set: 20 nodes, sha256 `8d70e46e6f076049cacd8bdf16feeb42c6c078377d9d350e6bfbe1a8de4beceb`.**
That is the recorded `main` baseline hash from cycles 01–05 — the node set is **identical**, so
this change introduces no regression and repairs no pre-existing node.

Attribution of the 20, unchanged from cycle 05 and re-confirmed here:

| node(s) | owner |
|---|---|
| `ERROR tests/test_autonomy.py` | sovereign-reserved (CE-01 module-vs-package) |
| `tests/test_ais_w2_living_gate_grove_handoff.py::…` | sovereign-reserved (FINDING F-01) |
| `test_identity_spine_w1`, `test_m02_reasomate_truth` (2) | open #700 |
| `test_m01_persistence`, `test_m05_files` (2) | open #690 |
| `test_solspire_r1_governance_convergence` (2) | open #693 |
| `test_solspire_r3_execution_runtime` (1) | open #691 |
| `test_static_ingestion_idempotency` (1) | open #698 |
| `test_mission_lifecycle_adapter_contract` (10) | **environment-only** — `web/arkadia_console/node_modules/typescript` is absent in this sandbox (verified), CI provisions it |

The `+7 passed` over a bare `main` run is exactly the new guard file; `--collect-only` on that file
reports 7 nodes.

## 6. Housekeeping

The full suite leaves an untracked `data/engineering_lab/agent_events.jsonl`. It was deleted, not
staged; sandboxing it is open PR #688's scope.

`ruff` was installed in this sandbox as a *discovery tool only*. It is not added to
`requirements.txt` and not added to any gate.

## 7. Next-action block

**Current state.** `main` = `bb19aabda34d59594615b0279a45e9cbd3d8204d`, deployment identical,
34 open drafts, 0 obsolete. This cycle adds one branch on top of `main`: one behaviour-preserving
repair and one class guard. `main` is unmodified.

**Evidence.** Sections 1–6; every command above is reproducible as written.

**Blockers.** (a) Merge execution is human-only (GOV-03); 34 drafts await human review.
(b) CE-01 and FINDING F-01 are reserved to the sovereign. (c) The anonymous
`/api/webhook/github` posture is sovereign-gated. (d) The `tests/`-only trigger gap for the
broad-suite step is a recorded workstream, not repaired here.

**Authorized next action.** A human reviews the queue for merge. A later cycle may re-measure the
baseline as the queue moves, or take up a newly measured, non-reserved defect.

**Forbidden.** Merging; pushing to `main`; force-pushing; deploying; bypassing protection or
required checks; weakening a guard to manufacture green; repairing CE-01 / F-01 / the webhook
posture without a sovereign decision.

**Completion condition.** This cycle is complete when this record and its PR are reviewable, with
`main` unmodified and no merge, deployment or acceptance claimed.
