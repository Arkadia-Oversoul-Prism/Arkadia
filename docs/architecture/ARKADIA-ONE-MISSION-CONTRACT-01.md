# Arkadia One — the smallest shared mission and worker contract

**Status:** DESIGN — not implemented, not deployed, not accepted.
**Date:** 2026-10-28
**Base revision measured:** `9195334c` (`main` at time of writing)
**Authority:** design only. This document proposes; it does not authorize, merge, or deploy.
**Predecessor:** `docs/control-plane/evidence/arkadia-one-console-walkthrough-01/EVIDENCE.md` (G2)

---

## 0. The answer, first

> **What is the smallest shared mission and worker contract that lets Arkadia coordinate its
> existing systems and one external engineering agent without surrendering human authority?**

**It already exists — twice. The contract is not missing. What is missing is a currency
binding, and that is a much smaller change than the one being proposed.**

Measured at `9195334c`:

| Contract | Where | Lifecycle vocabulary | Status |
|---|---|---|---|
| `ARKADIA-WORKER-CONTRACT-v1` (M09) | `weaver/engineering_worker.py` (141 L), `weaver/engineering_router.py` (326 L), `weaver/execution_adapter.py` (60 L) | WAKE→LOAD→VALIDATE→ROUTE→PLAN→EXECUTE→CHECKPOINT→VERIFY→REPORT→TERMINATE | implemented, scheduled |
| Engineering Lab substrate (EL-01…EL-10) | `lab/engineering_lab/` (16 modules), `api/lab_routes.py` (27 routes) | PROPOSED→AUTHORIZED→…→READY_FOR_REVIEW | implemented, HTTP-exposed |

Both carry the **same** state vocabulary (`PROPOSED, AUTHORIZED, QUEUED, RUNNING,
CHECKPOINTED, VERIFYING, READY_FOR_REVIEW, REVISION_REQUIRED, BLOCKED, FAILED, COMPLETED,
ABORTED, EXPIRED` — `lab/engineering_lab/contracts.py:93-106` and
`docs/control-plane/worker.contract.json:22`). Both forbid the same collapses
(`FORBIDDEN_DIRECT_TRANSITIONS`; `prohibitions: collapse_completed_into_accepted`).

They were built independently and **neither knows the other exists**:
`grep -rn engineering_lab weaver/` → one line, an *import* in `weaver/console_adapter.py:21`;
`grep -rn enterprise_orchestration lab/` → **0**.

So the real question is not "what should the contract be." It is:

> **Why can two implementations of the same contract both be correct and still not compose?**

Because **evidence in neither substrate carries a revision.** That is the same defect class as
G2, one layer down — and it is why this document is short.

---

## 1. The finding that sets the size of the work

The G2 repair established the currency contract for the *interface*: live state, source state,
verification state, historical state, and acceptance state must not collapse into one indicator.

**The same collapse exists in the execution substrate, and it is structural — not a bug.**

### 1.1 Neither evidence table can answer "true of which revision?"

```sql
-- weaver/enterprise_orchestration.py:127
CREATE TABLE IF NOT EXISTS ew_evidence (
    id TEXT PRIMARY KEY, subject TEXT NOT NULL, execution_attempt_id TEXT,
    source_ref TEXT, evidence_type TEXT NOT NULL, content_or_ref TEXT NOT NULL,
    captured_at REAL NOT NULL, correlation_id TEXT NOT NULL, ...
);

-- lab/engineering_lab/store.py:125
CREATE TABLE IF NOT EXISTS el_evidence (
    evidence_id TEXT PRIMARY KEY, subject_ref TEXT NOT NULL, workspace_ref TEXT NOT NULL,
    run_ref TEXT NOT NULL, state TEXT NOT NULL, summary TEXT NOT NULL,
    payload TEXT NOT NULL, timestamp_utc TEXT NOT NULL
);
```

`grep -rniE "revision|head_sha|commit_sha|source_rev"` over **both** files → **0 matches**.

`ew_evidence.source_ref` is free-form and unconstrained. `el_evidence` has no such column at
all. `EvidenceRecord` (`contracts.py:211`) documents "Every field is required to be truthful"
and carries a `provenance` dict — but the dict written by the runtime holds
`session_id, agent_id, authorization_ref, sandbox_root` (`runtime.py:436-441`), **not a
revision**.

