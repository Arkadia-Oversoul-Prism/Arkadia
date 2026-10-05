# Oversoul Prism to Arkadia Substrate Mapping

## Status
Architecture mapping. No new authority. No 144-cell runtime integration.

This document maps the proven PR #291 vertical slice onto the existing Arkadia substrate. The mapping reuses existing primitives instead of creating a parallel Prism runtime.

## Canonical mapping

| Boundary | Existing substrate | Responsibility | Status |
|---|---|---|---|
| Human Intent | authenticated human + Arkana session/thread | establish who is asking and what they want | EXISTING |
| Context | Arkana Oracle spine + Knowledge OS context | assemble bounded context | EXISTING |
| Prism Transformation | Arkana reasoning/proposal layer | transform context into candidate result | EXISTING / MAPPING |
| Candidate Result | Weaver Proposal | explicit objective, rationale, actions | EXISTING |
| Evidence | Weaver EvidenceRecord / evidence spine | support an observable claim | EXISTING |
| Verification | Weaver VerificationRecord | assess claim against evidence | EXISTING |
| Human Acceptance | human authority / decision surface | accept verified result for operational use | PARTIAL |
| Execution Authorization | Weaver HumanAuthorityEvent + Authorization | grant bounded action and constraints | EXISTING |
| Execution | Weaver ExecutionAttempt / Engineering Lab | perform authorized action | EXISTING |
| WorkEvent | SolSpire WorkEvent spine | record consequential state transition | EXISTING, CAUSAL JOIN GAP |
| Review | Prism review/amendment contract | inspect event without rewriting it | RESEARCH CONTRACT |
| Completion | Prism completion contract | establish explicit outcome condition | RESEARCH CONTRACT |
| Production Acceptance | governance boundary | permit durable production projection | RESEARCH CONTRACT |
| Knowledge Projection | Knowledge OS / Weaver knowledge mutation | persist accepted durable knowledge | EXISTING PRIMITIVES, GATE GAP |

## Target architecture

Human → Arkana → Weaver → Human Acceptance → Weaver Authorization → Weaver Execution → SolSpire WorkEvent → Review → Completion → Production Acceptance → Knowledge OS → Arkana context

### Arkana
Arkana is the interaction and reasoning expression, not the authority owner.

Arkana may receive human intent, resolve the authenticated session/thread, retrieve Knowledge OS context, generate candidate interpretations and proposals, surface evidence and uncertainty, request acceptance or authorization, and display the resulting state chain.

Arkana must not silently authorize itself, convert model confidence into verification, convert verification into acceptance, infer execution permission from conversation, or write production knowledge merely because a response was generated.

The existing session_id to thread_id mapping remains the continuity spine.

### Weaver
Weaver is the governed orchestration and execution surface.

The existing EnterpriseOrchestrationStore already provides canonical records, interpretations, proposals, human authority events, bounded authorization, execution attempts, evidence, verification, and causal correlation. The Prism integration should reuse these primitives.

Required correlation envelope for the integrated slice:

- prism_trace_id
- project_ref
- thread_id
- proposal_id
- verification_id
- acceptance_id
- authorization_id
- execution_attempt_id
- work_event_id

Identifiers are references, not proof. Each referenced record remains independently inspectable.

### Acceptance
The existing authorization path is not the same thing as the Prism acceptance boundary.

Target state: VERIFIED → ACCEPTED → AUTHORIZED, unless one explicit human decision contains both bounded acceptance and execution authorization. Even then, the records remain conceptually distinct.

Acceptance means a verified result is eligible for operational use. Authorization means a bounded actor/action/scope is permitted to execute.

### WorkEvent
The existing solspire WorkEvent is the correct observable consequence substrate. It already carries stable identity, version, timestamps, subject/workspace binding, parent and sequence references, actor/scope references, state-before/state-after references, decision/witness references, and supersession/reversal references.

WorkEvent creation must remain distinct from authorization, evidence, verification, completion, and production acceptance.

