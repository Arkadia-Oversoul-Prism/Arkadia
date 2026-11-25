# GOV-04 post-activation reconciliation — 2026-11-24

## Authority state
- GOV-04 authorization: **ACTIVE** following human merge of PR #722.
- Merge commit: `fd0a4fdc081064b2074aab9e17b4c7841736dd9f`.
- Policy record and canonical references are being reconciled in a documentation-only follow-up PR.
- This follow-up does not alter merge authority and is not itself a merge authorization.

## Live queue snapshot
GitHub open-PR search after PR #722 merged returned **44 open PRs**:
- 44 drafts
- 0 ready-for-review
- 0 delegated merges executed during this snapshot

Draft status is a hard eligibility stop under GOV-04. Owners must explicitly mark PRs ready; no operator may silently convert drafts or infer author readiness.

## Work completed / not claimed
- Verified PR #722 is closed and merged; confirmed its exact merge commit.
- Refreshed the open-PR inventory and recorded the draft/readiness totals.
- Updated GOV-04 activation status in the authorization record and canonical governance references.
- **Not yet completed:** full M1–M13, per-file semantic, test/check/review, dependency, and open-PR composition review for the 44 queued PRs. No PR is represented as approved or merge-ready.
- The next batch pass begins only after owners make candidates ready; then review all candidates together, collect reserved-human decisions in one consolidated exception/decision packet, and merge only those that pass every gate in deterministic dependency order.

## Gate repair — the activation record broke the guard that pins activation (2026-11-25)

The first commit of this PR (`1ab40328`) rewrote the `**State:**` line from `PROPOSED` to
`ACTIVE`. That removed three literals that
`tests/test_gov04_bounded_merge_delegation.py::test_activation_requires_human_merge_of_this_governance_pr`
pins — `proposed`, `human-merged`, `this pr cannot self-authorize` — so the PR that records
activation could not pass the gate that guards activation.

Measured, not inferred, from the PR's own gate (run `45449878172`, head `1ab40328`):

```
verdict:            FAIL
baseline_nodes:     21        candidate_nodes: 22
newly_failing:      tests/test_gov04_bounded_merge_delegation.py::test_activation_requires_human_merge_of_this_governance_pr
reasons:            1 newly failing node(s)
```

Local reproduction on that head: `2 failed, 2 passed` for the file — the newly failing node plus
`test_bounded_merge_is_exact_head_and_protected_fail_closed`, which already fails on `main` and is
repaired by a different open PR (#725).

**Repair chosen: keep the guard, restore the record's chronology.** The authorization-time sentence
is restored verbatim and the verified activation is recorded on its own dated line:

```diff
-**State:** ACTIVE — activated by human merge of PR #722 on 2026-11-24. Merge commit: `fd0a4fdc…`
+**State:** PROPOSED at authorization; effective only after this dedicated PR is independently reviewed and human-merged. This PR cannot self-authorize.
+**Activation:** ACTIVE since 2026-11-24 — PR #722 was human-merged at `fd0a4fdc081064b2074aab9e17b4c7841736dd9f`. This record documents the verified repository state; it does not grant itself authority.
```

The guard is **not** relaxed: a future edit that drops the pre-activation obligations, or that
claims activation without naming a human merge, still fails it. This also follows the repository
convention that a line carrying a pinned claim is corrected by appending, never by rewriting.

**Negative control (live, on the real file).**

| step | result |
|---|---|
| delete the restored authorization-time line | `2 failed, 2 passed` — the node reddens |
| restore it byte-identically | `1 failed, 3 passed` — only the node that already fails on `main` |

**Verification run after the repair**

```
tests/test_gov04_bounded_merge_delegation.py                 1 failed, 3 passed
  (the 1 failure is main's own; repaired by #725)
gov04 + m02a + agents-md adjudication + boot-syntax + lane currency   171 passed, 2 skipped
cp10_mutation_boundary_policy.py --judge (AUTHORIZATION.md)  PASS (exit 0)
```

## Queue snapshot — refreshed, and it supersedes the figure above

Measured 2026-11-25T02:19Z against `main` `fd0a4fdc`:

- **49** open PRs: **48 drafts**, **1 non-draft** (this PR, #724).
- 0 delegated merges executed; no PR was marked ready by this pass.

The `44 open PRs / 44 drafts` figure earlier in this document is the 2026-11-24 snapshot. It is
**superseded** by this measurement, not contradicted by it: five further PRs were opened after that
snapshot and this PR was made ready by its owner.

## Boundaries
No auto-merge, direct/force push, protection or check bypass, deployment, product acceptance, or worker actuator activation. The runtime adapter remains fail-closed. This pass executed no merge, pushed nothing to `main`, and claims no acceptance.