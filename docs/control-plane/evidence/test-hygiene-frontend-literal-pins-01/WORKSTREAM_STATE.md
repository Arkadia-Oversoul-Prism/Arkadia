# WORKSTREAM STATE — test-hygiene/frontend-literal-pins-01

**Recorded**: 2026-10-04 (Weaver heartbeat, hourly bounded execution)
**Base main**: `357fbd83001924e909979fbaebdedbd991a2aadb` (`Merge pull request #244`)
**Branch**: `test-hygiene/frontend-literal-pins-01`
**PR**: #251
**Classification**: IMPLEMENTED — awaiting sovereign merge

## Current state

Six frontend/source **test-side literal pins** repaired; each test now asserts the
surface that actually carries the governance property. Test-side only — no production
source, no governance surface, no authority path, no `api/main.py`.

All guards independently re-measured on this tree at PR head `162996c`:

| Check | Result |
|---|---|
| `python -m py_compile api/main.py` | OK (2582 / 2600 budget) |
| `pytest tests/architecture tests/test_m02a_ci_gate_integrity.py -q` | 66 passed |
| CP10 judge on diff | RC 0 — PASS |
| repaired test files | 16 passed |
| full suite (branch) | 21F / 1369P / 20S / 1E |
| full suite (base `357fbd8`, isolated worktree) | 27F / 1363P / 20S / 1E |
| **node-set delta** | **28 → 22, new nodes = 0, removed = exactly the 6 repaired** |

## CI state at PR head (recorded)

- `check-runs`: **Full-history secret scan — success**, Vercel Preview Comments — success.
- `commit statuses`: `Vercel – arkadia-prism` success, `Vercel – console` failure.
- The `console` failure is **pre-existing baseline**: base main `357fbd8` carries
  **both** Vercel contexts failing. Not a regression from this change.
- CP10 (`sg-02-fe-2-v.yml`) is path-filtered and does **not** trigger on this diff
  (`tests/**`, `docs/**`). Its invariant — every tracked path admitted — is still
  enforced here by `tests/test_m02a_ci_gate_integrity.py`, which passes.

## Dependencies / overlap

No overlap with open PRs #245, #248, #249, #250 (checked via `GET /pulls/{n}/files`).

## Blockers

None. The earlier `gh` CLI 401 was a credential-name mismatch, not a read-only token:
`GITHUB_TOKEN` is empty; the working credential is `github_token` (API 200 + push
succeeded). PR #251 was created through the REST API with that credential.

## Next bounded task (deterministic resume block)

- **State**: this workstream is complete pending merge. Do not extend it.
- **Authorized action**: sovereign review of PR #251 → merge.
- **Forbidden**: merging, pushing to `main`, widening this PR's scope.
- **Next candidate workstream** (separate branch, needs its own bounded PR):
  the two **authority-boundary** nodes —
  `test_evidence_verification_boundary.py::test_no_http_route_creates_evidence_or_verification`
  and
  `test_workevent_evidence_boundary.py::test_no_http_route_exposes_evidence_verification_or_the_enterprise_walk`.
  Verified genuine, not test-side defects: `solspire/console_authority_router.py:204`
  (`@router.post("/executions/{execution_id}/evidence")`) and `:269`
  (`@router.post("/verification")`) expose evidence/verification as first-class HTTP
  records, and `api/nodes.py` routes `weaver/runs/{run_id}/evidence`. This is an
  **authority-surface question reserved to the human sovereign** — it must not be
  repaired by weakening the test or by editing the route surface without authorization.
- **Explicitly out of scope**: Docker-unavailable
  `test_actual_oci_runtime_hardens_process_and_mount`; the `test_autonomy.py`
  collection error (`weaver.autonomy` module/package collision); the remaining
  unrelated baseline failures.
