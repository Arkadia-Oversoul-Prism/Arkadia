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


# Captured rendered CBN NFEM table excerpt from the official Exchange Rates page.
# The column order and date/rate values match the published page's visible table.
CBN_NFEM_SOURCE_FIXTURE = """<table>
<tr><th>Date</th><th>NFEM Rate (₦/US$)</th><th>Highest Rate (₦/US$)</th><th>Lowest Rate (₦/US$)</th><th>Closing Rate (₦/US$)</th><th>Simple Aver. Rate (Mean) (₦/US$)</th><th>NFEM Interbank Turnover (US$)</th><th>No. of Deals at Interbank</th><th>NFEM Total Turnover (US$)</th><th>No. of Deals at NFEM</th></tr>
<tr><td>September-25-2026</td><td>1,329.5138</td><td>1,331.0000</td><td>1,328.0000</td><td>1,330.0000</td><td>1,329.4957</td><td>111,064,460.7600</td><td>108</td><td>0.0000</td><td>0</td></tr>
</table>"""


def test_cbn_captured_nfem_fixture_selects_named_rate_not_adjacent_columns():
    from economic_seams.market_data import parse_cbn_nfem_rows
    rows = parse_cbn_nfem_rows(
        CBN_NFEM_SOURCE_FIXTURE,
        source_url="https://www.cbn.gov.ng/rates/ExchRateByCurrency.html",
    )
    assert len(rows) == 1
    assert rows[0]["observed_date"] == "2026-09-25"
    assert rows[0]["numeric_values"] == ["1329.5138"]
    assert rows[0]["quote_basis"] == "CBN NFEM volume-weighted average official rate"
    assert rows[0]["source_url"] == "https://www.cbn.gov.ng/rates/ExchRateByCurrency.html"


def test_cbn_captured_fixture_normalizes_only_with_explicit_quote_context():
    from economic_seams.market_data import normalize_cbn_fx_row, parse_cbn_nfem_rows
    import pytest
    row = parse_cbn_nfem_rows(
        CBN_NFEM_SOURCE_FIXTURE,
        source_url="https://www.cbn.gov.ng/rates/ExchRateByCurrency.html",
    )[0]
    normalized = normalize_cbn_fx_row(
        row,
        observed_date=row["observed_date"],
        quote_basis=row["quote_basis"],
        currency=row["currency"],
        unit=row["unit"],
    )
    assert normalized["price"] == "1329.5138"
    assert normalized["currency"] == "USD"
    assert normalized["unit"] == "₦ per US$1"
    with pytest.raises(ValueError, match="requires date"):
        normalize_cbn_fx_row(row, observed_date="", quote_basis=row["quote_basis"],
                              currency="USD", unit=row["unit"])


def test_cbn_nfem_parser_rejects_malformed_rows_and_ambiguous_headers():
    from economic_seams.market_data import parse_cbn_nfem_rows
    malformed = """<table><tr><th>Date</th><th>NFEM Rate (₦/US$)</th></tr>
    <tr><td>not-a-date</td><td>not-published</td></tr>
    <tr><td>2026-10-09</td><td>n/a</td></tr></table>"""
    assert parse_cbn_nfem_rows(
        malformed, source_url="https://www.cbn.gov.ng/rates/ExchRateByCurrency.html"
    ) == []
    ambiguous = """<table><tr><th>Date</th><th>Rate</th></tr>
    <tr><td>2026-10-09</td><td>1500.25</td></tr></table>"""
    assert parse_cbn_nfem_rows(
        ambiguous, source_url="https://www.cbn.gov.ng/rates/ExchRateByCurrency.html"
    ) == []


def test_cbn_nfem_fixture_persists_source_date_rate_and_quote_basis(monkeypatch, tmp_path):
    import economic_seams.engine as engine

    monkeypatch.setattr(engine, "DB_PATH", str(tmp_path / "economic-seams.db"))
    source = next(item for item in engine.SOURCES if item.id == "cbn_fx")

    class FixtureResponse:
        url = "https://www.cbn.gov.ng/rates/ExchRateByCurrency.html"
        text = CBN_NFEM_SOURCE_FIXTURE

        @staticmethod
        def raise_for_status():
            return None

    monkeypatch.setattr(engine.requests, "get",
                        lambda url, timeout, headers: FixtureResponse())
    conn = engine._db()
    rows = engine._scan_market_reference(conn, source)
    persisted = conn.execute(
        "SELECT source_id, url, title, excerpt FROM observations WHERE source_id='cbn_fx'"
    ).fetchall()
    conn.commit()
    conn.close()

    assert len(rows) == 1
    assert len(persisted) == 1
    assert persisted[0]["url"] == FixtureResponse.url
    assert "2026-09-25" in persisted[0]["excerpt"]
    assert "1329.5138" in persisted[0]["excerpt"]
    assert "CBN NFEM volume-weighted average official rate" in persisted[0]["excerpt"]


