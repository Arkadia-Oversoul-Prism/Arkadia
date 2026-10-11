"""Agentic Civic Federation — versioned Agent Card / Passport contract (v0.1).

This module is a **data contract only**. It defines the shape of an Agent Card /
Passport and the vocabularies it is written in. It contains no router, no
persistence, no protocol adapter, no network call, and no credential-signing
claim. Nothing here creates a live federation, verifies a passport, or grants
anything to anyone.

Epistemic boundaries the contract is built to preserve
------------------------------------------------------
The governance substrate is IDENTITY -> AUTHORITY -> AUTHORIZATION -> PROPOSAL ->
APPROVAL -> EXECUTION -> WORK EVENT -> EVIDENCE -> VERIFICATION -> REVIEW. A card
is an *identity* artifact. It is deliberately incapable of expressing the stages
after it:

* **Declared is not verified.** A subject's own statement about itself is
  ``DECLARED``. ``VERIFIED`` requires an evidence reference supplied by a party
  that is not the subject. The two live in different fields
  (:class:`DeclaredCapability` vs :class:`VerifiedCapability`), so a declared
  claim cannot be promoted to a verified one by editing a flag — promotion is a
  different object with a different required field (``evidence_ref``).
* **Membership is not personhood, authority, or authorization.** ``status``
  records a membership lifecycle position. It carries no legal personality, no
  authority, and no permission to act. The contract exposes no field named
  ``authority`` or ``authorization`` at all.
* **An operator relationship is not inferred from self-description.** The
  operator link is an assertion by the *issuer* (``operator_assertion``), whose
  ``source`` is recorded and whose default is ``DECLARED``. A card never derives
  an operator from the subject's own prose; it carries the assertion and says who
  made it.

Vocabulary values are lowercase strings. The enum members are UPPERCASE and map
to those wire values through :class:`_WireEnum`; ``use_enum_values`` is
deliberately **off** so that a validator can compare against enum members by
identity and a ``str`` can never be silently accepted in their place.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

#: Wire-contract version. Bump on any incompatible shape change.
AGENT_CARD_VERSION = "0.1"

#: ``schema_version`` value a v0.1 document must carry.
SCHEMA_VERSION = f"federation.agent-card/{AGENT_CARD_VERSION}"

#: Prefix for the opaque federation subject identifier.
SUBJECT_ID_PREFIX = "fed:"

#: Conservative identifier shape for an opaque federation subject id.
#: The id is opaque — it carries no meaning about the subject — but it must be
#: well-formed so that it can be exchanged and compared without ambiguity.
SUBJECT_ID_PATTERN = r"^fed:[A-Za-z0-9][A-Za-z0-9._:-]*$"
_SUBJECT_ID_RE = re.compile(SUBJECT_ID_PATTERN)

#: Maximum accepted subject-id length. Bounds the contract's input surface.
MAX_SUBJECT_ID_LENGTH = 128


class _WireEnum(str, Enum):
    """A vocabulary whose members are UPPERCASE and whose values are lowercase.

    Subclassing ``str`` keeps the members JSON-serialisable and comparable to
    plain strings, while the wire form stays the lowercase value.
    """

    def __str__(self) -> str:  # pragma: no cover - trivial
        return str(self.value)


class SubjectKind(_WireEnum):
    """Who the passport is about.

    ``AGENT`` and ``AGENT_SOCIETY`` are artificial subjects. ``PARTNER`` covers a
    human or organizational counterparty. None of these values confer legal
    personhood; ``PARTNER`` does not make an organization an agent, and
    ``AGENT`` does not make an agent a legal person.
    """

    AGENT = "agent"
    AGENT_SOCIETY = "agent_society"
    PARTNER = "partner"


class MembershipStatus(_WireEnum):
    """Position in the federation membership lifecycle.

    A lifecycle position, not a permission. ``MEMBER`` and ``ACCREDITED_AGENT``
    describe standing in the federation register; neither is an authority grant
    and neither authorizes any action.
    """

    VISITOR = "visitor"
    APPLICANT = "applicant"
    MEMBER = "member"
    ACCREDITED_AGENT = "accredited_agent"
    DELEGATE = "delegate"
    PARTNER = "partner"
    OBSERVER = "observer"
    SUSPENDED = "suspended"
    WITHDRAWN = "withdrawn"


class ProvenanceState(_WireEnum):
    """How far a piece of card material has been established.

    ``DECLARED`` — asserted by the subject, unverified.
    ``PENDING`` — submitted for verification, no outcome yet.
    ``VERIFIED`` — an independent verifier attested it, with evidence.
    ``REJECTED`` — verification was attempted and did not hold.

    Only ``VERIFIED`` may carry a verifier and an evidence reference; the others
    must not, so an unverified claim cannot be dressed as an attested one.
    """

    DECLARED = "declared"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class CapabilityState(_WireEnum):
    """Whether a capability is merely claimed or has been attested.

    ``DECLARED`` means the subject says it can do this. ``VERIFIED`` means an
    independent party attested it and supplied evidence. There is no third state
    that upgrades one into the other in place.
    """

    DECLARED = "declared"
    VERIFIED = "verified"


class AssertionSource(_WireEnum):
    """Who made a statement carried on the card.

    ``SUBJECT`` is the card's own holder (self-description). ``ISSUER`` is the
    party that minted the card. ``OPERATOR`` is the party that runs the subject.
    ``EXTERNAL_VERIFIER`` is an independent third party. Recording the source is
    what lets a reader refuse to treat a self-description as an operator fact.
    """

    SUBJECT = "subject"
    ISSUER = "issuer"
    OPERATOR = "operator"
    EXTERNAL_VERIFIER = "external_verifier"


class EndpointKind(_WireEnum):
    """Transport kind of a declared communication endpoint.

    A declared address only. Nothing in this module resolves, contacts, or trusts
    an endpoint, and no value here asserts that the endpoint is reachable or
    that it belongs to the subject.
    """

    HTTPS = "https"
    WSS = "wss"
    MCP = "mcp"
    A2A = "a2a"
    OTHER = "other"


class PublicKeyRef(_WireEnum):
    """Reference scheme for a declared public key.

    ``JWKS_URI`` and ``DID_KEY`` are *references* to key material held
    elsewhere. ``INLINE_JWK`` is a public key embedded in the card.

    No value here implies a signature was checked. This slice performs no
    cryptographic verification and claims none.
    """

    JWKS_URI = "jwks_uri"
    DID_KEY = "did_key"
    INLINE_JWK = "inline_jwk"


def _require_aware(value: datetime, field_name: str) -> datetime:
    """Reject naive datetimes so issuance/expiry cannot be read in an assumed zone."""
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(
            f"{field_name} must be timezone-aware (e.g. '2026-01-01T00:00:00Z'); "
            "a naive timestamp has no unambiguous instant"
        )
    return value


class _CardModel(BaseModel):
    """Base for every object in the contract.

    ``extra="forbid"`` makes an unknown key a hard error rather than silently
    dropped data — a card with a misspelled or unrecognised field is malformed,
    not merely thinner. ``use_enum_values`` is left off on purpose: keeping enum
    members means a validator compares by identity, so a raw string cannot pass
    where a member is required.
    """

    model_config = ConfigDict(extra="forbid")


class DeclaredCapability(_CardModel):
    """A capability the subject claims for itself.

    The presence of this object is the claim. It has no field that could mark it
    verified — that would conflate declaration with verification — so promotion
    requires constructing a :class:`VerifiedCapability` instead.
    """

    name: str = Field(min_length=1, description="Capability identifier, e.g. 'summarise'.")
    state: CapabilityState = CapabilityState.DECLARED
    assertion_source: AssertionSource = AssertionSource.SUBJECT
    detail: str | None = Field(default=None, description="Free-text description of the claim.")

    @field_validator("state")
    @classmethod
    def _declared_only(cls, value: CapabilityState) -> CapabilityState:
        if value is not CapabilityState.DECLARED:
            raise ValueError(
                "DeclaredCapability.state must be 'declared'; a verified capability "
                "must be expressed as VerifiedCapability with an evidence_ref "
                "(declaration is not verification)"
            )
        return value


class VerifiedCapability(_CardModel):
    """A capability an independent party attested, carrying its evidence.

    ``verifier`` and ``evidence_ref`` are required and non-empty. There is no way
    to express a verified capability without naming who verified it and on what
    evidence, so an unattested claim cannot be written into this type.
    """

    name: str = Field(min_length=1)
    state: CapabilityState = CapabilityState.VERIFIED
    assertion_source: AssertionSource = AssertionSource.EXTERNAL_VERIFIER
    verifier: str = Field(min_length=1, description="Party that attested the capability.")
    evidence_ref: str = Field(
        min_length=1,
        description="Reference to the evidence supporting the attestation.",
    )

    @field_validator("state")
    @classmethod
    def _verified_only(cls, value: CapabilityState) -> CapabilityState:
        if value is not CapabilityState.VERIFIED:
            raise ValueError(
                "VerifiedCapability.state must be 'verified'; a declared claim is a "
                "DeclaredCapability, not a verified one"
            )
        return value

    @field_validator("assertion_source")
    @classmethod
    def _not_self_attested(cls, value: AssertionSource) -> AssertionSource:
        if value is AssertionSource.SUBJECT:
            raise ValueError(
                "a subject cannot verify its own capability; VerifiedCapability."
                "assertion_source must not be 'subject'"
            )
        return value


class ProvenanceRecord(_CardModel):
    """Provenance of one piece of card material.

    ``state`` carries the epistemic standing. ``verifier`` and ``evidence_ref``
    are required **iff** the state is ``VERIFIED``: a verified record without
    evidence is refused, and a non-verified record that names a verifier is
    refused too, so an unverified material cannot borrow the appearance of an
    attested one.
    """

    subject_ref: str = Field(
        min_length=1,
        description="What this record is about (a field name, artifact, or claim).",
    )
    state: ProvenanceState
    assertion_source: AssertionSource = AssertionSource.SUBJECT
    verifier: str | None = None
    evidence_ref: str | None = None
    detail: str | None = None

    @model_validator(mode="after")
    def _verification_requires_evidence(self) -> "ProvenanceRecord":
        if self.state is ProvenanceState.VERIFIED:
            missing = [
                name
                for name, value in (("verifier", self.verifier), ("evidence_ref", self.evidence_ref))
                if not (value or "").strip()
            ]
            if missing:
                raise ValueError(
                    "provenance state 'verified' requires non-empty "
                    + " and ".join(missing)
                    + " (a verified state without evidence is an unsupported claim)"
                )
        else:
            borrowed = [
                name
                for name, value in (("verifier", self.verifier), ("evidence_ref", self.evidence_ref))
                if value is not None
            ]
            if borrowed:
                raise ValueError(
                    f"provenance state '{self.state.value}' must not carry "
                    + " or ".join(borrowed)
                    + " (only 'verified' may name a verifier and evidence)"
                )
        return self


class OperatorAssertion(_CardModel):
    """A declared operator relationship, attributed to whoever asserted it.

    An agent's self-description is not evidence of who operates it. This object
    therefore never claims the relationship as fact: it records the assertion,
    who made it (``source``), and its provenance state. An assertion sourced from
    the subject defaults to ``DECLARED`` provenance and stays unverified until an
    independent verifier says otherwise.
    """

    operator_id: str = Field(min_length=1, description="Opaque id of the asserted operator.")
    source: AssertionSource = AssertionSource.SUBJECT
    state: ProvenanceState = ProvenanceState.DECLARED
    evidence_ref: str | None = None

    @model_validator(mode="after")
    def _self_description_is_never_verified(self) -> "OperatorAssertion":
        if self.source is AssertionSource.SUBJECT and self.state is ProvenanceState.VERIFIED:
            raise ValueError(
                "an operator relationship asserted by the subject itself cannot be "
                "'verified' by that assertion (an operator link is not inferred from "
                "an agent's self-description)"
            )
        if self.state is ProvenanceState.VERIFIED and not (self.evidence_ref or "").strip():
            raise ValueError(
                "operator assertion state 'verified' requires a non-empty evidence_ref"
            )
        if self.state is not ProvenanceState.VERIFIED and self.evidence_ref is not None:
            raise ValueError(
                f"operator assertion state '{self.state.value}' must not carry an "
                "evidence_ref (only 'verified' may)"
            )
        return self


class CommunicationEndpoint(_CardModel):
    """A declared communication endpoint reference.

    A reference only. Nothing here is resolved, contacted, or trusted, and a
    present endpoint does not assert reachability or ownership.
    """

    kind: EndpointKind
    uri: str = Field(min_length=1, description="Declared address of the endpoint.")
    state: ProvenanceState = ProvenanceState.DECLARED
    note: str | None = None

    @model_validator(mode="after")
    def _validate_declared_uri(self) -> "CommunicationEndpoint":
        """Validate syntax and the declared transport without contacting the endpoint.

        HTTPS/WSS require a matching scheme and a non-empty host; malformed
        ports and embedded userinfo are refused. MCP/A2A use their declared
        scheme markers. OTHER accepts any absolute URI scheme. These checks
        establish syntax only, never reachability, ownership, or trust.
        """
        if any(ch.isspace() or ord(ch) < 32 or ord(ch) == 127 for ch in self.uri):
            raise ValueError("endpoint uri must not contain whitespace or control characters")
        try:
            parsed = urlsplit(self.uri)
        except ValueError as exc:
            raise ValueError("endpoint uri is malformed") from exc

        if not parsed.scheme:
            raise ValueError("endpoint uri must include an absolute URI scheme")
        if self.kind is not EndpointKind.OTHER and parsed.scheme.lower() != self.kind.value:
            raise ValueError(
                f"endpoint kind '{self.kind.value}' requires URI scheme '{self.kind.value}'"
            )

        if self.kind in (EndpointKind.HTTPS, EndpointKind.WSS):
            if not parsed.netloc or not parsed.hostname:
                raise ValueError("HTTPS/WSS endpoint uri requires a non-empty host")
            if "@" in parsed.netloc:
                raise ValueError("HTTPS/WSS endpoint uri must not embed userinfo")
            try:
                port = parsed.port
            except ValueError as exc:
                raise ValueError("endpoint uri has an invalid port") from exc
            if port is not None and not 1 <= port <= 65535:
                raise ValueError("endpoint uri port must be between 1 and 65535")
        elif self.kind in (EndpointKind.MCP, EndpointKind.A2A) and not parsed.scheme:
            raise ValueError(f"{self.kind.value.upper()} endpoint uri requires an absolute URI")

        return self


class PublicKeyReference(_CardModel):
    """A declared public-key reference.

    Carries a reference or an inline public key; it carries **no** statement that
    a signature was ever checked. Verification is out of scope for this slice and
    the contract does not imply it.
    """

    scheme: PublicKeyRef
    ref: str = Field(min_length=1, description="Key reference or inline public JWK.")
    state: ProvenanceState = ProvenanceState.DECLARED
    algorithm: str | None = None


class AgentCard(_CardModel):
    """A versioned Agent Card / Passport for one federation subject.

    Identity material only. The card states who a subject is, what it claims, who
    asserts what about it, and where it may be addressed — and nothing about
    authority, authorization, or permission to act.
    """

    schema_version: str = SCHEMA_VERSION
    subject_id: str = Field(
        min_length=1,
        max_length=MAX_SUBJECT_ID_LENGTH,
        description=f"Opaque federation subject id, e.g. 'fed:agent-0001'.",
    )
    subject_kind: SubjectKind
    display_name: str | None = Field(default=None, max_length=200)
    issuer: str = Field(min_length=1, description="Party that minted this card.")
    status: MembershipStatus
    operator_assertion: OperatorAssertion | None = None

    declared_capabilities: list[DeclaredCapability] = Field(default_factory=list)
    verified_capabilities: list[VerifiedCapability] = Field(default_factory=list)
    provenance: list[ProvenanceRecord] = Field(default_factory=list)

    public_keys: list[PublicKeyReference] = Field(default_factory=list)
    endpoints: list[CommunicationEndpoint] = Field(default_factory=list)

    issued_at: datetime | None = None
    expires_at: datetime | None = None
    withdrawn_at: datetime | None = None

    @field_validator("schema_version")
    @classmethod
    def _known_schema_version(cls, value: str) -> str:
        if value != SCHEMA_VERSION:
            raise ValueError(
                f"unsupported schema_version {value!r}; this build implements "
                f"{SCHEMA_VERSION!r}"
            )
        return value

    @field_validator("subject_id")
    @classmethod
    def _well_formed_subject_id(cls, value: str) -> str:
        if not _SUBJECT_ID_RE.match(value):
            raise ValueError(
                "subject_id must be an opaque federation id matching "
                f"{SUBJECT_ID_PATTERN} (e.g. 'fed:agent-0001')"
            )
        return value

    @field_validator("issued_at", "expires_at", "withdrawn_at")
    @classmethod
    def _timestamps_are_aware(cls, value: datetime | None, info: Any) -> datetime | None:
        if value is None:
            return None
        return _require_aware(value, info.field_name)

    @model_validator(mode="after")
    def _window_is_coherent(self) -> "AgentCard":
        if self.issued_at and self.expires_at and self.expires_at <= self.issued_at:
            raise ValueError("expires_at must be later than issued_at")
        return self

    # ── Read-only queries ────────────────────────────────────────────────────
    # These report what the card says. None of them grants anything, and none
    # upgrades a declared claim into a verified one.

    def is_expired(self, at: datetime | None = None) -> bool:
        """Whether the card's declared validity window has elapsed at ``at``.

        Expiry is a statement about the declared window, not a judgement about
        the subject's standing or permission.
        """
        if self.expires_at is None:
            return False
        moment = at or datetime.now(timezone.utc)
        _require_aware(moment, "at")
        return moment >= self.expires_at

    def declared_capability_names(self) -> set[str]:
        """Names of capabilities the subject merely claims."""
        return {c.name for c in self.declared_capabilities}

    def verified_capability_names(self) -> set[str]:
        """Names of capabilities an independent party attested."""
        return {c.name for c in self.verified_capabilities}

    def claims_but_does_not_verify(self) -> set[str]:
        """Capability names asserted by the subject that carry no attestation.

        The set difference is the point of the contract: a reader asks this
        question instead of trusting a single ``verified`` flag.
        """
        return self.declared_capability_names() - self.verified_capability_names()
