# Prism Execution → WorkEvent Governance Boundary

This implementation extends the existing Arkadia substrate. It does not create a
second Prism runtime and it does not move the historical 144-cell lattice into
production execution.

## 1. Causal bridge

The new bridge is:

`Weaver ExecutionAttempt → SolSpire WorkEvent`

Implemented by `weaver/execution_workevent_bridge.py`.

A WorkEvent may be created only from a matching terminal Weaver execution
attempt:

- `SUCCEEDED`
- `FAILED`
- `BLOCKED`

The WorkEvent now carries an explicit `execution_attempt_ref` in the existing
SolSpire WorkEvent spine. `work_ref` remains populated with the same execution
identifier for compatibility, while the explicit field makes the causal join
inspectable and queryable.

The bridge is idempotent. Replaying the same execution attempt returns the
existing WorkEvent rather than minting a second consequence record.

The bridge does **not**:

- grant authorization;
- convert execution into completion;
- create evidence;
- declare verification;
- create production acceptance;
- mutate the original execution attempt.

## 2. Governance records

The existing Weaver operational database now contains four explicit append-only
record types:

### Acceptance

`Verification → Acceptance`

Acceptance requires:

- a matching verification;
- verification verdict `VERIFIED`;
- explicit accepting authority;
- explicit bounded authorization scope;
- explicit operational context.

Acceptance is distinct from authorization.

### Review

`WorkEvent → Review`

Review references the immutable WorkEvent and records:

- reviewer;
- verdict: `ACCEPTED | REJECTED | CLARIFIED`;
- findings;
- optional amendment reference.

Review does not mutate the WorkEvent.

### Completion

`Review → Completion`

Completion requires:

- the matching WorkEvent;
- an `ACCEPTED` review;
- an explicit outcome condition;
- supporting evidence references.

Execution alone cannot produce completion.

### Production Acceptance

`Completion → Production Acceptance`

Production acceptance requires:

- a matching `COMPLETED` record;
- explicit accepting authority;
- explicit production context.

Production acceptance is not implied by merge, deployment, verification, or model confidence.

## 3. Authorization binding

Existing Weaver authorization remains backward-compatible, but it now accepts an
optional `acceptance_id`.

When supplied, the authorization is causally bound to the acceptance record and
the acceptance must belong to the same subject and proposal correlation.

The resulting distinction is explicit:

`Acceptance ≠ Authorization ≠ Execution ≠ WorkEvent ≠ Review ≠ Completion ≠ Production Acceptance`

## 4. Canonical path

The live substrate can now represent:

`Verified Result
→ Acceptance
→ Authorization
→ ExecutionAttempt
→ WorkEvent
→ Review
→ Completion
→ Production Acceptance`

The historical 12×12 Oversoul Prism lattice remains outside this path. An
`Axx-Lyy` coordinate still carries no runtime authority.

## 5. Invariants

1. A non-terminal execution cannot create a WorkEvent.
2. One execution attempt can have at most one causal WorkEvent.
3. WorkEvent creation does not authorize anything.
4. WorkEvent creation does not imply completion.
5. Review does not rewrite WorkEvent history.
6. Completion requires an explicit condition and supporting evidence.
7. Production acceptance requires explicit authority and completed status.
8. Acceptance requires independently verified input.
9. Acceptance and authorization remain separate records.
10. UNKNOWN remains available wherever the substrate lacks evidence.

## 6. Remaining integration boundary

The causal and governance records now exist as substrate primitives. UI exposure
and production knowledge projection still require their own verified integration
work. No claim of production acceptance or deployment is made by this change.
