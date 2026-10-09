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
        "ONIONS (UNIT:50KG PER BAG)\nSTATES\nKATSINA ₦ 58,000.00 ₦ 58,000.00 ₦ 60,000.00 ₦ 60,000.00\n% PER WEEK 0% 0% 0% 0%",
        source_url="https://nepc.gov.ng/cms/wp-content/uploads/2026/08/example.pdf",
    )
    assert len(rows) == 1
    assert rows[0]["state"] == "KATSINA"
    assert rows[0]["commodity_unit_heading"] == "ONIONS (UNIT:50KG PER BAG)"
    assert rows[0]["reported_values"] == ["₦ 58,000.00", "₦ 58,000.00", "₦ 60,000.00", "₦ 60,000.00"]


def test_nepc_price_parser_does_not_infer_from_percent_summary():
    from economic_seams.market_data import parse_nepc_pdf_text

    rows = parse_nepc_pdf_text(
        "ONIONS (UNIT:50KG PER BAG)\n% PER WEEK 0% 0% 0% 0%",
        source_url="https://nepc.gov.ng/example.pdf",
    )
    assert rows == []


def test_market_comparability_requires_all_dimensions_to_align():
    from economic_seams.market_data import comparable_market_observations
    base = {
        "commodity": "ONIONS",
        "unit": "50KG PER BAG",
        "location": "KATSINA",
        "period": "2026-W35",
        "quote_basis": "INDICATIVE_LOCAL_PRICE",
    }
    assert comparable_market_observations(base, dict(base))
    mismatch = dict(base, period="2026-W36")
    assert not comparable_market_observations(base, mismatch)


def test_nepc_normalization_refuses_unmapped_pdf_columns():
    from economic_seams.market_data import normalize_nepc_price_row
    row = {
        "source_url": "https://nepc.gov.ng/example.pdf",
        "commodity_unit_heading": "ONIONS (UNIT:50KG PER BAG)",
        "state": "KATSINA",
        "reported_values": ["₦ 58,000.00", "₦ 60,000.00"],
    }
    import pytest
    with pytest.raises(ValueError, match="multiple period"):
        normalize_nepc_price_row(row, period="2026-W35", unit="50KG PER BAG")


def test_cbn_normalization_requires_explicit_quote_context():
    from economic_seams.market_data import normalize_cbn_fx_row
    row = {
        "source_url": "https://www.cbn.gov.ng/rates/ExchRateByCurrency.html",
        "numeric_values": ["1500.25"],
    }
    import pytest
    with pytest.raises(ValueError, match="date"):
        normalize_cbn_fx_row(row, observed_date="", quote_basis="NFEM reference",
                             currency="USD")


def test_cbn_fixture_requires_explicit_quote_context_and_preserves_rate():
    from economic_seams.market_data import normalize_cbn_fx_row
    fixture = """<table><tr><th>Currency</th><th>Rate</th></tr><tr><td>USD</td><td>1500.25</td></tr><tr><td>GBP</td><td>1900.10</td></tr></table>"""
    rows = normalize_market_tables(fixture, source_id="cbn_fx", source_url="https://www.cbn.gov.ng/rates/ExchRateByCurrency.html")
    assert len(rows) == 2
    normalized = normalize_cbn_fx_row(rows[0], observed_date="2026-10-09", quote_basis="CBN published reference rate", currency="USD")
    assert normalized["price"] == "1500.25"
    assert normalized["observed_date"] == "2026-10-09"
    assert normalized["quote_basis"] == "CBN published reference rate"


def test_cbn_malformed_rows_fail_closed():
    import pytest
    html = """<table><tr><th>Currency</th><th>Rate</th></tr><tr><td>USD</td><td>not published</td></tr><tr><td></td><td>1500.25</td></tr></table>"""
    rows = normalize_market_tables(html, source_id="cbn_fx", source_url="https://www.cbn.gov.ng/rates/ExchRateByCurrency.html")
    assert rows == []
    with pytest.raises(ValueError, match="exactly one explicit numeric rate"):
        from economic_seams.market_data import normalize_cbn_fx_row
        normalize_cbn_fx_row({"numeric_values": ["1500.25", "1501.00"]}, observed_date="2026-10-09", quote_basis="CBN published reference rate", currency="USD")


def test_nepc_unparseable_pdf_text_fails_with_no_rows():
    from economic_seams.market_data import parse_nepc_pdf_text
    assert parse_nepc_pdf_text("NEPC indicative prices\\nCommodity report\\nNo state prices available", source_url="https://nepc.gov.ng/example.pdf") == []


def test_nepc_rows_persist_without_cbn_response_variable(monkeypatch, tmp_path):
    import economic_seams.engine as engine
    from economic_seams import market_data
    monkeypatch.setattr(engine, "DB_PATH", str(tmp_path / "economic-seams.db"))
    source = next(item for item in engine.SOURCES if item.id == "nepc_prices")
    row = {"source_id": "nepc_prices", "source_url": "https://nepc.gov.ng/example.pdf", "commodity_unit_heading": "ONIONS (UNIT:50KG PER BAG)", "state": "KATSINA", "reported_values": ["₦ 58,000.00"], "interpretation": "INDICATIVE_LOCAL_PRICE"}
    monkeypatch.setattr(market_data, "fetch_nepc_price_rows", lambda session, url, timeout=25: [row])
    conn = engine._db()
    rows = engine._scan_market_reference(conn, source)
    persisted = conn.execute("SELECT source_id, url, title, excerpt FROM observations WHERE source_id='nepc_prices'").fetchall()
    conn.commit()
    conn.close()
    assert len(rows) == 1
    assert len(persisted) == 1
    assert persisted[0]["url"] == row["source_url"]
    assert "KATSINA" in persisted[0]["excerpt"]


def test_nepc_unparseable_document_does_not_persist_rows(monkeypatch, tmp_path):
    import pytest
    import economic_seams.engine as engine
    from economic_seams import market_data
    monkeypatch.setattr(engine, "DB_PATH", str(tmp_path / "economic-seams.db"))
    source = next(item for item in engine.SOURCES if item.id == "nepc_prices")
    monkeypatch.setattr(market_data, "fetch_nepc_price_rows", lambda session, url, timeout=25: [])
    conn = engine._db()
    with pytest.raises(ValueError, match="No parseable market reference rows"):
        engine._scan_market_reference(conn, source)
    count = conn.execute("SELECT COUNT(*) FROM observations WHERE source_id='nepc_prices'").fetchone()[0]
    conn.close()
    assert count == 0
