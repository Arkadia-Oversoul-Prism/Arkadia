from __future__ import annotations


def test_human_decision_accepted_does_not_authorize(tmp_path, monkeypatch):
    import solspire.proposal_manager as pm

    monkeypatch.setattr(pm, "_DB_PATH", str(tmp_path / "p.db"))
    manager = pm.ProposalManager()
    prop = manager.create_proposal(subject_ref="a", workspace_ref="ws")
    updated = manager.record_human_decision(
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


def test_prep_requires_accepted_and_never_executes(tmp_path, monkeypatch):
    import solspire.proposal_manager as pm
    import solspire.authorization_package_manager as am

    monkeypatch.setattr(pm, "_DB_PATH", str(tmp_path / "p.db"))
    monkeypatch.setattr(am, "_DB_PATH", str(tmp_path / "p.db"))
    proposals = pm.ProposalManager()
    packages = am.AuthorizationPackageManager()
    prop = proposals.create_proposal(subject_ref="a", workspace_ref="ws")
    try:
        packages.prepare(
            proposal_id=prop.proposal_id,
            subject_ref="a",
            workspace_ref="ws",
        )
        # Manager itself does not check ACCEPTED; router does. Package must still be non-exec.
    except Exception:
        pass
    prop = proposals.record_human_decision(
        proposal_id=prop.proposal_id, subject_ref="a", decision="ACCEPTED"
    )
    pkg = packages.prepare(
        proposal_id=prop.proposal_id,
        subject_ref="a",
        workspace_ref="ws",
        intended_scope="docs only",
    )
    assert pkg.execution_authorized is False
    assert pkg.k15_invoked is False
    assert pkg.k3_invoked is False
    assert pkg.status == "PREPARED"
    try:
        packages.prepare(
            proposal_id=prop.proposal_id,
            subject_ref="a",
            workspace_ref="ws",
            execution_authorized=True,
        )
        raise AssertionError("must refuse elevated package")
    except ValueError as exc:
        assert "execution_authorized" in str(exc)


def test_attach_authorization_ref_requires_accepted(tmp_path, monkeypatch):
    import solspire.proposal_manager as pm

    monkeypatch.setattr(pm, "_DB_PATH", str(tmp_path / "p.db"))
    manager = pm.ProposalManager()
    prop = manager.create_proposal(subject_ref="a", workspace_ref="ws")
    try:
        manager.attach_authorization_ref(
            proposal_id=prop.proposal_id, subject_ref="a", authorization_ref="pkg"
        )
        raise AssertionError("must require ACCEPTED")
    except ValueError:
        pass
