# RECONCILED-CONSOLE-ARCHITECTURE-01

**Workstream:** RECONCILED-CONSOLE-01 — operator console, derived
**Branch:** `reconciliation/verified-boundary-01` (Arkadia) — design artifact, unpushed
**Inputs:**
- Source 1 — Existing Arkadia UI (`web/public_prism`)
- Source 2 — Derived backend console (`relational-substrate/web`)
- Source 3 — `RECONCILED-BOUNDARY-MAP-01.md` @ `6ab98d6`
**Status:** architecture only. No pages, no implementation. PR held.

---

## 0. Derivation — read this first

```
Existing Arkadia UI          (what Arkadia intended to communicate)
        +
Derived backend console      (what the backend exposed when no UI was imposed)
        +
Verified Boundary Map        (what the system can now actually prove)
        ↓
RECONCILED CONSOLE ARCHITECTURE
```

**Not** this:

```
Existing UI + Derived UI → redesign        ✗
```

The distinction is the experiment. A redesign blends two *opinions about
appearance*. This derivation blends an **intent**, an **exposure**, and a
**proof** — and the proof has veto power. Where the map says a boundary is not
enforced, not deployed, or not provisioned, the console must say so, even if
both UIs would have drawn it as settled.

The console does not ask *"what should it look like?"* It asks:

> **What must a human be able to see, distinguish, authorize, inspect, and
> verify because these boundaries are real?**

---

## 1. What each source contributes (and what it does not)

| Source | Contributes | Does **not** contribute |
|---|---|---|
| **1. Existing Arkadia UI** | Intent: identity-first, the operator as a *node*; surfaces as workspaces; a mythic register; the identity strip as a persistent presence | Authority over what is true; the surfaces are organized by *workspace*, not by *boundary*; its "AUTHENTICATED" badge reads as arrival |
| **2. Derived console** | A truthful rendering discipline (errors shown verbatim, 404s honored, authorship "UNKNOWN not inferred"); a Boundary nav group; a non-collapse doctrine; an authority ceiling | Enforcement provenance: its non-collapses are largely *declared* in lab contracts, not shown as machine-checked |
| **3. Verified Boundary Map** | What is **machine-enforced** vs merely declared; the four-state claim status; the explicit non-claims (Render UNVERIFIED, Flamekeeper UNPROVISIONED, AUTHORITY-CLOSURE-01 PRE-PRODUCTION) | Any opinion about presentation |

**The reconciliation in one line:** Source 2's non-collapse doctrine gains an
*enforcement dimension* (Source 3), and Source 1's "authenticated = arrived"
is corrected to "authenticated = the first of ten stages."

---

## 2. The boundary grammar

The grammar is **derived**, not asserted. Each stage is grounded in a surface
the map proves exists, an enforcement point, and evidence. It is offered as a
**hypothesis** (§9), not as the final UI sequence.

```
IDENTITY
   │  who is calling                     — established, never inferred
   ▼
AUTHORITY
   │  what this principal may decide      — Govern, not merely authenticated
   ▼
AUTHORIZATION
   │  which operations this principal may reach
   ▼
PROPOSAL
   │  an intent, attributed to a subject
   ▼
APPROVAL
   │  a decision, by a distinct authority
   ▼
EXECUTION
   │  the act, authorized by the recorded decision
   ▼
WORK EVENT
   │  the kernel-loop record of what ran
   ▼
EVIDENCE
   │  what remains as proof it ran
   ▼
VERIFICATION
   │  whether it stayed in bounds
   ▼
REVIEW
   │  what a reviewer may see and decide
```

### 2.1 Stage grounding

