from __future__ import annotations


def test_human_decision_accepted_does_not_authorize(tmp_path, monkeypatch):
    import solspire.proposal_manager as pm

    monkeypatch.setattr(pm, "_DB_PATH", str(tmp_path / "p.db"))
    manager = pm.ProposalManager()
    prop = manager.create_proposal(subject_ref="a", workspace_ref="ws")
    updated = manager.record_decision(
        proposal_id=prop.proposal_id, subject_ref="a", decision="ACCEPTED"
    )
    assert updated.proposal_status == "ACCEPTED"
    assert updated.decision_ref is not None
    assert updated.authorization_ref is None


def test_feedback_cannot_accept(tmp_path, monkeypatch):
    import solspire.proposal_manager as pm

    monkeypatch.setattr(pm, "_DB_PATH", str(tmp_path / "p.db"))
    manager = pm.ProposalManager()
    prop = manager.create_proposal(subject_ref="a", workspace_ref="ws")
    updated, _ = manager.add_feedback(
        proposal_id=prop.proposal_id,
        subject_ref="a",
        workspace_ref="ws",
        observation="lgtm",
    )
    assert updated.proposal_status != "ACCEPTED"
    assert updated.authorization_ref is None


def test_preparation_requires_accepted_and_never_executes(tmp_path, monkeypatch):
    import solspire.proposal_manager as pm

    monkeypatch.setattr(pm, "_DB_PATH", str(tmp_path / "p.db"))
    manager = pm.ProposalManager()
    prop = manager.create_proposal(subject_ref="a", workspace_ref="ws")

    try:
        manager.prepare_execution(
            proposal_id=prop.proposal_id,
            subject_ref="a",
            workspace_ref="ws",
        )
        raise AssertionError("preparation must require ACCEPTED")
    except ValueError as exc:
        assert "ACCEPTED" in str(exc)

    prop = manager.record_decision(
        proposal_id=prop.proposal_id, subject_ref="a", decision="ACCEPTED"
    )
    updated, prep = manager.prepare_execution(
        proposal_id=prop.proposal_id,
        subject_ref="a",
        workspace_ref="ws",
        notes="docs only",
    )

    assert updated.authorization_ref is None
    assert prep.status == "PREPARED"
    assert prep.execution_authorized is False
    assert prep.auto_merge is False
    assert prep.auto_deploy is False
    assert prep.auto_execute is False
    assert prep.pass_spec_ref is None
    assert prep.k15_ref is None
    assert prep.k3_ref is None


def test_preparation_is_subject_and_workspace_bound(tmp_path, monkeypatch):
    import solspire.proposal_manager as pm

    monkeypatch.setattr(pm, "_DB_PATH", str(tmp_path / "p.db"))
    manager = pm.ProposalManager()
    prop = manager.create_proposal(subject_ref="a", workspace_ref="ws-a")
    manager.record_decision(
        proposal_id=prop.proposal_id, subject_ref="a", decision="ACCEPTED"
    )

    try:
        manager.prepare_execution(
            proposal_id=prop.proposal_id,
            subject_ref="b",
            workspace_ref="ws-a",
        )
        raise AssertionError("cross-subject preparation must fail")
    except ValueError as exc:
        assert "not found" in str(exc).lower()

    try:
        manager.prepare_execution(
            proposal_id=prop.proposal_id,
            subject_ref="a",
            workspace_ref="ws-b",
        )
        raise AssertionError("cross-workspace preparation must fail")
    except ValueError as exc:
        assert "workspace" in str(exc).lower()
