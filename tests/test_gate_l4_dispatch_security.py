"""GATE L4 dispatch input and provider-origin security tests."""
from __future__ import annotations

import pytest

from weaver.openhands_dispatch import (
    DispatchBlocked,
    DispatchRequest,
    Lane,
    UnconfiguredOpenHandsClient,
    make_idempotency_key,
    validate_dispatch_request,
    validate_provider_origin,
)

BASE = "49809f45274f2f81b24e01fefdfb3009e8717495"


def request(**overrides):
    values = {
        "assignment_id": "GATE-L4-W1-001",
        "lane": Lane.W1,
        "base_sha": BASE,
        "instruction": "Inspect and implement the assigned lane only.",
        "idempotency_key": make_idempotency_key("GATE-L4-W1-001", Lane.W1, BASE),
    }
    values.update(overrides)
    return DispatchRequest(**values)


def test_valid_request_passes():
    validate_dispatch_request(request())


@pytest.mark.parametrize("bad_sha", ["", "deadbeef", "A" * 40, "0" * 39 + "g"])
def test_invalid_base_sha_rejected(bad_sha):
    with pytest.raises(ValueError, match="base_sha"):
        validate_dispatch_request(request(base_sha=bad_sha))


def test_mismatched_idempotency_key_rejected():
    with pytest.raises(ValueError, match="idempotency_key"):
        validate_dispatch_request(request(idempotency_key="0" * 64))


def test_invalid_assignment_id_rejected():
    with pytest.raises(ValueError, match="assignment_id"):
        validate_dispatch_request(request(assignment_id="../W1"))


def test_empty_and_oversized_instructions_rejected():
    with pytest.raises(ValueError, match="non-empty"):
        validate_dispatch_request(request(instruction="  "))
    with pytest.raises(ValueError, match="20000"):
        validate_dispatch_request(request(instruction="x" * 20001))


def test_lane_is_restricted_to_four_contract_lanes():
    with pytest.raises(ValueError, match="lane"):
        validate_dispatch_request(request(lane="W5"))


def test_idempotency_key_is_stable_and_lane_scoped():
    first = make_idempotency_key("GATE-L4-W1-001", Lane.W1, BASE)
    assert first == make_idempotency_key("GATE-L4-W1-001", Lane.W1, BASE)
    assert first != make_idempotency_key("GATE-L4-W2-001", Lane.W2, BASE)


def test_provider_origin_requires_https_allowlisted_host():
    assert validate_provider_origin("https://openhands.example", {"openhands.example"}) == "https://openhands.example"
    for url in (
        "http://openhands.example",
        "https://user:pass@openhands.example",
        "https://evil.example",
        "https://openhands.example:8443",
        "https://openhands.example/path?token=secret",
    ):
        with pytest.raises(ValueError):
            validate_provider_origin(url, {"openhands.example"})


def test_unconfigured_client_fails_closed_instead_of_simulating_dispatch():
    client = UnconfiguredOpenHandsClient()
    with pytest.raises(DispatchBlocked, match="not configured"):
        client.dispatch(request())
    with pytest.raises(DispatchBlocked, match="not configured"):
        client.inspect("run-123")