| Stage | Proven backend surface | Enforcement | Evidence (test) |
|---|---|---|---|
| **IDENTITY** | `GET /api/me`, `/api/me/identity-spine`; bearer token | `api/auth.require_auth`; production fail-closed guard | perimeter §1; posture (3) |
| **AUTHORITY** | `governance/roles.json` (Flamekeeper → `Govern`); `access_level >= 3` | BC-2 `_has_govern_authority` | perimeter §4 |
| **AUTHORIZATION** | route `Depends(require_auth)`; tool registry lookup | BC-1 auth; `get_tool` existence | perimeter §1–2 |
| **PROPOSAL** | `POST /api/approvals/request` | subject attribution (`subject_ref`) | perimeter §5 |
| **APPROVAL** | `POST /api/approvals/{id}/approve\|reject` | Govern authority; **self-approval prohibited** | perimeter §4–5 |
| **EXECUTION** | `POST /api/tools/{tool}/run` | `requires_approval` gate; single-use; same-subject | perimeter §2–3 |
| **WORK EVENT** | `POST /api/job/create`, `GET /api/jobs`, `…/trace` | loop router auth (BC-3) | perimeter §1 |
| **EVIDENCE** | job `trace`, tool result envelope, `consumed_at`/`consumed_by` | — (recorded, not yet separately surfaced) | perimeter §3 |
| **VERIFICATION** | `validate_plan`; shell allowlist; read containment | BC-3; `kernel/tools_real` | perimeter §6; plan §5 |
| **REVIEW** | `GET /api/approvals` | subject-scoped listing (Flamekeeper sees all) | perimeter §5 |

Every stage in the grammar has a real surface and a real enforcement point. No
stage is aspirational.

---

## 3. The two axes — the console's core primitive

A boundary has **two independent properties**, and conflating them is the
central error the reconciled console exists to prevent.

### Axis A — Flow (the sequence)
Where in `IDENTITY → … → REVIEW` the operator is. This is the *narrative* axis.

### Axis B — Posture (the truth about each boundary)
Each boundary carries a **posture** pair:

| Mechanism status | Meaning |
|---|---|
| `ENFORCED` | machine-checked at the boundary, with a test |
| `ENFORCED (untested)` | machine-checked, no dedicated test |
| `DECLARED` | asserted in governance/contracts, not machine-checked |

| Deployment status | Meaning |
|---|---|
| `IMPLEMENTED` | code exists on the branch |
| `TESTED` | a test exercises it and passes |
| `DEPLOYED` | running on a host |
| `PRODUCTION-VERIFIED` | a live probe observed it holding |

**The console renders posture, not just presence.** A boundary drawn as a green
step without its posture is a claim the map does not support. This is the
primitive that neither Source 1 nor Source 2 has: Source 1 has no provenance;
Source 2 has live data but not enforcement provenance.

---

## 4. The non-collapse doctrine, reconciled

Source 2 renders a non-collapse list as doctrine. Source 3 tells us which of
those `≠` are now **machine-enforced** and which remain **declared**. The
reconciled console renders the difference — this is where the map has veto power.

| Non-collapse | Mechanism | Evidence | Status |
|---|---|---|---|
| **IDENTITY ≠ AUTHORITY** | `require_auth` vs `_has_govern_authority` | `test_ordinary_principal_cannot_approve` | **ENFORCED + tested** |
| **AUTHORITY ≠ AUTHORIZATION** | holding `Govern` ≠ route reachability / execution right | `test_distinct_unauthoritative_reviewer_cannot_decide`, `test_authority_denial_is_forbidden_not_unauthenticated` | **ENFORCED + tested** (Expansion Gate 01) |
| **AUTHORIZATION ≠ APPROVAL** | authenticated ≠ a recorded approval exists | `test_authenticated_but_unapproved_gated_tool_is_denied` | **ENFORCED + tested** |
| **APPROVAL ≠ EXECUTION** | approve records a decision; execution is a separate act | `test_approve_decision_does_not_execute`, `test_approved_gated_tool_runs_once` | **ENFORCED + tested** ← the discovery |
| **EXECUTION ≠ EVIDENCE** | the act vs the record (`consumed_at`, envelope, trace) | `test_approved_gated_tool_runs_once` | **ENFORCED (record), not yet surfaced** |
| **EVIDENCE ≠ VERIFICATION** | evidence vs containment/plan validation | `test_shell_allowlist_still_holds_after_approval`, `test_read_containment_still_holds` | **ENFORCED + tested** |
| **WORK EVENT ≠ EVIDENCE** | recording continuity ≠ producing evidence; the two records are separate and not joined | `test_creating_a_workevent_produces_no_evidence_or_verification`, `test_no_table_joins_a_workevent_to_evidence_or_verification` | **ENFORCED as an absence + tested** (Expansion Gate 03) |
| **EVIDENCE ≠ VERIFICATION (enterprise chain)** | capturing evidence ≠ verifying a claim; correlated by `evidence_refs`, not joined | `test_evidence_is_persisted_with_a_durable_id_and_creates_no_verification`, `test_evidence_can_exist_without_any_verification` | **ENFORCED as a correlation + tested** (Expansion Gate 04) |
| **EXECUTION ≠ WORK EVENT** | performing an act ≠ recording a Work Event; the two records are separate and not joined | `test_gated_execution_creates_no_job_and_no_workevent`, `test_kernel_job_records_execution_events_without_a_workevent` | **ENFORCED as an absence + tested** (Expansion Gate 02) |

