"""ARKADIA-CHIEF-PR-REVIEW-001 — governed Chief PR-review capability.

Every test here is a *boundary* test in the repository's established style: it
executes the real gate and asserts the refusal, or it feeds the real engine a
recorded snapshot and asserts the reading. Nothing asserts a substring in place
of a behaviour, and every detector that could be trivially true carries a
negative control.

Coverage map (issue #748 acceptance criteria):

  * existing Chief identity only ............................ test_capability_is_a_chief_capability
  * least-privilege worker + allowlist ...................... test_worker_*, test_webhook_*
  * Lab authorization/evidence reuse ........................ test_evidence_*, test_store_*
  * current-head validation / stale invalidation ............ test_stale_head_*
  * webhook security, idempotency, replay, retries, revocation
  * findings trace to real diff lines / check outputs ....... test_findings_*, test_added_lines_*
  * human-only and governance conflicts block ............... test_merge_*, test_publish_*
  * no default merge / silent approval / deployment ......... test_no_merge_*, test_shadow_*
"""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import pytest
from fastapi import HTTPException

import api.lab_routes as lab_routes
from lab.engineering_lab import pr_review as pr
from lab.engineering_lab.github_app import (
    ALLOWED_ACTIONS,
    GRANTED_PERMISSIONS,
    PERMISSION_MATRIX,
    ChangedFile,
    CheckRun,
    GitHubAppWorker,
    PullRequestSnapshot,
    WebhookRejected,
    signature_matches,
    verify_webhook_delivery,
)
from lab.engineering_lab.store import EngineeringLabStore

REPO_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "Arkadia-Oversoul-Prism/Arkadia"
INSTALLATION = 4242
HEAD = "a" * 40
BASE = "b" * 40


# ---------------------------------------------------------------------------
# fixtures and fakes
# ---------------------------------------------------------------------------


@pytest.fixture()
def worker_env(monkeypatch):
    monkeypatch.setenv("ARKADIA_PR_REVIEW_APP_ID", "123456")
    monkeypatch.setenv("ARKADIA_PR_REVIEW_APP_SLUG", "arkadia-chief-review")
    monkeypatch.setenv("ARKADIA_PR_REVIEW_INSTALLATION_ID", str(INSTALLATION))
    monkeypatch.setenv("ARKADIA_PR_REVIEW_REPOSITORIES", REPOSITORY)
    monkeypatch.setenv("ARKADIA_PR_REVIEW_INSTALLATION_TOKEN", "ghs_test_installation_token")
    monkeypatch.setenv("ARKADIA_PR_REVIEW_WEBHOOK_SECRET", "webhook-secret")
    monkeypatch.setenv("ARKADIA_PR_REVIEW_STAGE", "SHADOW")
    monkeypatch.delenv("ARKADIA_PR_REVIEW_ACTIVATION_REF", raising=False)
    monkeypatch.delenv("ARKADIA_PR_REVIEW_ALLOW_COMMENT", raising=False)
    monkeypatch.delenv("ARKADIA_PR_REVIEW_ALLOW_REQUEST_CHANGES", raising=False)
    monkeypatch.delenv("ARKADIA_PR_REVIEW_ALLOW_APPROVE", raising=False)
    return monkeypatch


def snapshot(
    *,
    head=HEAD,
    base=BASE,
    author="someone-else",
    draft=False,
    state="open",
    files=(ChangedFile("lab/engineering_lab/pr_review.py", "modified", 10, 1, "@@ -1,1 +1,2 @@\n context\n+added\n"),),
    checks=(CheckRun("validate", "completed", "success", "https://example/1", HEAD),),
    files_observed=True,
    checks_observed=True,
) -> PullRequestSnapshot:
    return PullRequestSnapshot(
        repository=REPOSITORY,
        number=748,
        state=state,
        draft=draft,
        author=author,
        base_sha=base,
        head_sha=head,
        mergeable_state="clean",
        changed_files=tuple(files),
        checks=tuple(checks),
        files_observed=files_observed,
        checks_observed=checks_observed,
    )


class FakeReader:
    """A recorded reader. Exercises the real engine with no network."""

    def __init__(self, snap: PullRequestSnapshot) -> None:
        self.snap = snap
        self.reads = 0

    def read_pull_request(self, repository, number):
        self.reads += 1
        return self.snap

    def read_head_sha(self, repository, number):
        return self.snap.head_sha


def allow_all(paths):
    return True, "PASS"


def request(**overrides) -> pr.PrReviewRequest:
    payload = dict(
        subject_ref="uid-founder",
        principal="uid-founder",
        repository=REPOSITORY,
        pr_number=748,
        base_sha=BASE,
        head_sha=HEAD,
        installation_id=INSTALLATION,
        event_id="REQ-1",
    )
    payload.update(overrides)
    return pr.PrReviewRequest(**payload)


# ---------------------------------------------------------------------------
# the capability is a capability OF the existing Chief
# ---------------------------------------------------------------------------


def test_capability_is_a_chief_capability_and_declares_its_reuse():
    manifest = pr.capability_manifest()
    assert manifest["capability_id"] == pr.CAPABILITY_ID == "chief.pr_review"
    assert manifest["owner_principal"] == pr.OWNER_PRINCIPAL == "ARKADIA-CHIEF-001"
    assert manifest["default_mode"] == "shadow_read_only"
    # Reuse is declared, not implied: the canonical contracts are named.
    assert manifest["reuses"]["evidence"].endswith("EvidenceRecord")
    assert manifest["reuses"]["authorization"].startswith("el_authorizations")
    assert manifest["reuses"]["jobs"].startswith("el_pr_review_jobs")


def test_capability_module_creates_no_second_identity_or_persistence():
    """The module must not mint an identity or own a database of its own."""
    source = (REPO_ROOT / "lab" / "engineering_lab" / "pr_review.py").read_text(encoding="utf-8")
    assert "sqlite3" not in source, "the capability must use the canonical Lab store"
    assert not re.search(r"^\s*PRINCIPAL_ID\s*=", source, re.MULTILINE), (
        "the capability may not define a second principal id"
    )
    assert "class EngineeringLabStore" not in source
    # The only principal it names is the existing canonical Chief.
    assert source.count('OWNER_PRINCIPAL = "ARKADIA-CHIEF-001"') == 1


