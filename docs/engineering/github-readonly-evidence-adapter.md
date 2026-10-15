# Read-only GitHub evidence adapter

The `weaver.github_readonly_evidence_adapter` module collects GitHub pull-request, check-run, review, and base-branch protection facts for the Engineering Acceptance Authority evaluator.

## Safety boundary

- All outbound GitHub requests are constructed with HTTP `GET` only.
- The adapter has no merge, contents-write, workflow-dispatch, or deployment method.
- GitHub approval is not automatically sovereign authorization. A `HumanApprovalEvidence` is marked authorized only when the review is approved on the exact observed head SHA and the reviewer's stable numeric GitHub user ID is in the explicit allow-list.
- It re-reads the pull request after collecting evidence. Head/base movement during collection fails closed.
- Branch-protection access failures (including 403/404) produce incomplete evidence and a blocked evaluator decision. The adapter does not infer that protection is satisfied when it cannot inspect it.
- Risk classification is supplied explicitly by the caller; the default is `UNKNOWN`, which the evaluator blocks.
- A readiness decision is evidence only. No action is taken from the decision.

## Configuration

Provide a read-only token through `GITHUB_TOKEN` and comma-separated stable numeric user IDs through `ARKADIA_EAA_AUTHORIZED_REVIEWER_IDS`. Grant only the repository read permissions needed to inspect pull requests, checks, reviews, and branch protection. Never print or commit the token. If GitHub does not grant branch-protection read access, the adapter returns a fail-closed result.

## Example

```python
from weaver.engineering_acceptance import MergePolicy, RiskClass
from weaver.github_readonly_evidence_adapter import GitHubReadOnlyEvidenceAdapter

policy = MergePolicy(version="eaa-v1", required_gates=("provider-routing", "acceptance-contract"))
adapter = GitHubReadOnlyEvidenceAdapter("Arkadia-Oversoul-Prism/Arkadia")
result = adapter.collect(502, policy, risk_class=RiskClass.PROTECTED)
print(result.decision.decision.value, result.decision.reasons)
```

This example only collects evidence and evaluates it. It does not merge or deploy.
