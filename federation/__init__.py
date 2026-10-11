"""Agentic Civic Federation — identity contract surfaces.

Slice 1 exposes one surface: the versioned Agent Card / Passport data contract
(:mod:`federation.agent_card`). It is a schema, not a service — there is no
federation runtime, no route, and no persistence in this package.
"""
from __future__ import annotations

from federation.agent_card import (
    AGENT_CARD_VERSION,
    SCHEMA_VERSION,
    AgentCard,
    AssertionSource,
    CapabilityState,
    CommunicationEndpoint,
    DeclaredCapability,
    EndpointKind,
    MembershipStatus,
    OperatorAssertion,
    ProvenanceRecord,
    ProvenanceState,
    PublicKeyRef,
    PublicKeyReference,
    SubjectKind,
    VerifiedCapability,
)

__all__ = [
    "AGENT_CARD_VERSION",
    "SCHEMA_VERSION",
    "AgentCard",
    "AssertionSource",
    "CapabilityState",
    "CommunicationEndpoint",
    "DeclaredCapability",
    "EndpointKind",
    "MembershipStatus",
    "OperatorAssertion",
    "ProvenanceRecord",
    "ProvenanceState",
    "PublicKeyRef",
    "PublicKeyReference",
    "SubjectKind",
    "VerifiedCapability",
]
