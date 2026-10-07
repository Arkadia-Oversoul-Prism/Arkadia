# ARK-$200K-G01 — Gate 01 Plan and Proof-Test Proposal

**Protocol:** ARK-$200K-READINESS-01
**Gate:** 01 / 12 — Canonical Portfolio Substrate
**Source instruction:** issue #345 (body + `/weaver` comment `6043270954`, 2026-10-07T17:32:27Z)
**Authority:** human sovereign · plan-and-proof-test-proposal only
**BASE_MAIN:** `af3a3541d9fedf8c2d38bb7a0aac56856a879523`
**Pass:** `gate01/ark-200k-portfolio-substrate-plan` (Weaver hourly bounded execution)
**Status:** PLAN — no substrate implemented. `docs/readiness/ARK-200K-GATE-01-EVIDENCE.md`
is deliberately **not** created, because Gate 01 requires it to carry an *implementation
commit SHA*, *test results*, and *exact proof-test output* that do not yet exist.

---

## 0. What this document is, and what it is not

The sovereign comment on #345 authorizes, verbatim:

> `/weaver ARK-$200K-G01 implementation target: inspect the canonical relational substrate and
> Engineering Lab first; map the existing portfolio/initiative/budget/vendor/contract/milestone/
> work-event/evidence/acceptance/invoice/decision/outcome primitives; identify the smallest
> evidence-preserving implementation; produce a Gate 01 plan and proof-test proposal. Do not
> fabricate data, create a parallel store, merge, or deploy. Stop at any human/provider
> authorization boundary.`

That instruction names four deliverable verbs — **inspect, map, identify, produce a plan and
proof-test proposal** — and three prohibitions. It does **not** authorize committing a new
substrate. This document therefore executes the four verbs and stops at the authorization
boundary the instruction itself names. Implementing the slice is the *next* bounded task and
requires the sovereign to select a staged option in §7.

