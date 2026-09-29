# GATE L1 — Native Agent Runtime: Implementation Record

Status: IMPLEMENTED (pending human review)
Base SHA: ee3fac1 (main)
Branch: gate-l1-agent-runtime

## The claim this gate makes (and no more)

> An Arkadia Engineering Lab agent can reason through multiple tool turns
> inside its governed Lab boundary.

Not "we built an AI coding agent." Not "OpenHands integrated." Not "automation
complete." The single truthful claim is the one above.

## What was missing before

Verified against `ee3fac1`:

- `lab/engineering_lab/gateway.py` exposed `describe` / `catalog` / `select` —
  it described models but never called one. No `generate()`.
- `EngineeringLabRuntime.execute_bounded_task()` ran a *predeclared* list of
  `task.operations`. There was no model turn, no tool intent, no observation
  fed back to a model. Grep for `AgentLoop` / `ToolRegistry` in `lab/` returned
  nothing.
- The runtime recorded `"prepared, not applied to repository"` for write-class
  runs — it could not edit a real worktree.

## What this gate adds (all native in `lab/`, per decision 2)

| File | Role |
|------|------|
| `gateway.py` (extended) | `ModelGateway.generate()` — the first real inference call; `ModelAdapter` / `ModelResponse`; `OllamaAdapter` (local-first); `ModelUnavailable` fail-closed |
| `tools.py` (new) | `ToolRegistry` — agent-facing layer over `sandbox.py`; read-only specs only; browser-ready extension point |
| `agent_loop.py` (new) | `AgentLoop` — MODEL → decision → TOOL CALL → observation → MODEL … terminating on DONE / BLOCKED / ERROR / HUMAN_AUTHORIZATION_REQUIRED |
| `runtime.py` (extended) | `execute_agent_loop()` — runs the loop inside a governed session, records evidence, ends READY_FOR_REVIEW |
| `models.py` (extended) | four additive `AGENT_EVENT_TYPES`: MODEL_TURN, TOOL_INTENT, TOOL_OBSERVATION, AGENT_DECISION |

## Decisions honoured

1. **Local-first provider.** `OllamaAdapter` is the first real provider, bound
   through `register_adapter`. The deterministic stub is the CI acceptance
   path; a real-Ollama test skips cleanly when no endpoint is configured.
2. **Native in `lab/`.** `AgentLoop` and `ToolRegistry` live in the existing
   substrate. OpenHands remains a future adapter, not the runtime's owner.
3. **K15/K3 is the only mutation boundary.** The L1 loop does not reach
   `enterprise_orchestration`, K15, or K3 — enforced by an AST-based test.
   *Correction (see GATE-L1.1):* the original claim that the tool set was
   "read-only by construction" was **wrong**. `terminal.run` reached
   `Sandbox.run`, which validated only the binary against the allow-list, so
   `git commit`/`reset`/`branch`/`tag` executed. GATE-L1.1 adds a git
   read-only subcommand policy and a negative-mutation test suite.
4. **Browser deferred to L3.** `ToolRegistry` is the extension point; adding
   `browser.*` is a new spec, not an AgentLoop change. No Docker/Playwright in
   L1.

## The L1 acceptance sequence

The deterministic stub plays the directive's known sequence:

| Turn | Model decision |
|------|----------------|
| 1 | `filesystem.list` |
| 2 | `filesystem.read` |
| 3 | `terminal.run` (`git status --short`) |
| 4 | (no tool call) → DONE |

Asserted in `tests/test_engineering_lab_agent_loop.py`:

- every tool call produces an AgentEvent (MODEL_TURN ×4, TOOL_INTENT ×3,
  TOOL_OBSERVATION ×3)
- every observation returns to the loop
- termination is deterministic across runs
- termination is one of the four allowed states
- evidence references the run
- the session ends READY_FOR_REVIEW, not COMPLETED
- **the repository is not mutated** (before/after `git status --porcelain` equal)
- the loop does not couple to K15/K3/`enterprise_orchestration`
- the provider can be swapped without changing the loop

## Evidence

- `tests/test_engineering_lab_agent_loop.py`: 13 tests, all passing, real
  loop + real sandbox + real SQLite store + real event stream. Only inference
  is scripted.
- Full Lab regression: **71 passed, 1 skipped, 2 failed**. The 2 failures are
  `test_engineering_scheduler_bootstrap.py::test_blocked_dependency_skips_move`
  and `::test_dry_run_evidence` — reproduced on base `ee3fac1` with the L1
  changes stashed, so they pre-exist and are out of scope.
- Architecture suite: 11 passed.
- No new mutation path; the code does not touch `ew_*`, K15, or K3.

## Out-of-scope observed (not implemented)

- **GATE L2** — real worktree mutation routed through PassSpec → K15 → K3.
- **GATE L3** — browser tool + artifact rendering + the Canvas run view.
- **GATE L4** — automation dispatcher.
- **GATE L5** — Android Lab + Google Tasks/Keep/voice integrations.
- The pre-existing scheduler-bootstrap failures (2).
- `api/lab_routes.py` was not extended for the loop; the runtime method is the
  seam the L3 Canvas will call through a route.

## Verdict

IMPLEMENTED. The loop is real and verified against a deterministic stub; no
state is claimed beyond that. It awaits human review.
