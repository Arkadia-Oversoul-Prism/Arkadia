# GOV-04 — Bounded merge delegation

**Authorization:** Explicit user authorization in ChatGPT, 2026-11-24.
**State:** PROPOSED at authorization; effective only after this dedicated PR is independently reviewed and human-merged. This PR cannot self-authorize.
**Activation:** ACTIVE since 2026-11-24 — PR #722 was human-merged at `fd0a4fdc081064b2074aab9e17b4c7841736dd9f`. This record documents the verified repository state; it does not grant itself authority.
**Scope:** Existing PRs targeting canonical main; protected GitHub merge API only, with exact-head checks.
**No authorization:** auto-merge, direct push, force-push, protection/check bypass, deployment, provider configuration, or acceptance.

After activation, the designated reconciliation operator may merge only when every condition is affirmatively verified immediately before execution:
1. PR is open, non-draft, targets main, and exact head SHA is unchanged.
2. All required checks pass; required reviews/CODEOWNERS approvals are present; branch protections and merge queue are satisfied. Pending, skipped, stale, neutral, missing, or unknown required evidence fails closed.
3. M1–M13 checklist is complete with exact-head evidence and no unresolved findings.
4. Changed files and semantics are reviewed; no secret, security/privacy, destructive migration, authority/identity/governance, scope/lane, or reserved-human issue is implicated.
5. Dependencies and open-PR composition are freshly checked against main; deterministic order and no conflicts are established.
6. No contradictory instruction, review request, human stop, or scope ambiguity exists.
7. Normal GitHub protected merge API is used with expected head SHA; no bypass.
8. GitHub confirms the merge; record PR/head/checks/reviews/merge SHA/time and reconcile main afterward.

**Human-reserved:** this governance PR and all governance/constitutional changes, K15/K3, approval enforcement, scope/lane changes, security/privacy, destructive/data-loss decisions, deployment/configuration, review waivers, conflicts, and acceptance. Any unknown, stale, or contradictory fact means HUMAN_AUTHORITY_REQUIRED.

Batch reconciliation is authorized, not blind bulk merging. Review every PR; merge only eligible PRs in dependency order. Drafts must be explicitly made ready by their owner; no silent draft conversion. Report all exceptions and decisions together.

**Activation evidence:** PR #722 is closed and merged; GitHub reports merge commit `fd0a4fdc081064b2074aab9e17b4c7841736dd9f`. GOV-04 is active for the designated reconciliation operator within the bounded protected-API scope above. The PR queue inventory after activation showed 44 open PRs, all 44 drafts; therefore none was eligible for delegated merge at that snapshot. No PR was merged during that inventory.

This amendment does not enable auto-merge, alter protections, provision credentials, or commission a worker actuator. The runtime adapter remains fail-closed until a separately verified implementation exists. A merge is not deployment or acceptance.