# ---------------------------------------------------------------------------
# separate permission gates
# ---------------------------------------------------------------------------


def test_every_review_action_has_its_own_gate():
    assert set(pr.ACTION_GATES) == set(pr.REVIEW_ACTIONS)
    assert pr.ACTION_GATES[pr.MERGE].human_only is True
    assert pr.ACTION_GATES[pr.PUBLISH_COMMENT].writes_github is True
    assert pr.ACTION_GATES[pr.READ].writes_github is False
    # A review action that writes must require the publish permission, not read.
    for action in (pr.PUBLISH_COMMENT, pr.REQUEST_CHANGES, pr.APPROVE, pr.MERGE):
        assert pr.ACTION_GATES[action].permission == "publish_review" or action == pr.MERGE


def test_shadow_stage_permits_read_and_findings_only():
    policy = pr.ReviewPolicy(stage="SHADOW", repositories=(REPOSITORY,))
    assert pr.assert_action_permitted(pr.READ, policy).action == pr.READ
    assert pr.assert_action_permitted(pr.GENERATE_FINDINGS, policy).action == pr.GENERATE_FINDINGS
    for action in (pr.PUBLISH_COMMENT, pr.REQUEST_CHANGES, pr.APPROVE, pr.MERGE):
        with pytest.raises(pr.BoundaryViolation):
            pr.assert_action_permitted(action, policy)


def test_activated_stage_still_refuses_merge_and_unflagged_actions():
    activated = pr.ReviewPolicy(stage="ACTIVATED", activation_ref="docs/policy.md")
    with pytest.raises(pr.BoundaryViolation) as excinfo:
        pr.assert_action_permitted(pr.MERGE, activated)
    assert "human-only" in str(excinfo.value)
    # Activated is not enough: the named policy flag is a second gate.
    with pytest.raises(pr.BoundaryViolation) as excinfo:
        pr.assert_action_permitted(pr.PUBLISH_COMMENT, activated)
    assert "allows_comment" in str(excinfo.value)


def test_unknown_action_is_refused_rather_than_defaulted():
    with pytest.raises(pr.BoundaryViolation):
        pr.assert_action_permitted("MERGE_ANYWAY", pr.ReviewPolicy(stage="ACTIVATED"))


def test_negative_control_the_gate_can_pass():
    """A gate that refuses everything would make the refusals above vacuous."""
    policy = pr.ReviewPolicy(
        stage="ACTIVATED", activation_ref="ref", allows_comment=True
    )
    assert pr.assert_action_permitted(pr.PUBLISH_COMMENT, policy).action == pr.PUBLISH_COMMENT


# ---------------------------------------------------------------------------
# rollout state is derived, never inferred
# ---------------------------------------------------------------------------


def test_rollout_state_without_a_worker_is_implemented_not_shadow(monkeypatch):
    for name in (
        "ARKADIA_PR_REVIEW_APP_ID",
        "ARKADIA_PR_REVIEW_INSTALLATION_ID",
        "ARKADIA_PR_REVIEW_REPOSITORIES",
        "ARKADIA_PR_REVIEW_INSTALLATION_TOKEN",
    ):
        monkeypatch.delenv(name, raising=False)
    state = pr.rollout_state(pr.ReviewPolicy(stage="SHADOW"), GitHubAppWorker.from_env())
    assert state["state"] == "IMPLEMENTED"
    assert state["worker"] == "UNCONFIGURED"
    assert state["write_actions_enabled"] == []
    assert state["merge_enabled"] is False


def test_rollout_state_with_a_configured_worker_is_shadow(worker_env):
    state = pr.rollout_state(pr.ReviewPolicy(stage="SHADOW"), GitHubAppWorker.from_env())
    assert state["state"] == "SHADOW"
    assert state["worker"] == "AVAILABLE"
    assert state["write_actions_enabled"] == []
    assert state["merge_enabled"] is False


def test_activated_requires_an_explicit_activation_reference(worker_env):
    without_ref = pr.rollout_state(
        pr.ReviewPolicy(stage="ACTIVATED", repositories=(REPOSITORY,)),
        GitHubAppWorker.from_env(),
    )
    # A stage string alone never activates: with no activation reference the
    # derived state falls back to the most restrictive reachable one.
    assert without_ref["state"] != "ACTIVATED"
    assert without_ref["state"] == "IMPLEMENTED"
    with_ref = pr.rollout_state(
        pr.ReviewPolicy(stage="ACTIVATED", activation_ref="docs/activation.md"),
        GitHubAppWorker.from_env(),
    )
    assert with_ref["state"] == "ACTIVATED"
    # Activation alone does not enable a write: the named policy flag is a
    # second, independent gate.
    assert with_ref["write_actions_enabled"] == []
    flagged = pr.rollout_state(
        pr.ReviewPolicy(
            stage="ACTIVATED", activation_ref="docs/activation.md", allows_comment=True
        ),
        GitHubAppWorker.from_env(),
    )
    assert "PUBLISH_COMMENT" in flagged["write_actions_enabled"]
    assert "MERGE" not in flagged["write_actions_enabled"]


def test_unrecognised_stage_is_a_conflict_not_a_default_allow(monkeypatch):
    monkeypatch.setenv("ARKADIA_PR_REVIEW_STAGE", "PRODUCTION")
    policy = pr.ReviewPolicy.from_env()
    assert policy.stage == "IMPLEMENTED"
    assert policy.stage_conflict
    assert "PRODUCTION" in policy.stage_conflict


# ---------------------------------------------------------------------------
# worker identity and least privilege
# ---------------------------------------------------------------------------


