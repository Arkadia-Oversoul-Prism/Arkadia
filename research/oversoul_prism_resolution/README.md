# Resolution Authority Probe

Run:

    python3 probe.py

The probe tests four rejection paths and one eligible resolution path.

- Missing evidence → rejected.
- Missing authority → rejected.
- Evidence without authority → rejected.
- Wrong authorization scope → rejected.
- Sufficient evidence plus explicit scoped authorization → `RESOLVED_PENDING_VERIFICATION`.

The prototype does not define the production authority registry.