# Sovereign Workspace Arc — Move 8 Closure + Arc Completion

**STATUS:** Move 8 CLOSED / VERIFIED / LIVE · Arc COMPLETE (Moves 2–8)  
**BASE MERGE:** `34b0f7c769faeb0f355308f433e8363b5e0536bb`  
**MODE:** Schema-only archival record — no new runtime authority  
**PRIOR ARCHIVE:** `docs/verification/SOVEREIGN_WORKSPACE_ARC_MOVES_2_7_CLOSURE.md`  
**K15 → K3:** UNTOUCHED  
**Live Barnabas operational data:** NOT INGESTED  
**Provenance frontier:** OPEN  

> This document records Move 8 verification, the runtime-enforced  
> `ACCEPTED ≠ AUTHORIZED ≠ EXECUTED` boundary, and the completion of the  
> sovereign workspace implementation arc. It does not authorize execution,  
> PassSpec binding, or recursive autonomous work.

---

## 1. Purpose

Close the archive after Move 8 so a future session can reconstruct:

1. What Move 8 added  
2. How the acceptance → preparation boundary was proven  
3. That the sovereign workspace arc (Moves 2–8) is complete  
4. What remains explicitly unclaimed  

This is **not** authorization for Barnabas data ingestion, CP-10 mechanism selection, or K15 → K3 invocation.

---

## 2. Final live stack

| Move | Name | State |
|------|------|--------|
| 0 | Credential Boundary | PASSED |
| 1 | Architect Identity | PASSED |
| 2 | Canonical Workspace | CLOSED / VERIFIED / LIVE |
| 3 | WorkEvent Spine | CLOSED / VERIFIED / LIVE |
| 4 | Barnabas Workload | CLOSED / VERIFIED / LIVE (structure only) |
| 5 | Daily Pulse | CLOSED / VERIFIED / LIVE |
| 6 | Weekly Synthesis | CLOSED / VERIFIED / LIVE |
| 7 | Proposal Feedback | CLOSED / VERIFIED / LIVE |
| 8 | Execution Preparation | CLOSED / VERIFIED / LIVE |

**Sovereign workspace arc:** COMPLETE.

---

## 3. Move 8 contract (summary)

Governing design: `docs/control-plane/CP-MOVE8-PROPOSAL-EXECUTION-PREPARATION.md`

| Distinction | Enforced |
|-------------|----------|
| ACCEPTED ≠ AUTHORIZED | Decision sets status + `decision_ref`; `authorization_ref` remains null |
| PREPARATION ≠ PassSpec | `pass_spec_ref` always null on this surface |
| PREPARATION ≠ K15 | `k15_ref` always null |
| PREPARATION ≠ K3 | `k3_ref` always null |
| `execution_authorized` | Always `false` on preparation records |
| `auto_merge` / `auto_deploy` / `auto_execute` | Always `false` |

### API (production)

```
POST /solspire/proposals/{id}/decision
POST /solspire/proposals/{id}/prepare-execution
GET  /solspire/proposals/{id}/preparations
```

Prepare before ACCEPTED → **400**.  
Prepare after ACCEPTED → **200** with locked package (`status: PREPARED`).

---

## 4. Verification evidence (compressed)

### Pattern

```
IMPLEMENT → PREVIEW DEPLOY → RUNTIME PROBES → MERGE → PRODUCTION RE-VERIFY
```

PR: **#34** · Merge SHA: **`34b0f7c`**

### Preview (representative)

| Probe | Result |
|-------|--------|
| Unauth decision / prepare | 401 |
| Prepare before ACCEPTED | 400 |
| Decision ACCEPTED | 200; `authorization_ref=null`; boundary `ACCEPTED_equals_AUTHORIZED: false` |
| Prepare-execution | 200; `PREPARED`; `execution_authorized=false`; pass/k15/k3 null |
| Isolation | Subject B cannot get/decide Subject A’s proposal (404) |
| Regression | workspace / workevents / pulses / syntheses / proposals intact |

### Production (representative)

| Probe | Result |
|-------|--------|
| Create proposal | 200 |
| ACCEPTED | 200; `authorization_ref=None` |
| Prepare | 200; `PREPARED`; `execution_authorized=False`; k15/k3 None |

Illustrative production proposal id (smoke only): `989615a5-db09-4aa9-8c76-c90ca88ffa37`

---

## 5. Arc-level verification pattern (Moves 2–8)

Six consecutive moves closed under the same discipline after the Move 5 composition lesson:

| Move | Boundary sharpened |
|------|-------------------|
| 3 | Continuity without authority/memory claim |
| 4 | Workload `PROPOSED`; authority-ish refs empty |
| 5 | Pulse descriptive; composition discovery → sibling `include_router` |
| 6 | Synthesis descriptive; sibling composition applied |
| 7 | Feedback → `UNDER_REVIEW`; never ACCEPTED/authorize |
| 8 | ACCEPTED + PREPARED still not authorized; no K15/K3 path |

**Lesson retained:** code on `main` is not proof of a live public endpoint until probed.

---

## 6. Complete bounded SolSpire surface (auth required)

```
/solspire/workspace
/solspire/workevents
/solspire/workevents/{id}
/solspire/workloads
/solspire/pulses
/solspire/pulses/today
/solspire/syntheses
/solspire/syntheses/current
/solspire/proposals
/solspire/proposals/{id}
/solspire/proposals/{id}/feedback
/solspire/proposals/{id}/decision
/solspire/proposals/{id}/prepare-execution
/solspire/proposals/{id}/preparations
```

Composition rule: sibling `console_router.include_router(...)` mounts.

---

## 7. Semantic chain (runtime)

```
IDENTITY → WORKSPACE → WORKEVENT → WORKLOAD
        → PULSE → SYNTHESIS → PROPOSAL → FEEDBACK
        → DECISION (ACCEPTED) → EXECUTION PREPARATION (locked)
        → [HUMAN AUTHORIZATION / PassSpec / K15 → K3]   ← NOT IMPLEMENTED HERE
```

Protected mutation chain remains external to Moves 2–8:

`HUMAN INTENT → APPROVAL → PROVENANCE → AUTHORIZATION → PASS SPEC → K15 → K3`

---

## 8. Explicit non-claims

This completion record does **not** claim:

- Any surface can authorize repository mutation  
- `ACCEPTED` equals `AUTHORIZED` or `EXECUTED`  
- Preparation packages bind PassSpec, PatchApproval, K15, or K3  
- Barnabas live market data or deliverable completion  
- Provenance frontier closed  
- CP-10 mechanism selected  
- Recursive autonomous engineering loop running  
- K15 or K3 behavior changed  

---

## 9. Next gates (require new human authorization)

1. **Barnabas operational ingest** — populate workload with real R01 structure/evidence (still not authority)  
2. **PassSpec / human authorization event binding** — only if separately designed and authorized  
3. **Governed K15 → K3 execution** — only after explicit PassSpec + approval gates  
4. **CP-10 / provenance mechanism work** — independent vocabulary track  

---

## 10. Closure verdict

**MOVE 8:** CLOSED / VERIFIED / LIVE  

**SOVEREIGN WORKSPACE ARC (MOVES 2–8):** COMPLETE  

**Constitutional mutation boundary:** HELD  

**Archive role:** resume from `main` without mythology  

`HUMAN SOVEREIGNTY` remains absolute for any further move.
