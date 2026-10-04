# Sovereign adjudication: Console evidence and verification routes

**Date:** 2026-10-04  
**Decision authority:** human sovereign  
**Disposition:** **Option A selected**  
**Scope:** Gate-03 / Gate-04 route-surface classification

## Decision

Recognize the authenticated SolSpire Console authority bridge as the intended
first-class HTTP surface for evidence and verification records. Amend the
canonical boundary map and tests accordingly. Do not remove these routes merely
to preserve the earlier route-absence statement.

The routes are:
- `POST /solspire/authority/executions/{execution_id}/evidence`
- `POST /solspire/authority/verification`

## Conditions preserved

1. Authentication is not interchangeable with authorization.
2. Evidence and verification are separate append-only records.
3. Verification must reference existing evidence and must not be implied by
   execution or evidence creation.
4. The verifier identity is derived server-side from the authenticated Firebase
   UID, not trusted from a request-supplied label.
5. First-class evidence/verification routes do not expose `forward_walk` or
   `reverse_walk` lineage traversal.
6. Route recognition is not proof of runtime success, sufficient evidence, or
   production deployment. Those claims require separate verification.

## Reconciliation

- `RECONCILED-BOUNDARY-MAP-01.md`: appended this adjudication and superseded
  the route-absence claim for the Console authority bridge.
- `tests/test_evidence_verification_boundary.py`: now asserts the intended
  evidence/verification route contract and server-derived verifier identity.
- `tests/test_workevent_evidence_boundary.py`: now distinguishes first-class
  record routes from the still-unexposed enterprise graph traversal.
- `docs/control-plane/evidence/phase1-runtime-stabilization-01/EVIDENCE.md`:
  prior classifications updated so the old absence assumption is not carried
  forward as current truth.

## Evidence state

Repository changes and CI results are pending review. Production deployment,
authenticated end-to-end execution, and independent verification are **not
claimed** by this ruling.
