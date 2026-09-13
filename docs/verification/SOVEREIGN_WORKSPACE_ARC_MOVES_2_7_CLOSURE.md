# Sovereign Workspace Arc — Moves 2–7 Closure

**STATUS:** CLOSED / VERIFIED / LIVE (as of merge `80755e4`)  
**MODE:** Schema-only archival record — no new runtime authority  
**K15 → K3:** UNTOUCHED  
**Live Barnabas operational data:** NOT INGESTED  
**Provenance frontier:** OPEN  

> This document records what was built, how it was verified, what was discovered and fixed, and what remains deliberately unclaimed.

---

## 1. Purpose

Close the sovereign workspace implementation arc from **canonical workspace through cadence** with an honest repository record so a later session can resume without re-deriving the lineage from chat.

This is **not** authorization for Move 8, Barnabas data ingestion, provenance closure, or autonomous recursion.

---

## 2. Final live stack

| Move | Name | State | Notes |
|------|------|--------|--------|
| 0 | Credential Boundary | PASSED | Prerequisite |
| 1 | Architect Identity | PASSED | Prerequisite |
| 2 | Canonical Workspace | CLOSED / VERIFIED / LIVE | Subject-bound workspace |
| 3 | WorkEvent Spine | CLOSED / VERIFIED / LIVE | Continuity records |
| 4 | Barnabas Workload | CLOSED / VERIFIED / LIVE | Structure only (`PROPOSED`) |
| 5 | Daily Pulse | CLOSED / VERIFIED / LIVE | Descriptive cadence |
| 6 | Weekly Synthesis | CLOSED / VERIFIED / LIVE | Descriptive aggregation |
| 7 | Proposal Feedback | CLOSED / VERIFIED / LIVE | Deliberation without authorization |

**Cadence arc:** COMPLETE (Pulse → Synthesis → Proposal Feedback).

---

## 3. Production API surface (bounded)

Sibling composition under `/solspire` (auth required on all):

```
GET  /solspire/workspace
POST/GET /solspire/workevents
GET  /solspire/workevents/{id}
POST/GET /solspire/workloads
POST/GET /solspire/pulses
GET  /solspire/pulses/today
POST/GET /solspire/syntheses
GET  /solspire/syntheses/current
POST/GET /solspire/proposals
GET  /solspire/proposals/{id}
POST/GET /solspire/proposals/{id}/feedback
```

**Composition rule (post–Move 5):** new surfaces are mounted with `console_router.include_router(...)` as **siblings**, not via `routes.extend` under WorkEvent.

---

## 4. Semantic distinctions enforced at runtime

| Distinction | Runtime evidence |
|-------------|------------------|
| Cadence ≠ memory / authority | Pulse/synthesis refs empty of authority/provenance; status descriptive |
| Pattern ≠ causation | Synthesis provisions empty `patterns` / `candidate_directions` |
| Recommendation ≠ approval | Synthesis does not set approval/authorization refs |
| Feedback ≠ authorization | Feedback → `UNDER_REVIEW`; `authorization_ref` remains null; not `ACCEPTED` |
| Workload ≠ authority | Workload remains `PROPOSED`; authority-ish refs empty |
| Scope ≠ authorization | Design + implementation gate held |

Protected mutation chain remains:

`HUMAN INTENT → APPROVAL → PROVENANCE → AUTHORIZATION → PASS SPEC → K15 → K3`

No Move 2–7 surface invents an alternate mutation path.

---

## 5. Verification discipline (repeated pattern)

For Moves 2–7 the closure pattern was:

```
IMPLEMENT → DEPLOY (preview) → VERIFY (runtime probes) → MERGE → RE-VERIFY (production)
```

Implemented ≠ deployed ≠ verified ≠ merged. Each step was earned separately.

Typical probe classes:

1. Unauthenticated access → **401**
2. Authenticated create/read
3. Idempotency where designed (workspace, workload, pulse-day, synthesis-week)
4. Cross-subject isolation
5. Empty authority/provenance/approval refs where required
6. Prior surfaces not regressed
7. Source boundary: no K15/K3 path introduced

---

## 6. Composition discovery (Move 5) — investment and return

### Discovery

Move 5 implementation was merged to main (`1ba4f58`) while production **`GET /solspire/pulses` returned 404**.

Root cause: composing the pulse router with `routes.extend` under the WorkEvent router did not yield a clean public sibling path. Probes of nested-looking paths either 404’d or collided with WorkEvent id routing.

### Fix

PR **#29** (`4c88ed3`):

- `console_router`: `include_router(workload_router)`, `include_router(pulse_router)`
- `workevent_router`: remove workload/pulse `routes.extend`

### Return

Moves **6** and **7** used sibling `include_router` from the start. No further composition discovery was required for those surfaces.

**Lesson recorded:** code on main is not proof the public endpoint works; production OpenAPI + unauth/auth probes are required.

---

## 7. Notable merge commits (lineage anchors)

Exact SHAs may be extended by later docs-only commits; anchors at cadence completion:

| Event | SHA (short) | Note |
|-------|-------------|------|
| Move 2 merge | `d05027e` | Canonical workspace |
| Move 3 merge | `16ddcce` | WorkEvent spine |
| Move 4 merge | `49231ec` | Barnabas workload structure |
| Move 5 implementation | `1ba4f58` | Pulse code |
| Move 5 path fix | `4c88ed3` | `/solspire/pulses` sibling mount |
| Move 6 merge | `7ba7ffe` | Weekly synthesis |
| Move 7 merge | `80755e4` | Proposal feedback |

---

## 8. Representative production smoke (illustrative)

These identifiers are **runtime smoke artifacts**, not operational Barnabas ingestion:

| Surface | Example evidence |
|---------|------------------|
| WorkEvent | Create/list under authenticated Architect subject |
| Workload | `PROPOSED`, empty authority/provenance/event refs |
| Pulse | `RECORDED`, empty authority-ish refs |
| Synthesis | `RECORDED`, empty patterns/directions/decisions/proposal/feedback refs |
| Proposal | Create `PRESENTED`; feedback → `UNDER_REVIEW`, `authorization_ref=null`, not `ACCEPTED` |

---

## 9. Explicit non-claims

This closure does **not** claim:

- Barnabas live market data, evidence packs, or deliverable completion
- Provenance frontier closed
- Any surface can authorize repository mutation
- `ACCEPTED` proposal equals `AUTHORIZED` execution
- Recursive autonomous engineering loop is running
- Move 8 (execution preparation) is designed or authorized
- K15/K3 behavior changed

---

## 10. What is ready / what is next

**Ready (infrastructure):** identity → workspace → workevents → workload structure → cadence → proposal/feedback, all subject-bound and isolatable.

**Not started without new human authorization:**

1. Move 8 — boundary between accepted proposal and human-authorized execution  
2. First real Barnabas operational workload population  
3. Provenance / authorization event wiring into K15→K3  

---

## 11. Governing one-liners

- The pulse describes the day; it does not govern the work.  
- The synthesis reveals the week; it is not authority over what happens next.  
- Feedback can change a proposal; it cannot authorize execution.  
- Merged code is not a live endpoint until probed.  

---

## 12. Closure verdict

**SOVEREIGN WORKSPACE ARC (MOVES 2–7): CLOSED**

Cadence arc: **COMPLETE**  
Constitutional mutation boundary: **HELD**  
Archive purpose: **resume without mythology**

`HUMAN SOVEREIGNTY` remains absolute for any further move.
