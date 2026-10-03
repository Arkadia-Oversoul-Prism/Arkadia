from economic_seams.deal_sheet import DealSheet, evaluate_deal


def base(**overrides):
    values = dict(
        commodity="Irish potato",
        specification="Grade A, 50kg bags",
        source_location="Plateau",
        buyer_location="Abuja",
        buyer="verified buyer",
        supplier="verified supplier",
        quantity="100",
        unit="kg",
        buyer_unit_price="2500",
        supplier_unit_price="1800",
        logistics_cost="30000",
        other_costs="10000",
        payment_terms="buyer pays on acceptance",
        settlement_days="1",
        capital_required="100000",
        evidence_ids=("buyer-1", "supplier-1", "logistics-1"),
        eligibility_verified=True,
        counterparties_verified=True,
        prices_verified=True,
        logistics_verified=True,
        buyer_commitment_verified=True,
        supplier_commitment_verified=True,
        human_authorized=True,
    )
    values.update(overrides)
    return DealSheet(**values)


def test_computes_net_realizable_spread():
    result = evaluate_deal(base())
    assert result["revenue"] == "250000"
    assert result["total_cost"] == "220000"
    assert result["net_realizable_spread"] == "30000"
    assert result["capital_efficiency"] == "0.3"
    assert result["executable"] is True
    assert result["cash_deployment_authorized"] is True


def test_price_spread_without_verification_is_not_executable():
    result = evaluate_deal(base(prices_verified=False))
    assert result["net_realizable_spread"] == "30000"
    assert result["executable"] is False
    assert any("prices" in blocker for blocker in result["blockers"])


def test_missing_data_stays_unknown():
    result = evaluate_deal(base(buyer_unit_price="", supplier_unit_price=""))
    assert result["net_realizable_spread"] is None
    assert result["capital_efficiency"] is None
    assert result["executable"] is False


def test_negative_net_spread_blocks_execution():
    result = evaluate_deal(base(buyer_unit_price="1700"))
    assert result["net_realizable_spread"] == "-50000"
    assert result["executable"] is False


def test_human_authorization_is_required_for_cash_deployment():
    result = evaluate_deal(base(human_authorized=False))
    assert result["executable"] is False
    assert result["cash_deployment_authorized"] is False
    assert any("Human authorization" in blocker for blocker in result["blockers"])
