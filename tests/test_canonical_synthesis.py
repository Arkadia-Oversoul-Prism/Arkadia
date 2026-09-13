from __future__ import annotations


def _manager(tmp_path, monkeypatch):
    import solspire.synthesis_manager as mod

    monkeypatch.setattr(mod, "_DB_PATH", str(tmp_path / "synthesis.db"))
    return mod.SynthesisManager()


def test_weekly_synthesis_is_idempotent_and_bounded(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)
    first = manager.create_or_get_current_week(subject_ref="subject-a", workspace_ref="ws-a")
    second = manager.create_or_get_current_week(subject_ref="subject-a", workspace_ref="ws-a")
    assert first.synthesis_id == second.synthesis_id
    assert first.status == "RECORDED"
    assert first.period_start <= first.period_end
    assert first.evidence_refs == []
    assert first.proposal_refs == []
    assert first.feedback_refs == []
    assert first.candidate_directions == []
    assert first.decisions_pending == []
    assert first.created_by_event is None
    assert first.patterns == []


def test_weekly_synthesis_isolated_by_subject(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)
    a = manager.create_or_get_current_week(subject_ref="subject-a", workspace_ref="ws-a")
    b = manager.create_or_get_current_week(subject_ref="subject-b", workspace_ref="ws-b")
    assert a.synthesis_id != b.synthesis_id
    assert manager.list_for_subject("subject-a", "ws-a")[0].synthesis_id == a.synthesis_id
    assert manager.list_for_subject("subject-b", "ws-b")[0].synthesis_id == b.synthesis_id
    assert manager.get_current_week("subject-b", "ws-a") is None


def test_empty_subject_is_rejected(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)
    try:
        manager.create_or_get_current_week(subject_ref="", workspace_ref="ws-a")
    except ValueError as exc:
        assert "subject" in str(exc).lower()
    else:
        raise AssertionError("empty subject must be rejected")
