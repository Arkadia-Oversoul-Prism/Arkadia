# G12-B · Durable Offline Queue State Machine

Bounded move: prove the existing CaptureStore state machine survives process recreation and that an acknowledgement-loss retry converges to the same canonical WorkEvent. Do not add unrelated background scheduling in this move.

Required evidence: persisted state transition, restart reconstruction, exact retry replay, no duplicate WorkEvent.

## Source repair: interrupted `SYNCING` recovery

Source inspection at `6115de9a` found a stranded-state path: reconciliation persists `SYNCING` before the network request, while `pending()` only selects `PENDING_SYNC` and `RETRYABLE_FAILURE`. If the process stops after `SYNCING` reaches disk but before a terminal state is stored, the next process would reconstruct a record that is never selected for replay.

The bounded repair normalizes stale `SYNCING` records once during the first `CaptureStore` construction of a process to `RETRYABLE_FAILURE`, increments the retry count, records a recovery explanation, and synchronously commits that recovery before reconciliation begins. A process-level guard avoids reclassifying a live in-flight sync during Activity recreation. The backend's existing subject + stable-capture-ID idempotency remains unchanged; no WorkEvent contract, identity boundary, API, or authorization rule changes.

The Android CI gate now runs `testDebugUnitTest` before `assembleDebug`. Pure policy tests cover recovery, preservation of all other states, and idempotence. These tests establish the policy mapping, **not** device/process-death acceptance.

## Acceptance still required

G12-B remains human-gated until a real Android run records the persisted transition, process recreation, acknowledgement-loss retry, and exactly one canonical WorkEvent. No device run, acknowledgement-loss trace, production API trace, or duplicate-WorkEvent measurement is claimed by this source repair.
