# Phase 6 Opening Record — Persistent Execution

**Status:** IMPLEMENTATION IN PROGRESS — gate not yet earned  
**Authorization:** Explicit human authorization on 2026-09-10  
**Phase 1:** SEALED  
**Phase 2 opening gate:** PASS  
**Phase 3:** PASS  
**Phase 4:** PASS  
**Phase 5:** PASS — governed execution stopped at PR boundary  

## Authorized scope

Extend the existing `kernel/jobs.py` and `kernel/worker.py` execution path so a long-running task can survive worker restart through:

- durable execution records
- checkpoints
- worker leases
- heartbeats
- lease expiry recovery
- resume from the last durable checkpoint

A new queue architecture is explicitly out of scope. The existing JobStore queue remains the execution transport.

## Gate

The Phase 6 gate is deterministic:

1. start a long-running task;
2. kill the worker while the task is executing;
3. verify the checkpoint survived the worker death;
4. verify the lease is released/recoverable;
5. start a fresh worker;
6. verify the same task resumes from the last checkpoint rather than beginning with an empty execution state;
7. verify the task reaches the correct terminal state.

The gate is implemented in `tests/test_phase6_persistent_execution.py` and run by `.github/workflows/phase6-persistent-execution.yml`.

## Boundary

- Authority ceiling remains Level 2.
- No autonomous merge.
- No deploy.
- No production mutation.
- No new queue architecture.
- Phase 7 is not authorized by this record.

## Closure condition

Phase 6 is **not PASS** until the CI gate produces direct green evidence for the kill-worker → checkpoint → resume sequence. Until then this record remains an opening/implementation record only.
