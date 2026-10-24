"""GATE L4 OpenHands dispatch boundary.

This module defines the governed dispatch/inspection contract only. It deliberately
ships without a network client until a concrete OpenHands deployment and its
versioned API/authentication contract are configured and verified. No method here
can merge a PR or deploy a service.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import re
from typing import Protocol
from urllib.parse import urlparse


_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_ASSIGNMENT_RE = re.compile(r"^[A-Z0-9][A-Z0-9._:-]{0,127}$")
_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_LANE_RE = re.compile(r"^W[1-4]$")


class DispatchBlocked(RuntimeError):
    """Dispatch cannot proceed because the integration is not configured."""


class Lane(str, Enum):
    W1 = "W1"
    W2 = "W2"
    W3 = "W3"
    W4 = "W4"


class RunStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class DispatchRequest:
    assignment_id: str
    lane: Lane
    base_sha: str
    instruction: str
    idempotency_key: str


@dataclass(frozen=True)
class RunEvidence:
    run_id: str
    status: RunStatus
    lane: Lane
    base_sha: str
    branch: str | None = None
    commit_sha: str | None = None
    test_exit_code: int | None = None
    test_summary: str | None = None
    pull_request_url: str | None = None
    merge_permitted: bool = False
    deploy_permitted: bool = False


class OpenHandsClient(Protocol):
    """Transport contract to implement against a verified OpenHands API version."""

    def dispatch(self, request: DispatchRequest) -> str:
        """Create or recover a run by idempotency key and return its stable run ID."""

    def inspect(self, run_id: str) -> RunEvidence:
        """Return evidence fetched from the provider for this exact run."""


def make_idempotency_key(assignment_id: str, lane: Lane, base_sha: str) -> str:
    """Stable key for one assignment/lane/base tuple; safe to log."""
    validate_assignment_id(assignment_id)
    validate_sha(base_sha, "base_sha")
    raw = f"gate-l4:v1:{assignment_id}:{lane.value}:{base_sha}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def validate_sha(value: str, field: str = "sha") -> None:
    if not isinstance(value, str) or not _SHA_RE.fullmatch(value):
        raise ValueError(f"{field} must be a full 40-character lowercase Git SHA")


def validate_assignment_id(value: str) -> None:
    if not isinstance(value, str) or not _ASSIGNMENT_RE.fullmatch(value):
        raise ValueError("assignment_id has invalid syntax")


def validate_dispatch_request(request: DispatchRequest) -> None:
    validate_assignment_id(request.assignment_id)
    validate_sha(request.base_sha, "base_sha")
    if not isinstance(request.lane, Lane):
        raise ValueError("lane must be one of W1, W2, W3, W4")
    if not isinstance(request.instruction, str) or not request.instruction.strip():
        raise ValueError("instruction must be non-empty")
    if len(request.instruction) > 20_000:
        raise ValueError("instruction exceeds 20000 characters")
    expected = make_idempotency_key(request.assignment_id, request.lane, request.base_sha)
    if request.idempotency_key != expected:
        raise ValueError("idempotency_key does not match assignment/lane/base tuple")


def validate_provider_origin(base_url: str, allowed_hosts: set[str]) -> str:
    """Validate configured provider origin; reject plaintext, credentials and host drift."""
    parsed = urlparse(base_url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("OpenHands base URL must be HTTPS")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("OpenHands base URL must not contain credentials, query or fragment")
    if parsed.hostname.lower() not in {host.lower() for host in allowed_hosts}:
        raise ValueError("OpenHands host is not allow-listed")
    if parsed.port not in (None, 443):
        raise ValueError("OpenHands base URL must use the default HTTPS port")
    return base_url.rstrip("/")


def validate_run_evidence(evidence: RunEvidence, expected_lane: Lane, expected_base_sha: str) -> None:
    """Reject provider results that cannot be tied to the dispatched assignment."""
    if not isinstance(evidence, RunEvidence):
        raise ValueError("inspection must return RunEvidence")
    if not isinstance(evidence.run_id, str) or not _RUN_ID_RE.fullmatch(evidence.run_id):
        raise ValueError("provider returned invalid run_id")
    if evidence.lane != expected_lane:
        raise ValueError("run evidence lane does not match dispatched lane")
    validate_sha(expected_base_sha, "expected_base_sha")
    if evidence.base_sha != expected_base_sha:
        raise ValueError("run evidence base SHA does not match dispatched base")
    if evidence.commit_sha is not None:
        validate_sha(evidence.commit_sha, "commit_sha")
    if evidence.test_exit_code is not None and (
        not isinstance(evidence.test_exit_code, int) or isinstance(evidence.test_exit_code, bool)
    ):
        raise ValueError("test_exit_code must be an integer or null")
    if evidence.pull_request_url is not None:
        parsed = urlparse(evidence.pull_request_url)
        if parsed.scheme != "https" or parsed.hostname != "github.com" or not parsed.path.startswith("/Arkadia-Oversoul-Prism/Arkadia/pull/"):
            raise ValueError("pull request URL must refer to this repository on github.com")
    if evidence.merge_permitted or evidence.deploy_permitted:
        raise ValueError("worker evidence cannot grant merge or deployment authority")
    if evidence.status == RunStatus.SUCCEEDED and not evidence.commit_sha:
        raise ValueError("succeeded run must provide a commit SHA")
    if evidence.status == RunStatus.SUCCEEDED and evidence.test_exit_code is None:
        raise ValueError("succeeded run must provide a test exit code")


class UnconfiguredOpenHandsClient:
    """Default adapter: fail closed until endpoint and auth are explicitly configured."""

    def dispatch(self, request: DispatchRequest) -> str:
        validate_dispatch_request(request)
        raise DispatchBlocked(
            "OpenHands dispatch is not configured: provider endpoint, API version, "
            "and authorized credentials have not been verified"
        )

    def inspect(self, run_id: str) -> RunEvidence:
        raise DispatchBlocked(
            "OpenHands run inspection is not configured: no verified provider client"
        )