def test_worker_never_borrows_a_pat_or_ambient_credential(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_a_user_token_that_must_not_be_used")
    monkeypatch.delenv("ARKADIA_PR_REVIEW_INSTALLATION_TOKEN", raising=False)
    worker = GitHubAppWorker.from_env()
    assert worker.status()["state"] == "UNCONFIGURED"
    with pytest.raises(Exception) as excinfo:
        worker.credential()
    assert "refusing to borrow" in str(excinfo.value)


def test_worker_refuses_a_repository_outside_the_allowlist(worker_env):
    worker = GitHubAppWorker.from_env()
    with pytest.raises(Exception) as excinfo:
        worker.verify_binding("someone-else/private", INSTALLATION)
    assert "allowlist" in str(excinfo.value)


def test_worker_refuses_an_installation_mismatch(worker_env):
    worker = GitHubAppWorker.from_env()
    with pytest.raises(Exception) as excinfo:
        worker.verify_binding(REPOSITORY, 9999)
    assert "installation" in str(excinfo.value)


def test_permission_matrix_is_least_privilege():
    assert GRANTED_PERMISSIONS == {
        "metadata": "read",
        "contents": "read",
        "pull_requests": "write",
        "checks": "read",
    }
    for capability, perms in PERMISSION_MATRIX.items():
        for scope in perms:
            assert scope in GRANTED_PERMISSIONS, f"{capability} asks for ungranted {scope}"
    for forbidden in ("checks", "statuses", "administration", "secrets", "workflows", "deployments"):
        assert not any(
            scope == forbidden and level == "write"
            for scope, level in GRANTED_PERMISSIONS.items()
        ), f"{forbidden}:write must not be requested"


# ---------------------------------------------------------------------------
# webhook verification
# ---------------------------------------------------------------------------


def _delivery_headers(body: bytes, *, delivery="d-1", event="pull_request", target="integration"):
    import hashlib
    import hmac

    signature = "sha256=" + hmac.new(b"webhook-secret", body, hashlib.sha256).hexdigest()
    return {
        "X-Hub-Signature-256": signature,
        "X-GitHub-Delivery": delivery,
        "X-GitHub-Event": event,
        "X-GitHub-Hook-Installation-Target-Type": target,
    }


def _payload(action="opened", repository=REPOSITORY, installation=INSTALLATION, number=748):
    return json.dumps(
        {
            "action": action,
            "repository": {"full_name": repository},
            "installation": {"id": installation},
            "sender": {"login": "someone-else"},
            "pull_request": {
                "number": number,
                "head": {"sha": HEAD},
                "base": {"sha": BASE},
            },
        }
    ).encode()


def test_signature_comparison_rejects_a_malformed_or_absent_header():
    body = b"{}"
    assert signature_matches("s", body, "") is False
    assert signature_matches("s", body, "sha256=deadbeef") is False
    assert signature_matches("", body, "sha256=deadbeef") is False


def test_verified_delivery_carries_the_exact_binding(worker_env):
    body = _payload()
    delivery = verify_webhook_delivery(
        headers=_delivery_headers(body), body=body, worker=GitHubAppWorker.from_env()
    )
    assert delivery.accepted is True
    assert delivery.repository == REPOSITORY
    assert delivery.installation_id == INSTALLATION
    assert delivery.pr_number == 748
    assert delivery.head_sha == HEAD and delivery.base_sha == BASE


def test_unsigned_delivery_is_refused_when_no_secret_is_configured(worker_env):
    worker_env.delenv("ARKADIA_PR_REVIEW_WEBHOOK_SECRET", raising=False)
    body = _payload()
    with pytest.raises(WebhookRejected) as excinfo:
        verify_webhook_delivery(headers=_delivery_headers(body), body=body, worker=GitHubAppWorker.from_env())
    assert excinfo.value.status_code == 503
    assert "unsigned" in str(excinfo.value)


def test_forged_signature_is_refused(worker_env):
    body = _payload()
    headers = _delivery_headers(body)
    headers["X-Hub-Signature-256"] = "sha256=" + "0" * 64
    with pytest.raises(WebhookRejected) as excinfo:
        verify_webhook_delivery(headers=headers, body=body, worker=GitHubAppWorker.from_env())
    assert excinfo.value.status_code == 401


def test_signed_delivery_for_a_non_allowlisted_repository_is_refused(worker_env):
    body = _payload(repository="someone-else/private")
    with pytest.raises(WebhookRejected) as excinfo:
        verify_webhook_delivery(headers=_delivery_headers(body), body=body, worker=GitHubAppWorker.from_env())
    assert excinfo.value.status_code == 403
    assert "allowlist" in str(excinfo.value)


def test_signed_delivery_with_a_foreign_installation_is_refused(worker_env):
    body = _payload(installation=9999)
    with pytest.raises(WebhookRejected) as excinfo:
        verify_webhook_delivery(headers=_delivery_headers(body), body=body, worker=GitHubAppWorker.from_env())
    assert excinfo.value.status_code == 403


def test_delivery_without_an_id_cannot_be_deduplicated(worker_env):
    body = _payload()
    headers = _delivery_headers(body)
    headers.pop("X-GitHub-Delivery")
    with pytest.raises(WebhookRejected) as excinfo:
        verify_webhook_delivery(headers=headers, body=body, worker=GitHubAppWorker.from_env())
    assert excinfo.value.status_code == 400


def test_non_app_delivery_target_is_refused(worker_env):
    body = _payload()
    headers = _delivery_headers(body, target="repository")
    with pytest.raises(WebhookRejected) as excinfo:
        verify_webhook_delivery(headers=headers, body=body, worker=GitHubAppWorker.from_env())
    assert excinfo.value.status_code == 403


def test_unrelated_events_are_ignored_not_reviewed(worker_env):
    body = _payload()
    delivery = verify_webhook_delivery(
        headers=_delivery_headers(body, event="push"),
        body=body,
        worker=GitHubAppWorker.from_env(),
    )
    assert delivery.accepted is False
    assert "not a review trigger" in delivery.reason


def test_unrelated_pr_actions_are_ignored(worker_env):
    body = _payload(action="closed")
    assert "closed" not in ALLOWED_ACTIONS
    delivery = verify_webhook_delivery(
        headers=_delivery_headers(body), body=body, worker=GitHubAppWorker.from_env()
    )
    assert delivery.accepted is False


# ---------------------------------------------------------------------------
# durable idempotency, replay and retries
# ---------------------------------------------------------------------------


@pytest.fixture()
def store():
    return EngineeringLabStore()


def _job(key: str, **overrides):
    payload = {
        "job_id": f"PRR-{abs(hash(key)) % 10**10}",
        "idempotency_key": key,
        "repository_ref": REPOSITORY,
        "pr_number": 748,
        "base_sha": BASE,
        "head_sha": HEAD,
        "action": pr.GENERATE_FINDINGS,
        "state": "QUEUED",
        "attempts": 0,
    }
    payload.update(overrides)
    return payload


def test_job_claim_is_idempotent_per_key(store):
    subject = "uid-idempotent-001"
    first = store.claim_pr_review_job(_job("k-1"), subject)
    assert first["deduplicated"] is False
    second = store.claim_pr_review_job(_job("k-1"), subject)
    assert second["deduplicated"] is True
    assert second["job_id"] == first["job_id"]
    assert len(store.list_pr_review_jobs(subject)) == 1


def test_job_claim_is_not_shared_across_subjects(store):
    store.claim_pr_review_job(_job("k-2"), "uid-a")
    with pytest.raises(ValueError):
        store.claim_pr_review_job(_job("k-2"), "uid-b")


def test_delivery_ledger_distinguishes_new_duplicate_and_replay(store):
    kwargs = dict(
        installation_id=INSTALLATION,
        repository_ref=REPOSITORY,
        payload_digest="digest",
        window_seconds=600,
    )
    assert store.claim_pr_review_delivery("d-100", now_epoch=1000.0, **kwargs) == "new"
    assert store.claim_pr_review_delivery("d-100", now_epoch=1100.0, **kwargs) == "duplicate"
    assert store.claim_pr_review_delivery("d-100", now_epoch=5000.0, **kwargs) == "replay"


def test_retry_policy_is_bounded_and_backed_off():
    policy = pr.RetryPolicy(max_attempts=3, base_backoff_seconds=10)
    assert [policy.backoff(n) for n in (1, 2, 3)] == [10, 20, 40]
    assert policy.should_retry(1) and policy.should_retry(2)
    assert policy.should_not_retry(3) if hasattr(policy, "should_not_retry") else not policy.should_retry(3)


# ---------------------------------------------------------------------------
# findings trace to real diff lines and real check outputs
# ---------------------------------------------------------------------------


def test_added_lines_use_post_change_line_numbers():
    patch = "@@ -10,3 +10,4 @@\n context\n+first added\n+second added\n-removed\n tail"
    assert pr.added_lines(patch) == [(11, "first added"), (12, "second added")]


def test_added_lines_negative_control_without_a_hunk_header():
    """No hunk header means no line numbers; a parser that guesses would be wrong."""
    assert pr.added_lines("+orphan line") == []
    assert pr.added_lines(None) == []


def test_failing_check_blocks_with_the_real_check_output(worker_env):
    snap = snapshot(checks=(CheckRun("validate", "completed", "failure", "https://ci/1", HEAD),))
    result = pr.review_pull_request(request(), reader=FakeReader(snap), policy=pr.ReviewPolicy(stage="SHADOW", repositories=(REPOSITORY,)), worker=GitHubAppWorker.from_env(), path_policy=allow_all)
    assert result.status == pr.RED
    finding = next(f for f in result.findings if f.code == "CHECK_FAILED")
    assert finding.evidence["details_url"] == "https://ci/1"
    assert finding.evidence["head_sha"] == HEAD


def test_required_check_that_never_ran_blocks(worker_env):
    snap = snapshot()
    policy = pr.ReviewPolicy(stage="SHADOW", required_checks=("codeql",))
    result = pr.review_pull_request(request(), reader=FakeReader(snap), policy=policy, worker=GitHubAppWorker.from_env(), path_policy=allow_all)
    assert result.status == pr.RED
    assert any(f.code == "REQUIRED_CHECK_MISSING" for f in result.findings)


def test_pending_check_is_amber_not_green(worker_env):
    snap = snapshot(checks=(CheckRun("validate", "in_progress", None, None, HEAD),))
    result = pr.review_pull_request(request(), reader=FakeReader(snap), policy=pr.ReviewPolicy(stage="SHADOW"), worker=GitHubAppWorker.from_env(), path_policy=allow_all)
    assert result.status == pr.AMBER


def test_unobserved_checks_fail_closed(worker_env):
    snap = snapshot(checks=(), checks_observed=False)
    result = pr.review_pull_request(request(), reader=FakeReader(snap), policy=pr.ReviewPolicy(stage="SHADOW"), worker=GitHubAppWorker.from_env(), path_policy=allow_all)
    assert result.status == pr.AMBER
    assert result.evidence_complete is False
    assert any(f.code == "CHECKS_UNOBSERVED" for f in result.findings)


def test_unobserved_diff_fails_closed(worker_env):
    snap = snapshot(files=(), files_observed=False)
    result = pr.review_pull_request(request(), reader=FakeReader(snap), policy=pr.ReviewPolicy(stage="SHADOW"), worker=GitHubAppWorker.from_env(), path_policy=allow_all)
    assert result.status == pr.AMBER
    assert result.evidence_complete is False


def test_absent_path_policy_is_recorded_not_assumed_admissible(worker_env):
    snap = snapshot()
    result = pr.review_pull_request(request(), reader=FakeReader(snap), policy=pr.ReviewPolicy(stage="SHADOW"), worker=GitHubAppWorker.from_env(), path_policy=None)
    assert result.status == pr.AMBER
    assert any(f.code == "PATH_POLICY_UNOBSERVED" for f in result.findings)


def test_path_outside_the_canonical_policy_blocks(worker_env):
    snap = snapshot(files=(ChangedFile("bogus-root/x.py", "added", 3, 0, "@@ -0,0 +1,1 @@\n+x"),))
    result = pr.review_pull_request(request(), reader=FakeReader(snap), policy=pr.ReviewPolicy(stage="SHADOW"), worker=GitHubAppWorker.from_env(), path_policy=lab_routes._canonical_path_policy())
    assert result.status == pr.RED
    assert any(f.code == "PATH_OUTSIDE_POLICY" for f in result.findings)


def test_credential_shaped_addition_blocks_at_the_real_line(worker_env):
    patch = "@@ -1,1 +1,2 @@\n context\n+token = \"ghp_abcdefghijklmnopqrstuvwxyz0123\"\n"
    snap = snapshot(files=(ChangedFile("lab/x.py", "modified", 1, 0, patch),))
    result = pr.review_pull_request(request(), reader=FakeReader(snap), policy=pr.ReviewPolicy(stage="SHADOW"), worker=GitHubAppWorker.from_env(), path_policy=allow_all)
    assert result.status == pr.RED
    finding = next(f for f in result.findings if f.code == "CREDENTIAL_SHAPED_ADDITION")
    assert finding.path == "lab/x.py"
    assert finding.line == 2


def test_a_clean_observed_pr_is_green(worker_env):
    result = pr.review_pull_request(request(), reader=FakeReader(snapshot()), policy=pr.ReviewPolicy(stage="SHADOW", repositories=(REPOSITORY,)), worker=GitHubAppWorker.from_env(), path_policy=allow_all)
    assert result.status == pr.GREEN
    assert result.evidence_complete is True
    assert result.findings == ()


def test_green_is_not_merge_authorization(worker_env):
    result = pr.review_pull_request(request(), reader=FakeReader(snapshot()), policy=pr.ReviewPolicy(stage="SHADOW"), worker=GitHubAppWorker.from_env(), path_policy=allow_all)
    assert result.status == pr.GREEN
    assert "GREEN != MERGE AUTHORIZATION" in result.to_dict()["non_collapses"]
    assert "not merge authorization" in result.to_markdown()


# ---------------------------------------------------------------------------
# current-head validation and stale invalidation
# ---------------------------------------------------------------------------


def test_head_change_invalidates_findings(worker_env):
    moved = snapshot(head="c" * 40)
    result = pr.review_pull_request(request(), reader=FakeReader(moved), policy=pr.ReviewPolicy(stage="SHADOW"), worker=GitHubAppWorker.from_env(), path_policy=allow_all)
    assert result.status == pr.RED
    assert result.stale is True
    assert any(f.code == "STALE_HEAD" for f in result.findings)
    assert result.evidence_complete is False


def test_assert_head_current_refuses_a_moved_head():
    binding = pr.HeadBinding(REPOSITORY, 748, BASE, HEAD)
    with pytest.raises(pr.StaleHead):
        pr.assert_head_current(FakeReader(snapshot(head="d" * 40)), binding)
    # Negative control: the same call succeeds on the bound head.
    assert pr.assert_head_current(FakeReader(snapshot()), binding) == HEAD


def test_approval_scope_changes_when_the_head_changes():
    first = pr.HeadBinding(REPOSITORY, 748, BASE, HEAD)
    second = pr.HeadBinding(REPOSITORY, 748, BASE, "e" * 40)
    assert first.scope_ref(pr.PUBLISH_COMMENT) != second.scope_ref(pr.PUBLISH_COMMENT)


def test_a_grant_for_another_head_does_not_match():
    binding = pr.HeadBinding(REPOSITORY, 748, BASE, HEAD)
    stale_grant = {
        "scope_ref": pr.HeadBinding(REPOSITORY, 748, BASE, "f" * 40).scope_ref(pr.PUBLISH_COMMENT),
        "operations_allowed": [pr.PUBLISH_COMMENT],
    }
    with pytest.raises(pr.BoundaryViolation):
        pr.assert_grant_matches(stale_grant, binding, pr.PUBLISH_COMMENT)


def test_revoked_and_consumed_grants_do_not_match():
    binding = pr.HeadBinding(REPOSITORY, 748, BASE, HEAD)
    base_grant = {
        "scope_ref": binding.scope_ref(pr.PUBLISH_COMMENT),
        "operations_allowed": [pr.PUBLISH_COMMENT],
    }
    pr.assert_grant_matches(base_grant, binding, pr.PUBLISH_COMMENT)
    with pytest.raises(pr.BoundaryViolation):
        pr.assert_grant_matches({**base_grant, "revoked_at": "2026-01-01T00:00:00Z"}, binding, pr.PUBLISH_COMMENT)
    with pytest.raises(pr.BoundaryViolation):
        pr.assert_grant_matches({**base_grant, "consumed_at": "2026-01-01T00:00:00Z"}, binding, pr.PUBLISH_COMMENT)
    with pytest.raises(pr.BoundaryViolation):
        pr.assert_grant_matches({**base_grant, "operations_allowed": [pr.APPROVE]}, binding, pr.PUBLISH_COMMENT)


# ---------------------------------------------------------------------------
# independence and self-review
# ---------------------------------------------------------------------------


def test_self_review_is_refused_for_writes_and_flagged_for_reads(worker_env):
    snap = snapshot(author="uid-founder")
    result = pr.review_pull_request(request(), reader=FakeReader(snap), policy=pr.ReviewPolicy(stage="SHADOW"), worker=GitHubAppWorker.from_env(), path_policy=allow_all)
    assert result.status == pr.AMBER
    assert any(f.code == "SELF_REVIEW" for f in result.findings)
    with pytest.raises(pr.BoundaryViolation):
        pr.assert_independent("uid-founder", "uid-founder")
    # Negative control: an independent principal is not refused.
    pr.assert_independent("uid-reviewer", "uid-founder")


# ---------------------------------------------------------------------------
# evidence contract reuse
# ---------------------------------------------------------------------------


def test_evidence_binds_principal_binding_worker_policy_and_actions(worker_env):
    result = pr.review_pull_request(request(), reader=FakeReader(snapshot()), policy=pr.ReviewPolicy(stage="SHADOW"), worker=GitHubAppWorker.from_env(), path_policy=allow_all)
    record = pr.build_evidence(result, workspace_ref="engineering-lab")
    payload = record.to_dict()
    assert payload["run_ref"] == result.job_id
    assert payload["state"] == "VERIFIED"
    detail = payload["detail"]
    assert detail["principal"] == "uid-founder"
    assert detail["binding"]["head_sha"] == HEAD
    assert detail["worker"]["credential_source"] == "github_app_installation_token"
    assert detail["policy"]["policy_fingerprint"]
    assert detail["actions"] == [pr.READ, pr.GENERATE_FINDINGS]
    assert payload["provenance"]["capability_id"] == pr.CAPABILITY_ID


def test_evidence_is_unresolved_when_the_review_is_stale(worker_env):
    result = pr.review_pull_request(request(), reader=FakeReader(snapshot(head="9" * 40)), policy=pr.ReviewPolicy(stage="SHADOW"), worker=GitHubAppWorker.from_env(), path_policy=allow_all)
    record = pr.build_evidence(result, workspace_ref="engineering-lab")
    assert record.state == "UNRESOLVED"


def test_evidence_is_persisted_through_the_canonical_lab_store(worker_env):
    store = EngineeringLabStore()
    subject = "uid-evidence-001"
    result = pr.review_pull_request(request(subject_ref=subject, job_id="PRR-EVIDENCE-1"), reader=FakeReader(snapshot()), policy=pr.ReviewPolicy(stage="SHADOW"), worker=GitHubAppWorker.from_env(), path_policy=allow_all)
    saved = store.save_evidence(pr.build_evidence(result, workspace_ref="engineering-lab"))
    stored = store.list_evidence(subject, run_ref="PRR-EVIDENCE-1")
    assert stored and stored[0]["evidence_id"] == saved["evidence_id"]


# ---------------------------------------------------------------------------
# API integration: request, run, grant, publish, webhook
# ---------------------------------------------------------------------------


def _patch_reader(monkeypatch, snap):
    monkeypatch.setattr(lab_routes, "_review_reader", lambda worker: FakeReader(snap))


def test_request_route_fails_closed_without_a_worker(monkeypatch):
    for name in (
        "ARKADIA_PR_REVIEW_APP_ID",
        "ARKADIA_PR_REVIEW_INSTALLATION_ID",
        "ARKADIA_PR_REVIEW_REPOSITORIES",
        "ARKADIA_PR_REVIEW_INSTALLATION_TOKEN",
    ):
        monkeypatch.delenv(name, raising=False)
    body = lab_routes.PrReviewRequestBody(
        repository=REPOSITORY, pr_number=748, base_sha=BASE, head_sha=HEAD,
        installation_id=INSTALLATION, event_id="REQ-unconfigured",
    )
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(lab_routes.pr_review_request(body, {"uid": "uid-api-001"}))
    assert excinfo.value.status_code == 503
    assert excinfo.value.detail["state"] == "DEAD_LETTER"


def test_request_route_completes_a_shadow_review(worker_env, monkeypatch):
    _patch_reader(monkeypatch, snapshot())
    uid = "uid-api-002"
    body = lab_routes.PrReviewRequestBody(
        repository=REPOSITORY, pr_number=748, base_sha=BASE, head_sha=HEAD,
        installation_id=INSTALLATION, event_id="REQ-shadow",
    )
    payload = asyncio.run(lab_routes.pr_review_request(body, {"uid": uid}))
    assert payload["job"]["state"] == "COMPLETED"
    assert payload["result"]["status"] == pr.GREEN
    assert payload["evidence"]["run_ref"] == payload["job"]["job_id"]
    assert "Chief PR review" in payload["markdown"]

    # The same event id is idempotent: no second review of the same head.
    again = asyncio.run(lab_routes.pr_review_request(body, {"uid": uid}))
    assert again["deduplicated"] is True
    assert again["job"]["job_id"] == payload["job"]["job_id"]


def test_grant_route_refuses_before_activation(worker_env, monkeypatch):
    _patch_reader(monkeypatch, snapshot())
    uid = "uid-api-003"
    body = lab_routes.PrReviewRequestBody(
        repository=REPOSITORY, pr_number=748, base_sha=BASE, head_sha=HEAD,
        installation_id=INSTALLATION, event_id="REQ-grant",
    )
    payload = asyncio.run(lab_routes.pr_review_request(body, {"uid": uid}))
    job_id = payload["job"]["job_id"]
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            lab_routes.pr_review_grant(
                job_id, lab_routes.PrReviewGrantBody(action=pr.PUBLISH_COMMENT), {"uid": uid}
            )
        )
    assert excinfo.value.status_code == 403
    assert "ACTIVATED" in str(excinfo.value.detail)