**The discovery, made first-class.** BC-2 established `APPROVAL ≠ EXECUTION` in
code — previously the system could conceptually collapse *Approve → Execute*.
This is no longer a philosophical distinction; it is a machine-enforced
boundary, and the console should make it the spine of the approval surface: the
decision and the act are visibly two events, connected by the approval id, not
one button.

**The honesty it forces.** `EXECUTION ≠ EVIDENCE` is recorded but not surfaced.
The console must mark that as such rather than drawing it as proven. As of
Boundary Expansion Gate 01, `AUTHORITY ≠ AUTHORIZATION` is no longer in this
category — it now has a dedicated test (`tests/test_authority_boundary.py`).

**Expansion Gate 02.** `EXECUTION ≠ WORK EVENT` is not a boundary to
repair but an absence to record: execution creates no WorkEvent, and no
durable identifier joins the two. Measured by
`tests/test_execution_workevent_boundary.py` and mutation-verified. The
console renders it as a worked boundary instance
(`/boundary/execution-not-workevent`) and states the absence on the Work /
Consequence surface rather than drawing a join the substrate does not have.

**Expansion Gate 03.** `WORK EVENT ≠ EVIDENCE` is likewise an absence,
measured from an actual WorkEvent: creating one produces no evidence and no
verification, its references stay opaque, and the runtime evidence chain
binds to an execution attempt instead. Measured by
`tests/test_workevent_evidence_boundary.py` and mutation-verified. The console
renders it as a worked boundary instance (`/boundary/workevent-not-evidence`)
and states the absence on the Work / Consequence surface.

**Expansion Gate 04.** `EVIDENCE ≠ VERIFICATION` is a correlation, not a
join: evidence is created alone (`evidence()`), verification is a separate call
(`verify()`) citing evidence by `evidence_refs`, and the relationship is
asymmetric — evidence can exist unverified. Measured by
`tests/test_evidence_verification_boundary.py` and mutation-verified. The console
renders it as a worked boundary instance (`/boundary/evidence-not-verification`)
and states the correlation on the Work / Consequence surface.

---

## 5. The five operator verbs

The console's question decomposes into five affordances. Each maps to a proven
surface.

| Verb | What the human does | Proven surface |
|---|---|---|
| **SEE** | read the boundary sequence and each stage's posture | the grammar (§2) + posture (§3) |
| **DISTINGUISH** | tell enforced from declared; decision from act | non-collapse table (§4) |
| **AUTHORIZE** | make a decision as a *distinct* authority — and see whether authority is seated | `POST /api/approvals/{id}/approve\|reject`; Flamekeeper provision state |
| **INSPECT** | follow the evidence: approval → consumption → job → trace → envelope | `/api/jobs`, `…/trace`, `consumed_at` |
| **VERIFY** | see whether the act stayed in bounds (allowlist, containment, plan validation) | `validate_plan`, `kernel/tools_real` outcomes |

---

## 6. Reconciliation decisions

These are the explicit choices that make this a *derivation*, not a blend.

**From Source 1 (existing Arkadia UI) — kept:**
- Identity-first: the operator is a node; IDENTITY is stage one, and identity is
  a persistent presence, not a page.
- The mythic register and surface destinations (NovaNet/Solariun/SolSpire/Oracle)
  are kept as *destinations reachable through the boundary*.

