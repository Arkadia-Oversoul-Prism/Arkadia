# G12-B · Durable Offline Queue State Machine

Bounded move: prove the existing CaptureStore state machine survives process recreation and that an acknowledgement-loss retry converges to the same canonical WorkEvent. Do not add unrelated background scheduling in this move.

Required evidence: persisted state transition, restart reconstruction, exact retry replay, no duplicate WorkEvent.
