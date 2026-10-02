from __future__ import annotations


def test_no_legal_basis_no_lead(tmp_path, monkeypatch):
    import economic_seams.engine as e
    monkeypatch.setattr(e, 'DB_PATH', str(tmp_path / 'seams.db'))
    c = e._db()
    src = e.Source('x', 'Test', 'example.gov', 'https://example.gov', 'TEST', '')
    oid = e._upsert_observation(c, src, src.url, 'tax credit procurement')
    assert e._detect(c, src, oid, 'tax credit procurement') == []
    c.close()


def test_legal_basis_creates_evidenced_lead(tmp_path, monkeypatch):
    import economic_seams.engine as e
    monkeypatch.setattr(e, 'DB_PATH', str(tmp_path / 'seams.db'))
    c = e._db()
    src = e.Source('x', 'Test', 'example.gov', 'https://example.gov', 'INCENTIVE', 'Nigeria Tax Act 2025')
    oid = e._upsert_observation(c, src, src.url, 'qualifying tax credit and duty waiver')
    ids = e._detect(c, src, oid, 'qualifying tax credit and duty waiver')
    c.commit()
    rows = c.execute('SELECT * FROM opportunities').fetchall()
    assert ids and len(rows) == 1
    assert rows[0]['status'] == 'LEAD'
    assert rows[0]['legal_basis'] == 'Nigeria Tax Act 2025'
    c.close()