**From Source 1 — corrected:**
- "PRISM · AUTHENTICATED" is demoted. Authentication is stage one of ten, not
  arrival. The strip becomes an *identity posture* readout that says what the
  identity is and what it does **not** yet carry (no Govern authority, etc.).
- Workspace-first navigation is subordinated to boundary-first navigation.

**From Source 2 (derived console) — kept:**
- Truthful rendering: errors verbatim, 404s honored, "UNKNOWN not inferred."
- The Boundary nav group and the non-collapse doctrine — as the seed of §4.

**From Source 2 — extended:**
- Non-collapses gain an enforcement column (§4). A declared `≠` and an enforced
  `≠` are drawn differently.
- Live data gains provenance: a value is shown with the boundary and posture
  that produced it.

**From Source 3 (verified map) — adopted wholesale:**
- The four-state claim status becomes a UI primitive (posture chip).
- The explicit non-claims become **standing banners** (§7), not footnotes.

---

## 7. What the console must never imply

Source 3's §0 non-claims become first-class, persistent, non-dismissible
surfaces. The console must not let a human infer a state the map does not
support.

| Standing state | Console obligation |
|---|---|
| **Render — UNVERIFIED** | The live host runs pre-hardening code. The console shows deployed posture as UNVERIFIED, never as green. |
| **Flamekeeper — UNPROVISIONED** | The `Govern` role is declared but no principal is seated in it. **Amended (Expansion Gate 01):** the enforcement layer also admits the `access_level >= 3` sovereign tier, which existing nodes occupy, so approvals *are* decidable today. The console states this declared/enforced gap as an unresolved boundary — the AUTHORIZE verb is blocked for ordinary principals, not universally. |
| **AUTHORITY-CLOSURE-01 — PRE-PRODUCTION** | The authority model is not closed. The AUTHORITY stage carries a pre-production marker. |
| **Nothing deployed** | Every BC carries `IMPLEMENTED · TESTED` and no more. |

This is the console honoring the experiment: **the proof has veto power over the
presentation.**

---

## 8. Structural consequences (architecture, not pages)

- **The boundary is the primary navigation axis; surfaces are destinations
  within it.** A user does not navigate to "Governance" and separately to
  "Kernel"; they navigate along the boundary and the surfaces appear where the
  boundary reaches them.
- **Posture chips are a shared primitive.** Any element that represents a
  boundary, a value, or a capability carries its `(mechanism, deployment)`
  posture.
- **Decision and act are two linked objects, never one control.** The approval
  surface cannot offer a single "approve and run"; it offers *decide* and, as a
  distinct step, *execute with this approval id* — mirroring the enforced
  boundary rather than the old collapse.
- **The evidence chain is traversable.** approval id → subject → decision →
  consumption → job → trace → tool envelope is one inspectable path.
- **Provisioning is a visible precondition.** The console distinguishes "denied
  by rule" from "not yet provisioned" — Flamekeeper is the latter.

---

## 9. Resolved — the interaction model

§9's five questions are now settled. They determine the interaction model, so
they are recorded as decisions, not left open.

**Q1 — Sequence or cycle? → Cycle, with a causal spine.**
The grammar is the **causal spine**, not a linear wizard. Review can change the
state of authorization; evidence can expose an execution problem; verification
can leave a boundary unresolved. A linear UI would imply completion merely
because the operator moved forward.

```
                    ┌──────────────┐
                    │    REVIEW    │
                    └──────┬───────┘
                           │
                           ▼
IDENTITY → AUTHORITY → AUTHORIZATION
              │              │
              ▼              ▼
          PROPOSAL → APPROVAL
                         │
                         ▼
                     EXECUTION
                         │
                         ▼
                    WORK EVENT
                         │
                         ▼
                      EVIDENCE
                         │
                         ▼
                    VERIFICATION
                         │
                         └──────────────→ REVIEW
```

The causal direction stays inspectable; the console does not pretend the system
is a one-way conveyor belt.

