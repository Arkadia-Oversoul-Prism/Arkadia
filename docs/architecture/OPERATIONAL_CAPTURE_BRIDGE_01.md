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


## Causal chain closure

Enterprise proposals may carry `caused_by_kind/caused_by_id`, and the Eden path binds the verification proposal to its interpretation. Reverse/forward walks therefore preserve the causal path from the captured source through interpretation, proposal, authority, authorization, execution, evidence, and verification without treating correlation IDs as causal proof.


## Evidence-side closure

The lineage surface is now bidirectional without creating a second provenance store.

**Forward acceptance path**

`CANONICAL_RECORD` → `INTERPRETATION` → `PROPOSAL` → `AUTHORIZATION` → `EXECUTION_ATTEMPT` → `EVIDENCE` → `VERIFICATION`

A forward walk rooted at a captured canonical record must reach the resulting verification when those records exist. The canonical record retains `capture_ref` and the capture checksum remains equal to the canonical payload hash.

**Reverse acceptance path**

`VERIFICATION` → `EVIDENCE` → `EXECUTION_ATTEMPT` → `AUTHORIZATION` → `PROPOSAL` → `INTERPRETATION` → `CANONICAL_RECORD` → `CAPTURE` → `SOURCE`

The reverse walk resolves `capture_ref` through the existing read-only GATE-01 provenance function. It exposes the captured checksum, source identity, source reference, authorship state, and capture metadata. It does not infer authorship.

For canonical roots, `complete=true` now means the operational ancestry reaches both a GATE-01 capture and its registered source. Missing capture provenance therefore cannot be silently treated as complete lineage.

This is a read-only projection over existing records. No second provenance authority, graph store, or mutation path is introduced.
