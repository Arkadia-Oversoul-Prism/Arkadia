# WORKSTREAM STATE — test-hygiene/oci-runtime-daemon-probe-01

## Current state

| | value |
|---|---|
| BASE_MAIN | `357fbd83001924e909979fbaebdedbd991a2aadb` (`Merge pull request #244`) |
| branch | `test-hygiene/oci-runtime-daemon-probe-01` |
| gate | Phase 1 (runtime stabilization) · `test-hygiene` |
| status | IMPLEMENTED — sovereign review required |
| PR | (opened by this pass) |

## Bounded objective

Close the one Phase 1 §4.2 node with no owner and no measured assertion failure:
`tests/test_solspire_project_execution_service.py::test_actual_oci_runtime_hardens_process_and_mount`.

## Defect (measured at BASE_MAIN)

The skip guard `shutil.which(runtime)` finds the Docker **client**, not a reachable
**daemon**. On a host with the client but no daemon the guard passes, `run_isolated`
fails on the container call, and the test fails with a raw process error instead of
skipping. `run_isolated` itself fails closed the same opaque way rather than with its
typed `BoundaryError`.

## Change

- `solspire/project_execution_boundary.py` — `_container_runtime_available()` probe
  (`docker info` / `<runtime> version`, 10 s, sanitized env, fail-closed); `run_isolated`
  raises `BoundaryError("container runtime daemon unavailable; refusing host execution")`.
- `tests/test_solspire_project_execution_service.py` — skip on unreachable daemon;
  +1 negative control pinning "reachable CLI + unreachable daemon must be rejected".

## Evidence

- `docs/control-plane/evidence/test-hygiene-oci-runtime-daemon-probe-01/EVIDENCE.md`

## Verification

| check | result |
|---|---|
| `tests/test_solspire_project_execution_service.py` | 9 passed, 1 skipped |
| negative control with guard removed (failing-first) | FAIL (`DID NOT RAISE`) — detector proven |
| `tests/architecture` | 11 passed |
| full suite node delta vs BASE_MAIN | **new failures: none**; one node now skipped |
| `python -m py_compile api/main.py` | PASS (untouched) |

## Blockers / dependencies

- None. Independent of PRs #249 / #251 / #252.

## Not in scope

- The `solspire/console_authority_router.py` evidence/verification boundary question
  (open in PR #252, sovereign-reserved).
- Any other residual baseline node.

## Next bounded task

Sovereign review of this PR. Re-entry condition: a recorded ruling on PR #252's
boundary contradiction, which governs two of the residual nodes.

## Authority boundary

No merge, no push to `main`, no force-push, no authority-path change, no scope
expansion. Human authority is required to merge.
