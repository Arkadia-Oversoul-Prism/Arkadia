# Operational Capture Bridge 01

Status: AUTHORIZED

The existing ARK-WEAVER enterprise operational spine already expresses:

CANONICAL RECORD → INTERPRETATION → KNOWLEDGE MUTATION / OPERATIONAL EVENT → PROPOSAL → HUMAN AUTHORITY → AUTHORIZATION → EXECUTION → EVIDENCE → VERIFICATION.

This change makes the enterprise CANONICAL RECORD a downstream operational projection of the existing GATE-01 capture boundary.

The enterprise store does not become a second provenance authority.

For every operational canonical record:
1. GATE-01 registers the source.
2. GATE-01 captures the raw canonical payload and checksum.
3. The enterprise canonical record stores the capture reference and the same payload hash.
4. Interpretation and all later operational transitions retain the enterprise correlation chain.
5. Existing authorization, execution, evidence, and verification semantics remain unchanged.

Authorship is never inferred from ingested_by.

The bridge is deliberately one-way:

GATE-01 provenance → enterprise operational chain

not

enterprise operational records → inferred provenance.
