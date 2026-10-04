# TEST-HYGIENE · OCI runtime daemon probe 01

**Status:** IMPLEMENTED — sovereign review required
**Date:** 2026-10-04
**Base main:** `357fbd83001924e909979fbaebdedbd991a2aadb` (`Merge pull request #244`)
**Branch:** `test-hygiene/oci-runtime-daemon-probe-01`
**Gate:** Phase 1 (runtime stabilization) · `test-hygiene`

## 1. Objective

Close the one Phase 1 §4.2 node whose classification was **UNKNOWN** — neither a
literal-pin repair (PR #251) nor a boundary-regex false positive (PR #249) owns it:

```
tests/test_solspire_project_execution_service.py::test_actual_oci_runtime_hardens_process_and_mount
```

`docs/control-plane/evidence/phase1-runtime-stabilization-01/EVIDENCE.md` §4.2 lists
it in the "test-side literal defect" class but assigns it no measured assertion
failure, and §6's workstream list does not carry it. This pass measures it.

## 2. Measured cause (main @ `357fbd8`)

```
$ python -m pytest tests/test_solspire_project_execution_service.py::test_actual_oci_runtime_hardens_process_and_mount -q
E  AssertionError: failed to connect to the docker API at unix:///var/run/docker.sock;
   check if the path is correct and if the daemon is running: dial unix /var/run/docker.sock:
   connect: no such file or directory
E  assert 1 == 0
```

**Class: environment / guard defect — not a production defect, not a literal pin.**

The test's skip guard is `if not shutil.which(runtime): pytest.skip(...)`. `shutil.which`
finds the **client binary** only. A host that has the Docker *client* installed but no
running *daemon* (or no `/var/run/docker.sock`) passes the guard, reaches
`run_isolated`, and fails on the container call with an opaque process error. The
production module's own guard (`run_isolated`'s `shutil.which` check) has the same gap:
it fails closed with a process error instead of the boundary's typed `BoundaryError`.

This is the recurring "guard cannot observe the condition it names" class — the same
shape as the Phase 1 boundary regexes that matched substrings inside unrelated paths.

## 3. Bounded change

| File | Change |
|---|---|
| `solspire/project_execution_boundary.py` | + `_container_runtime_available()` daemon probe; `run_isolated` raises `BoundaryError("container runtime daemon unavailable; refusing host execution")` when the CLI cannot reach its daemon |
| `tests/test_solspire_project_execution_service.py` | the live OCI acceptance test skips when the daemon is unreachable; +1 negative control |
| this evidence dir | record the classification + proof |

The probe runs `docker info` (or `<runtime> version` for a non-docker runtime) with a
10 s timeout and the same sanitized `env` the container call uses. It is **fail-closed**:
any `OSError`/`SubprocessError` returns `False`, so a probe that cannot run is treated as
"daemon unavailable" and the caller refuses.

No authority path, no boot code, no `api/main.py`, no governance surface.

### Why the negative control is required

Without it, "the node now skips" is satisfiable by weakening the guard to always skip —
which would make the live acceptance test vacuous. The control pins the property that
carries the boundary: a **reachable CLI with an unreachable daemon must be rejected**.

## 4. Verification

| Check | Result |
|---|---|
| Negative control, guard **present** | `test_daemon_probe_does_not_treat_a_client_without_a_daemon_as_ready` **PASS** |
| Negative control, guard **removed** (failing-first) | **FAIL** — `DID NOT RAISE BoundaryError`; a reverted probe fails the control, so the property cannot go vacuously green |
| `tests/test_solspire_project_execution_service.py` | **9 passed, 1 skipped** (was 1 failed / 8 passed) |
| Container argv invariants | unchanged — `--network=none`, `--read-only`, `--cap-drop=ALL`, `--user 65532:65532`, digest pin all still asserted by the pre-existing mocked tests |
| `pytest tests/architecture -q` | **11 passed** |
| `python -m py_compile solspire/project_execution_boundary.py` | PASS |
| `python -m py_compile api/main.py` | PASS (boot code untouched) |

### Full-suite delta (node set, not counts)

```
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q --continue-on-collection-errors
```

| tree | result |
|---|---|
| `main` @ `357fbd8` | 27 failed, 1363 passed, 20 skipped, 1 error — 28 failing/error nodes |
| this branch | 26 failed, 1364 passed, 21 skipped, 1 error — 27 failing/error nodes |

Node-set diff:

- **new failures: none**
- **now passing/skipped: exactly one** —
  `test_solspire_project_execution_service.py::test_actual_oci_runtime_hardens_process_and_mount`

The passed-count is **not** the oracle: `test_engineering_lab_agent_loop.py::test_agent_loop_does_not_mutate_repository`
is order-dependent under the full suite, so counts vary run to run on the same tree.
Attribution here is the sorted node set.

## 5. Remaining uncertainty

- The 27 residual nodes are **pre-existing, classified debt**, not caused by this change.
  PR #249 owns `test_verification_review_boundary`; PR #251 owns six frontend literal
  pins; PR #252 records the `test_evidence_verification_boundary` /
  `test_workevent_evidence_boundary` contradiction for **sovereign adjudication**.
- This pass makes **no** claim about the `solspire/console_authority_router.py`
  evidence/verification routes — that boundary question is open in PR #252 and is
  reserved to the sovereign.
- No production-runtime claim: the container boundary is exercised against a live
  daemon only where one exists.

## 6. Authority boundary

No merge, no push to `main`, no force-push, no authority-path change, no scope
expansion. Human authority is required to merge.

---
*This evidence record was created by an AI agent (OpenHands) on behalf of the human sovereign.*
