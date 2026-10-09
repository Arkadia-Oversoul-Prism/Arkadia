import sqlite3

from economic_seams.market_data import normalize_market_tables, parse_nepc_pdf_text


def test_cbn_table_parser_preserves_raw_cells_and_numeric_values():
    html = """
    <table>
      <tr><th>Currency</th><th>Rate</th></tr>
      <tr><td>US Dollar</td><td>1,501.25</td></tr>
    </table>
    """
    rows = normalize_market_tables(html, source_id="cbn_fx",
                                   source_url="https://www.cbn.gov.ng/rates/ExchRateByCurrency.html")
    assert rows
    assert rows[0]["labels"] == ["US Dollar"]
    assert rows[0]["numeric_values"] == ["1,501.25"]
    assert rows[0]["raw_cells"] == ["US Dollar", "1,501.25"]


def test_nepc_pdf_parser_retains_source_line_and_state():
    text = "MAIZE UNIT: NGN/TONNE\nLAGOS ₦120,000\nPLATEAU ₦98,500"
    rows = parse_nepc_pdf_text(text, source_url="https://nepc.gov.ng/example.pdf")
    assert [row["state"] for row in rows] == ["LAGOS", "PLATEAU"]
    assert rows[0]["reported_values"] == ["₦120,000"]
    assert rows[0]["raw_line"] == "LAGOS ₦120,000"
    assert rows[0]["source_url"].endswith("example.pdf")


def test_sqlite_busy_timeout_is_set_before_use(tmp_path, monkeypatch):
    import knowledge.db as knowledge_db

    monkeypatch.setattr(knowledge_db, "_DB_PATH", tmp_path / "knowledge.sqlite")
    monkeypatch.setattr(knowledge_db, "_SCHEMA_PATH", tmp_path / "schema.sql")
    (tmp_path / "schema.sql").write_text("CREATE TABLE IF NOT EXISTS timeout_probe (id INTEGER)")
    if hasattr(knowledge_db._local, "conn") and knowledge_db._local.conn is not None:
        knowledge_db._local.conn.close()
    knowledge_db._local.conn = None

    conn = knowledge_db.get_connection()
    assert conn.execute("PRAGMA busy_timeout").fetchone()[0] == 30000
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    conn.close()
    knowledge_db._local.conn = None
