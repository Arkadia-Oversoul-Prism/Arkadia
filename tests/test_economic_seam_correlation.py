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
    )
    values.update(overrides)
    return TransactionFacts(**values)


def test_single_source_remains_lead():
    result = assess_seam(
        title="Example", seam_type="procurement",
        evidence=[ev("e1", "portal", "procurement")],
        facts=complete_facts(),
    )
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


def test_duplicate_source_cannot_fake_independence():
    first = ev("e1", "portal", "procurement")
    repost = Evidence(
        evidence_id="e2", source_id="portal", source_class="price",
        source_url=first.source_url, content_hash=first.content_hash,
        observed_at=first.observed_at, fact_key="price", fact_value="same copy",
        independently_verified=True,
    )
    result = assess_seam(title="Example", seam_type="trade",
                         evidence=[first, repost], facts=complete_facts())
    assert result["status"] == "LEAD"
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
