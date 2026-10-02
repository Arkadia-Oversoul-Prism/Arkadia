from economic_seams.correlation import Evidence, TransactionFacts, assess_seam


def ev(eid, source, cls, url=None, verified=True):
    return Evidence(
        evidence_id=eid,
        source_id=source,
        source_class=cls,
        source_url=url or f"https://{source}.example/data",
        content_hash=f"hash-{source}",
        observed_at="2026-10-02T00:00:00+00:00",
        fact_key="support",
        fact_value="observed",
        independently_verified=verified,
    )


def complete_facts(**overrides):
    values = dict(
        demand="buyer purchase order PO-123",
        supply="supplier quote SQ-456",
        price_basis="dated buyer and supplier quotes in NGN",
        costs="logistics, duties, tax, fees and settlement cost itemized",
        capital_requirement="working capital requirement calculated from payment terms",
        counterparty="buyer and supplier identities independently checked",
        execution_path="documented delivery, acceptance and settlement sequence",
        failure_conditions="price expiry, failed inspection, late delivery, buyer default",
        legal_basis="applicable procurement and commercial contract terms reviewed",
        why_spread_exists="supplier payment terms and buyer settlement timing differ",
        human_eligibility_review=True,
        reviewer_uid="sovereign-test-user",
        reviewed_at="2026-10-02T00:00:00+00:00",
    )
    values.update(overrides)
    return TransactionFacts(**values)


def test_single_source_remains_lead():
    result = assess_seam(title="Example", seam_type="procurement",
                         evidence=[ev("e1", "portal", "procurement")], facts=complete_facts())
    assert result["status"] == "LEAD"
    assert not result["verified"]


def test_two_classes_with_missing_facts_are_not_verified():
    result = assess_seam(
        title="Example", seam_type="trade",
        evidence=[ev("e1", "portal", "procurement"), ev("e2", "prices", "price")],
        facts=complete_facts(counterparty=""),
    )
    assert result["status"] == "CANDIDATE_SEAM"
    assert "counterparty" in result["missing_facts"]


def test_duplicate_provider_cannot_fake_independence_with_new_url_or_class():
    first = ev("e1", "portal", "procurement")
    repost = Evidence(
        evidence_id="e2", source_id="portal", source_class="price",
        source_url="https://portal.example/another-page", content_hash="different-hash",
        observed_at=first.observed_at, fact_key="price", fact_value="new page",
        independently_verified=True,
    )
    result = assess_seam(title="Example", seam_type="trade",
                         evidence=[first, repost], facts=complete_facts())
    assert result["status"] == "LEAD"
    assert result["independent_source_count"] == 1
    assert not result["verified"]


def test_verified_candidate_requires_all_gates():
    result = assess_seam(
        title="Example", seam_type="trade",
        evidence=[ev("e1", "portal", "procurement"), ev("e2", "prices", "price")],
        facts=complete_facts(),
    )
    assert result["status"] == "VERIFIED_CANDIDATE"
    assert result["verified"]
    assert result["missing_facts"] == []


def test_unverified_evidence_blocks_promotion():
    result = assess_seam(
        title="Example", seam_type="trade",
        evidence=[ev("e1", "portal", "procurement", verified=False),
                  ev("e2", "prices", "price", verified=True)],
        facts=complete_facts(),
    )
    assert result["status"] == "CANDIDATE_SEAM"
    assert not result["verified"]


def test_review_boolean_without_auditable_identity_does_not_verify():
    result = assess_seam(
        title="Example", seam_type="trade",
        evidence=[ev("e1", "portal", "procurement"), ev("e2", "prices", "price")],
        facts=complete_facts(reviewer_uid="", reviewed_at=""),
    )
    assert result["status"] == "CANDIDATE_SEAM"
    assert not result["verified"]


def test_public_api_assessment_is_capped_even_if_internal_gate_is_satisfied():
    from economic_seams.correlation import cap_public_assessment
    assessment = {
        "status": "VERIFIED_CANDIDATE",
        "verified": True,
        "blockers": [],
    }
    result = cap_public_assessment(assessment)
    assert result["status"] == "CANDIDATE_SEAM"
    assert result["verified"] is False
    assert "source-backed review workflow" in result["blockers"][0]


def test_unknown_provider_identity_cannot_satisfy_independence():
    from economic_seams.correlation import Evidence
    unknown = Evidence(
        evidence_id="e3", source_id="unregistered-provider", source_class="price",
        source_url="https://unregistered.example/data", content_hash="hash",
        observed_at="2026-10-02T00:00:00+00:00", fact_key="price", fact_value="observed",
        independently_verified=True,
    )
    known = ev("e4", "portal", "procurement", verified=True)
    result = assess_seam(title="Example", seam_type="trade",
                         evidence=[known, unknown], facts=complete_facts())
    assert result["independent_source_count"] == 1
    assert result["status"] == "LEAD"
