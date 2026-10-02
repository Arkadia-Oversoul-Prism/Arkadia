# UPSTREAM CAUSAL CONTINUITY 01

Status: FORENSIC FINDINGS FROZEN + MEASUREMENT UPDATE
Evidence base: `a3045dd1f4ed5b488ca2c770919a8851f1434928`
Preservation branch: `reconciliation/verified-boundary-01-recovered`
Investigation branch: `reconciliation/upstream-causal-continuity-01`
Implementation head inspected: `dc873ed1b33cc0875cce7461d8b14eb57087a051`
Mutation scope: investigation branch only
Merge: NO
Deployment: NO

## Question

Can a consequential action be traced forward from legitimate identity and authority through authorization, proposal, approval, execution, durable work, evidence, verification, and review without inventing relationships?

This investigation starts upstream of the already preserved Gates 01–05.

## Baseline reused

The preserved recovery commit contains 91 boundary tests covering Gates 01–05.

Already-established evidence reused here:

- AUTHORITY ≠ AUTHORIZATION: authenticated identity does not itself confer Govern authority; distinct reviewer tests and source-level authority-gate assertions exist.
- EXECUTION ≠ WORK EVENT: execution and WorkEvent are separate records with no durable execution/job join.
- WORK EVENT ≠ EVIDENCE: WorkEvent and enterprise evidence are separate spines with no durable join.
- EVIDENCE ≠ VERIFICATION: evidence can stand alone; verification requires evidence references.
- VERIFICATION ≠ REVIEW: Gate 05 is present in the preserved 91-test set.

The preserved branch remains untouched.

## Runtime/data paths observed

### Identity

Runtime authentication path:

Firebase token -> `get_current_user` -> `build_user_profile` -> user dict containing `uid`, role, access level and optional node metadata.

Production mode requires Firebase credentials; development mode uses decoded token identity without signature verification.

Identity is represented at runtime by the user dictionary. The enterprise orchestration tables do not contain a foreign key to the Firebase identity/profile store.

### API approval path

`POST /api/approvals/request`
-> `require_auth`
-> `queue_approval(... subject_ref=user["uid"])`
-> module-memory `PENDING_APPROVALS`.

Approval decision:

`POST /api/approvals/{id}/approve`
-> `require_auth`
-> `_require_govern_authority(user)`
-> distinct-decider check
-> in-memory status/decision fields.

Execution then consumes that in-memory approval separately.

This path does not create an `ew_authorizations` row and does not create an `ew_authority_events` row.

### Enterprise/SolSpire path

`EdenOps.ingest_supplier_signal`
-> canonical record
-> interpretation
-> knowledge mutation
-> operational event
-> proposal.

For approval:

`EdenOps.decide_proposal`
-> reads `ew_proposals`
-> validates supplied `actor_identity` for APPROVE
-> creates `ew_authority_events`
-> calls `EnterpriseOrchestrationStore.authorize`
-> creates `ew_authorizations`.

Then:

`ew_authorizations`
-> `ew_execution_attempts`
-> `ew_evidence`
-> `ew_verifications`.

The enterprise chain has explicit SQL foreign keys:

- authorization.proposal_id -> proposal.id
- authorization.authority_event_id -> authority_event.id
- execution_attempt.authorization_id -> authorization.id
- evidence.execution_attempt_id -> execution_attempt.id

The existing reverse/forward walk therefore has real persisted joins for this spine.

## Explicitly persisted relationships

| Boundary | Persisted relationship | Classification |
|---|---|---|
| identity -> authority event | authority event stores `actor` as TEXT; no identity FK | attribution with new enforcement at decision boundary, not identity join |
| proposal -> authority event | shared `correlation_id`; no FK from proposal to authority event | causal correlation, not FK |
| proposal -> authorization | `ew_authorizations.proposal_id` FK | explicit join |
| authority event -> authorization | `ew_authorizations.authority_event_id` FK | explicit join |
| authorization -> execution | `ew_execution_attempts.authorization_id` FK | explicit join |
| execution -> evidence | `ew_evidence.execution_attempt_id` FK | explicit join |
| evidence -> verification | verification stores evidence IDs in `evidence_refs`; no FK | explicit reference, not relational FK |
| API approval -> enterprise authorization | no shared persisted identifier/table relation found | absent join |
| API approval -> enterprise authority event | no persisted relation found | absent join |

## Boundary measurements

### IDENTITY -> AUTHORITY

**Measurement result: enforcement added and source-inspected; runtime test evidence pending.**

The inspected implementation at `dc873ed1...` now requires, for enterprise APPROVE:

- an `actor_identity` mapping
- `actor_identity["uid"] == actor`
- role `Flamekeeper` OR numeric `access_level >= 3`

The check occurs before creation of the authority event and authorization. The unauthorized test then asserts both durable tables remain at zero.

The authorized control test supplies a Flamekeeper identity and asserts one authority event and one authorization.

This changes the implementation boundary from the previously observed condition, where an arbitrary actor string could reach authority-event creation, to an identity-bearing caller check.

**However, the negative test has not been independently executed in the observed CI run. Therefore the enforcement is source-inspected, not yet runtime-verified.**

The enterprise tables still do not carry a foreign key to the Firebase identity/profile store. The remaining relational classification is therefore:

