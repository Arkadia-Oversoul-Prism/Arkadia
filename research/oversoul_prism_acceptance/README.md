# Acceptance and WorkEvent Boundary Probe

Run:

    python3 probe.py

The probe tests two paths:

1. Verified → Accepted without execution authorization → execution rejected.
2. Verified → Accepted with explicit bounded execution authorization → execution → WorkEvent.

The WorkEvent references execution but cannot create authority, declare completion, or declare review.