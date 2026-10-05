# Verification Boundary Probe

Run:

    python3 probe.py

The probe separates resolution from verification and acceptance.

- Verification receives a resolved-pending-verification state.
- Verification emits its own record with the resolution digest.
- The verifier cannot rewrite the resolver or resolution evidence.
- Verification may produce VERIFIED, VERIFICATION_FAILED, or UNKNOWN.
- Acceptance remains UNKNOWN and is never inferred from verification.