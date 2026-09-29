# M02A — CI Gate Integrity

**Status:** PENDING (Architect-authorized intervening move)  
**Depends on:** M02 (accepted)  
**Blocks:** M03 until this move is accepted  

## Authority

Explicit Architect authorization: temporary pause before M03 to restore a truthful validation boundary. No M03 product work is authorized by this move.

## Objective

Ensure `.github/workflows/sg-02-fe-2-v.yml` mutation-boundary validation distinguishes:

- **legitimate repository mutation** (product, control-plane moves, lab harness, docs, tests)
- **forbidden architectural mutation** (constitutional surfaces and automation of merge/deploy)

It must not reject legitimate product tip commits solely because paths fall outside an obsolete Lab-phase harness allow-list.

## Out of scope

NovaNet (M03), ReasoMate product changes, Solariun product redesign, AEAS semantic change, K15/K3, provenance, WorkEvent semantics, second CI system, auto-merge, auto-deploy.

## Acceptance

1. Representative product/frontend tip paths are not rejected by the mutation boundary.
2. Control-plane path changes remain allowable under governed surfaces.
3. Forbidden patterns (merge/deploy automation in workflow; dual-shell V2/V3 introduction; unauthorized AEAS/trajectory-only constitutional rewrite without move packet) remain detectable.
4. Focused tests document positive and negative cases.
5. M03 remains unexecuted.

## Stop

Human review. No merge by automation. No M03.