- identity -> decision-time authority predicate: **implemented in code, runtime verification pending**
- identity -> persisted authority event: **attribution/correlation, not FK**
- authority event -> authorization: **explicit FK**

### AUTHORITY -> AUTHORIZATION

**Result: PERSISTED AND GATED.**

`authorize` requires:

- proposal exists
- authority event exists
- subject matches
- action is AUTHORIZE / APPROVE_PROPOSAL
- authority-event correlation_id equals proposal correlation_id

It then creates an authorization with foreign keys to both proposal and authority event.

Existing tests already prove the negative case for an unrelated authority event: causal mismatch is rejected.

The new implementation adds an upstream authority predicate before authority-event creation. Its mutation resistance has not yet been measured.

### PROPOSAL -> APPROVAL / AUTHORIZATION

**Result: two distinct mechanisms, not one continuous approval spine.**

The enterprise loop has a persisted proposal -> authority event -> authorization chain.

The API approval surface has an independent in-memory approval record.

The new API test exercises request -> approve and then counts enterprise records. Its expected finding is zero `ew_authorizations` and zero `ew_authority_events`.

This demonstrates the intended cross-surface discontinuity if the test executes successfully.

**Runtime execution of this test is pending.**

Thus the statement "an API approval authorizes the enterprise execution chain" remains an inference and must not be recorded as fact.

### APPROVAL -> EXECUTION

The preserved Gate 02 evidence already establishes that the API approval decision is consumed by a separate tool-execution path and does not create a WorkEvent.

The enterprise execution path is separately authorization-bound through `authorization_id`.

These are therefore distinct execution authorization mechanisms, not one proven end-to-end spine.

## Mutation / negative-test inspection

The new upstream test file contains three tests:

1. unauthorized identity cannot create authority or authorization
2. authorized identity can create authority and authorization
3. API approval does not create enterprise authorization

**Important finding: the new upstream test file does not contain an actual mutation test.**

It tests the intended behavior of the added authority predicate, but it does not deliberately remove/bypass that predicate and prove the test fails.

Therefore:

- unauthorized test presence: **YES**
- unauthorized test source logic inspected: **YES**
- unauthorized test runtime execution: **NOT YET VERIFIED**
- mutation of the new predicate and expected test failure: **NOT YET MEASURED**

Existing mutation evidence from the preserved Gates 01–04 remains valid:

- Gate 01 authority mutation caused authority tests to fail.
- Gate 02 execution-to-WorkEvent mutation was rejected by the boundary tests.
- Gate 03 evidence/WorkEvent collapse mutation was rejected.
- Gate 04 evidence auto-verification mutation was rejected.

Those are downstream/preserved mutation measurements. They do not substitute for a mutation test specifically targeting the new upstream identity-authority predicate.

## CI evidence

For implementation head `dc873ed1b33cc0875cce7461d8b14eb57087a051`:

- `security-secret-scan` run `36958546349`: COMPLETED / SUCCESS.
- `Weaver MVP2 validation` run `36958546338`: COMPLETED / SUCCESS.
- The Weaver validation job executed only:
  `tests/test_weaver_mvp2_05.py`
  and
  `tests/test_weaver_mvp2_07.py`.
- The upstream test file `tests/test_upstream_causal_continuity_01.py` was not included in that workflow command.

Therefore the successful CI run is **not evidence that the three new upstream tests passed**.

The combined status also reports the Vercel context as success, but that is not a test result for this forensic boundary.

No new upstream test failures are claimed because those tests have not executed in the observed CI evidence.

## Resulting graph classification

Current truthful graph:

IDENTITY
-> AUTHORITY: **IMPLEMENTED DECISION-TIME ENFORCEMENT, RUNTIME VERIFICATION PENDING; NO PERSISTED IDENTITY FK**

AUTHORITY
-> AUTHORIZATION: **PERSISTED JOIN; AUTHORITY LEGITIMACY NOW CODE-GATED, RUNTIME VERIFICATION PENDING**

PROPOSAL
-> AUTHORIZATION: **PERSISTED JOIN**

AUTHORIZATION
-> EXECUTION: **PERSISTED JOIN**

EXECUTION
-> EVIDENCE: **PERSISTED JOIN**

EVIDENCE
-> VERIFICATION: **REFERENCE-BASED, NOT FK**

VERIFICATION
-> REVIEW: **PRESERVED GATE 05 BOUNDARY**

API APPROVAL
-> ENTERPRISE AUTHORIZATION: **ABSENT JOIN, RUNTIME TEST PENDING**

API APPROVAL
-> ENTERPRISE AUTHORITY EVENT: **ABSENT JOIN**

The full chain is therefore still **not a single proven causal spine**.

## Decision on the next measurement

**Do not advance to another causal boundary yet.**

The current evidence gap is validation of the measurement we just introduced, not discovery of a new downstream relationship.

The next authorized measurement should therefore be:

1. execute the three upstream tests against the investigation head;
2. run the relevant preserved regression set;
3. perform a mutation specifically removing/bypassing the new identity-authority predicate and confirm the unauthorized test fails;
4. confirm the API approval test's zero enterprise-record result;
5. then freeze the resulting runtime evidence.

Only after those measurements are complete should the graph advance.

No merge. No deployment. Preservation branch unchanged.
