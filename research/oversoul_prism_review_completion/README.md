# Review, Completion, and Production Acceptance Probe

Run:

    python3 probe.py

The probe demonstrates:

1. EXECUTED does not imply COMPLETED.
2. Review is a separate record.
3. Completion requires an explicit condition and observation.
4. Production acceptance requires verification plus explicit authority.
5. Amendments reference the original WorkEvent without rewriting it.

The probe has no LLM calls, external side effects, or production route.