`INSPECT → MAP → SMALLEST REVERSIBLE CHANGE → TEST → OBSERVE → DOCUMENT → COMMIT → CHECK GATE
→ STOP` (issue #345 body) is the gate's own execution rhythm. This pass completes INSPECT and
MAP and prepares SMALLEST REVERSIBLE CHANGE as a selected option. It does not skip to COMMIT.

---

## 1. Canonical substrate inventory (INSPECT)

Everything below was read from `main` @ `af3a3541`. Line references are to that revision.

### 1.1 Enterprise orchestration spine — `weaver/enterprise_orchestration.py` (1059 lines)

The canonical, owner-scoped, append-only operational spine. **This is the substrate Gate 01
must extend; it is not to be duplicated.** One SQLite database
(`data/solspire_projects.db`, env `SOLSPIRE_PROJECTS_DB`), shared with SolSpire and the
Engineering Lab. `PRAGMA foreign_keys=ON`, `PRAGMA journal_mode=WAL`.

Tables (`weaver/enterprise_orchestration.py:67-172`):

| table | role | key columns |
| --- | --- | --- |
| `ew_canonical_records` | captured source of truth | `id, subject, source_channel, raw_payload, payload_hash, received_at, ingested_by, correlation_id` |
| `ew_authority_events` | human-origin authority | `id, subject, actor, authority_context, action, previous_state, new_state, origin, authentication_context, correlation_id, evidence_refs` |
| `ew_interpretations` | derived reading of a record | `id, canonical_record_id → ew_canonical_records, interpreter, interpretation, confidence` |
| `ew_knowledge_mutations` | knowledge change | `caused_by_kind, caused_by_id` |
| `ew_operational_events` | event stream | `subject, enterprise_id, workload_id, workstream_id, event_type, payload, caused_by_kind, caused_by_id` |
| `ew_proposals` | proposal lifecycle | `objective, rationale, recommended_actions, required_authority, tool_selections, status` |
| `ew_authorizations` | bounded authority | `proposal_id → ew_proposals, authority_event_id → ew_authority_events, acceptance_id, scope, constraints, expires_at` |
| `ew_execution_attempts` | bounded execution | `authorization_id → ew_authorizations, tool_channel, request_payload, result_status` |
| `ew_evidence` | attributable evidence | `execution_attempt_id → ew_execution_attempts, source_ref, evidence_type, content_or_ref` |
| `ew_verifications` | verdict on a claim | `claim, evidence_refs, verdict, verifier` |
| `ew_acceptances` | acceptance of a verified result | `verification_id → ew_verifications, accepted_result_ref, accepting_authority, authorization_scope, context_ref, status` |
| `ew_reviews` | human review of a WorkEvent | `work_event_id, reviewer, verdict, findings, amendment_of` |
| `ew_completions` | completion of a reviewed WorkEvent | `work_event_id, review_id → ew_reviews, condition, supporting_evidence_refs, status` |
| `ew_production_acceptances` | production acceptance | `completion_id → ew_completions, accepting_authority, context_ref, status` |

Public store API (`EnterpriseOrchestrationStore`, line 358):
`canonical_record`, `interpretation`, `knowledge_mutation`, `operational_event`, `proposal`,
`authority_event`, `authorize`, `authorization`, `execution_attempt`,
`complete_execution_attempt`, `evidence`, `attention_delivery_ack`, `verify`, `acceptance`,
`review`, `completion`, `production_acceptance`, plus the read models `stream`,
`operational_state`, `reverse_walk`, `forward_walk`, `explain_execution`.

### 1.2 SolSpire WorkEvent spine — `solspire/workevent_manager.py`

A **distinct** continuity record bound to `(subject_ref, workspace_ref)` — the enterprise
orchestration module docstring states the two are deliberately separate. Frozen dataclass
`WorkEvent` (line 28) carries: `work_event_id, event_type, event_version, occurred_at,
recorded_at, effective_from, effective_until, subject_ref, workspace_ref, work_ref,
execution_attempt_ref, parent_event_ref, sequence_ref, scope_ref, actor_ref, artifact_refs,
state_before_ref, state_after_ref, decision_ref, witness_ref, status, supersedes_ref,
reversal_of_ref, created_by_event, schema_version`. Status vocabulary is closed:
`PROPOSED, OBSERVED, RECORDED, VERIFIED, SUPERSEDED, REVERSED, DISPUTED, UNKNOWN`.
`execution_attempt_ref` is UNIQUE where non-null — this is the one existing seam between a
WorkEvent and an `ew_execution_attempts` row, and Gate 01 should reuse it rather than invent
a new link.

### 1.3 Engineering Lab — `lab/engineering_lab/`

`contracts.py::EvidenceRecord` (line 211) — durable, attributable evidence for a bounded run
(`evidence_id, subject_ref, workspace_ref, run_ref, state, summary, detail, timestamp_utc,
provenance`). `contracts.py` also owns the run state machine and `BoundaryViolation`, with
`FORBIDDEN_DIRECT_TRANSITIONS` preventing state collapse (e.g. an attempt may not jump
straight to a terminal state without the intermediate state). `models.py` holds EL-01/EL-02
agent/role/session/run/event models keyed on `subject_ref` / `workspace_ref`. The Lab is the
execution substrate; it is **not** a portfolio store.

### 1.4 Economic seams — `economic_seams/`

The commercial/real-world seam. `deal_sheet.py::DealSheet` (line 21) already models a
transaction with an explicit evidence set and an explicit gate vector:
`evidence_ids: tuple[str, ...]`, `eligibility_verified, counterparties_verified,
prices_verified, logistics_verified, buyer_commitment_verified, supplier_commitment_verified,
human_authorized`. Its docstring is the governing rule Gate 01 must inherit: *"It never
treats a headline spread as profit and never authorizes cash movement."*
`nocopo.py` is a read-only OCDS bulk-data adapter that *"retain[s] malformed records and
implausible dates as diagnostics, never silently convert[ing] them into actionable
opportunities."* `engine.py` holds `Source`/`opportunity` records and `correlation.py` holds
an `Evidence` primitive. `market_data.py` exists for price evidence.

### 1.5 Decision — `lab/decision/schema.py`

`Decision` (line 16) is a frozen record of a **human** decision bound to an opportunity:
`opportunity_title, kind (APPROVE|REJECT|DEFER), rationale, decided_by='human',
opportunity_provenance, notes`, and `to_dict()` explicitly stamps
`execution_authorized=False, auto_build=False, auto_merge=False`. This is the canonical
Decision primitive and it already refuses to confer authority.

### 1.6 Enterprise structure — `solspire/enterprise_router.py`

`EnterpriseManager` (line 180) models an organisation: seven workstreams `D01–D07` each with
`budget_ngn`, an operating context with `budget_total`, and a "workload" projection. Its own
boundary note is the model Gate 01 should copy for Budget:
`"financial": "budget allocations are context; committed/spent/remaining remain UNKNOWN
without evidence"` (line 522) and `"budget is allocation context, not spend evidence"`
(line 352).

### 1.7 What does **not** exist

| primitive | live state |
| --- | --- |
| **Portfolio** | No portfolio record. `api/ais_profile.py:8` uses `portfolio` only as the name of the capability-profile store (`_KEY='ais_capability_portfolio'`) — an unrelated identity artefact. |
| **Initiative** | **Absent.** `grep -rliE '\binitiative\b' --include=*.py` over non-vendored source returns zero files. |
| **Vendor** | **Absent.** Same query returns zero files. |
| **Contract / SOW** | No domain record. The only `contract` hits are module-docstring uses ("worker contract", `worker.contract.json`) and `project_templates.py`'s `"contract_version"`. |
| **Milestone** | No domain record. Every `milestone` hit is the phrase "Milestone 1" in a SolSpire module docstring; `solspire/console_router.py:776` returns a literal `"milestone": 1`. |
| **Invoice** | No domain record. `kernel/intent_types.py:118` matches the *word* "invoice" as a log-transaction verb; `tests/test_gate_01_canonical_authorship.py:144` uses `"invoice-7"` as an opaque `source_ref` string. Neither is an Invoice model. |
| **Outcome** | No outcome record. The `outcome` hits are pytest/agent "outcome" fields, not a portfolio Outcome. |
| **Budget (as a record)** | Allocation context only (`enterprise_router.py`); no first-class Budget entity. |

`docs/readiness/` did not exist before this pass.

---

## 2. Primitive map (MAP) — the twelve named nodes against live substrate

The gate names a chain:
`Portfolio → Initiative → Budget → Vendor → Contract → Milestone → Work Event → Evidence →
Acceptance → Invoice → Decision → Outcome`.
The column "disposition" is the honest verdict: **REUSE** (exists and is canonical),
**STAGE** (needs a new record that reuses an existing table pattern), or **UNRESOLVED**
(cannot be implemented without inventing semantics the substrate cannot support).

| # | node | canonical home today | disposition |
| --- | --- | --- | --- |
| 1 | Portfolio | none | **STAGE** — smallest new root record |
| 2 | Initiative | none | **STAGE** — child of Portfolio |
| 3 | Budget | `enterprise_router` allocation context | **STAGE** as a bounded allocation record; spend stays UNKNOWN without evidence |
| 4 | Vendor | none | **STAGE** — party record with verification flags mirroring `DealSheet` |
| 5 | Contract/SOW | none | **STAGE** — child of (Vendor, Initiative) |
| 6 | Milestone | none | **STAGE** — child of Contract |
| 7 | Work Event | `solspire/workevent_manager.WorkEvent` | **REUSE verbatim** — do not model a second one |
| 8 | Evidence | `ew_evidence` **and** `lab.EvidenceRecord` **and** `economic_seams.Evidence` | **REUSE** — bind to the existing ref; do not add a fourth Evidence type |
| 9 | Acceptance | `ew_acceptances` (human authority, scope) | **REUSE verbatim** |
| 10 | Invoice | none | **STAGE** — but see §3.3; its *settlement* semantics are UNRESOLVED |
| 11 | Decision | `lab.decision.schema.Decision` | **REUSE** — the non-authority human decision record |
| 12 | Outcome | none | **STAGE** as an *observed* record only; predictive/attributive outcome is UNRESOLVED |

### 2.1 Edges — how each relation is carried

| edge | carrier | notes |
| --- | --- | --- |
| Portfolio → Initiative | new FK `initiative.portfolio_id` | staging |
| Initiative → Budget | new FK `budget.initiative_id` | staging; amount is *allocation*, not spend |
| Initiative → Vendor | new link table `initiative_vendor` | a vendor can serve many initiatives — many-to-many |
| Vendor → Contract | new FK `contract.vendor_id` | staging |
| Contract → Milestone | new FK `milestone.contract_id` | staging |
| Milestone → Work Event | **reuse** `WorkEvent.work_ref` / `scope_ref` (existing) | no new link table |
| Work Event → Evidence | **reuse** `WorkEvent.artifact_refs` + `ew_evidence` refs | no new link table |
| Evidence → Acceptance | **reuse** `ew_acceptances.verification_id` → `ew_verifications.evidence_refs` | existing two-hop |
| Acceptance → Invoice | new `invoice.acceptance_id` (FK to `ew_acceptances`) | staging; see §3.3 |
| Invoice → Decision | `Decision.opportunity_provenance` dict ref | reuse |
| Decision → Outcome | new `outcome.decision_id` | staging |

The forward and backward traversals the gate demands already exist as read models:
`EnterpriseOrchestrationStore.forward_walk` (line 841) and `reverse_walk` (line 794) follow
stored foreign keys and *"never invent a link — a record absent from the store is not
traversed."* The staging nodes must therefore be reachable by those same walks, which means
they must store real FKs (not JSON blobs) and live in the same database.

---

## 3. The smallest evidence-preserving implementation (IDENTIFY)

### 3.1 The single design decision that keeps this minimal

**Do not create a second store.** Add the staging nodes to
`weaver/enterprise_orchestration.py`'s existing `_db()` schema — the same
`data/solspire_projects.db`, the same `PRAGMA foreign_keys=ON`, the same `subject`-scoped
ownership — and extend `forward_walk`/`reverse_walk` with the new kinds. Everything else is
REUSE. This satisfies issue #345's first constraint ("Reuse the canonical relational
substrate. Do not create a second database or parallel persistence system") literally, and it
means the traversal proof (§4) is a test of the *existing* walk functions, not of a new
traversal engine.

### 3.2 Staging tables (six new, additive, reversible)

Proposed — names prefixed `ew_` to sit inside the existing namespace, all `subject NOT NULL`:

```
ew_portfolios     (id, subject, name, mandate, status, created_at, correlation_id)
ew_initiatives    (id, subject, portfolio_id → ew_portfolios, name, objective, status,
                   created_at, correlation_id)
ew_budgets        (id, subject, initiative_id → ew_initiatives, currency, allocated_amount,
                   evidence_refs, status, created_at, correlation_id)
ew_parties        (id, subject, role CHECK(role IN ('VENDOR','BUYER','SUPPLIER')),
                   legal_name, verification_state, evidence_refs, created_at, correlation_id)
ew_contracts      (id, subject, initiative_id → ew_initiatives, party_id → ew_parties,
                   kind CHECK(kind IN ('CONTRACT','SOW')), status, effective_from,
                   evidence_refs, created_at, correlation_id)
ew_milestones     (id, subject, contract_id → ew_contracts, name, sequence, status,
                   evidence_refs, created_at, correlation_id)
ew_invoices       (id, subject, acceptance_id → ew_acceptances, party_id → ew_parties,
                   currency, amount, status, evidence_refs, created_at, correlation_id)
ew_outcomes       (id, subject, decision_ref, observed_statement, evidence_refs, status,
                   created_at, correlation_id)
```

`ew_parties` merges Vendor/Buyer/Supplier into one table with a `role` discriminator — three
tables would be duplication, and `DealSheet` already treats them as symmetric parties.

Rules carried into the schema, not left to convention:

- `status` vocabularies are **closed sets** validated in Python, exactly as
  `_ALLOWED_STATUS` is in `workevent_manager.py` and `PROPOSAL_STATUSES` in
  `enterprise_orchestration.py`.
- Every node that makes a factual claim carries `evidence_refs NOT NULL DEFAULT '[]'`, and a
  claim with an empty evidence set is `UNKNOWN` — mirroring `operational_state()`'s rule that
  *"Missing evidence stays UNKNOWN."*
- `amount`/`allocated_amount` are stored as **text decimals** (the `DealSheet._money`
  convention), never floats, so currency is not corrupted by binary rounding.
- No table has an `authorized`/`approved` boolean. Authority is conferred only by
  `ew_authorizations`, whose `authorize()` already rejects a non-human-origin authority event
  and requires causal binding to the proposal (`weaver/enterprise_orchestration.py:444-484`).

### 3.3 What is deliberately UNRESOLVED

Per issue #345: *"If a relationship is not yet implementable, record it explicitly as
UNRESOLVED rather than creating a false abstraction."*

1. **Invoice settlement semantics.** An `ew_invoices` row records that an invoice *exists and
   is evidenced*. It must **not** record paid/outstanding/settled, because no settlement
   evidence source exists in the repository — the same reason `enterprise_router.py:522`
   reports committed/spent/remaining as UNKNOWN. Settlement state is UNRESOLVED.
2. **Outcome attribution.** An Outcome can be *observed* (a statement with evidence). Causal
   attribution of an outcome to a decision is UNRESOLVED — the substrate has no counterfactual
   model and inventing one would fabricate semantics.
3. **Contract → Budget coupling.** Whether a contract draws down a budget is a real-world
   accounting relation the repository cannot currently evidence. UNRESOLVED.
4. **Milestone completion authority.** A milestone reaching a terminal state is an authority
   act, not a data edit. It must route through `ew_authority_events` → `ew_authorizations`.
   The *shape* of that authorization (scope vocabulary) is UNRESOLVED pending a sovereign
   decision.
5. **Vendor identity.** `ew_parties.legal_name` is a label, not a verified legal identity.
   The repository has no vendor-registry integration; `verification_state` stays UNKNOWN
   until an evidence source exists.

### 3.4 Governance preserved

`Identity ≠ Authority ≠ Authorization ≠ Approval ≠ Execution` is already enforced and must not
be weakened:

- Identity — `subject` (the verified Firebase uid) on every row; reads are owner-scoped.
- Authority — `ew_authority_events.origin` (human) + `authorize()`.
- Authorization — `ew_authorizations` (bounded `scope`/`constraints`, `_scope_contains`).
- Approval/Acceptance — `ew_acceptances` (requires a VERIFIED verification and explicit
  accepting authority).
- Execution — `ew_execution_attempts` + the Engineering Lab run state machine.

The staging nodes add **no** new path into any of these five. They are records, not authority.

---

## 4. Proof-test proposal

### 4.1 Harness

`tests/test_ark_200k_gate_01_portfolio_substrate.py`, deterministic, synthetic data only,
running against a temporary `SOLSPIRE_PROJECTS_DB` (the established sandbox convention — the
existing enterprise-orchestration tests already isolate the DB path). No network, no external
service, no real portfolio/financial/vendor data.

### 4.2 Fixture

Build one chain with synthetic identifiers:

```
portfolio P1 → initiative I1 → budget B1 → party V1 (VENDOR) → contract C1 (SOW)
→ milestone M1 → work event W1 → evidence E1 → acceptance A1 → invoice N1
→ decision D1 → outcome O1
```

`W1` is a real `WorkEvent` created through `get_workevent_manager().create(...)`; `E1` is a
real `ew_evidence` row attached to a real `ew_execution_attempts` row under a real
`ew_authorizations` row granted by a real human-origin `ew_authority_events` row. `A1` is a
real `ew_acceptances` row obtained through `store.acceptance(...)` after
`store.verify(...)` returns `VERIFIED`. The fixture therefore exercises the *canonical*
authority path rather than asserting the shape of a mock.

### 4.3 The eight assertions, mapped to what proves each

| gate requirement | proof |
| --- | --- |
| 1. every node has a stable identifier | every returned record's `id` is non-empty and matches `^[a-z]+-[0-9a-f]{32}$`; re-reading by id returns the identical row |
| 2. every edge is queryable | each edge is read back by its own FK column (`initiative.portfolio_id`, `contract.party_id`, …), not by scanning a JSON blob |
| 3. provenance is preserved | every node's `evidence_refs` resolves to an existing `ew_evidence`/`ew_canonical_records` row; a node claiming a fact with empty evidence reports `UNKNOWN`, never `VERIFIED` |
| 4. chain traversed forward | `forward_walk(subject, "CANONICAL_RECORD", …)` / `forward_walk(..., "PROPOSAL", …)` reaches `OUTCOME` from the root, following only stored FKs |
| 5. chain reconstructed backward | `reverse_walk(subject, "OUTCOME", O1)` reaches a root of kind `CANONICAL_RECORD` or `AUTHORITY_EVENT`, with `complete == True` |
| 6. unauthorized mutation rejected | `store.authorize(...)` with a non-`AUTHORIZE`/`APPROVE_PROPOSAL` action, a foreign `subject`, or an unbound `correlation_id` raises `ValueError`; a milestone terminal state attempted without an authority event raises |
| 7. no silent orphan on parent change | deleting a parent under `PRAGMA foreign_keys=ON` either fails the FK constraint or is refused; the test asserts the consequential child (`ew_acceptances`/`ew_evidence`) is **never** silently orphaned, and that a `SUPERSEDED` status (not deletion) is the only legal way to retire a node |
| 8. no second authoritative persistence layer | `sqlite3` connection count to a *new* DB file is zero; every staging table is created by the existing `_db()`; a filesystem assertion proves no second `.db` was introduced |

### 4.4 Negative controls (required by this repository's convention)

A proof test that cannot fail proves nothing. The harness must include:

- **control A** — a fixture with a broken edge (an `initiative` pointing at a non-existent
  `portfolio`) must make the traversal assert fail, proving assertions 4/5 detect an orphan.
- **control B** — a node with empty `evidence_refs` must report `UNKNOWN`, proving assertion 3
  detects unproven provenance rather than defaulting to VERIFIED.
- **control C** — `reverse_walk` on an id absent from the store must return `complete == False`,
  proving the walk does not invent the link it is looking for.

### 4.5 Expected result

Gate 01 = **PASS** only when the eight assertions hold *and* the three negative controls fail
as designed. Anything less is BLOCKED, recorded as such.

---

## 5. Regression boundary

- Additive schema only. `_db()` uses `CREATE TABLE IF NOT EXISTS` and column-add guards
  (the file already does this for `execution_attempt_ref` and `acceptance_id`), so an existing
  database migrates in place with no destructive change and no data loss.
- `forward_walk`/`reverse_walk` gain new `kind` branches; existing kinds are untouched.
- No change to `api/main.py` (2434 / 2600 lines — the new routes, if any, belong in a router
  module, never in `main.py`).
- No change to `solspire/workevent_manager.py`, `lab/`, or `economic_seams/` semantics.
- `python -m py_compile api/main.py` before any commit that touches boot code.
- Protected suites that must stay green: `tests/architecture` (**11/11** measured this pass)
  and `tests/test_m02a_ci_gate_integrity.py` (**64 passed** measured this pass).
- Baseline debt is **not** repaired by this workstream: full suite at `af3a3541` is
  **10 failed / 1760 passed / 21 skipped / 1 error** (11 nodes; §6 of the pass-08 evidence).

## 6. Rollback

The change is a single additive commit on a dedicated branch. Reverting it removes the staging
tables from source; because `_db()` is `IF NOT EXISTS`, an already-migrated database keeps the
empty tables harmlessly, and dropping them is a one-line operator action. No destructive
migration, no data transform.

---

## 7. Staged options for sovereign selection

The sovereign instruction says *"identify the smallest evidence-preserving implementation."*
The options are ordered smallest-first; **none is executed by this pass.**

| option | scope | reversible? | requires |
| --- | --- | --- | --- |
| **A — Root slice** | `ew_portfolios` + `ew_initiatives` only; prove traversal P→I and back | trivially | — |
| **B — Commercial slice** | A + `ew_budgets`, `ew_parties`, `ew_contracts`, `ew_milestones` | trivially | a sovereign ruling on UNRESOLVED #3/#4 |
| **C — Full chain** | B + `ew_invoices`, `ew_outcomes`, full 12-node proof test | trivially | sovereign rulings on UNRESOLVED #1/#2/#5 |
| **D — Defer** | record the plan, implement nothing | n/a | — |

Recommendation: **A**, then B, then C — each as its own bounded PR with its own evidence
artifact, so the traversal proof grows one verifiable edge at a time rather than asserting a
twelve-node chain in one un-reviewable step.

---

## 8. Authority boundary

- This pass: **no substrate implemented, no merge, no deploy, no push to `main`, no
  force-push.** Artifacts are documentation only.
- `docs/readiness/ARK-200K-GATE-01-EVIDENCE.md` is **not** produced, because its required
  contents (implementation commit SHA, test results, exact proof-test output) do not exist.
  Producing it now would be exactly the "mark the gate PASS without the proof test" failure
  the instruction forbids.
- Human authority remains final for merge, deployment, and Gate 02 advancement.
- Next permitted action: **sovereign selects an option in §7.** The next bounded engineering
  task is then that option, on its own branch, with its own proof test.

*Where evidence stops, claim stops.*