**Consequence.** An evidence record proves a run happened and what it observed. It cannot
prove *which tree* it observed. Verification that cannot name its revision is not verification
of a revision — it is verification of "something, at some point."

This is precisely why `AGENTS.md` had to record, as a defect class:

> "`musical-intention-engine/BUILD-STATE.md` cited run `37007483734` (`a336ec30`) as 'Kotlin unit
> tests: SUCCESS' while `MieMusicalInterpreterTest.kt` **did not exist** at that revision — it
> arrived four hours later in `bd98696`. The run was real; the conclusion was not transferable."

That defect was found by a human reading two documents. Nothing in the substrate could have
caught it, because nothing in the substrate records the binding.

### 1.2 Two authorization records that cannot be joined

```sql
-- ew_authorizations: proposal-centric
id, subject, proposal_id, authority_event_id, acceptance_id,
scope, constraints, expires_at, granted_at, correlation_id

-- el_authorizations: scope-centric
authorization_id, subject_ref, scope_ref, payload, created_at
```

Different key shapes, different provenance, different lifetimes. `weaver/console_adapter.py`
bridges them **in one direction only** — it consumes a Weaver authorization and drives a Lab
`Sandbox`, and never writes back. So a Lab session's authorization is invisible to the Weaver
authority chain, and vice versa.

The user's requirement — *"one permission model: explicit, bounded permissions for each worker
and action"* — is therefore not satisfied today, and the reason is **not** that a model is
missing. It is that there are two, each internally sound, with no join.

---

## 2. What this means for the design

**Do not build a third contract.** Adding a "unified mission record" above M09 and the Lab
would create exactly the duplication the repository already suffers from, and would need its own
currency guard on day one.

**The smallest contract that composes the existing two has three parts**, each of which is a
*binding*, not a new abstraction:

### Part 1 — `revision_ref` on evidence (the currency binding)

Add one field to evidence in both substrates: the revision the evidence is true of.

```python
# conceptual — applies to el_evidence and ew_evidence alike
revision_ref: str        # 40-char git SHA, or an explicit "unbound" sentinel
revision_source: str     # "RENDER_GIT_COMMIT" | "git rev-parse HEAD" | "caller"
```

Rules:
- **Required, but explicitly nullable.** A record may carry `revision_ref: null` with a reason;
  it may never carry a *guessed* revision. The G2 lesson applies: an unreadable probe reports
  "unavailable", it does not fall back to a remembered value.
- **Never inferred from prose.** Read from the same authority the console now uses
  (`GET /api/version → source_revision`, backed by `RENDER_GIT_COMMIT`).
- **A claim that spans revisions must say so** rather than silently binding to the newest.

This is the whole of the "verification state" pillar. It is one column and one resolver.

### Part 2 — one join key between the two authority records (the composition binding)

The existing `correlation_id` is already present in every `ew_*` table. The Lab's
`el_authorizations.scope_ref` is already the session id. The missing piece is that nothing
states the correspondence.

Smallest form: a single **`mission_ref`** carried by both, with the invariant

> **every `el_*` authorization for a mission resolves to exactly one `ew_*` authorization, or
> declares itself standalone with a reason.**

That is a foreign-key-shaped constraint and a test — not a new service, not a new store, not a
new lifecycle. It makes the two chains *queryable together* while leaving both authoritative
for their own scope.

### Part 3 — the external worker plugs in at the seam that already exists

`weaver/execution_adapter.py` is already the provider-neutral seam:

```python
class ExecutionAdapter(Protocol):
    def execute(self, request: ExecutionRequest) -> ExecutionResult: ...

class NullExecutionAdapter:      # bootstrap: refuses mutation
class ForbiddenMergeAdapter:     # sentinel: merge/deploy raise
```

An OpenHands worker is **an `ExecutionAdapter` implementation**. It needs no new architecture,
no new lifecycle, and no new authority model. It needs:

1. to receive `revision_ref` in `ExecutionRequest` (Part 1), so its evidence is bound;
2. to be constructed only under an authorization that resolves through Part 2;
3. to return `ExecutionResult` whose `files_changed` is the mutation evidence.

`ForbiddenMergeAdapter` stays. An external worker that can merge is a different authority
decision, and this design does not make it.

---

## 3. Why this is the smallest version

Every named system maps onto the existing contract without extension:

