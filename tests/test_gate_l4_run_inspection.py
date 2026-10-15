"""GATE L4 provider run-inspection evidence validation tests."""
from __future__ import annotations

import pytest

from weaver.openhands_dispatch import (
    Lane,
    RunEvidence,
    RunStatus,
    validate_run_evidence,
)

BASE = "49809f45274f2f81b24e01fefdfb3009e8717495"
HEAD = "c1e7718b084f35a47322256f7f4ef58b8e34b31c"


def evidence(**overrides):
    values = {
        "run_id": "openhands-run-123",
        "status": RunStatus.SUCCEEDED,
        "lane": Lane.W1,
        "base_sha": BASE,
        "branch": "openhands/gate-l4-w1",
        "commit_sha": HEAD,
        "test_exit_code": 0,
        "test_summary": "pytest result artifact: tests-123",
        "pull_request_url": "https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/501",
    }
    values.update(overrides)
    return RunEvidence(**values)


def test_complete_run_evidence_passes():
    validate_run_evidence(evidence(), Lane.W1, BASE)


def test_wrong_lane_and_wrong_base_are_rejected():
    with pytest.raises(ValueError, match="lane"):
        validate_run_evidence(evidence(lane=Lane.W2), Lane.W1, BASE)
    with pytest.raises(ValueError, match="base SHA"):
        validate_run_evidence(evidence(base_sha=HEAD), Lane.W1, BASE)


def test_invalid_commit_sha_is_rejected():
    with pytest.raises(ValueError, match="commit_sha"):
        validate_run_evidence(evidence(commit_sha="not-a-sha"), Lane.W1, BASE)


def test_succeeded_run_requires_commit_and_test_exit_code():
    with pytest.raises(ValueError, match="commit SHA"):
        validate_run_evidence(evidence(commit_sha=None), Lane.W1, BASE)
    with pytest.raises(ValueError, match="test exit code"):
        validate_run_evidence(evidence(test_exit_code=None), Lane.W1, BASE)


def test_pull_request_must_point_to_canonical_repository():
    with pytest.raises(ValueError, match="this repository"):
        validate_run_evidence(
            evidence(pull_request_url="https://github.com/attacker/repo/pull/1"),
            Lane.W1,
            BASE,
        )
    with pytest.raises(ValueError, match="this repository"):
        validate_run_evidence(
            evidence(pull_request_url="http://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/1"),
            Lane.W1,
            BASE,
        )


def test_worker_cannot_grant_merge_or_deploy_authority():
    with pytest.raises(ValueError, match="cannot grant"):
        validate_run_evidence(evidence(merge_permitted=True), Lane.W1, BASE)
    with pytest.raises(ValueError, match="cannot grant"):
        validate_run_evidence(evidence(deploy_permitted=True), Lane.W1, BASE)


def test_nonterminal_status_does_not_require_completion_artifacts():
    pending = evidence(
        status=RunStatus.RUNNING,
        commit_sha=None,
        test_exit_code=None,
        pull_request_url=None,
    )
    validate_run_evidence(pending, Lane.W1, BASE)


def test_unknown_provider_status_is_explicit_not_success():
    unknown = evidence(status=RunStatus.UNKNOWN, commit_sha=None, test_exit_code=None)
    validate_run_evidence(unknown, Lane.W1, BASE)
