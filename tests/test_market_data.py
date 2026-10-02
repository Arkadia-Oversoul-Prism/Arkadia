from economic_seams.market_data import normalize_market_tables, parse_html_tables


def test_parses_html_table_cells():
    tables = parse_html_tables("<table><tr><th>Currency</th><th>Rate</th></tr><tr><td>USD</td><td>1500.25</td></tr></table>")
    assert tables == [[["Currency", "Rate"], ["USD", "1500.25"]]]


def test_fx_rows_are_reference_observations_not_spreads():
    rows = normalize_market_tables(
        "<table><tr><th>Currency</th><th>Rate</th></tr><tr><td>USD</td><td>1500.25</td></tr></table>",
        source_id="cbn_fx", source_url="https://www.cbn.gov.ng/rates/ExchRateByCurrency.html",
    )
    assert len(rows) == 1
    assert rows[0]["labels"] == ["USD"]
    assert rows[0]["numeric_values"] == ["1500.25"]
    assert rows[0]["interpretation"] == "UNCLASSIFIED_REFERENCE_ROW"


def test_ignores_navigation_and_text_without_numeric_cells():
    rows = normalize_market_tables(
        "<table><tr><td>Home</td><td>About</td></tr><tr><td>Latest prices</td><td>See more</td></tr></table>",
        source_id="nepc_prices", source_url="https://nepc.gov.ng/indicative-market-prices/",
    )
    assert rows == []


def test_rejects_unknown_source():
    import pytest
    with pytest.raises(ValueError, match="unsupported"):
        normalize_market_tables("<table></table>", source_id="unknown", source_url="https://example.com")



def test_parses_nepc_price_rows_with_commodity_and_state_context():
    from economic_seams.market_data import parse_nepc_pdf_text

    rows = parse_nepc_pdf_text(
        "ONIONS (UNIT:50KG PER BAG)\\nSTATES\\nKATSINA ₦ 58,000.00 ₦ 58,000.00 ₦ 60,000.00 ₦ 60,000.00\\n% PER WEEK 0% 0% 0% 0%",
        source_url="https://nepc.gov.ng/cms/wp-content/uploads/2026/08/example.pdf",
    )
    assert len(rows) == 1
    assert rows[0]["state"] == "KATSINA"
    assert rows[0]["commodity_unit_heading"] == "ONIONS (UNIT:50KG PER BAG)"
    assert rows[0]["reported_values"] == ["₦ 58,000.00", "₦ 58,000.00", "₦ 60,000.00", "₦ 60,000.00"]


def test_nepc_price_parser_does_not_infer_from_percent_summary():
    from economic_seams.market_data import parse_nepc_pdf_text

    rows = parse_nepc_pdf_text(
        "ONIONS (UNIT:50KG PER BAG)\\n% PER WEEK 0% 0% 0% 0%",
        source_url="https://nepc.gov.ng/example.pdf",
    )
    assert rows == []
