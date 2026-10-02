from __future__ import annotations


def test_sovereign_field_is_idempotent_and_buyer_recon_persists(tmp_path, monkeypatch):
    import solspire.sovereign_field as field
    import solspire.workspace_manager as workspace

    db = tmp_path / "sovereign.db"
    monkeypatch.setattr(field, "_DB_PATH", str(db))
    monkeypatch.setattr(workspace, "_DB_PATH", str(db))

    subject = "sovereign-subject"
    first = field.ensure_field(subject)
    second = field.ensure_field(subject)

    assert first["field_id"] == second["field_id"]
    assert first["workspace_ref"] == second["workspace_ref"]
    assert first["field_kind"] == "SOVEREIGN_HIDDEN_OS"

    created = field.create_buyer_candidate(
        subject,
        {
            "prospect": "Test Buyer",
            "location": "Abuja",
            "commodity": "Irish Potato",
        },
    )
    assert created["status"] == "UNCONTACTED"
    assert created["buyer_price"] == "UNKNOWN"

    updated = field.update_buyer_candidate(
        subject,
        created["candidate_id"],
        {"status": "REQUIREMENT_CAPTURED", "quantity": "20 bags"},
    )
    assert updated["status"] == "REQUIREMENT_CAPTURED"
    assert updated["quantity"] == "20 bags"

    rows = field.list_buyer_recon(subject)
    assert len(rows) == 1
    assert rows[0]["candidate_id"] == created["candidate_id"]


def test_sovereign_field_is_subject_bound(tmp_path, monkeypatch):
    import solspire.sovereign_field as field
    import solspire.workspace_manager as workspace

    db = tmp_path / "sovereign.db"
    monkeypatch.setattr(field, "_DB_PATH", str(db))
    monkeypatch.setattr(workspace, "_DB_PATH", str(db))

    a = field.ensure_field("subject-a")
    b = field.ensure_field("subject-b")

    assert a["field_id"] != b["field_id"]
    assert a["workspace_ref"] != b["workspace_ref"]
