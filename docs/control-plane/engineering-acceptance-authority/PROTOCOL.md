# Engineering Acceptance Authority (EAA) — Protocol v1

Status: **IMPLEMENTED AS A PURE EVALUATOR; LIVE ADAPTERS AND ENFORCEMENT NOT YET ACCEPTED**

## Purpose

EAA is the shared decision protocol across worker dispatch, evidence collection, acceptance, merge authorization, and post-merge verification. It replaces manual inspection of routine gate outcomes with machine-verifiable evidence while preserving human decisions for uncertainty and protected consequences.

GATE L4 remains the execution/provider boundary. EAA consumes authoritative observations from GitHub and the execution provider; it does not become another worker runtime, invent provider state, or infer acceptance from a successful agent run.

## Authority model

- **Worker:** proposes a diff and emits evidence references. It cannot certify its own authority.
- **Verifier:** checks that evidence is authentic, complete, current, and bound to the exact candidate SHA.
- **EAA evaluator:** deterministically classifies readiness using a versioned policy. It has no network access and cannot merge or deploy.
- **Policy enforcement adapter:** may call GitHub merge only after re-fetching PR head, checks, reviews, branch protection, policy version, and evidence immediately before the mutation.
- **Human sovereign:** owns policy approval, risk boundaries, protected decisions, and deployment authority. Policy-authorized routine auto-merge is only enabled after explicit human adoption of that policy.
- **Post-merge verifier:** evaluates the actual merge commit and required integration checks. A successful merge is not acceptance.

Capability never confers authority. A green check is evidence for one gate at one SHA, not blanket permission to merge.

## Decision contract

The evaluator returns one of:

- `BLOCKED`: evidence is missing, stale, mismatched, or required branch protection is unsatisfied.
- `NOT_READY`: a gate failed/is blocked/not tested, the PR is draft/non-mergeable, policy versions differ, or approval requirements are unmet.
- `READY_FOR_HUMAN_DECISION`: required evidence passes but policy does not authorize an automated merge and no explicit human approval is recorded.
- `READY_TO_MERGE`: required gates and independent review pass, exact-SHA evidence is complete, repository requirements pass, and either (a) policy explicitly authorizes auto-merge for this risk class or (b) a valid explicit human approval is recorded.

The decision is a snapshot, not a durable capability token. Any new commit, changed policy, dismissed review, changed check, or changed branch-protection state invalidates the snapshot and requires re-evaluation.

## Minimum evidence envelope

Every decision record must include:

- PR number, repository, base SHA, candidate head SHA, observed head SHA and observation time.
- Policy ID/version and risk classification, including why the classification applies.
- Each required gate's state (`PASS`, `FAIL`, `BLOCKED`, `NOT_TESTED`), tested SHA, run/check identifier, artifact URL and verifier identity.
- Independent approval identity and reviewed SHA where required.
- Branch protection and mergeability observations.
- Decision, reason codes, evaluator version, actor/policy authority, and immutable record identifier.
- If merged: merge method, merge commit SHA, and post-merge verification record tied to that commit.
- If deployed: separate deployment authorization and live deployment evidence. Deployment is never implied by merge readiness.

An artifact URL is a locator, not proof by itself: the verifier must fetch the artifact from an authenticated trusted source and validate its binding to the run and SHA. The pure evaluator's inputs are trusted adapter observations, not user- or agent-authored claims.

## Risk policy

- **ROUTINE:** isolated, reversible, low-blast-radius changes may become auto-merge eligible only when a human-approved policy explicitly allows it.
- **ELEVATED:** changes affecting shared runtime behavior, user-visible product flows, data handling, or cross-lane contracts require an explicit human decision until a reviewed policy states otherwise.
- **PROTECTED:** authorization/authentication, secrets, permissions, branch protection, evidence/acceptance code, policy engines, deployment infrastructure, destructive migrations, and changes that can weaken gates require explicit human approval and may be designated human-merge-only.

Risk classification is itself policy-controlled. Workers may suggest a class but cannot lower the enforced class. If classification is uncertain, fail closed to the more restrictive class.

## Required control-plane flow

1. **Assign:** bind assignment, lane, risk class, base SHA, and applicable policy version.
2. **Dispatch (GATE L4):** idempotent provider dispatch; persist the real run ID before polling.
3. **Capture:** retrieve branch, commit, test output, PR, provider status, and immutable run references. Missing/unknown values stay unknown.
4. **Verify:** validate provider identity, run identity, exact SHA, artifact provenance, required gates, independent review, and policy version.
5. **Evaluate:** compute readiness without side effects.
6. **Authorize:** for routine changes, use only an explicitly human-approved auto-merge policy; for protected or uncertain changes, route to a human.
7. **Revalidate and merge:** immediately re-fetch every mutable precondition. Reject stale decisions; never rely on a prior cached green result.
8. **Verify after merge:** bind required integration checks to the actual merge commit. If they fail or remain unknown, mark acceptance pending and stop dependent work.
9. **Deploy separately:** require distinct deployment authorization and live verification.
10. **Record and route:** append evidence and state transitions to the canonical work-event/attention path. No legal move means no move; surface the exact blocker.

## Non-negotiable negative tests

- A worker cannot approve its own change or supply its own policy authority.
- Missing, failed, blocked, or not-tested required gates never yield readiness.
- Evidence from an older or different SHA never satisfies a candidate.
- A provider `SUCCEEDED` status without commit and test evidence is not success for acceptance.
- Policy-version drift, unknown risk, unknown branch protection, or unknown mergeability fail closed.
- A gate cannot grant merge/deploy permission by changing its own output.
- A successful merge cannot be labeled accepted before post-merge verification.
- A green PR cannot authorize deployment.
- Retried dispatch cannot create duplicate provider runs when the prior create outcome is uncertain.
- No adapter may claim live OpenHands dispatch until a real non-production run is captured.

## Implementation boundary and rollout

This PR implements the pure decision evaluator and negative tests. It does **not** connect GitHub APIs, enforce branch rules, enable auto-merge, change existing PRs, dispatch OpenHands, merge, or deploy.

Rollout sequence:
1. Land evaluator and contract only after review.
2. Add read-only GitHub/provider evidence adapter and signed/immutable decision records.
3. Run observe-only against real PRs; compare decisions with actual gate states.
4. Test adversarial cases and stale-state races.
5. Obtain explicit human approval for policy version and eligible risk classes.
6. Enable auto-merge only for explicitly authorized routine changes, with least-privilege credentials and audit trail.
7. Add post-merge verification and dependency gating.
8. Integrate Weaver, hourly coordinator, GATE L4 and operator surfaces through the same contract.

## Current acceptance status

- Pure evaluator and unit tests: implemented in this branch; execution evidence must be obtained from CI for the exact head SHA.
- Live GitHub evidence adapter: **NOT IMPLEMENTED**.
- Live OpenHands provider binding: **BLOCKED** pending verified endpoint/API/auth and a real run.
- Durable decision ledger and event integration: **NOT IMPLEMENTED**.
- Auto-merge enforcement: **NOT ENABLED**.
- Post-merge verification adapter: **NOT IMPLEMENTED**.
- Production acceptance: **NOT CLAIMED**.