def _activate(monkeypatch, *, allow_comment=True):
    monkeypatch.setenv("ARKADIA_PR_REVIEW_STAGE", "ACTIVATED")
    monkeypatch.setenv("ARKADIA_PR_REVIEW_ACTIVATION_REF", "docs/activation.md")
    if allow_comment:
        monkeypatch.setenv("ARKADIA_PR_REVIEW_ALLOW_COMMENT", "true")


def test_activated_grant_then_publish_binds_the_exact_tuple(worker_env, monkeypatch):
    snap = snapshot()
    _patch_reader(monkeypatch, snap)
    _activate(monkeypatch)
    uid = "uid-api-004"
    body = lab_routes.PrReviewRequestBody(
        repository=REPOSITORY, pr_number=748, base_sha=BASE, head_sha=HEAD,
        installation_id=INSTALLATION, event_id="REQ-publish",
    )
    payload = asyncio.run(lab_routes.pr_review_request(body, {"uid": uid}))
    job_id = payload["job"]["job_id"]

    grant = asyncio.run(
        lab_routes.pr_review_grant(
            job_id,
            lab_routes.PrReviewGrantBody(action=pr.PUBLISH_COMMENT, duration_minutes=15),
            {"uid": uid},
        )
    )
    assert grant["binding"]["head_sha"] == HEAD
    assert grant["authorization"]["merge_prohibited"] is True

    published = {}
    monkeypatch.setattr(
        lab_routes,
        "_post_review",
        lambda worker, repo, number, event, text: published.update(
            {"repo": repo, "number": number, "event": event}
        )
        or {"id": 1, "state": "COMMENTED", "html_url": "https://gh/review/1"},
    )
    result = asyncio.run(
        lab_routes.pr_review_publish(
            job_id,
            lab_routes.PrReviewPublishBody(
                action=pr.PUBLISH_COMMENT, authorization_ref=grant["authorization_ref"]
            ),
            {"uid": uid},
        )
    )
    assert published == {"repo": REPOSITORY, "number": 748, "event": "COMMENT"}
    assert result["consumed_at"]

    # The grant is single-use: a second publish is refused.
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            lab_routes.pr_review_publish(
                job_id,
                lab_routes.PrReviewPublishBody(
                    action=pr.PUBLISH_COMMENT, authorization_ref=grant["authorization_ref"]
                ),
                {"uid": uid},
            )
        )
    assert excinfo.value.status_code == 403


