# GATE L4 — OpenHands Dispatch and Run-Inspection API Contract

Status: **CONTRACT DEFINED; PROVIDER BINDING BLOCKED**  
Base SHA for this workstream: `49809f45274f2f81b24e01fefdfb3009e8717495`  
Authority: worker runs stop at evidence/review. Merge and deployment remain human-only.

## Scope

GATE L4 connects the hourly coordinator to a real OpenHands provider. It does not
replace the Arkadia worker, create a second agent runtime, merge PRs, deploy
services, or infer acceptance from provider status.

The implementation is intentionally fail-closed until the actual OpenHands
deployment, API version, authentication method, and response schemas are verified.
The repository currently documents OpenHands as a future adapter; no provider
endpoint or credentials are assumed by this contract.

## Dispatch operation

Logical operation: `dispatch(request) -> run_id`.

Required request fields:

- `assignment_id`: stable identifier from the accepted coordinator contract.
- `lane`: one of `W1`, `W2`, `W3`, `W4`.
- `base_sha`: full 40-character lowercase commit SHA against which the assignment
  was validated.
- `instruction`: bounded assignment instructions, not credentials.
- `idempotency_key`: SHA-256 of `gate-l4:v1:{assignment_id}:{lane}:{base_sha}`.

Provider binding must implement create-or-recover semantics for the idempotency key.
If the provider cannot enforce idempotency, Arkadia must persist a dispatch ledger
and reconcile uncertain requests before retrying. A timeout is not permission to
create a second run.

Expected result: stable provider `run_id`. Persist it before polling or doing further
work. No result without a run ID may be described as a dispatched worker.

## Inspection operation

Logical operation: `inspect(run_id) -> RunEvidence`.

Required evidence fields:

- `run_id`, `status`, `lane`, `base_sha`
- `branch` when a work branch exists
- `commit_sha` and `test_exit_code` for a succeeded run
- `test_summary` with a link or identifier for the actual test output
- `pull_request_url` when a PR exists

Allowed statuses: `QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED`,
`CANCELLED`, `UNKNOWN`. Unknown provider statuses map to `UNKNOWN`, not success.
Evidence must match the original run, lane, and base SHA. A successful provider
status without a commit and test exit code is invalid evidence.

## Security contract

1. Require an authenticated provider identity with least privilege.
2. Require HTTPS, an allow-listed provider hostname, and no credentials embedded in URLs.
3. Keep tokens in the platform secret store; never commit or echo them.
4. Reject malformed assignment IDs, invalid SHAs, unrecognized lanes, overlong
   instructions, mismatched idempotency keys, and evidence that changes lane/base.
5. Treat provider output and worker-generated text as untrusted data, not policy.
6. Workers cannot grant themselves merge or deployment permission.
7. Do not dispatch PR code with write-capable credentials unless the execution
   environment and trust boundary have been reviewed explicitly.
8. Log run IDs, assignment IDs, lane, base/head SHAs and status; redact credentials
   and sensitive prompt content.
9. Bound request and polling timeouts; rate-limit dispatch; never retry uncertain
   create calls without idempotency reconciliation.
10. Keep a human acceptance gate between evidence collection and merge/deployment.

## Four-lane isolation

Each run is bound to exactly one lane and one assignment/base tuple. W1 Shell/navigation,
W2 NovaNet/Opportunity Radar, W3 Solariun/Knowledge OS and W4 Arkana/Engineering Lab
remain independent. The dispatcher may enforce bounded concurrency, but it must not
rewrite their contracts or treat existing PRs as evidence of dispatch.

## State model

`NOT_CONFIGURED -> READY -> DISPATCHED -> RUNNING -> RESULT_CAPTURED -> REVIEW_REQUIRED`

Failure branches: `BLOCKED`, `FAILED`, `UNKNOWN`. A timeout or unavailable
provider remains `UNKNOWN`/ `BLOCKED` until reconciled. Only a human can accept
the result and authorize merge or deployment.

## Provider binding checklist

Before a live client is merged, record:

- Provider origin and deployed OpenHands version.
- Official API documentation URL and exact create/inspect endpoints.
- Auth mechanism and least-privilege scopes (never the secret value).
- Request/response fixtures captured from a real non-production run.
- Behavior for duplicate idempotency key, timeout after create, missing run,
  provider 4xx/5xx, cancelled run, malformed response and provider schema drift.
- An end-to-end run ID, branch, commit SHA, test output reference and PR reference.

Until those artifacts exist, live dispatch acceptance is **BLOCKED**, not passed.
