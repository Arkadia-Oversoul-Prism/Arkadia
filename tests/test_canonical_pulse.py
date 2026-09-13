from __future__ import annotations


def test_daily_pulse_is_unique_per_subject_workspace_date(tmp_path, monkeypatch):
    import solspire.pulse_manager as pulse_mod

    monkeypatch.setattr(pulse_mod, "_DB_PATH", str(tmp_path / "pulse.db"))
    manager = pulse_mod.PulseManager()

    first = manager.create_or_get_today(subject_ref="subject-a", workspace_ref="ws-a")
    second = manager.create_or_get_today(subject_ref="subject-a", workspace_ref="ws-a")

    assert first.pulse_id == second.pulse_id
    assert first.subject_ref == "subject-a"
    assert first.workspace_ref == "ws-a"
    assert first.status == "RECORDED"
    assert first.work_event_refs == []
    assert first.evidence_refs == []
    assert first.decision_refs == []
    assert first.proposal_refs == []
    assert first.feedback_refs == []
    assert first.human_attention_refs == []
    assert first.created_by_event is None


def test_daily_pulse_isolated_by_subject(tmp_path, monkeypatch):
    import solspire.pulse_manager as pulse_mod

    monkeypatch.setattr(pulse_mod, "_DB_PATH", str(tmp_path / "pulse.db"))
    manager = pulse_mod.PulseManager()

    a = manager.create_or_get_today(subject_ref="subject-a", workspace_ref="ws-a")
    b = manager.create_or_get_today(subject_ref="subject-b", workspace_ref="ws-b")

    assert a.pulse_id != b.pulse_id
    assert manager.list_for_subject("subject-a", "ws-a")[0].pulse_id == a.pulse_id
    assert manager.list_for_subject("subject-b", "ws-b")[0].pulse_id == b.pulse_id
    assert manager.list_for_subject("subject-a", "ws-a")[0].subject_ref == "subject-a"


def test_empty_subject_is_rejected(tmp_path, monkeypatch):
    import solspire.pulse_manager as pulse_mod

    monkeypatch.setattr(pulse_mod, "_DB_PATH", str(tmp_path / "pulse.db"))
    manager = pulse_mod.PulseManager()

    try:
        manager.create_or_get_today(subject_ref="", workspace_ref="ws-a")
    except ValueError as exc:
        assert "subject" in str(exc).lower()
    else:
        raise AssertionError("empty subject must be rejected")