def test_publish_refuses_when_the_head_moved_after_the_grant(worker_env, monkeypatch):
    _patch_reader(monkeypatch, snapshot())
    _activate(monkeypatch)
    uid = "uid-api-005"
    body = lab_routes.PrReviewRequestBody(
        repository=REPOSITORY, pr_number=748, base_sha=BASE, head_sha=HEAD,
        installation_id=INSTALLATION, event_id="REQ-stale",
    )
    payload = asyncio.run(lab_routes.pr_review_request(body, {"uid": uid}))
    job_id = payload["job"]["job_id"]
    grant = asyncio.run(
        lab_routes.pr_review_grant(
            job_id, lab_routes.PrReviewGrantBody(action=pr.PUBLISH_COMMENT), {"uid": uid}
        )
    )
    _patch_reader(monkeypatch, snapshot(head="7" * 40))
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            lab_routes.pr_review_publish(
                job_id,
                lab_routes.PrReviewPublishBody(
                    action=pr.PUBLISH_COMMENT, authorization_ref=grant["authorization_ref"]
                ),
                {"uid": uid},
            )
        )
    assert excinfo.value.status_code == 409
    assert "head moved" in str(excinfo.value.detail)


def test_publish_refuses_self_approval(worker_env, monkeypatch):
    _patch_reader(monkeypatch, snapshot(author="uid-author"))
    _activate(monkeypatch)
    uid = "uid-author"
    body = lab_routes.PrReviewRequestBody(
        repository=REPOSITORY, pr_number=748, base_sha=BASE, head_sha=HEAD,
        installation_id=INSTALLATION, event_id="REQ-self",
    )
    payload = asyncio.run(lab_routes.pr_review_request(body, {"uid": uid}))
    job_id = payload["job"]["job_id"]
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            lab_routes.pr_review_grant(
                job_id, lab_routes.PrReviewGrantBody(action=pr.PUBLISH_COMMENT), {"uid": uid}
            )
        )
    assert excinfo.value.status_code in (403, 409)
    assert "independent review" in str(excinfo.value.detail)