| System | Contract role | Existing surface | Gap |
|---|---|---|---|
| **Arkana** | conversational entry | `api/oracle_spine.py`, `/api/commune/resonance` | none for the contract; it is a *client* of missions |
| **Weaver** | orchestration + authority chain | `weaver/enterprise_orchestration.py` (14 tables, 43 methods) | Part 1, Part 2 |
| **Engineering Lab** | execution control plane | `lab/engineering_lab/` + 27 routes | Part 1, Part 2 |
| **M09 Worker** | scheduled bounded session | `weaver/engineering_worker.py` | Part 1; HTTP-reachability is a separate decision |
| **SolSpire** | knowledge / projects | `solspire/console_router.py` (`prefix="/solspire"`) | none — it is a *surface*, not a worker |
| **Solariun** | proposals | `solspire/proposal_manager.py::ProposalManager` | none — already produces proposals the chain consumes |
| **External worker (OpenHands)** | `ExecutionAdapter` | `weaver/execution_adapter.py` | implement the Protocol |

Nothing above requires a new mission record, a new state machine, or a new store. **Five of the
seven roles already satisfy the contract.** Two need a binding. One needs an implementation of
an interface that already exists.

### What is explicitly NOT in scope

- A unified mission record that supersedes `ew_*` and `el_*`. Rejected: creates a third
  contract, needs its own guard, duplicates authority.
- Merging the two substrates. Rejected: they have different scopes (enterprise vs. session) and
  both are sound; the defect is the missing join, not the separation.
- Any change to who may merge or deploy. Human-only stays.
- OpenClaw / ClawBot / Moltbot / MyClaw. Their identities and capabilities are **unverified**;
  they are candidates for later `ExecutionAdapter` implementations, not part of this contract.
- HTTP-exposing the M09 worker. Real question, separate decision, and it is a *new mutation
  surface* — squarely sovereign.

---

## 4. The guard this design requires on day one

The G2 lesson generalizes: **a contract with no guard drifts.** Before any of Parts 1–3 is
implemented, the following must be assertable, in the repo's existing source-assertion
convention:

| Invariant | Negative control (must fail on the pre-repair tree) |
|---|---|
| Every evidence record has `revision_ref` present (may be null-with-reason) | evidence written without the field |
| No evidence record carries an inferred/guessed revision | a record whose `revision_source` is not a read |
| Every `el_*` authorization resolves to an `ew_*` authorization or declares standalone | an orphan authorization |
| No `ExecutionAdapter` may merge or deploy | an adapter exposing `merge`/`deploy` outside `ForbiddenMergeAdapter` |
| Evidence cannot claim VERIFIED at a revision other than the one it ran at | a claim bound to a different SHA |

Each needs its **negative control run against the pre-repair tree**, as G2's did (8 failed on
restore, 20 passed when repaired). A guard that is silent on both trees is not a guard.

---

## 5. Honest status

| Item | State |
|---|---|
| The contract's existence | **VERIFIED** — measured in two substrates |
| The same state vocabulary in both | **VERIFIED** — compared line by line |
| No cross-reference between them | **VERIFIED** — `grep` both directions |
| No revision binding on evidence | **VERIFIED** — `grep` both schemas, 0 matches |
| The external-worker seam exists | **VERIFIED** — `weaver/execution_adapter.py` |
| This design is implemented | **NO** — this document is a proposal |
| This design is deployed | **NO** |
| This design is accepted | **NO** — acceptance is the human's |

**Not claimed:** that the two substrates *should* be joined this way, that the M09 worker should
become HTTP-reachable, that any external runtime is suitable, or that the current authorization
split is wrong. Each is a decision above this document.

---

## 6. Next bounded step

The smallest implementable unit, if authorized:

1. Add `revision_ref` / `revision_source` to `el_evidence` and `ew_evidence` (additive
   migration; `store.py` already carries an additive-migration precedent at line 173).
2. Resolve it from `GET /api/version → source_revision` — the same authority G2 now uses, so
   the interface and the substrate agree by construction.
3. Write the guard with its negative control.
4. Wire it into CI as a **dedicated gate** — not an incidental executor. `sg-02-fe-2-v.yml` and
   `provider-routing.yml` run the whole `tests/` tree and would execute the guard "in passing"
   while neither *names* it; that is exactly the wiring defect G8's G2 pass found and repaired.

That is one migration, one resolver, one guard, one gate. Everything else in the Arkadia One
vision — Arkana, SolSpire, Solariun, the Lab UI, the external worker — composes on top of it
without renegotiating authority.
