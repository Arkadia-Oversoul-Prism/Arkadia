# AEAS-01 · P0.5 — Native agent dispatch (model-backed worker through an adapter contract)

**Status: IMPLEMENTED AND VERIFIED — provider dispatch `UNAVAILABLE`, `LIVE` NOT CLAIMED**

| Field | Value |
| --- | --- |
| Date | 2026-10-30 |
| Branch | `feat/aeas-01-p05-agent-dispatch` |
| Starting revision | `b0945011` (= PR #591 head `feat/dea-01-mission-state-guard-01`) |
| Authorization | Issue #590, comment `6512665071` (separate reviewable branch; no merge, no deployment, no production change) |
| Predecessors | P0.3 repository observation (PR #592, merged `776766b9`); P0.4 bounded test execution (PR #593, open) |

## 1. Objective and non-goals

Connect the existing `run-agent` route to the mission workspace through a provider-neutral
adapter, so a human-authored mission can be dispatched to an actual worker and its reasoning,
tool activity, events and outcome are observable and attributable to that mission.

Non-goals, held throughout: no merge, no deployment, no production configuration; no
unrestricted shell; no widening of the L1 terminal grammar; no autonomous git mutation; and
**no `test` capability for `run-agent`** — the two capabilities remain independently authorized.

## 2. What changed

| Path | Change |
| --- | --- |
| `lab/engineering_lab/gateway.py` | `ModelDescriptor` gains `adapter_bound` and `dispatchable`; `describe()` now composes configuration truth (`_describe_configuration`) with binding truth; `get_gateway()` binds `OllamaAdapter` **from configuration** (`OLLAMA_BASE_URL`/`OLLAMA_HOST`) instead of leaving it dead code. No adapter class or generate signature changed — the `ModelAdapter.generate` contract is untouched. |
| `lab/engineering_lab/runtime.py` | `execute_agent_loop` result carries `loop_state`, `loop_reason`, `effective_tools`, `provider`, `model`, so the outcome is legible without opening evidence rows. |
| `tests/test_engineering_lab_dispatch_truth.py` | New, 12 nodes: availability≠dispatchability, config-driven binding, fail-closed generation, `BLOCKED` with reason and no invented turns, granted envelope, event attribution, and four `test`-vs-`run-agent` boundary nodes. |
| `web/arkadia_console/src/components/lab/missionContract.ts` | `run-agent` added to the session action union; `dispatchWorker()`, `LabDispatchResult`, `LabDispatchTurn`, `LabGatewayView`, `getGatewayView()` — all composed from the `endpoints.ts` registry, no raw `/api/` literals. |
| `web/arkadia_console/src/components/lab/LabWorkerDispatch.tsx` | New console panel: gateway catalog with `status` and `dispatchable` shown as separate columns, dispatch button gated on an authorized session, rendering of `loop_state`/`loop_reason`/`effective_tools`/turns. |
| `web/arkadia_console/src/components/lab/MissionWorkspace.tsx` | Mounts the panel (gated on `session`), placed with the event-timeline panel it reads from. |
| `docs/control-plane/evidence/aeas-01-lab-dispatch-01/` | This document plus the three probe scripts under `probes/`. |

## 3. Requirement 1 — provider independence

The adapter contract (`ModelAdapter.generate`) is unchanged; only binding changed. Adapters are
registered from configuration, and the gateway now reports two independent facts:

```
GET /api/lab/engineering/gateway   (no inference env vars set)
  ollama     status=UNCONFIGURED  adapter_bound=False dispatchable=False
  ...
  n_atlas    status=UNCONFIGURED  adapter_bound=True  dispatchable=False
             detail="N_ATLAS_BASE_URL is not configured"

GET /api/lab/engineering/gateway   (OLLAMA_BASE_URL=http://127.0.0.1:8125 set)
  ollama     status=AVAILABLE     adapter_bound=True  dispatchable=True
             detail="host reachable via /api/tags"
  n_atlas    status=UNCONFIGURED  adapter_bound=True  dispatchable=False
```

The first row set is the defect P0.5 removes: a provider that is *described* but cannot be
*called* is now reported as not dispatchable rather than silently AVAILABLE. A second adapter
can be added without touching the Lab: implement `generate`, register it, configure it.

## 4. Requirement 2 — observable execution

Served-path probe (`probes/p05_positive_probe.py`) against a local endpoint, one authorized
session, one dispatch — HTTP 200:

```
state=VERIFYING  result_state=IMPLEMENTED  loop_state=DONE  provider=ollama  model=stub-local
effective_tools=["filesystem.read"]  human_decision_required=true
merge=false  deploy=false  self_authorized=false  evidence_refs=["EVD-6b16bd9b588e"]
run_id=RUN-b070b9ec7b07

turn 1: decision=TOOL_FAILED  tool=filesystem.list  args={'path': '.'}
turn 2: decision=DONE         text="Stub endpoint: the workspace listing was observed..."
```

All 17 stored events carry the run id (`run=RUN-b070b9ec7b07`), in sequence:

```
RUN_STARTED → MODEL_TURN → TOOL_INTENT → TOOL_OBSERVATION → AGENT_DECISION
→ MODEL_TURN → AGENT_DECISION → EVIDENCE_RECORDED → AUTHORIZATION_REQUIRED
→ SESSION_TRANSITION×5 → RUN_FINISHED
session_state=READY_FOR_REVIEW  reached_review_boundary=True  runs=1  evidence=1
```

Every failure is reported as itself: turn 1's refusal is stored verbatim as
`{"tool": "filesystem.list", "ok": false, "error": "tool 'filesystem.list' not granted to this run"}`.

## 5. Requirement 3 — honest availability (no `LIVE` claim)

**No inference provider is configured in this environment.** `N_ATLAS_BASE_URL`, `OLLAMA_*`,
`OPENAI_*`, `GEMINI_*` and `ANTHROPIC_*` are all absent. Measured served outcome with no
provider (`probes/p05_e2e.py`):

```
HTTP 200  state=BLOCKED  result_state=BLOCKED  loop_state=BLOCKED
loop_reason="no inference adapter bound for provider 'ollama';
             the gateway describes models but cannot call them"
turns=[]   effective_tools=["filesystem.read"]
```

No turn, observation or artifact is invented when the loop cannot run. Consequently:

* **Model-backed dispatch: `UNAVAILABLE`. `LIVE` is NOT claimed.**
* The positive-path run in §4 executed against `probes/ollama_stub.py`, a local stub of the
  `/api/chat` endpoint — **it is not a model**. It proves the adapter contract, tool execution,
  event attribution and terminal-state reporting over real HTTP; it does not prove a provider
  works. `status=AVAILABLE` is a *reachability* claim ("host reachable via /api/tags"), which is
  exactly what the gateway reports — not a claim of inference.
* `LIVE` requires a configured provider and one dispatch observed end to end against it.

## 6. The named boundary: `run-agent` never gets `test`

| Check | Measured |
| --- | --- |
| Session authorized with `operations_allowed=["read","test"]`, then dispatched | `effective_tools=["filesystem.read"]` — no `test` tool (served, §4) |
| Model requests a tool outside the granted envelope | refused: `tool 'filesystem.list' not granted to this run` |
| `"test" not in OPERATION_TOOLS`, `"test" not in _specs()`, not in `CAPABILITY_OPERATIONS[RUN|READ]` | 1 node |
| Authorizing `test` does not widen the loop | 1 node |
| Registry cannot expose a mutating tool in L1 | 1 node |
| A grant cannot smuggle an unregistered tool | 1 node |
| **Negative control:** dispatch on a `PROPOSED` session | `HTTP 409 "session must be AUTHORIZED or QUEUED to execute (currently PROPOSED); SESSION != AUTHORIZATION"` |
| Auth boundary | `GET /gateway` without a token → `HTTP 401` |

The human authorization is recorded with `originated_by="human"`, `merge=false`,
`production=false`, `merge_prohibited=true`; the dispatch response returns
`human_decision_required=true`, `merge=false`, `deploy=false`, `self_authorized=false` and the
session stops at `READY_FOR_REVIEW`.

## 7. Verification (measured, 2026-10-30, this branch)

| Command | Result |
| --- | --- |
| `.venv/bin/python -m pytest tests/test_engineering_lab_dispatch_truth.py -q` | **12 passed** |
| `… tests/test_lab_mission_workspace_contract.py -q` | **21 passed** |
| `… tests/test_console_endpoint_registry_contract.py -q` | **20 passed** |
| `… tests/test_openapi_security_production_contract.py -q` | **1 passed** |
| `… tests/test_engineering_lab_api.py -q` | **2 failed, 3 passed** — pre-existing (see §8) |
| `cd web/arkadia_console && corepack pnpm build` | **exit 0** (`tsc --noEmit && vite build`, 112 modules) |
| `{ git diff --name-only; git ls-files -o --exclude-standard; } \| python scripts/cp10_mutation_boundary_policy.py --judge` | **Mutation boundary PASS** |
| **Composition:** P0.4 head `05414274` + this diff (`git apply --3way`, clean) + these suites | **134 passed, 1 skipped, exit 0** — includes P0.4's `test_engineering_lab_test_boundary.py` alongside the `test`-not-a-loop-tool nodes |
| Served probes (`probes/p05_e2e.py`, `probes/p05_positive_probe.py`) | executed as recorded in §4–§6 |

## 8. Known failures and limitations

* `tests/test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated` and
  `::test_lab_mutation_endpoints_are_exactly_the_lab_state_set` fail with **2 failed, 3 passed**.
  Re-measured at the unmodified base `b0945011` in a clean worktree: **identical 2 failed,
  3 passed** — pre-existing (the n-atlas routes are missing from `ALLOWED_MUTATION_ENDPOINTS`),
  not introduced here, and out of scope for P0.5.
* **No real provider ⇒ no model-backed task was proven.** The end-to-end model run the directive
  asks for remains `BLOCKED` on provider credentials.
* Docker is unavailable in this VM (socket group-restricted), so container-backed paths were not
  re-exercised here (P0.4's live-container evidence stands on its own PR).
* The console panel was **built** (`tsc` + `vite`, exit 0) but **not rendered in a browser** in
  this environment — UI behaviour is NOT CLAIMED beyond the source-level contract tests.
* PR #591 (`mergeable=False` against `main`) is the base of this branch; its own conflict
  resolution is a separate, human-owned decision.

## 9. Next authorized action

1. Review/merge PR #593 (P0.4) independently.
2. Review this branch's dispatch slice; retarget the PR base to `main` once #591 lands.
3. Configure one real inference provider and dispatch a single mission end to end; only then
   report `LIVE`.