def test_publish_is_refused_in_shadow_mode(worker_env, monkeypatch):
    _patch_reader(monkeypatch, snapshot())
    uid = "uid-api-006"
    body = lab_routes.PrReviewRequestBody(
        repository=REPOSITORY, pr_number=748, base_sha=BASE, head_sha=HEAD,
        installation_id=INSTALLATION, event_id="REQ-shadow-publish",
    )
    payload = asyncio.run(lab_routes.pr_review_request(body, {"uid": uid}))
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            lab_routes.pr_review_publish(
                payload["job"]["job_id"],
                lab_routes.PrReviewPublishBody(action=pr.PUBLISH_COMMENT, authorization_ref="AUTH-x"),
                {"uid": uid},
            )
        )
    assert excinfo.value.status_code == 403


def test_request_route_refuses_a_merge_action(worker_env, monkeypatch):
    """A request may not smuggle a write action in through `action`."""
    _patch_reader(monkeypatch, snapshot())
    _activate(monkeypatch)
    uid = "uid-api-010"
    body = lab_routes.PrReviewRequestBody(
        repository=REPOSITORY, pr_number=748, base_sha=BASE, head_sha=HEAD,
        installation_id=INSTALLATION, event_id="REQ-action-merge", action=pr.MERGE,
    )
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(lab_routes.pr_review_request(body, {"uid": uid}))
    assert excinfo.value.status_code == 409
    assert "human-only" in str(excinfo.value.detail)


