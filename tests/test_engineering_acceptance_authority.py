from weaver.engineering_acceptance import (
    CheckState, Decision, GateEvidence, HumanApprovalEvidence, MergePolicy,
    PullRequestEvidence, ReviewEvidence, RiskClass, evaluate_merge_readiness,
)


SHA = "a" * 40
BASE = "b" * 40
POLICY = MergePolicy(
    version="eaa-v1",
    required_gates=("unit", "security"),
    auto_merge_risk_classes=frozenset({RiskClass.ROUTINE}),
)


def ready_pr(**changes):
    checks = {
        name: GateEvidence(name, CheckState.PASS, SHA, f"https://evidence.example/{name}")
        for name in POLICY.required_gates
    }
    values = dict(
        pr_number=17, head_sha=SHA, base_sha=BASE, observed_head_sha=SHA, observed_base_sha=BASE,
        checks=checks,
        reviews=(ReviewEvidence(True, "independent-reviewer", SHA),),
        draft=False, mergeable=True, branch_protection_satisfied=True,
        risk_class=RiskClass.ROUTINE, human_approvals=(),
        policy_authorizes_auto_merge=True, evidence_complete=True,
        policy_version=POLICY.version,
    )
    values.update(changes)
    return PullRequestEvidence(**values)


def test_authorized_routine_candidate_is_ready_to_merge():
    result = evaluate_merge_readiness(ready_pr(), POLICY)
    assert result.decision is Decision.READY_TO_MERGE
    assert result.candidate_sha == SHA
    assert result.post_merge_verification_required is True


def test_passed_gates_without_authority_never_imply_merge_permission():
    result = evaluate_merge_readiness(
        ready_pr(policy_authorizes_auto_merge=False), POLICY
    )
    assert result.decision is Decision.READY_FOR_HUMAN_DECISION


def test_protected_risk_requires_explicit_human_approval_even_if_auto_merge_flagged():
    pr = ready_pr(
        risk_class=RiskClass.PROTECTED,
        policy_authorizes_auto_merge=True,
    )
    assert evaluate_merge_readiness(pr, POLICY).decision is Decision.READY_FOR_HUMAN_DECISION


def test_stale_gate_evidence_blocks_candidate():
    checks = dict(ready_pr().checks)
    checks["security"] = GateEvidence(
        "security", CheckState.PASS, BASE, "https://evidence.example/security"
    )
    result = evaluate_merge_readiness(ready_pr(checks=checks), POLICY)
    assert result.decision is Decision.BLOCKED
    assert any("stale" in reason for reason in result.reasons)


def test_non_pass_gate_cannot_be_overridden_by_other_green_checks():
    checks = dict(ready_pr().checks)
    checks["security"] = GateEvidence(
        "security", CheckState.BLOCKED, SHA, "https://evidence.example/security"
    )
    result = evaluate_merge_readiness(ready_pr(checks=checks), POLICY)
    assert result.decision is Decision.NOT_READY


def test_missing_artifact_blocks_even_when_gate_says_pass():
    checks = dict(ready_pr().checks)
    checks["unit"] = GateEvidence("unit", CheckState.PASS, SHA, None)
    result = evaluate_merge_readiness(ready_pr(checks=checks), POLICY)
    assert result.decision is Decision.BLOCKED


def test_head_movement_after_evaluation_blocks_old_evidence():
    result = evaluate_merge_readiness(ready_pr(observed_head_sha=BASE), POLICY)
    assert result.decision is Decision.BLOCKED


def test_policy_version_mismatch_blocks_evaluation():
    result = evaluate_merge_readiness(ready_pr(policy_version="eaa-v0"), POLICY)
    assert result.decision is Decision.BLOCKED


def test_draft_and_unprotected_branch_are_not_merge_ready():
    result = evaluate_merge_readiness(
        ready_pr(draft=True, branch_protection_satisfied=False), POLICY
    )
    assert result.decision is Decision.BLOCKED
    assert len(result.reasons) >= 2


def test_self_review_does_not_satisfy_independent_approval():
    pr = ready_pr(reviews=(ReviewEvidence(True, "worker-agent", SHA, independent=False),))
    result = evaluate_merge_readiness(pr, POLICY)
    assert result.decision is Decision.NOT_READY
    assert any("independent approval" in reason for reason in result.reasons)


def test_missing_required_gate_is_blocked():
    checks = dict(ready_pr().checks)
    del checks["security"]
    result = evaluate_merge_readiness(ready_pr(checks=checks), POLICY)
    assert result.decision is Decision.BLOCKED


def test_protected_change_can_be_ready_after_explicit_human_approval():
    pr = ready_pr(
        risk_class=RiskClass.PROTECTED,
        policy_authorizes_auto_merge=False,
        human_approvals=(HumanApprovalEvidence(
            approved=True, reviewer="sovereign-reviewer", reviewer_id="user-42",
            reviewed_sha=SHA, record_id="approval-2026-10-12-001",
            source="github-review", authorized=True,
        ),),
    )
    assert evaluate_merge_readiness(pr, POLICY).decision is Decision.READY_TO_MERGE


def test_base_movement_invalidates_acceptance_snapshot():
    result = evaluate_merge_readiness(ready_pr(observed_base_sha=SHA), POLICY)
    assert result.decision is Decision.BLOCKED
    assert any("base differs" in reason for reason in result.reasons)


def test_unknown_risk_class_fails_closed():
    result = evaluate_merge_readiness(ready_pr(risk_class=RiskClass.UNKNOWN), POLICY)
    assert result.decision is Decision.BLOCKED
