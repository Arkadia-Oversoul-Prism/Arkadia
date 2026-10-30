# AEAS-01 · P0.4 — Bounded containerized test execution for the Engineering Lab

**Directive:** GitHub Issue #590 — Engineering Lab becomes the execution substrate for Arkadia One
**Priority:** P0.4 (third vertical slice; follows P0.3 repository observation in PR #592)
**Branch:** `freebuff/aeas-01-p04-test-boundary` — stacked on `freebuff/f6a4fd1dd162a73f0b053afb` at `3fc5f701`
**Base (main):** `d9a16f12` (unchanged by this work)
**Authorization used:** the Lab's own `require_auth` only. No authority, approval, identity or
sovereign-gate change. No merge, no push to `main`, no deployment.

---

## 1. Objective

Close the largest remaining P0 gap between the Lab and an external engineering tool: the Lab could
*read* a repository but had **no way to run a test suite and report what happened**. The directive
for this slice was explicit — *"a bounded containerized test-execution operation, with an explicit
command allowlist and resource limits"*, without widening the L1 terminal grammar and without
giving an agent a shell.

Measured starting state: `SandboxPolicy.containerized` and
`solspire.project_execution_service.execute_container_command` already existed, but `Sandbox.run`
applies the L1 grammar *first*, so a `python -m pytest` request was refused before the container
branch was ever reached. The container machinery was real and unused for tests.

## 2. The contract

A new bounded operation kind, `test`, in `lab/engineering_lab/bounded_test_execution.py`:

| Rule | Enforcement |
| --- | --- |
| **Explicit command allowlist** | `TEST_COMMAND_ALLOWLIST` — pinned argv *prefixes* (`python -m pytest`, `python -m unittest`, `pytest`, `node --test`, `npm/pnpm/yarn/bun test`, `cargo test`, `go test`). A caller supplies **no argv**; a `test` operation carries only an optional selector. |
| **Operator re-pointing is still bounded** | `ENGINEERING_LAB_TEST_COMMAND` may change the command, but it must still match an allowlisted prefix; an unparseable or blank value is a refusal, never a silent fallback. |
| **Selector validation** | `validate_target` refuses a leading `-` (option injection), absolute paths, `..`/`.`/empty segments, whitespace and shell punctuation, and anything over 200 chars. |
| **Resource limits** | `configured_timeout_seconds()` — operator-tunable via `ENGINEERING_LAB_TEST_TIMEOUT_SECONDS`, clamped to the 1–900 s window the container boundary accepts, and **not** caller-influenceable. |
| **Container-only** | `Sandbox.run_test` refuses a non-containerized policy outright; there is no host fallback. |
| **Digest-pinned image** | Refused unless `SOLSPIRE_AGENT_IMAGE` carries a 64-hex `@sha256:` digest. |
| **Hardened argv** | Delegation is to `build_container_argv`: `--network=none`, `--read-only`, `--cap-drop=ALL`, `--security-opt=no-new-privileges:true`, `--pids-limit 128`, `--memory 512m`, `--cpus 1.0`, `--user 65532:65532`, tmpfs `/tmp`, bind-mounted workspace. |
| **Approval bound to the operation** | A `test` operation requires the session's linked **human** authorization to name `test` in `operations_allowed`. No record → fail closed. Refusal happens **before** any run record exists. |
| **L1 grammar untouched** | `test` is its own operation set — not in `READ_OPERATIONS`, not in `WRITE_OPERATIONS`. `python -c` on the host path is still refused (negative control below). |

## 3. Changed paths (7)

- `lab/engineering_lab/bounded_test_execution.py` — **new**: allowlist, selector rule, timeout envelope, `resolve_test_command`.
- `lab/engineering_lab/sandbox.py` — `Sandbox.run_test()`: container-only entry point, re-validates the allowlist, pins the image, delegates, records a `test` sandbox event.
- `lab/engineering_lab/runtime.py` — `TEST_OPERATIONS`, pre-flight refusals (container / authorization / selector), `_authorization_operations()` fail-closed helper, `_run_operation` branch that turns a real exit code into evidence.
- `api/lab_routes.py` — the project-session gate now admits exactly `read/list/test`; everything else still 409s. **No new route**, so the OpenAPI inventory stays 332 and its security adjudication is untouched.
- `tests/test_engineering_lab_test_boundary.py` — **new**: 41 nodes.
- `tests/solspire/test_live_container_execution.py` — one added `@pytest.mark.live_container` node, so CI's existing live OCI job executes this path against a real digest-pinned image.
- `docs/control-plane/evidence/aeas-01-lab-test-boundary-01/EVIDENCE.md` — this record.

## 4. Verification (measured in this workspace, Python 3.12)

| Check | Command | Result |
| --- | --- | --- |
| New contract suite | `pytest tests/test_engineering_lab_test_boundary.py -q` | **41 passed** |
| Lab + live + contract set | `pytest tests/test_engineering_lab_test_boundary.py tests/solspire/test_live_container_execution.py tests/test_engineering_lab_substrate.py tests/test_engineering_lab_agent_loop.py tests/test_engineering_lab_candidate_proposals.py tests/test_openapi_security_production_contract.py -q` | **129 passed, 3 skipped**, exit 0 |
| Broader lab/console/guard set | 10 files incl. `test_engineering_lab_api.py`, `test_prism_w4_*`, `test_console_endpoint_registry_contract.py` | **233 passed, 3 failed** (failures attributed below) |
| Substrate API file alone | `pytest tests/test_engineering_lab.py -q` | **6 passed** |
| CP10 mutation boundary | `python scripts/cp10_mutation_boundary_policy.py --judge < changed paths` | **PASS** |
| Boot/syntax | `python -m py_compile api/lab_routes.py lab/engineering_lab/runtime.py lab/engineering_lab/sandbox.py lab/engineering_lab/bounded_test_execution.py` | **OK** |

### Negative controls executed (each must fail, and does)

1. `python -c …` through the **host** path → `SandboxCommandDenied`, workspace byte-unchanged, and `python ∉ L1_TERMINAL_BINARIES`.
2. `run_test` on a **non-containerized** policy → refused with "host execution is refused"; nothing executed.
3. `bash -c …` / `curl …` as `ENGINEERING_LAB_TEST_COMMAND` → `BoundaryViolation` (the env cannot escape the allowlist).
4. Selector shapes (`-k evil`, `/etc/passwd`, `../escape`, `a/../../b`, `$(id)`, `x;y`, NUL, 201 chars …) → all refused, 14 parametrized cases.
5. `python:3.12` (unpinned image) → refused at `run_test` *and* at `build_container_argv`.
6. Authorization whose `operations_allowed` lacks `test` → `BoundaryViolation`, **zero run records** and **zero evidence records** created.
7. Real (unstubbed) boundary in this VM → observation `ok=False` with the boundary's reason, `result_state=BLOCKED`, evidence `BLOCKED` — never `IMPLEMENTED`.

### Real exit-code → evidence mapping (executed with the boundary stubbed to a known code)

- return code 0 → observation `ok=True`, evidence **`IMPLEMENTED`**, `human_decision_required=True`, `merge=False`, `deploy=False`.
- return code 1 → observation `ok=False` with `"test command exited with return code 1"`, evidence **`BLOCKED`** (not `NOT_ATTEMPTED` — the suite ran).

## 5. Failure states, stated as observed

| Claim | Status | Evidence |
| --- | --- | --- |
| Allowlist / selector / timeout contract | **LIVE** | 41 nodes executed |
| Container-only refusal ladder, authorization binding, evidence states | **LIVE** | 7 negative controls above |
| Hardened resource limits | **LIVE** (argv builder executed for real; pure function) | `build_container_argv` assertions + digest-pin refusal |
| **A real container running the pinned suite command here** | **UNAVAILABLE — NOT CLAIMED** | This VM has a docker *client* but the daemon socket is `root:docker` 0660 and this uid is not in that group (`permission denied while trying to connect`); no `SOLSPIRE_AGENT_IMAGE`. Reported as BLOCKED by the code path itself, never as a pass. |
| The same path against a live runtime | **LIVE (CI)** | `SolSpire project execution boundary` run [`40982796062`](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/40982796062), job `boundary`, step **Live OCI acceptance gate** → `2 passed, 1 deselected`: the pre-existing boundary node **plus** `test_p04_test_operation_executes_pinned_argv_in_a_real_container`, both executed against a real digest-pinned `alpine:3.20.10` image. The non-zero branch is what ran (the acceptance image carries no Python interpreter), proving the container executed the pinned argv and its **true** exit code came back with the container's own output — never a fabricated pass. The unit step of the same job: `29 passed, 2 skipped` (both live nodes correctly skipped without an image). |
| Authenticated operator running tests from the Lab UI | **NOT IMPLEMENTED** | no UI surface added (mission workspace files are owned by open PR #591) |
| Test execution from the *agent loop* (`run-agent` tool envelope) | **NOT IMPLEMENTED — deliberate** | would widen the model's tool set; belongs to P0.5 with the inference adapter |

## 6. Pre-existing failures reproduced, not repaired (out of scope)

- `tests/test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated` and `::test_lab_mutation_endpoints_are_exactly_the_lab_state_set` — **reproduced with this change stashed** (`git stash push -u` → same 2 failures at `3fc5f701`). Cause: `/api/lab/engineering/n-atlas/test-session` and `/api/lab/engineering/n-atlas/run` are mutating endpoints not present in `ALLOWED_MUTATION_ENDPOINTS`.
- `tests/test_lane_instruction_doc_currency.py::test_live_snapshot_is_fresh_against_current_main` — environment: this clone has **no `main` or `origin/main` ref** (`git rev-parse --verify main` → `fatal: Needed a single revision`), and the guard fails closed by design.

No test was skipped, weakened or deleted to produce the results above.

## 7. Next permitted action

Human review of this stacked PR (**merge only after PR #592**, its base branch). Not authorized
here: merge, push to `main`, deployment, widening `TEST_COMMAND_ALLOWLIST`, routing `test` into the
agent-loop tool envelope, or any change to the L1 grammar.