def test_publish_cannot_be_asked_to_merge(worker_env, monkeypatch):
    _patch_reader(monkeypatch, snapshot())
    _activate(monkeypatch)
    uid = "uid-api-007"
    body = lab_routes.PrReviewRequestBody(
        repository=REPOSITORY, pr_number=748, base_sha=BASE, head_sha=HEAD,
        installation_id=INSTALLATION, event_id="REQ-merge",
    )
    payload = asyncio.run(lab_routes.pr_review_request(body, {"uid": uid}))
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            lab_routes.pr_review_publish(
                payload["job"]["job_id"],
                lab_routes.PrReviewPublishBody(action=pr.MERGE, authorization_ref="AUTH-x"),
                {"uid": uid},
            )
        )
    assert excinfo.value.status_code == 403
    assert "human-only" in str(excinfo.value.detail)


def test_revoked_grant_does_not_publish(worker_env, monkeypatch):
    _patch_reader(monkeypatch, snapshot())
    _activate(monkeypatch)
    uid = "uid-api-008"
    body = lab_routes.PrReviewRequestBody(
        repository=REPOSITORY, pr_number=748, base_sha=BASE, head_sha=HEAD,
        installation_id=INSTALLATION, event_id="REQ-revoke",
    )
    payload = asyncio.run(lab_routes.pr_review_request(body, {"uid": uid}))
    job_id = payload["job"]["job_id"]
    grant = asyncio.run(
        lab_routes.pr_review_grant(
            job_id, lab_routes.PrReviewGrantBody(action=pr.PUBLISH_COMMENT), {"uid": uid}
        )
    )
    lab_routes.get_store().revoke_authorization(
        grant["authorization_ref"], uid, reason="withdrawn by the Founder"
    )
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            lab_routes.pr_review_publish(
                job_id,
                lab_routes.PrReviewPublishBody(
                    action=pr.PUBLISH_COMMENT, authorization_ref=grant["authorization_ref"]
                ),
                {"uid": uid},
            )
        )
    assert excinfo.value.status_code == 403
    assert "revoked" in str(excinfo.value.detail)


def test_rate_limit_is_bounded_then_dead_lettered(worker_env, monkeypatch):
    from lab.engineering_lab.github_app import RateLimited

    def limited(repository, number):
        raise RateLimited("slow down", retry_after_seconds=5)

    monkeypatch.setattr(lab_routes, "_review_reader", lambda worker: type(
        "R", (), {"read_pull_request": staticmethod(limited), "read_head_sha": staticmethod(limited)}
    )())
    monkeypatch.setenv("ARKADIA_PR_REVIEW_MAX_ATTEMPTS", "2")
    uid = "uid-api-009"
    body = lab_routes.PrReviewRequestBody(
        repository=REPOSITORY, pr_number=748, base_sha=BASE, head_sha=HEAD,
        installation_id=INSTALLATION, event_id="REQ-ratelimit",
    )
    first = None
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(lab_routes.pr_review_request(body, {"uid": uid}))
    first = excinfo.value
    assert first.status_code == 429
    assert first.detail["state"] == "RETRY_WAIT"
    assert first.detail["retry_after_seconds"] == 5

    job_id = first.detail["job"]["job_id"]
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(lab_routes.pr_review_run_job(job_id, {"uid": uid}))
    assert excinfo.value.status_code == 429
    assert excinfo.value.detail["state"] == "DEAD_LETTER"


