# AEAS-01 · Bounded test surface on the mission workspace

**Status: IMPLEMENTED AND SOURCE-VERIFIED. A test run is not `LIVE`. Browser execution is NOT CLAIMED.**

| Field | Value |
| --- | --- |
| Date | 2026-10-30 |
| Branch | `feat/aeas-01-bounded-test-surface` |
| Base | `feat/aeas-01-p05-agent-dispatch` @ `3865bfcb19771701a478f476d42aa8dde93b8b40` |
| Directive | Issue #590. This slice is the inspectable test step the mission workspace did not have. |
| Depends on | PR #593 for the runtime to admit `kind: "test"`. This branch does not copy that backend. |

## What changed

The mission workspace can request one `test` operation through the existing
`POST /sessions/{id}/execute` route. The client sends an optional selector and
`requires_write: false`. It does not send a command. The panel renders
`result_state`, run id, exit code, and stdout/stderr only when the server
returns them.

A transport refusal is classified, not decorated:

- `unknown operation kind`, read/list-only gate, or container/digest boundary → `UNAVAILABLE`
- authorization or session-state refusal → `REFUSED`
- any other execute failure → `FAILED`

`IMPLEMENTED` stays the substrate's word. The panel says that report is not an
independent verification and not acceptance. The request uses its own in-flight
flag and does not take the workspace busy lock.

`run-agent` is unchanged. Authorizing `test` still does not grant the model loop
a test tool.

## Verification

| Command | Result |
| --- | --- |
| `python3 -m pytest tests/test_lab_mission_workspace_contract.py -q --noconftest` | **22 passed** in 0.12s, exit 0 |
| `corepack pnpm exec tsc --noEmit` in `web/arkadia_console` | exit 0 (Node v22.23.3; package engine asks for Node 24) |
| `corepack pnpm exec vite build` in `web/arkadia_console` | exit 0, 115 modules |

No served dispatch, no container test, and no browser click-through were run.
Those are not claimed. On this revision, a press of **Run bounded test** against
the P0.5 runtime is expected to return the server's `unknown operation kind 'test'`
(or the project-canvas read/list refusal) and the panel must show `UNAVAILABLE`.
That becomes a real suite result only when the #593 boundary is on the same
revision and a container policy is actually available. Without that boundary the
honest state is unavailable, not a pass.

## Governance

No merge, no push to `main`, no deployment, no production configuration, no
credential change. The test operation is not added to the agent tool envelope.
