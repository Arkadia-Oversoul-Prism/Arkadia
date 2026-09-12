# ARKADIA ATLAS v1.1

**Status:** synchronized architectural reference + provenance arc map  
**As of:** 2026-09-12  
**Runtime source baseline:** `29b33022049016acb7d3a382ee32586102bc24b0`  
**Documentation branch:** `architecture/control-plane-contracts-v1`

> This document is cartography, not an execution plan. It describes boundaries and current evidence. It does not grant authority.

## Master distinctions

```text
PHYSICAL REPOSITORY ≠ RUNTIME SYSTEM ≠ GOVERNANCE SYSTEM
                         ≠ ENGINEERING CAPABILITY
                         ≠ CURRENT AUTHORITY

EVIDENCE ≠ PROVENANCE ≠ AUTHORIZATION ≠ EXECUTION
```

## Status legend
- 🟢 LIVE
- 🔵 WIRED
- 🟡 PARTIAL
- 🟠 EXPERIMENTAL
- 🟣 LEGACY
- ⚪ UNKNOWN
- 🔐 GOVERNED
- 🚫 BLOCKED

## MAP 01 — Physical Repository

The repository contains presentation, API composition, Kernel, SolSpire, Knowledge OS, Corpus, Providers, Weaver, Lab, governance, deployment/configuration, Android and bot surfaces, plus historical or experimental material. Directory presence is not liveness evidence.

| Plane | Principal locations | Current reading |
|---|---|---|
| Presentation | `web/public_prism/`, `sonata-android/` | 🟢 / 🟡 |
| Composition | `api/main.py` | 🟢 |
| Execution | `kernel/` | 🟢 |
| Project runtime | `solspire/` | 🟢 |
| Knowledge | `knowledge/` | 🟢 |
| Ingestion | `corpus/` | 🔵 |
| Intelligence | `providers/` | 🟡 |
| Engineering | `weaver/` | 🔐 |
| Governance | `lab/`, `governance/` | 🔐 / 🚫 |
| Experimental / legacy | `arkana_rasa/`, `arkana_space/`, `sonata/`, `engine/`, `parsers/`, `schemas/`, `sanctum/` | 🟠 / 🟣 / ⚪ |

## MAP 02 — Runtime Circuit

```text
Human / Interface
    ↓ AUTH
Prism / Android / Bots
    ↓ CALL
Canonical API
    ↓ COMPOSE
Auth + Identity + Oracle + Services
    ├── Knowledge OS ← Corpus
    ├── Provider Fabric
    ├── Kernel
    └── SolSpire

Engineering:
Objective → Weaver Recon → Analysis → Proposal → PassSpec
    → K15 → K3 → Verify → Git publication
```

The canonical engineering mutation boundary remains K15 → K3. The provenance arc has not modified that path.

## MAP 03 — Lab Circuit

```text
PHASE 1 Observe
  ↓
PHASE 2 Pattern recognition
  ↓
PHASE 3 Council
  ↓
PHASE 4 Proposal
  ↓
PHASE 5 Execution framework
  ↓
PHASE 6 Persistence / durability
  ↓
PHASE 7 Calibration
  ↓
PHASE 8 Possibility / recognition
  ↓
PHASE 9 Human decision
  ↓
PHASE 10 Governed binding
  ↓
DRY-RUN PACKAGE
```

Lab Phases 1–10 are sealed complete under Level 2. Phase 10 does not merge, deploy, or autonomously mutate.

## MAP 04 — Authority Boundary

```text
CAPABILITY
    ↓
ELIGIBILITY
    ↓
AUTHORIZATION
    ↓
EXECUTION
    ↓
VERIFICATION
    ↓
PUBLICATION
```

Capability ≠ authorization. Existence ≠ current use. Human sovereignty remains external.

## MAP 05 — Five Architectural Dialects

| Dialect | Function | Boundary |
|---|---|---|
| Lab | staged observation, calibration, possibility, decision, governed binding | no autonomous authority |
| Control Plane | contract, observation, drift, exception, seam definition | observation/contract layer |
| Provenance | evidence, origin, authority-event semantics, collision analysis | does not grant authority |
| Spiral Grammar | symbolic transformation vocabulary | interface/framework, not sovereignty |
| Oracle | structured encounter with possibility | pattern ≠ truth; interpretation ≠ decision |

These are distinct dialects of one architectural field, not five competing authorities.

## MAP 06 — Shared Meta-Grammar

A common semantic structure has emerged across the Lab, Control Plane, Provenance, Spiral Grammar and Oracle:

```text
STATE
  ↓
OBSERVATION
  ↓
EVALUATION
  ↓
DECISION
  ↓
NEXT STATE
```

Transformation connects states; provenance cross-cuts the chain. This is a semantic meta-grammar, not a claim that Spiral Grammar is the implementation language underneath the entire Control Plane.

## MAP 07 — Control Plane / Provenance Arc

```text
CP-05 Authority Boundary
        ↓
CP-10 Authority Provenance
        ↓
CP-10.1 Provenance Evidence Semantics
        ↓
CP-10.2 Mechanism Acceptance Criteria
        ↓
CP-10.3 Collision Resolution Criteria
        ↓
CP-10.4 Evidence of Origin Semantics
        ↓
CP-10.5 Hybrid Origin Candidate
        ↓
CP-10.6 Origin Discrimination Semantics
        ↓
CP-10.7 Mechanism Arena Frame
        ↓
CP-10.8 Deliberate Attestation Candidate
        ↓
CP-10.9 Existence-Bound Origination Candidate
        ↓
OPEN FRONTIER — CP-10.10 NOT YET AUTHORED
```

### Current arc state

| Item | State |
|---|---|
| CP102-G07 | 🔴 unresolved semantic collision |
| G08–G15 | 🔴 / 🟡 unresolved provenance gaps |
| Mechanism | unselected |
| Implementation | none |
| R3 eligibility | not established |
| Repository mutation by candidate work | none |
| CP-10.8 | discriminating failure |
| CP-10.9 | discriminating failure |
| CP-10.10 | open, not authored |

## MAP 08 — Permanent Distinctions

1. `ATTESTATION ≠ ORIGINATION`
2. `PRECEDENCE ≠ CAUSATION`
3. `EVENT-IDENTITY DEPENDENCE ≠ EVIDENCE OF CAUSAL ORIGINATION`

The arc has also fixed the three-layer epistemic distinction:

`CAUSAL CLAIM → CAUSAL FACT → EVIDENCE OF CAUSAL FACT`

The third remains uninstantiated by the current candidate work.

## MAP 09 — Closed False-Solution Classes

1. **Attestation-only:** deliberate attestation to an event does not prove origination of the event.
2. **Precedence-only:** an act occurring before an event does not prove that the act caused the event.
3. **Identity-dependence-only:** defining event identity through an alleged originating act does not independently prove the causal relation.

These are knowledge closures, not mechanism selections.

## MAP 10 — Collision Register

Primary collision: **CP102-G07 — PassSpec treated as human authorization.**

The repository is structurally strong around identity/session boundaries, role vocabulary, structural artifact binding, and K15→K3 mutation containment. It remains non-R3-eligible because the current semantics still collapse PassSpec into human authorization and no human-origin authority-event provenance primitive has been established.

Secondary gaps: event-level origin evidence, deliberate-origin evidence, first-class provenance state, provenance-specific fail-closed semantics, authority-event temporal semantics, complete delegation lineage, contradiction semantics, and witness attestation path.

## MAP 11 — Evidence / Truth Rule

```text
CURRENT CODE
      > CURRENT TESTS
      > CURRENT RUNTIME
      > CURRENT CONFIG
      > CLOSURE RECORD
      > HISTORICAL DOCUMENTATION
```

The hierarchy is an evidence discipline, not a claim that documentation has no value.

## MAP 12 — Control Plane Boundary

The Control Plane is a contract and observation layer. It may inspect, classify, compare, report drift and expose exceptions. It does not execute, authorize, mutate, deploy, or replace Kernel, SolSpire, Weaver, Knowledge OS, or Lab authority.

If the Control Plane acquires execution authority, the Atlas must treat that as a new architectural boundary and re-audit it.

## Calibration to originating trajectory

The current arc remains aligned with the continuity objective that initiated this thread: preserve architectural memory, make boundaries explicit, inspect before acting, distinguish evidence from assertion, and keep human decision sovereign.

The work has evolved beyond a component map into an epistemic architecture. That evolution is recorded, not smuggled into runtime authority.

## Atlas invariant

> A seam is acceptable when its boundary is explicit, its authority is known, its state ownership is defined, and its crossing is observable.

## Non-goals
- No subsystem merger
- No new runtime
- No new memory system
- No autonomous execution
- No authorization escalation
- No provider-convergence claim
- No assumption that repository presence proves liveness
- No replacement of existing governance or mutation machinery
- No mechanism selection by Atlas