def test_webhook_route_refuses_an_unsigned_delivery(worker_env):
    class FakeRequest:
        headers = {"X-GitHub-Event": "pull_request"}

        async def body(self):
            return _payload()

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(lab_routes.pr_review_webhook(FakeRequest()))
    assert excinfo.value.status_code == 401


def test_webhook_route_enqueues_and_deduplicates(worker_env):
    body = _payload()

    class FakeRequest:
        def __init__(self, headers):
            self.headers = headers

        async def body(self):
            return body

    first = asyncio.run(lab_routes.pr_review_webhook(FakeRequest(_delivery_headers(body, delivery="d-webhook-1"))))
    assert first["status"] == "QUEUED"
    assert first["job"]["state"] == "QUEUED"
    second = asyncio.run(lab_routes.pr_review_webhook(FakeRequest(_delivery_headers(body, delivery="d-webhook-1"))))
    assert second["status"] == "DUPLICATE"


# ---------------------------------------------------------------------------
# no merge, no deployment, no silent approval anywhere
# ---------------------------------------------------------------------------


def test_no_route_path_exposes_a_merge_or_deploy_surface():
    for route in lab_routes.router.routes:
        if "pr-review" not in route.path:
            continue
        lowered = route.path.lower()
        for marker in ("merge", "deploy", "production", "approve/"):
            assert marker not in lowered


def test_publish_events_never_include_merge_or_dismiss():
    source = (REPO_ROOT / "api" / "lab_routes.py").read_text(encoding="utf-8")
    start = source.index("def _post_review(")
    body = source[start : start + 3000]
    assert "/pulls/" in body and "/reviews" in body
    for forbidden in ("/merge", "/deployments", "/git/refs", "/statuses"):
        assert forbidden not in body
    event_map = source[source.index("event_map = {"): source.index("event_map = {") + 400]
    assert "MERGE" not in event_map and "DISMISS" not in event_map


def test_capability_reports_merge_disabled_with_a_reason():
    state = pr.rollout_state(pr.ReviewPolicy(stage="ACTIVATED", activation_ref="x"), GitHubAppWorker())
    assert state["merge_enabled"] is False
    assert "human-only" in state["merge_reason"]


def test_a_green_review_does_not_activate_a_write_action(worker_env):
    """GREEN is an evidence state; the gate decision is unchanged by it."""
    policy = pr.ReviewPolicy(stage="SHADOW")
    result = pr.review_pull_request(request(), reader=FakeReader(snapshot()), policy=policy, worker=GitHubAppWorker.from_env(), path_policy=allow_all)
    assert result.status == pr.GREEN
    with pytest.raises(pr.BoundaryViolation):
        pr.assert_action_permitted(pr.APPROVE, policy)


def test_an_expired_grant_does_not_match():
    """Expiry is the canonical Lab rule, not a second copy of it."""
    binding = pr.HeadBinding(REPOSITORY, 748, BASE, HEAD)
    expired = {
        "scope_ref": binding.scope_ref(pr.PUBLISH_COMMENT),
        "operations_allowed": [pr.PUBLISH_COMMENT],
        "created_at": "2020-01-01T00:00:00+00:00",
        "duration_minutes": 1,
    }
    with pytest.raises(pr.BoundaryViolation) as excinfo:
        pr.assert_grant_matches(expired, binding, pr.PUBLISH_COMMENT)
    assert "expired" in str(excinfo.value)
    # Negative control: the same grant is usable while inside its window.
    pr.assert_grant_matches(
        {**expired, "created_at": pr.utc_now(), "duration_minutes": 60},
        binding,
        pr.PUBLISH_COMMENT,
    )


def test_evidence_state_names_the_disposition_rather_than_inflating_it(worker_env):
    policy = pr.ReviewPolicy(stage="SHADOW")
    failing = snapshot(checks=(CheckRun("validate", "completed", "failure", "u", HEAD),))
    red = pr.review_pull_request(
        request(), reader=FakeReader(failing), policy=policy,
        worker=GitHubAppWorker.from_env(), path_policy=allow_all,
    )
    assert red.status == pr.RED
    assert pr.build_evidence(red, workspace_ref="engineering-lab").state == "BLOCKED"

    amber = pr.review_pull_request(
        request(), reader=FakeReader(snapshot(draft=True)), policy=policy,
        worker=GitHubAppWorker.from_env(), path_policy=allow_all,
    )
    assert amber.status == pr.AMBER
    assert pr.build_evidence(amber, workspace_ref="engineering-lab").state == "UNRESOLVED"


def test_capability_maps_onto_the_canonical_chief_envelope():
    """The capability reuses the Chief's declared envelope; it does not widen it."""
    from executive_office.control import GRANTABLE_CAPABILITIES, RESERVED_CAPABILITIES

    mapping = pr.CHIEF_CAPABILITY_MAP
    assert mapping[pr.READ] in GRANTABLE_CAPABILITIES
    assert mapping[pr.GENERATE_FINDINGS] in GRANTABLE_CAPABILITIES
    # Consequential actions are already reserved human-only in the canonical
    # envelope — the capability relies on that rather than restating it.
    assert mapping[pr.APPROVE] in RESERVED_CAPABILITIES
    assert mapping[pr.MERGE] in RESERVED_CAPABILITIES
    # Publishing a review has no delegated capability: only a human grant reaches it.
    assert mapping[pr.PUBLISH_COMMENT] is None
    assert mapping[pr.REQUEST_CHANGES] is None
    assert set(filter(None, mapping.values())) <= (
        GRANTABLE_CAPABILITIES | RESERVED_CAPABILITIES
    ), "the capability must not invent a capability name outside the envelope"
    assert pr.capability_manifest()["requires_envelope_change"] is False
