# UPSTREAM CAUSAL CONTINUITY 01

Status: FORENSIC FINDINGS FROZEN
Evidence base: `a3045dd1f4ed5b488ca2c770919a8851f1434928`
Preservation branch: `reconciliation/verified-boundary-01-recovered`
Investigation branch: `reconciliation/upstream-causal-continuity-01`
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
-> creates `ew_authority_events`
-> calls `EnterpriseOrchestrationStore.authorize`
-> creates `ew_authorizations`
-> proposal status becomes `AUTHORIZED`.

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
| identity -> authority event | authority event stores `actor` as TEXT; no identity FK | correlation / attribution, not identity join |
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

**Result: UNRESOLVED / first upstream enforcement gap.**

The enterprise authority event records `actor`, `subject`, `authentication_context`, and authority metadata, but does not resolve `actor` against the authenticated identity/authority model.

More importantly, `EdenOps.decide_proposal` accepts an arbitrary `actor` string and directly creates the human authority event. It does not call the API governance predicate `_has_govern_authority`, `require_sovereign`, or another identity-backed authority check.

Therefore the enterprise store can persist an authority event whose actor is merely a supplied string. The subsequent `authorize` call verifies subject match, action type, and causal correlation, but not whether the actor actually possessed the authority to issue the event.

This is a measured separation between **authority evidence** and **authority enforcement**, not evidence that the enterprise chain is entirely ungoverned.

### AUTHORITY -> AUTHORIZATION

**Result: PERSISTED AND GATED, but authority legitimacy is inherited from the caller that created the authority event.**

`authorize` requires:

- proposal exists
- authority event exists
- subject matches
- action is AUTHORIZE / APPROVE_PROPOSAL
- authority-event correlation_id equals proposal correlation_id

It then creates an authorization with foreign keys to both proposal and authority event.

Existing tests already prove the negative case for an unrelated authority event: causal mismatch is rejected.

The missing condition is upstream legitimacy of the authority event itself.

### PROPOSAL -> APPROVAL / AUTHORIZATION

**Result: two distinct mechanisms, not one continuous approval spine.**

The enterprise loop has a persisted proposal -> authority event -> authorization chain.

The API approval surface has an independent in-memory approval record.

No durable relation was found that converts the API approval decision into the enterprise `ew_authorizations` record or `ew_authority_events` record.

Thus the statement "an API approval authorizes the enterprise execution chain" would currently be an inference and must not be recorded as fact.

### APPROVAL -> EXECUTION

The preserved Gate 02 evidence already establishes that the API approval decision is consumed by a separate tool-execution path and does not create a WorkEvent.

The enterprise execution path is separately authorization-bound through `authorization_id`.

These are therefore distinct execution authorization mechanisms, not one proven end-to-end spine.

## Existing negative/mutation evidence reused

No mutation was applied to the preservation branch.

Existing evidence already demonstrates that the tests bite at several downstream boundaries:

- Gate 01 authority mutation caused authority tests to fail.
- Gate 02 execution-to-WorkEvent mutation was rejected by the boundary tests.
- Gate 03 evidence/WorkEvent collapse mutation was rejected.
- Gate 04 evidence auto-verification mutation was rejected.
- Enterprise authorization rejects an unrelated authority event through correlation mismatch.
- Enterprise execution rejects missing authorization.
- Enterprise execution refuses a self-asserted SUCCEEDED result without evidence.

These establish that the preserved boundary tests are not merely descriptive labels.

## Smallest new evidence required

The smallest useful new negative test is not another downstream gate. It should target the measured upstream gap:

1. Create a proposal.
2. Invoke the enterprise decision path with a caller/actor that lacks Govern authority.
3. Assert that no `ew_authority_events` or `ew_authorizations` record is created.
4. Control case: an authority-bearing identity may create the authority event and authorization.
5. Mutation check: removing the authority predicate from the proposed implementation should make the negative test fail.

A second minimal test should establish the cross-surface separation:

1. Create an API approval through `/api/approvals/request`.
2. Approve it through the governed API route.
3. Assert that no `ew_authorizations` record appears unless an explicit bridge exists.

These tests should be added only on a successor implementation branch after this finding is reviewed.

## Test execution status

The preserved baseline is known from the recovery record:

- 91 boundary tests passed.
- Console typecheck/build passed.
- Full-suite failure set matched pristine base.

For this investigation, the GitHub connector available in this session provides repository inspection and Git operations but no local test runner or workflow-dispatch operation. Therefore no new test execution is claimed here.

No new test failures are claimed because no new tests were executed.

## Verdict

The preserved Gates 01–05 remain intact.

The upstream enterprise chain is substantially real and relational from:

PROPOSAL -> AUTHORIZATION -> EXECUTION -> EVIDENCE

and from:

AUTHORITY EVENT -> AUTHORIZATION.

The first unproven upstream causal boundary is:

IDENTITY -> LEGITIMATE AUTHORITY EVENT.

The principal technical reason is that enterprise `EdenOps.decide_proposal` accepts an actor string and creates an authority event without consulting the authenticated identity's Govern authority.

A second discontinuity exists between the independent API approval surface and the enterprise authorization store.

Therefore the full statement

IDENTITY -> AUTHORITY -> AUTHORIZATION -> EXECUTION -> EVIDENCE -> VERIFICATION -> REVIEW

is not yet a single proven causal spine.

The truthful current classification is:

IDENTITY -> AUTHORITY: UNRESOLVED
AUTHORITY -> AUTHORIZATION: PERSISTED JOIN, upstream legitimacy unresolved
PROPOSAL -> AUTHORIZATION: PERSISTED JOIN
AUTHORIZATION -> EXECUTION: PERSISTED JOIN
EXECUTION -> EVIDENCE: PERSISTED JOIN
EVIDENCE -> VERIFICATION: reference-based, not FK
VERIFICATION -> REVIEW: preserved Gate 05 boundary

No merge. No deployment. Preservation branch unchanged.