**Q2 — Flamekeeper unprovisioned? → A first-class authority posture.**
Not an empty-state error. The console states that the declared Flamekeeper role is
`UNPROVISIONED` and that **no automatic provisioning is permitted**. **Amended
(Expansion Gate 01):** verification against the running substrate showed the
enforcement layer also admits the `access_level >= 3` sovereign tier, which
existing nodes occupy — so the console no longer claims approvals can never be
decided. It states the declared/enforced gap as an unresolved boundary. Inspection,
evidence review, boundary inspection, provenance traversal, proposals, and
non-authoritative observation all remain available.

> **Principle: unavailable authority is visible, but never simulated.**
> An unavailable authorization capability is never drawn as a button waiting to
> be clicked.

**Q3 — Unresolved boundaries? → Persistent posture, not transient warnings.**
The two-axis primitive (§3) means a stage renders as
`EXECUTION · POSTURE: IMPLEMENTED / TESTED / DEPLOYMENT UNVERIFIED`, never as a
bare `EXECUTION ✓`. The console makes it impossible to confuse *implemented*
with *tested* with *deployed* with *production-verified*.

**Q4 — Expose unsurfaced capabilities? → Yes, subordinate to authority and posture.**
The backend exposes ~275 operations that the existing UI barely surfaces. The
reconciled console does not repeat that mistake by dumping them into navigation.
The capability chain is:

```
CAPABILITY → AUTHORITY → ELIGIBILITY → POSTURE → OPERATOR ACTION
```

A capability can exist without being actionable. The chain is explicit so the
gap between the two is visible.

**Q5 — Primary unit? → The boundary state / consequential transition.**
Not a page. The smallest meaningful object is a **BOUNDARY INSTANCE**:

```
BOUNDARY INSTANCE
  Identity
  Authority
  Authorization
  Current transition
  Posture
  Evidence
  Verification
  Available operator verbs
```

Pages are views over these objects.

---

## 10. Derived shape — four surfaces

The interaction model yields **four surfaces**, not ten pages:

| # | Surface | Role | Answers |
|---|---|---|---|
| **01 · Spine** | causal system view | the grammar (§2), interactive and inspectable, never implying every edge is currently traversable | *where in the causal system is this?* |
| **02 · Boundary Inspector** | forensic view | for any boundary: meaning, implementation, enforcement, test, posture, provenance, limitations | *what is this, and what can be proven about it?* |
| **03 · Work / Consequence** | operational view | the proposals, approvals, executions and WorkEvents that actually exist | *what happened?* |
| **04 · Authority** | sovereign-control view | `IDENTITY ≠ AUTHORITY`, `AUTHORITY ≠ AUTHORIZATION`, `APPROVAL ≠ EXECUTION`; Flamekeeper `UNPROVISIONED` visible without a fake "activate" flow | *who may do what, and is authority seated?* |

The refusal to lie is preserved from the derived console and is now part of the
product's identity: `UNKNOWN`, `IMPLEMENTED / NOT DEPLOYED`,
`PRODUCTION UNVERIFIED`, `UNPROVISIONED` — never `✓ Ready`.

---

## 11. Implementation order (narrow)

**Implementation Gate: OPEN for the console foundation only.** Not the whole
application. Not a dashboard. The first unit is **one complete boundary
instance, inspectable end-to-end**:

> **`APPROVAL ≠ EXECUTION`** — chosen because it is machine-enforced *and*
> covered by tests that demonstrate the distinction (`test_approve_decision_does_not_execute`,
> `test_approved_gated_tool_runs_once`).

If the console can represent that one boundary correctly — authority, posture,
evidence, consequences — the first real unit of the reconciled console exists,
and expansion is outward from a verified abstraction rather than ten screens
around an unverified one.

The foundation establishes: (1) the flow × posture primitive; (2) the boundary
grammar; (3) the Boundary Inspector; (4) truthful authority/unprovisioned
states; (5) provenance/evidence representation; (6) the operator verbs
See / Distinguish / Authorize / Inspect / Verify.

---

## 12. Gate

This artifact remains **architecture + interaction model only**:

- no deployment, no Render action, no Flamekeeper provisioning is performed or
  proposed;
- the branch remains **unpushed**; the PR remains a controlled delivery artifact.

Implementation now proceeds narrowly under §11, in the Arkadia console scaffold
(`web/console/`), beginning from the grammar and the posture primitive.