AFDB_RSS_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Current Solicitations</title>
<item><title>Supply of solar equipment</title><link>https://www.afdb.org/en/corporate-procurement/supply-solar-equipment</link><pubDate>Thu, 08 Oct 2026 00:00:00 GMT</pubDate><description><![CDATA[Open tender for solar equipment and installation.]]></description></item>
</channel></rss>"""


def test_afdb_official_rss_parser_preserves_notice_evidence():
    from economic_seams.market_data import parse_afdb_rss_items
    items = parse_afdb_rss_items(
        AFDB_RSS_FIXTURE,
        feed_url="https://www.afdb.org/en/about-us/corporate-procurement/procurement-notices/current-solicitations.xml",
    )
    assert len(items) == 1
    assert items[0]["title"] == "Supply of solar equipment"
    assert items[0]["source_url"].startswith("https://www.afdb.org/")
    assert "solar equipment" in items[0]["excerpt"]
    assert items[0]["published_at"] == "Thu, 08 Oct 2026 00:00:00 GMT"


def test_afdb_official_rss_fetch_uses_bounded_timeout():
    from economic_seams.market_data import fetch_afdb_procurement_items

    class Response:
        content = AFDB_RSS_FIXTURE.encode("utf-8")
        encoding = "utf-8"
        url = "https://www.afdb.org/en/about-us/corporate-procurement/procurement-notices/current-solicitations.xml"

        @staticmethod
        def raise_for_status():
            return None

    class Session:
        called = None

        @classmethod
        def get(cls, url, *, timeout, headers):
            cls.called = (url, timeout, headers)
            return Response()

    items = fetch_afdb_procurement_items(
        Session,
        "https://www.afdb.org/en/about-us/corporate-procurement/procurement-notices/current-solicitations.xml",
    )
    assert len(items) == 1
    assert Session.called[1] == 25
    assert "application/rss+xml" in Session.called[2]["Accept"]


def test_afdb_rss_rejects_malformed_xml_and_non_official_links():
    import pytest
    from economic_seams.market_data import parse_afdb_rss_items

    with pytest.raises(ValueError, match="not valid XML"):
        parse_afdb_rss_items("<rss><item>", feed_url="https://www.afdb.org/feed.xml")
    unsafe = """<rss><channel><item><title>notice</title><link>https://example.com/not-afdb</link></item></channel></rss>"""
    with pytest.raises(ValueError, match="no valid official items"):
        parse_afdb_rss_items(unsafe, feed_url="https://www.afdb.org/feed.xml")


def test_afdb_procurement_scan_persists_each_official_rss_notice(monkeypatch, tmp_path):
    import economic_seams.engine as engine
    from economic_seams import market_data

    monkeypatch.setattr(engine, "DB_PATH", str(tmp_path / "economic-seams.db"))
    source = next(item for item in engine.SOURCES if item.id == "afdb_procurement")
    monkeypatch.setattr(market_data, "fetch_afdb_procurement_items",
                        lambda session, url, timeout=25: market_data.parse_afdb_rss_items(
                            AFDB_RSS_FIXTURE, feed_url=url))
    conn = engine._db()
    items, _created = engine._scan_afdb_procurement(conn, source)
    persisted = conn.execute(
        "SELECT source_id, url, title, evidence_level FROM observations WHERE source_id='afdb_procurement'"
    ).fetchall()
    conn.commit()
    conn.close()

    assert len(items) == 1
    assert len(persisted) == 1
    assert persisted[0]["url"] == items[0]["source_url"]
    assert persisted[0]["title"] == items[0]["title"]
    assert persisted[0]["evidence_level"] == "OFFICIAL_RSS_ITEM"


def test_nepc_unparseable_pdf_fails_closed_at_fetch_boundary(monkeypatch):
    import pytest
    import pdfminer.high_level
    from economic_seams.market_data import fetch_nepc_price_rows

    class PageResponse:
        url = "https://nepc.gov.ng/indicative-market-prices/"
        text = '<a href="/uploads/local-commodity-price.pdf">Local Commodity Price PDF</a>'

        @staticmethod
        def raise_for_status():
            return None

    class PdfResponse:
        url = "https://nepc.gov.ng/uploads/local-commodity-price.pdf"
        content = b"%PDF-1.4 fixture bytes"

        @staticmethod
        def raise_for_status():
            return None

    class Session:
        calls = []

        @classmethod
        def get(cls, url, *, timeout, headers):
            cls.calls.append((url, timeout))
            return PageResponse() if url.endswith("/indicative-market-prices/") else PdfResponse()

    monkeypatch.setattr(pdfminer.high_level, "extract_text",
                        lambda stream: "NEPC report with no recognizable state price rows")
    with pytest.raises(ValueError, match="yielded no recognizable state price rows"):
        fetch_nepc_price_rows(
            Session,
            "https://nepc.gov.ng/indicative-market-prices/",
            timeout=25,
        )
    assert len(Session.calls) == 2
    assert all(call[1] == 25 for call in Session.calls)
