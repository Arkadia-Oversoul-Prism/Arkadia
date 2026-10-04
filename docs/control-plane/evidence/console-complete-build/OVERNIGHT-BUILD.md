# Arkadia Console Complete Build

## Operating contract

This branch is the **single long-lived human-review surface** for completing the native Arkadia Console from the current main baseline.

**Base:** `296d741b838a33c18f25cbd898dea3792c23cc9b`  
**Branch:** `feat/console-complete-build`  
**Target:** `main`  
**PR title:** `feat(console): complete governed Arkadia Console`

### Authority

- Human authority remains final.
- The agent may inspect, implement, test, document, and propose.
- The agent must not merge this PR.
- Do not create parallel Console implementation PRs.
- Do not silently broaden scope.
- Do not claim runtime/device success from source inspection or compilation.
- `UNKNOWN` is a valid state.
- Where evidence stops, the claim stops.

### Execution protocol

For each build turn:

1. **INSPECT** the live branch/main state and relevant evidence.
2. **SELECT ONE BOUNDED MOVE** from the gate sequence.
3. **IMPLEMENT** only that move and its necessary tests/evidence.
4. **VERIFY** with the strongest available automated evidence.
5. **RECORD** the result, including failures and UNKNOWNs.
6. **COMMIT** to this branch only.
7. Re-check branch/PR state before the next move.

No speculative rewrites. No duplicate architecture. No rebuilding already-implemented boundaries.

## Gate sequence

### Already implemented, proof still required
- G01 Identity
- G02 Canonical Workspace
- G03 Personal Field
- G04 Knowledge / Files
- G05 Arkana
- G06 Proposal Discovery
- G07 Human Authorization
- G08 Weaver Execution
- G09 Evidence
- G10 Verification

### Current implementation frontier
- **G11 Durable Capture:** complete the durable artifact → stable ID → derived interpretation → human-readable interpretation contract.
- **G12 Offline Queue / Sync:** implement and prove offline queue lifecycle, restart survival, network restoration, reconciliation, duplicate retry, and deterministic conflict handling.
- **G13 Mobile UX:** verify native empty/loading/error/success states and governed interaction boundaries on the target device.
- **G14 Full E2E:** prove one authenticated physical/device loop:
  Firebase identity → canonical workspace → personal field → knowledge → Arkana/proposal → human authorization → Weaver execution → canonical evidence → verification.
- **G15 Regression / Security:** preserve green security checks while explicitly recording known baseline repository failures. Do not erase baseline debt to manufacture green.
- **G16 Release:** produce the final APK and SHA-256, tied to the verified commit and final gate ledger.

## Required G12 contract

The implementation must make these states explicit and durable:

`PENDING_SYNC` → reconciliation attempt → success / deterministic conflict / retryable failure.

The queue must survive process restart. Reconciliation must be idempotent. Duplicate retries must not create duplicate canonical captures. Conflict behavior must be deterministic and inspectable. Network availability must never be treated as proof of successful reconciliation.

## Required G14 proof

A single evidence chain must identify the same authenticated human, workspace, authorization, execution, evidence, and verification records. UI screenshots alone are insufficient. Build success alone is insufficient.

## Evidence rules

Every completed gate records:

- commit SHA
- test/verification command or source of truth
- observed result
- unresolved UNKNOWNs
- next bounded move

Never convert an implementation claim into a runtime claim without runtime evidence.

## Stop conditions

Stop the current move when:

- the requested boundary is proven;
- a test exposes an unrelated baseline failure;
- required runtime/device access is unavailable;
- a governance ambiguity is discovered;
- implementation would require crossing the human authorization boundary.

Record the stop condition rather than improvising around it.

## Overnight objective

Advance the live repository from the current state through **G11 → G12 → G14**, then perform G15/G16 release evidence work.

The objective is not a percentage score. The objective is a machine-verifiable, human-governed Console loop that survives the physical/offline world.
