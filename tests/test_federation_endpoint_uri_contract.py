from __future__ import annotations

import pytest
from pydantic import ValidationError

from federation.agent_card import CommunicationEndpoint, EndpointKind


def test_https_endpoint_accepts_a_syntactically_valid_host():
    endpoint = CommunicationEndpoint(kind=EndpointKind.HTTPS, uri="https://example.invalid")
    assert endpoint.uri == "https://example.invalid"


@pytest.mark.parametrize("uri", ["https://", "https:///path", "https://example.invalid:bad", "https://example.invalid:0"])
def test_https_endpoint_rejects_missing_host_or_malformed_port(uri: str):
    with pytest.raises(ValidationError):
        CommunicationEndpoint(kind=EndpointKind.HTTPS, uri=uri)


@pytest.mark.parametrize(
    ("kind", "uri"),
    [
        (EndpointKind.HTTPS, "wss://example.invalid/socket"),
        (EndpointKind.WSS, "https://example.invalid"),
        (EndpointKind.MCP, "https://example.invalid/mcp"),
        (EndpointKind.A2A, "mcp://example.invalid/agent"),
    ],
)
def test_transport_kind_must_match_declared_scheme(kind: EndpointKind, uri: str):
    with pytest.raises(ValidationError):
        CommunicationEndpoint(kind=kind, uri=uri)


@pytest.mark.parametrize("uri", ["https://example.invalid/a b", "https://example.invalid/agent\n"])
def test_https_endpoint_rejects_whitespace_and_control_characters(uri: str):
    with pytest.raises(ValidationError):
        CommunicationEndpoint(kind=EndpointKind.HTTPS, uri=uri)


def test_https_endpoint_rejects_embedded_userinfo():
    with pytest.raises(ValidationError):
        CommunicationEndpoint(kind=EndpointKind.HTTPS, uri="https://user:synthetic-token@example.invalid")


def test_mcp_and_a2a_use_explicit_declared_scheme_markers():
    assert CommunicationEndpoint(kind=EndpointKind.MCP, uri="mcp://example.invalid/server").kind is EndpointKind.MCP
    assert CommunicationEndpoint(kind=EndpointKind.A2A, uri="a2a://example.invalid/agent").kind is EndpointKind.A2A


def test_other_kind_accepts_an_absolute_custom_uri_scheme():
    endpoint = CommunicationEndpoint(kind=EndpointKind.OTHER, uri="custom+proto:opaque-resource")
    assert endpoint.uri == "custom+proto:opaque-resource"


def test_uri_validation_does_not_claim_reachability_or_trust():
    endpoint = CommunicationEndpoint(kind=EndpointKind.HTTPS, uri="https://example.invalid")
    assert endpoint.state.value == "declared"
    assert not any(field in CommunicationEndpoint.model_fields for field in ("reachable", "trusted", "verified_at"))
