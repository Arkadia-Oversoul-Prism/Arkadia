# Phase 1 / CP10 Acceptance Criteria Amendment

**Status:** ADOPTED (Path B)  
**Effective on:** commit that introduces this document  
**Amends:** Phase 1 sealing interpretation as previously implied by `.github/workflows/sg-02-fe-2-v.yml` Enforce step  
**Does not rewrite:** `docs/engineering-lab-v0.1.md` historical text as if it had always contained this rule  

---

## 1. Purpose

This document is an **explicit architectural/governance amendment** to the Phase 1 seal criteria for the Engineering Lab / CP10 verification path.

It exists so that:

1. Phase 1 sealing is defined by **accepted executable criteria**, not by an unstated workflow-only rule.
2. A surface that cannot yet be verified honestly is **not** reclassified as PASS.
3. Deferred evidence remains visible and becomes a **Phase 2 opening obligation**.

---

## 2. Rationale (audit trail)

Read-only audit of the repository established:

| Finding | Evidence class |
|---------|----------------|
| Lab v0.1 defines Phase 1 as observational/analytical and documents authenticated **API** Lab access | SOURCE (`docs/engineering-lab-v0.1.md`) |
| Lab v0.1 does **not** define a formal “Phase 1 seal” or mandate authenticated **browser** Lab verification | SOURCE |
| CP10 workflow browser step can succeed while logging authenticated Lab lens as BLOCKED | SOURCE (workflow) |
| CP10 Enforce step historically ended with unconditional `exit 2` after executable gates, stating seal cannot be earned while the authenticated browser lens is BLOCKED | SOURCE (workflow, since commit introducing CP10) |
| No separate ADR/spec mandated that `exit 2` rule outside the workflow file | SOURCE (absence) |

Therefore the authenticated browser Engineering Lab lens was elevated to a **seal-blocker by workflow implementation**, not by a standalone Phase 1 acceptance document.

Path B chooses to **clarify acceptance criteria** rather than invent credentials or treat BLOCKED as PASS.

---

## 3. Amended Phase 1 seal definition

### 3.1 Phase 1 seal requires

All of the following **executable CP10 gates** to PASS on the sealed commit:

| Gate | Meaning |
|------|---------|
| Lab unit/API tests (CP10-A) | Trajectory + router boundary tests |
| Backend readiness | Existing API process responds |
| Lab API verification | Unauthenticated 401; authenticated read of `/api/lab/overview` structure (existing CP10 API step) |
| Frontend readiness | Existing frontend process responds |
| Browser route verification | **Unauthenticated** route thresholds and absence of console/page/hard network errors as defined by the browser step |
| Security artifact scan | No forbidden secret patterns in CP10 logs |
| Mutation boundary | Tip commit does not introduce forbidden app/deploy mutation surface per workflow rules |

### 3.2 Explicitly **not** a Phase 1 sealing condition

| Item | Status under this amendment |
|------|----------------------------|
| Authenticated **browser** session loading Engineering Lab private content | **Not required** for Phase 1 seal |
| Full authenticated UI walkthrough of Lab | **Not required** for Phase 1 seal |

### 3.3 Epistemic rule

| Prior label | After this amendment |
|-------------|----------------------|
| Authenticated browser Engineering Lab lens: **BLOCKED** | **DEFERRED BY ACCEPTANCE CRITERIA** (Phase 2 opening gate) |
| BLOCKED | **Must not** be recorded or treated as **PASS** |

Honesty constraint: inability to verify remains visible; deferral is criteria scope, not evidence fabrication.

---

## 4. Deferred obligation (Phase 2 opening)

**Authenticated browser verification of the Engineering Lab** becomes the **opening verification obligation of Phase 2**.

Minimum legitimate form (when Phase 2 begins):

1. Use a real CI-controllable identity accepted by the same auth stack as production (no auth bypass).
2. Establish a browser session with that identity.
3. Assert Engineering Lab content that unauthenticated users must not obtain.
4. Record PASS only from that runtime evidence.

Phase 2 work (features, autonomy, mutation expansion) **must not** begin until:

1. This amendment is committed, and  
2. Phase 1 is sealed under the **amended** executable criteria (including aligned CP10 Enforce semantics), and  
3. Human authorization for Phase 2 is explicit.

---

## 5. Workflow alignment (separate authorization)

Aligning `.github/workflows/sg-02-fe-2-v.yml` Enforce semantics to this amendment is a **subsequent** verification-harness change.

It is **not** performed by this document alone.

Until the workflow is aligned:

- Executable gates may pass while Enforce still exits non-zero under the **legacy** workflow rule.
- Phase 1 remains **unsealed** until a CP10 run under **aligned** Enforce reports success against §3.1 only.

---

## 6. Non-goals

This amendment does **not**:

- weaken Lab API authentication;
- authorize auth bypass or forged production credentials in browser;
- convert BLOCKED → PASS;
- start Phase 2 implementation;
- alter application behavior.

---

## 7. Summary statement

> Phase 1 seal requires the defined executable CP10 gates to pass. Authenticated browser verification of the Engineering Lab is not a Phase 1 sealing condition. It remains required evidence, but is explicitly deferred to Phase 2 and becomes its opening verification gate.
>
> BLOCKED does not become PASS. It becomes DEFERRED BY ACCEPTANCE CRITERIA.

---

**Closure record:** `docs/verification/PHASE1_CLOSURE.md` (seal chain and archive boundary).