Required causal bridge:

ExecutionAttempt → observed transition → WorkEvent

The bridge must show what was observed. It must never retroactively create permission.

### Review and amendment
Review points to the immutable WorkEvent.

WorkEvent → Review → ACCEPTED / REJECTED / CLARIFIED

An amendment creates a new record referencing the original event. The original WorkEvent remains unchanged.

### Completion
Execution means an action occurred. WorkEvent means a consequential transition was observed. Completion means an explicit outcome condition was satisfied.

EXECUTED is not COMPLETED.

Completion must reference the WorkEvent and supporting completion evidence.

### Production acceptance
Production acceptance is the governance gate before a completed result becomes durable production knowledge or another consequential production state.

COMPLETED → PRODUCTION_ACCEPTANCE → KNOWLEDGE_PROJECTION

Merge, deployment, or model confidence cannot substitute for production acceptance.

MERGE is not DEPLOYMENT and DEPLOYMENT is not PRODUCTION_ACCEPTANCE.

### Knowledge OS
Knowledge OS remains the durable continuity substrate.

The projection path is accepted production result → knowledge projection → durable knowledge → future Arkana context.

A conversational response is not automatically a production knowledge mutation. Knowledge mutations must retain their causal source and remain distinguishable from interpretation, evidence, verification, acceptance, and execution.

## End-to-end target

HUMAN → ARKANA → WEAVER → HUMAN ACCEPTANCE → WEAVER AUTHORIZATION → WEAVER EXECUTION → SOLSpire WorkEvent → REVIEW → COMPLETION → PRODUCTION ACCEPTANCE → KNOWLEDGE OS → ARKANA CONTEXT

This creates a closed continuity loop without creating a closed authority loop.

Continuity may return to Arkana. Authority returns to the human.

## 144-cell research boundary

The historical 12×12 lattice remains outside this substrate integration.

Arkana and Weaver may eventually host an optional Prism transformation adapter that references Axx-Lyy research coordinates. That adapter is not authorized to create truth, verification, acceptance, authorization, execution, or WorkEvents merely because a lattice transformation occurred.

No production path may dispatch arbitrary Axx-Lyy nodes, treat lattice depth as authority, treat node output as verified fact, treat convergence as acceptance, create authorization from lattice state, or create WorkEvents merely because a lattice transformation occurred.

The lattice can enter the production substrate only through the same evidence, verification, acceptance, authorization, execution, and observability boundaries defined here.

## Integration gates

1. Every vertical-slice record has an inspectable causal identifier.
2. Arkana can show current boundary state without inventing missing state.
3. Weaver distinguishes proposal, verification, acceptance, authorization, execution, and evidence.
4. A consequential execution can produce a WorkEvent with explicit causal correlation.
5. Review cannot mutate the original WorkEvent.
6. Completion cannot be inferred solely from execution status.
7. Production acceptance is independently recorded.
8. Knowledge projection requires the appropriate acceptance boundary.
9. UNKNOWN survives every layer unless explicitly resolved.
10. No Axx-Lyy research node gains runtime authority merely by being referenced.

## Current gaps

The following remain UNKNOWN / not yet implemented:

- canonical acceptance record in the live substrate;
- canonical review store attached to WorkEvent;
- canonical completion record attached to WorkEvent;
- canonical production-acceptance record;
- canonical execution-attempt to WorkEvent causal join;
- UI that renders the complete chain in Arkana and Weaver;
- production enforcement of the final knowledge-projection gate.

These are implementation targets, not claims of existing capability.

## Decision

Do not build a second Prism runtime.

Fuse the proven Prism governance chain into the existing Arkadia substrate.

Arkana supplies interaction and reasoning. Weaver supplies governed orchestration and execution. SolSpire supplies WorkEvent observability. Knowledge OS supplies durable continuity. Human authority remains the acceptance and consequential decision boundary.

The Prism is the coherence architecture connecting these surfaces, not another store, agent, or destination.