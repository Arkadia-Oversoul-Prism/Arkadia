# Conflict Propagation Probe

Run:

    python3 probe.py

The probe establishes a hard separation between propagation and resolution.

- Propagation preserves `CONFLICT` and `UNKNOWN`.
- Propagation records provenance.
- Resolution requires explicit evidence and an explicit resolver.
- Even after resolution, verification remains `UNKNOWN` until separately verified.

This is a deterministic research artifact, not a production runtime.