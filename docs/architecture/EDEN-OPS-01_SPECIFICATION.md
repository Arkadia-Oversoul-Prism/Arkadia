# EDEN-OPS-01 — Live Eden Operations Cockpit

**Status:** AUTHORIZED — SPECIFICATION FROZEN 2026-09-28
**Baseline:** ARK-WEAVER-01 on main (`eab0690`); Eden Food Systems instantiation VERIFIED
**Parent invariants:** where evidence stops the claim stops; no arrow gets borrowed standing;
Human Authority Event ≠ WorkEvent; K15→K3 sole repository mutation path;
Eden truth boundary (RECORDED / COMMITTED / ESTIMATED / UNKNOWN)

## 1. Purpose

Give the two humans operating Eden (Divine Favour Yusuf + Jessica) a single
enterprise operating surface that turns real Eden information into recorded work,
visible decisions, governed actions, and verified outcomes using the ARK-WEAVER-01
primitives already on main.

This is the first living cell of the Ghost COO substrate.

It is not a second architecture exercise, a second event system, unrestricted
agent mode, a new Eden scaffold, a full multi-enterprise canvas, or autonomous
spending / outreach / commitment of funds.

## 2. Constitutional Invariants

1. Where evidence stops, the claim stops.
2. No arrow gets borrowed standing.
3. Identity ≠ Authority ≠ Authorization ≠ Execution ≠ Consequence ≠ Verification.
4. Human Authority Event is not a WorkEvent subtype.
5. K15 → K3 remains the sole mutation path for repository state.
6. UNKNOWN remains UNKNOWN until Evidence + Verification change it.
7. The cockpit is a projection of the machinery, never the source of truth.
8. High agency in analysis; low agency in authority.
9. Two humans may hold multiple desks; the system holds the complexity.

## 3. Scope

### In scope

| Zone | Responsibility |
|------|----------------|
| TODAY | Critical objectives, blockers, unknowns, decisions required |
| WORK | Tasks with owner, workstream, due, status, evidence, dependencies |
| INTELLIGENCE | Ingestion → Canonical → Interpretation → impact → unknowns → recommendation |
| DECISIONS | Proposals awaiting human authority (approve / reject / modify) |
| EXECUTION | Authorized → preparation → attempt → evidence → verification |
| FIELD | Master projection driven only by records |

Also: binding the two real humans to multiple desks; one living-cell supplier path;
Field updates that never invent RECORDED / COMMITTED / SPENT values.

### Out of scope

- New Eden scaffold or department structure
- Changes to K15 / K3 / PassSpec / PatchApproval
- Operational-store namespacing refactor
- Reverse-walk HTTP API productization
- Full Knowledge OS deep integration
- Multi-enterprise multi-tenancy
- Autonomous tool execution without Authorization
- Filling UNKNOWN dashboard fields by hand
- Pre-existing architecture debt (api/main.py budget, api/nodes.py inversions)

## 4. Binding Model

| Role | Human coverage |
|------|----------------|
| Procurement | Jessica / Divine Favour |
| Logistics | Jessica / Divine Favour |
| Quality | Jessica / Divine Favour |
| Marketing | Jessica / Divine Favour |
| Brand / CX | Jessica / Divine Favour |
| Digital | Jessica / Divine Favour |
| Operations / Finance | Jessica / Divine Favour |
| Contingency / Reserve | Financial control only |

Binding is explicit, reversible, and recorded. Multiple desks per human are normal.

## 5. Transition Contracts

```
HUMAN INPUT
  → CANONICAL RECORD
  → INTERPRETATION RECORD
  → KNOWLEDGE MUTATION (if warranted)
  → OPERATIONAL EVENT
  → PROPOSAL (if action recommended)
  → HUMAN AUTHORITY EVENT + AUTHORIZATION
  → EXECUTION ATTEMPT
  → EVIDENCE RECORD
  → VERIFICATION RECORD
  → FIELD PROJECTION UPDATE (only where verified)
```

- Cockpit never writes commercial facts except through Evidence → Verification.
- Proposal cannot become Execution Attempt without causally bound Authorization.
- Task completion is not verification of a business outcome.
- Field counters are derived queries over the ARK-WEAVER-01 store.

## 6. Living-Cell Acceptance Test

1. Human enters supplier message: availability indicated, price not confirmed.
2. Canonical Record created.
3. Interpretation records availability; price remains UNKNOWN.
4. Proposal surfaces: verify price.
5. Human Authority Event + Authorization.
6. Execution Attempt prepared.
7. Evidence captures result (e.g. price = ₦1,200/kg).
8. Verification establishes the claim.
9. Field updates only evidence-supported fields; other unknowns stay UNKNOWN.
10. Reverse-walk from verified claim reaches Evidence (and terminal sources as applicable).

## 7. Acceptance Criteria

1. Two real humans bound to multiple desks without inventing staff.
2. One supplier signal traverses the full living-cell path with durable records.
3. Field values for commercial/capital facts change only via Evidence → Verification.
4. UNKNOWN fields remain UNKNOWN when unsupported.
5. Reverse-walk from any surfaced claim reaches a terminal source.
6. ARK-WEAVER-01 contract suite remains 4/4 green.
7. No new repository mutation path; no Eden scaffold edits; no K15/K3 changes.
8. Cockpit does not claim autonomous authority.

## 8. Implementation Gate Sequence

```
EDEN-OPS-01 SPECIFICATION          ← FROZEN
  ↓
ARCHITECT AUTHORIZATION            ← GRANTED
  ↓
IMPLEMENTATION BRANCH
  ↓
Human role binding
  ↓
Minimal six-zone cockpit surface
  ↓
Wire ingestion → ARK-WEAVER-01 primitives
  ↓
Living-cell supplier path
  ↓
Field projection from records only
  ↓
VERIFY acceptance criteria + contract suite
  ↓
Ready for review → merge
```
