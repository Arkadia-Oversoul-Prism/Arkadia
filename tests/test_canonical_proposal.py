from __future__ import annotations


def _manager(tmp_path, monkeypatch):
    import solspire.proposal_manager as mod

    monkeypatch.setattr(mod, "_DB_PATH", str(tmp_path / "proposal.db"))
    return mod.ProposalManager()


def test_proposal_create_is_bounded(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)
    proposal = manager.create_proposal(
        subject_ref="subject-a",
        workspace_ref="ws-a",
        objective="Test objective",
        scope="bounded",
    )
    assert proposal.proposal_status == "PRESENTED"
    assert proposal.authorization_ref is None
    assert proposal.provenance_ref is None
    assert proposal.decision_ref is None
    assert proposal.feedback_refs == []
    assert proposal.created_by_event is None


def test_feedback_does_not_authorize(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)
    proposal = manager.create_proposal(subject_ref="subject-a", workspace_ref="ws-a")
    updated, feedback = manager.add_feedback(
        proposal_id=proposal.proposal_id,
        subject_ref="subject-a",
        workspace_ref="ws-a",
        observation="needs evidence",
        recommendation="revise scope",
    )
    assert feedback.status == "SUBMITTED"
    assert updated.proposal_status == "UNDER_REVIEW"
    assert updated.authorization_ref is None
    assert updated.provenance_ref is None
    assert feedback.feedback_id in updated.feedback_refs
    # ACCEPTED is not set by feedback
    assert updated.proposal_status != "ACCEPTED"


def test_proposals_isolated_by_subject(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)
    a = manager.create_proposal(subject_ref="subject-a", workspace_ref="ws-a")
    b = manager.create_proposal(subject_ref="subject-b", workspace_ref="ws-b")
    assert manager.get_proposal(a.proposal_id, "subject-b") is None
    assert manager.get_proposal(b.proposal_id, "subject-a") is None
    assert manager.list_proposals("subject-a", "ws-a")[0].proposal_id == a.proposal_id


def test_empty_subject_rejected(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)
    try:
        manager.create_proposal(subject_ref="", workspace_ref="ws-a")
    except ValueError as exc:
        assert "subject" in str(exc).lower()
    else:
        raise AssertionError("empty subject must be rejected")
