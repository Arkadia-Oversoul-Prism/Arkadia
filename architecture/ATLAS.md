# ARKADIA ATLAS v1.0

**Status:** synchronized architectural reference  
**As of:** 2026-09-10  
**Source commit:** `29b33022049016acb7d3a382ee32586102bc24b0`

> This document is cartography, not an execution plan. It describes boundaries and current evidence. It does not grant authority.

## Master distinction

```text
PHYSICAL REPOSITORY ≠ RUNTIME SYSTEM ≠ GOVERNANCE SYSTEM
                         ≠ ENGINEERING CAPABILITY
                         ≠ CURRENT AUTHORITY
```

## Status legend

- 🟢 LIVE
- 🔵 WIRED
- 🟡 PARTIAL
- 🟠 EXPERIMENTAL
- 🟣 LEGACY
- ⚫ ORPHANED
- ⚪ UNKNOWN
- 🔐 GOVERNED
- 🚫 BLOCKED

## MAP 01 — Physical Repository

The repository contains the presentation plane, API composition root, Kernel, SolSpire, Knowledge OS, Corpus, Providers, Weaver, Lab, governance, deployment/configuration, Android and bot surfaces, plus historical or experimental material.

The physical tree is intentionally larger than the proven live runtime. Directory presence is not liveness evidence.

### Primary planes

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

Engineering circuit:
Objective → Weaver Recon → Analysis → Proposal → PassSpec
    → K15 → K3 → Verify → Git publication
```

### Core runtime circuits

**A. Human/interface:** client → Firebase/AuthContext → `apiClient.ts` → FastAPI API.

**B. Intelligence:** conversational/Oracle route → Knowledge context assembly → provider selection → response and persistence/archive paths.

**C. Kernel execution:** JobStore → Worker → intent classification/planning → tool registry → verification → trace/runtime state.

**D. SolSpire:** console route → IntentRouter → Planner → in-process `ExecutionRuntime`; engineering mutation operations are blocked and redirected toward Weaver.

**E. Engineering:** objective → Weaver reconnaissance/analysis → PassSpec → K15 → K3 when explicitly authorized → verification → commit/push.

**F. Knowledge ingestion:** GitHub/Drive/Joplin/Obsidian/static/conversation sources → Corpus/Pipeline → vault/graph/embeddings → Knowledge DB → Context Engine.

**G. Governance:** human decision → binding package → governed execution boundary. Phase 10 binding currently ends at dry-run.

## MAP 03 — Engineering / Lab Circuit

```text
PHASE 1  Observe
   ↓
PHASE 2  Pattern recognition
   ↓
PHASE 3  Council
   ↓
PHASE 4  Proposal
   ↓
PHASE 5  Execution framework
   ↓
PHASE 6  Persistence / durability
   ↓
PHASE 7  Calibration
   ↓
PHASE 8  Possibility / recognition
   ↓
PHASE 9  Human decision
   ↓
PHASE 10 Governed binding
   ↓
DRY-RUN PACKAGE
```

Lab Phases 1–10 are sealed complete under the current Level 2 boundary. Phase 10 does not merge, deploy, or autonomously mutate.

Weaver is a deeper engineering capability boundary. Its existence does not authorize its use by the Lab.

## MAP 04 — Authority Map

| Capability | Exists | Current Lab path | Authority reading |
|---|---:|---:|---|
| Observe | ✅ | Yes | Read |
| Analyze | ✅ | Yes | Advisory |
| Propose | ✅ | Yes | Advisory |
| Recognize opportunities | ✅ | Yes | Recognition |
| Record human decision | ✅ | Yes | Human |
| Bind APPROVE | ✅ | Yes | Governed |
| K15 preflight | ✅ | Yes | Governed |
| K15 mutation | ✅ | No in Phase 10 | Governed capability |
| K3 mutation | ✅ | No in Phase 10 | Governed capability |
| Commit | ✅ | Via mutation path | PassSpec-governed |
| Push | ✅ | Via mutation path | PassSpec-governed |
| Merge | ❌ in Lab | No | Blocked / external human boundary |
| Deploy | ❌ in Lab | No | External boundary |
| Autonomous mutation | 🚫 | No | Governance-disabled |

### Authority invariant

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

**Capability ≠ authorization. Existence ≠ current use.**

## Nine architectural seams, now declared as contracts

1. `kernel ≠ solspire` → Execution Contract
2. Knowledge OS ≠ Kernel memory ≠ Weaver Echofield ≠ localStorage → State Contract
3. Corpus ≠ Knowledge OS → Ingestion Contract
4. Provider abstraction ≠ convergence → Provider Contract
5. Governance config ≠ universal enforcement → Authority Contract
6. Physical repository ≠ runtime → Runtime Manifest Contract
7. Canonical API ≠ every interface → Interface Contract
8. Phase 10 ≠ Weaver mutation → Mutation Boundary Contract
9. Current code ≠ all documentation → Evidence / Truth Contract

## Evidence / Truth rule

```text
CURRENT CODE
      > CURRENT TESTS
      > CURRENT RUNTIME
      > CURRENT CONFIG
      > CLOSURE RECORD
      > HISTORICAL DOCUMENTATION
```

The hierarchy is an evidence discipline, not a claim that documentation has no value.

## Control Plane boundary

The Control Plane is defined as a **contract and observation layer only**. It may inspect, classify, compare, report drift and expose exceptions. It does not execute, authorize, mutate, deploy, or replace Kernel, SolSpire, Weaver, Knowledge OS, or the Lab.

If the Control Plane acquires execution authority, this Atlas must treat that as a new architectural boundary and re-audit it.

## Atlas invariant

> A seam is acceptable when its boundary is explicit, its authority is known, its state ownership is defined, and its crossing is observable.

## Non-goals of this Atlas

- No subsystem merger
- No new runtime
- No new memory system
- No autonomous execution
- No authorization escalation
- No claim of provider convergence
- No assumption that repository presence proves liveness
- No replacement of existing governance or mutation machinery
