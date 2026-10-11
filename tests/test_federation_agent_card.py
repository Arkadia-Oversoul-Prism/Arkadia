"""Federation MVP-01 — Agent Card / Passport contract (v0.1).

These tests pin the *contract*, not a service. There is no route, no store, and
no cryptographic verification in this slice, and several tests below assert that
absence directly so the boundary cannot erode silently.

Two properties get explicit negative controls, because they are the ones a later
change is most likely to break while still looking green:

* **declaration is not verification** — the detector is fed a hand-built
  conflated card and must report it, and is fed a correct card and must stay
  silent (a detector that is silent on both is not a detector);
* **an operator link is not inferred from self-description** — the same
  two-sided proof.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from federation.agent_card import (
    AGENT_CARD_VERSION,
    MAX_SUBJECT_ID_LENGTH,
    SCHEMA_VERSION,
    SUBJECT_ID_PATTERN,
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

NOW = datetime(2026, 10, 11, 12, 0, 0, tzinfo=timezone.utc)


def minimal_card(**overrides) -> AgentCard:
    """A smallest-valid card, so each test varies exactly one thing."""
    payload = {
        "subject_id": "fed:agent-0001",
        "subject_kind": SubjectKind.AGENT,
        "issuer": "fed:issuer-arkadia",
        "status": MembershipStatus.APPLICANT,
    }
    payload.update(overrides)
    return AgentCard(**payload)


# ── Versioning ───────────────────────────────────────────────────────────────

def test_schema_version_is_declared_and_round_trips():
    card = minimal_card()
    assert card.schema_version == SCHEMA_VERSION
    assert SCHEMA_VERSION == f"federation.agent-card/{AGENT_CARD_VERSION}"
    assert card.model_dump()["schema_version"] == SCHEMA_VERSION


def test_unknown_schema_version_is_rejected():
    with pytest.raises(ValidationError) as exc:
        minimal_card(schema_version="federation.agent-card/9.9")
    assert "unsupported schema_version" in str(exc.value)


def test_missing_schema_version_defaults_to_the_implemented_version():
    # Absent is not unknown: the field defaults to the version this build speaks,
    # so a caller cannot accidentally assert a version it did not choose.
    assert minimal_card().schema_version == SCHEMA_VERSION


# ── Subject kind ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("kind", list(SubjectKind))
def test_every_declared_subject_kind_is_accepted(kind: SubjectKind):
    assert minimal_card(subject_kind=kind).subject_kind is kind


@pytest.mark.parametrize("bad", ["robot", "AI", "", "AGENT", "agent_society ", "human"])
def test_unknown_subject_kind_is_rejected(bad):
    with pytest.raises(ValidationError):
        minimal_card(subject_kind=bad)


def test_subject_kind_is_required():
    with pytest.raises(ValidationError):
        AgentCard(
            subject_id="fed:agent-0001",
            issuer="fed:issuer-arkadia",
            status=MembershipStatus.MEMBER,
        )


# ── Membership status ────────────────────────────────────────────────────────

def test_all_nine_membership_statuses_are_defined():
    assert {s.value for s in MembershipStatus} == {
        "visitor",
        "applicant",
        "member",
        "accredited_agent",
        "delegate",
        "partner",
        "observer",
        "suspended",
        "withdrawn",
    }


@pytest.mark.parametrize("status", list(MembershipStatus))
def test_every_membership_status_is_accepted(status: MembershipStatus):
    assert minimal_card(status=status).status is status


@pytest.mark.parametrize("bad", ["admin", "root", "MEMBER", "active", ""])
def test_unknown_membership_status_is_rejected(bad):
    with pytest.raises(ValidationError):
        minimal_card(status=bad)


def test_membership_status_does_not_confer_authority_fields():
    """Membership is not personhood, authority, or authorization.

    The contract has no field through which a card could assert any of those, so
    a later slice cannot grant authority by writing into one.
    """
    fields = set(AgentCard.model_fields)
    for forbidden in ("authority", "authorization", "authorized", "permissions", "legal_person"):
        assert forbidden not in fields
    # And the strongest membership value still carries no such field.
    card = minimal_card(status=MembershipStatus.ACCREDITED_AGENT)
    assert not hasattr(card, "authority")


# ── Subject id ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "good",
    ["fed:agent-0001", "fed:0", "fed:society.alpha", "fed:a_b:c-1.2"],
)
def test_well_formed_subject_ids_are_accepted(good):
    assert minimal_card(subject_id=good).subject_id == good


@pytest.mark.parametrize(
    "bad",
    [
        "",  # empty
        "agent-0001",  # missing the opaque federation prefix
        "fed:",  # prefix with nothing after it
        "fed: agent",  # whitespace
        "fed:agent/0001",  # path separator
        "FED:agent-0001",  # wrong case on the prefix
        "fed:" + "a" * (MAX_SUBJECT_ID_LENGTH),  # over the length bound
    ],
)
def test_malformed_subject_ids_are_rejected(bad):
    with pytest.raises(ValidationError):
        minimal_card(subject_id=bad)


def test_subject_id_is_required():
    with pytest.raises(ValidationError):
        AgentCard(
            subject_kind=SubjectKind.AGENT,
            issuer="fed:issuer-arkadia",
            status=MembershipStatus.MEMBER,
        )


def test_subject_id_is_opaque_not_derived_from_other_fields():
    """The id is carried, never computed — two cards differing only in id keep it."""
    a = minimal_card(subject_id="fed:agent-0001")
    b = minimal_card(subject_id="fed:agent-0002")
    assert a.subject_id != b.subject_id
    assert a.subject_kind == b.subject_kind
    assert SUBJECT_ID_PATTERN.startswith("^fed:")


# ── Declared vs verified capabilities ────────────────────────────────────────

def test_declared_and_verified_capabilities_are_separate_fields():
    card = minimal_card(
        declared_capabilities=[DeclaredCapability(name="summarise")],
        verified_capabilities=[
            VerifiedCapability(
                name="notarise",
                verifier="fed:auditor-1",
                evidence_ref="evd:0001",
            )
        ],
    )
    assert card.declared_capability_names() == {"summarise"}
    assert card.verified_capability_names() == {"notarise"}


def test_a_declared_capability_cannot_be_marked_verified():
    with pytest.raises(ValidationError) as exc:
        DeclaredCapability(name="summarise", state=CapabilityState.VERIFIED)
    assert "declared" in str(exc.value)


def test_a_verified_capability_cannot_be_marked_declared():
    with pytest.raises(ValidationError):
        VerifiedCapability(
            name="notarise",
            state=CapabilityState.DECLARED,
            verifier="fed:auditor-1",
            evidence_ref="evd:0001",
        )


def test_a_verified_capability_requires_a_verifier_and_evidence():
    with pytest.raises(ValidationError):
        VerifiedCapability(name="notarise", evidence_ref="evd:0001")
    with pytest.raises(ValidationError):
        VerifiedCapability(name="notarise", verifier="fed:auditor-1")
    with pytest.raises(ValidationError):
        VerifiedCapability(name="notarise", verifier="", evidence_ref="evd:0001")


def test_a_subject_cannot_verify_its_own_capability():
    with pytest.raises(ValidationError) as exc:
        VerifiedCapability(
            name="notarise",
            verifier="fed:agent-0001",
            evidence_ref="evd:0001",
            assertion_source=AssertionSource.SUBJECT,
        )
    assert "cannot verify its own capability" in str(exc.value)


def test_a_capability_claimed_and_attested_is_reported_as_claimed():
    """The same name in both lists still reports as un-attested-by-itself."""
    card = minimal_card(
        declared_capabilities=[DeclaredCapability(name="summarise")],
        verified_capabilities=[
            VerifiedCapability(name="summarise", verifier="fed:auditor-1", evidence_ref="evd:1")
        ],
    )
    assert card.claims_but_does_not_verify() == set()


def test_claims_but_does_not_verify_surfaces_unattested_claims():
    card = minimal_card(
        declared_capabilities=[
            DeclaredCapability(name="summarise"),
            DeclaredCapability(name="execute-trades"),
        ],
        verified_capabilities=[
            VerifiedCapability(name="summarise", verifier="fed:auditor-1", evidence_ref="evd:1")
        ],
    )
    assert card.claims_but_does_not_verify() == {"execute-trades"}


def test_an_empty_capability_name_is_rejected():
    with pytest.raises(ValidationError):
        DeclaredCapability(name="")
    with pytest.raises(ValidationError):
        VerifiedCapability(name="", verifier="fed:auditor-1", evidence_ref="evd:1")


# ── Negative control: the conflation detector ────────────────────────────────

def _capabilities_are_conflated(card: AgentCard) -> bool:
    """Detector: does this card present an unattested claim as verified?

    Reads the typed objects, not a raw dict, so a card that promoted a claim by
    editing a flag would be caught here.
    """
    for verified in card.verified_capabilities:
        if not verified.verifier.strip() or not verified.evidence_ref.strip():
            return True
        if verified.assertion_source is AssertionSource.SUBJECT:
            return True
    for declared in card.declared_capabilities:
        if declared.state is not CapabilityState.DECLARED:
            return True
    return False


def test_negative_control_detector_flags_a_conflated_card():
    """The detector must fire on a card that conflates declaration with verification.

    The conflation is built the way a buggy producer would build it — the same
    name in the verified list with no independent attestation behind it — because
    a detector never fed its own defect is not proven to detect anything.
    """
    conflated = minimal_card()
    conflated.verified_capabilities.append(
        VerifiedCapability.model_construct(
            name="execute-trades",
            state=CapabilityState.VERIFIED,
            assertion_source=AssertionSource.SUBJECT,
            verifier="",
            evidence_ref="",
        )
    )
    assert _capabilities_are_conflated(conflated) is True


def test_negative_control_detector_is_silent_on_a_correct_card():
    """The positive control: a well-formed card must not be reported."""
    card = minimal_card(
        declared_capabilities=[DeclaredCapability(name="summarise")],
        verified_capabilities=[
            VerifiedCapability(name="notarise", verifier="fed:auditor-1", evidence_ref="evd:1")
        ],
    )
    assert _capabilities_are_conflated(card) is False


def test_negative_control_the_producer_refuses_the_conflated_shape():
    """The detector's defect cannot be constructed through the public API.

    The negative control above proves the detector works; this proves the
    contract makes the defect unrepresentable, so the two facts are distinct.
    """
    with pytest.raises(ValidationError):
        VerifiedCapability(
            name="execute-trades",
            verifier="",
            evidence_ref="",
            assertion_source=AssertionSource.SUBJECT,
        )


# ── Provenance states ────────────────────────────────────────────────────────

@pytest.mark.parametrize("state", list(ProvenanceState))
def test_every_provenance_state_is_accepted(state: ProvenanceState):
    kwargs = {}
    if state is ProvenanceState.VERIFIED:
        kwargs = {"verifier": "fed:auditor-1", "evidence_ref": "evd:1"}
    record = ProvenanceRecord(subject_ref="capabilities", state=state, **kwargs)
    assert record.state is state


@pytest.mark.parametrize("bad", ["assumed", "trusted", "VERIFIED", "true"])
def test_unknown_provenance_state_is_rejected(bad):
    with pytest.raises(ValidationError):
        ProvenanceRecord(subject_ref="capabilities", state=bad)


def test_explicit_unknown_or_unverified_states_are_representable():
    """A card can say 'we do not know' and 'not yet verified' without guessing."""
    card = minimal_card(
        provenance=[
            ProvenanceRecord(subject_ref="display_name", state=ProvenanceState.DECLARED),
            ProvenanceRecord(subject_ref="operator", state=ProvenanceState.PENDING),
            ProvenanceRecord(subject_ref="endpoints", state=ProvenanceState.REJECTED),
            ProvenanceRecord(
                subject_ref="issuer",
                state=ProvenanceState.VERIFIED,
                assertion_source=AssertionSource.EXTERNAL_VERIFIER,
                verifier="fed:auditor-1",
                evidence_ref="evd:1",
            ),
        ]
    )
    assert {p.state for p in card.provenance} == set(ProvenanceState)


def test_verified_provenance_requires_a_verifier_and_evidence():
    with pytest.raises(ValidationError) as exc:
        ProvenanceRecord(subject_ref="issuer", state=ProvenanceState.VERIFIED)
    assert "requires non-empty" in str(exc.value)


def test_non_verified_provenance_must_not_borrow_a_verifier():
    with pytest.raises(ValidationError) as exc:
        ProvenanceRecord(
            subject_ref="issuer",
            state=ProvenanceState.PENDING,
            verifier="fed:auditor-1",
            evidence_ref="evd:1",
        )
    assert "must not carry" in str(exc.value)


def test_provenance_subject_ref_is_required():
    with pytest.raises(ValidationError):
        ProvenanceRecord(state=ProvenanceState.DECLARED)


# ── Operator assertion ───────────────────────────────────────────────────────

def test_operator_assertion_is_optional():
    assert minimal_card().operator_assertion is None


def test_operator_assertion_records_its_source_and_defaults_to_declared():
    assertion = OperatorAssertion(operator_id="fed:operator-1")
    assert assertion.source is AssertionSource.SUBJECT
    assert assertion.state is ProvenanceState.DECLARED
    assert assertion.evidence_ref is None


def test_an_operator_link_asserted_by_the_subject_cannot_be_verified():
    with pytest.raises(ValidationError) as exc:
        OperatorAssertion(
            operator_id="fed:operator-1",
            source=AssertionSource.SUBJECT,
            state=ProvenanceState.VERIFIED,
            evidence_ref="evd:1",
        )
    assert "self-description" in str(exc.value)


def test_an_operator_link_verified_by_a_third_party_is_representable():
    assertion = OperatorAssertion(
        operator_id="fed:operator-1",
        source=AssertionSource.EXTERNAL_VERIFIER,
        state=ProvenanceState.VERIFIED,
        evidence_ref="evd:1",
    )
    assert assertion.state is ProvenanceState.VERIFIED


def test_a_verified_operator_assertion_requires_evidence():
    with pytest.raises(ValidationError):
        OperatorAssertion(
            operator_id="fed:operator-1",
            source=AssertionSource.EXTERNAL_VERIFIER,
            state=ProvenanceState.VERIFIED,
        )


def test_an_unverified_operator_assertion_must_not_carry_evidence():
    with pytest.raises(ValidationError):
        OperatorAssertion(
            operator_id="fed:operator-1",
            state=ProvenanceState.DECLARED,
            evidence_ref="evd:1",
        )


# ── Negative control: operator inference ─────────────────────────────────────

def _operator_is_inferred(card: AgentCard) -> bool:
    """Detector: does this card present an operator link the subject cannot support?

    An operator link is inferred when it is carried without attribution, or when
    it is attributed to the subject yet presented as verified.
    """
    assertion = card.operator_assertion
    if assertion is None:
        return False
    if assertion.source is None:
        return True
    if assertion.source is AssertionSource.SUBJECT and assertion.state is ProvenanceState.VERIFIED:
        return True
    if assertion.state is ProvenanceState.VERIFIED and not (assertion.evidence_ref or "").strip():
        return True
    return False


def test_negative_control_detector_flags_an_inferred_operator_link():
    """The detector fires on a self-described link dressed as verified."""
    card = minimal_card()
    card.operator_assertion = OperatorAssertion.model_construct(
        operator_id="fed:operator-1",
        source=AssertionSource.SUBJECT,
        state=ProvenanceState.VERIFIED,
        evidence_ref="evd:1",
    )
    assert _operator_is_inferred(card) is True


def test_negative_control_detector_is_silent_on_a_declared_operator_link():
    """The positive control: an attributed, unverified link is not an inference."""
    card = minimal_card(operator_assertion=OperatorAssertion(operator_id="fed:operator-1"))
    assert _operator_is_inferred(card) is False


def test_negative_control_detector_is_silent_when_no_operator_is_asserted():
    assert _operator_is_inferred(minimal_card()) is False


# ── Optional key and endpoint shape ──────────────────────────────────────────

def test_keys_and_endpoints_default_to_empty():
    card = minimal_card()
    assert card.public_keys == []
    assert card.endpoints == []


def test_endpoints_accept_every_declared_kind():
    card = minimal_card(
        endpoints=[
            CommunicationEndpoint(kind=kind, uri=f"{kind.value}://subject.example/agent")
            for kind in EndpointKind
        ]
    )
    assert {e.kind for e in card.endpoints} == set(EndpointKind)


def test_an_endpoint_without_a_scheme_is_rejected():
    with pytest.raises(ValidationError) as exc:
        CommunicationEndpoint(kind=EndpointKind.HTTPS, uri="subject.example/agent")
    assert "scheme" in str(exc.value)


def test_an_endpoint_requires_a_kind_and_a_uri():
    with pytest.raises(ValidationError):
        CommunicationEndpoint(kind=EndpointKind.HTTPS)
    with pytest.raises(ValidationError):
        CommunicationEndpoint(uri="https://subject.example/agent")


def test_an_endpoint_carries_no_claim_that_it_was_contacted():
    """A declared endpoint is a reference, not a reachability or ownership claim."""
    endpoint = CommunicationEndpoint(kind=EndpointKind.HTTPS, uri="https://subject.example/agent")
    assert endpoint.state is ProvenanceState.DECLARED
    for forbidden in ("reachable", "verified_at", "owns", "trusted"):
        assert forbidden not in CommunicationEndpoint.model_fields


def test_public_key_references_accept_every_declared_scheme():
    card = minimal_card(
        public_keys=[
            PublicKeyReference(scheme=PublicKeyRef.JWKS_URI, ref="https://subject.example/jwks.json"),
            PublicKeyReference(scheme=PublicKeyRef.DID_KEY, ref="did:key:z6MkExample"),
            PublicKeyReference(scheme=PublicKeyRef.INLINE_JWK, ref='{"kty":"EC","crv":"P-256"}'),
        ]
    )
    assert {k.scheme for k in card.public_keys} == set(PublicKeyRef)


def test_a_public_key_reference_defaults_to_declared_and_claims_no_signature():
    key = PublicKeyReference(scheme=PublicKeyRef.DID_KEY, ref="did:key:z6MkExample")
    assert key.state is ProvenanceState.DECLARED
    for forbidden in ("signature_verified", "verified", "attested"):
        assert forbidden not in PublicKeyReference.model_fields


def test_a_public_key_reference_requires_a_scheme_and_a_ref():
    with pytest.raises(ValidationError):
        PublicKeyReference(scheme=PublicKeyRef.DID_KEY)
    with pytest.raises(ValidationError):
        PublicKeyReference(ref="did:key:z6MkExample")


# ── Issuance / expiry metadata ───────────────────────────────────────────────

def test_timestamps_are_optional():
    card = minimal_card()
    assert card.issued_at is None
    assert card.expires_at is None
    assert card.withdrawn_at is None
    assert card.is_expired() is False


def test_timestamps_must_be_timezone_aware():
    with pytest.raises(ValidationError) as exc:
        minimal_card(issued_at=datetime(2026, 10, 11, 12, 0, 0))
    assert "timezone-aware" in str(exc.value)


def test_expiry_must_be_after_issuance():
    with pytest.raises(ValidationError) as exc:
        minimal_card(issued_at=NOW, expires_at=NOW - timedelta(days=1))
    assert "later than issued_at" in str(exc.value)


def test_expiry_is_reported_relative_to_a_given_instant():
    card = minimal_card(issued_at=NOW, expires_at=NOW + timedelta(days=30))
    assert card.is_expired(at=NOW + timedelta(days=29)) is False
    assert card.is_expired(at=NOW + timedelta(days=30)) is True
    assert card.is_expired(at=NOW + timedelta(days=31)) is True


def test_is_expired_rejects_a_naive_instant():
    card = minimal_card(issued_at=NOW, expires_at=NOW + timedelta(days=1))
    with pytest.raises(ValueError):
        card.is_expired(at=datetime(2026, 10, 12, 12, 0, 0))


def test_a_withdrawn_card_can_record_when_it_was_withdrawn():
    card = minimal_card(
        status=MembershipStatus.WITHDRAWN,
        issued_at=NOW,
        withdrawn_at=NOW + timedelta(days=5),
    )
    assert card.withdrawn_at == NOW + timedelta(days=5)
    assert card.status is MembershipStatus.WITHDRAWN


# ── Malformed documents ──────────────────────────────────────────────────────

def test_unknown_fields_are_rejected_not_dropped():
    with pytest.raises(ValidationError):
        minimal_card(not_a_real_field="x")


def test_issuer_is_required_and_non_empty():
    with pytest.raises(ValidationError):
        AgentCard(
            subject_id="fed:agent-0001",
            subject_kind=SubjectKind.AGENT,
            status=MembershipStatus.MEMBER,
        )
    with pytest.raises(ValidationError):
        minimal_card(issuer="")


def test_a_card_with_an_unknown_status_value_is_rejected_end_to_end():
    payload = minimal_card().model_dump(mode="json")
    payload["status"] = "superuser"
    with pytest.raises(ValidationError):
        AgentCard(**payload)


def test_a_card_round_trips_through_its_wire_form():
    card = minimal_card(
        display_name="Arkadia Scout",
        issued_at=NOW,
        expires_at=NOW + timedelta(days=90),
        operator_assertion=OperatorAssertion(operator_id="fed:operator-1"),
        declared_capabilities=[DeclaredCapability(name="summarise")],
        verified_capabilities=[
            VerifiedCapability(name="notarise", verifier="fed:auditor-1", evidence_ref="evd:1")
        ],
        provenance=[
            ProvenanceRecord(subject_ref="issuer", state=ProvenanceState.PENDING)
        ],
        endpoints=[CommunicationEndpoint(kind=EndpointKind.HTTPS, uri="https://subject.example/a")],
        public_keys=[PublicKeyReference(scheme=PublicKeyRef.DID_KEY, ref="did:key:z6MkExample")],
    )
    again = AgentCard(**card.model_dump(mode="json"))
    assert again == card
    assert again.verified_capability_names() == {"notarise"}


# ── Boundary: the contract stays a contract ──────────────────────────────────

def test_the_package_exposes_no_route_or_persistence_surface():
    """Slice 1 ships a schema. A route, a store, or a signer would be a new surface."""
    import federation
    import federation.agent_card as agent_card

    exported = set(getattr(federation, "__all__", []))
    assert exported  # the package publishes its contract explicitly
    for module in (federation, agent_card):
        source = module.__doc__ or ""
        assert "no route" in source or "no router" in source or "no persistence" in source

    # No storage, network, or signing imports anywhere in the package.
    import inspect

    src = inspect.getsource(agent_card)
    for forbidden in ("sqlite3", "requests", "httpx", "fastapi", "jwt", "cryptography"):
        assert forbidden not in src, f"{forbidden} must not appear in the contract module"


def test_the_contract_module_does_not_import_application_layers():
    """The domain contract is a leaf: it must not depend on api/, kernel/, or lab/."""
    import ast
    import inspect

    import federation.agent_card as agent_card

    tree = ast.parse(inspect.getsource(agent_card))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    for module in imported:
        top = module.split(".")[0]
        assert top in {"__future__", "re", "datetime", "enum", "typing", "pydantic"}, (
            f"unexpected import {module!r}: the contract must remain a leaf module"
        )
