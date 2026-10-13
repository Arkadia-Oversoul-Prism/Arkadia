import json

import pytest

from weaver.engineering_acceptance import (
    CheckState, Decision, MergePolicy, RiskClass,
)
from weaver.github_readonly_evidence_adapter import (
    EvidenceCollectionError, GitHubReadOnlyEvidenceAdapter,
)


HEAD = "a" * 40
BASE = "b" * 40
POLICY = MergePolicy(version="eaa-v1", required_gates=("unit",))


def pr_payload(head=HEAD, base=BASE):
    return {
        "number": 17,
        "draft": False,
        "mergeable": True,
        "user": {"id": 7, "login": "author"},
        "head": {"sha": head, "ref": "feature"},
        "base": {"sha": base, "ref": "main"},
    }


def check_payload():
    return [{
        "id": 101,
        "name": "unit",
        "head_sha": HEAD,
        "status": "completed",
        "conclusion": "success",
        "html_url": "https://github.com/example/repo/actions/runs/101",
        "created_at": "2026-10-13T00:00:00Z",
    }]


def review_payload(reviewer_id=42, commit_id=HEAD, state="APPROVED"):
    return [{
        "id": 501,
        "user": {"id": reviewer_id, "login": "reviewer"},
        "state": state,
        "commit_id": commit_id,
        "submitted_at": "2026-10-13T00:01:00Z",
    }]


PROTECTION = {
    "required_status_checks": {"contexts": ["unit"], "checks": []},
    "required_pull_request_reviews": {"required_approving_review_count": 1},
}


class FakeAdapter(GitHubReadOnlyEvidenceAdapter):
    def __init__(self, *, reviewer_id=42, review_sha=HEAD, protection=PROTECTION, moved=False):
        super().__init__(
            "owner/repo",
            token="test-token",
            authorized_reviewer_ids=frozenset({"42"}),
        )
        self.reviewer_id = reviewer_id
        self.review_sha = review_sha
        self.protection = protection
        self.moved = moved
        self.get_calls = []
        self.pr_reads = 0

    def _get(self, url_or_path):
        self.get_calls.append(url_or_path)
        if "/pulls/17" in url_or_path:
            self.pr_reads += 1
            if self.moved and self.pr_reads == 2:
                return pr_payload(head="c" * 40), None
            return pr_payload(), None
        if "/branches/main/protection" in url_or_path:
            if isinstance(self.protection, Exception):
                raise self.protection
            return self.protection, None
        raise AssertionError(f"unexpected GET path: {url_or_path}")

    def _pages(self, path):
        if "/check-runs" in path:
            return check_payload()
        if "/reviews" in path:
            return review_payload(self.reviewer_id, self.review_sha)
        raise AssertionError(f"unexpected paginated GET path: {path}")


def test_collects_exact_sha_review_and_trusted_numeric_reviewer_id():
    adapter = FakeAdapter()
    result = adapter.collect(17, POLICY, risk_class=RiskClass.PROTECTED)

    assert result.evidence.head_sha == HEAD
    assert result.evidence.observed_head_sha == HEAD
    assert result.evidence.checks["unit"].state is CheckState.PASS
    assert len(result.evidence.human_approvals) == 1
    approval = result.evidence.human_approvals[0]
    assert approval.authorized is True
    assert approval.reviewer_id == "42"
    assert approval.reviewed_sha == HEAD
    assert result.evidence.branch_protection_satisfied is True
    assert all(call for call in adapter.get_calls)
    assert len([call for call in adapter.get_calls if "/pulls/17" in call]) == 2


def test_unlisted_reviewer_is_not_promoted_to_authorized_approval():
    result = FakeAdapter(reviewer_id=99).collect(17, POLICY, risk_class=RiskClass.PROTECTED)
    assert result.evidence.human_approvals == ()
    assert result.decision.decision is Decision.READY_FOR_HUMAN_DECISION


def test_approval_for_an_old_sha_does_not_count():
    result = FakeAdapter(review_sha=BASE).collect(17, POLICY, risk_class=RiskClass.PROTECTED)
    assert result.evidence.reviews == ()
    assert result.evidence.human_approvals == ()
    assert result.evidence.branch_protection_satisfied is False
    assert result.decision.decision is Decision.BLOCKED


def test_unavailable_branch_protection_fails_closed():
    result = FakeAdapter(protection=EvidenceCollectionError("HTTP 403")).collect(
        17, POLICY, risk_class=RiskClass.ROUTINE
    )
    assert result.evidence.evidence_complete is False
    assert result.evidence.branch_protection_satisfied is False
    assert result.decision.decision is Decision.BLOCKED
    assert any("fail-closed" in warning for warning in result.warnings)


def test_pr_head_movement_during_collection_blocks_snapshot():
    result = FakeAdapter(moved=True).collect(17, POLICY, risk_class=RiskClass.ROUTINE)
    assert result.evidence.observed_head_sha != result.evidence.head_sha
    assert result.evidence.evidence_complete is False
    assert result.decision.decision is Decision.BLOCKED


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.headers = {}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_transport_constructs_get_requests_only():
    methods = []

    def opener(request, timeout):
        methods.append(request.get_method())
        assert timeout > 0
        assert request.full_url.startswith("https://api.github.com/")
        return FakeResponse({"ok": True})

    adapter = GitHubReadOnlyEvidenceAdapter("owner/repo", token="test-token", opener=opener)
    payload, _ = adapter._get("/repos/owner/repo/pulls/17")
    assert payload == {"ok": True}
    assert methods == ["GET"]


def test_rejects_invalid_repository_and_non_numeric_allowlist():
    with pytest.raises(ValueError):
        GitHubReadOnlyEvidenceAdapter("../repo", token="test-token")
    with pytest.raises(ValueError):
        GitHubReadOnlyEvidenceAdapter(
            "owner/repo", token="test-token", authorized_reviewer_ids=frozenset({"reviewer-login"})
        )
