from __future__ import annotations


def test_canonical_workspace_is_unique_and_persistent(tmp_path, monkeypatch):
    import solspire.workspace_manager as workspace_mod

    monkeypatch.setattr(workspace_mod, "_DB_PATH", str(tmp_path / "workspace.db"))
    manager = workspace_mod.WorkspaceManager()

    first = manager.get_or_create("subject-a", "Architect Workspace")
    second = manager.get_or_create("subject-a", "Ignored Replacement Name")

    assert first.id == second.id
    assert second.canonical_subject_ref == "subject-a"
    assert second.display_name == "Architect Workspace"
    assert manager.count_for_subject("subject-a") == 1


def test_canonical_workspace_isolated_by_authenticated_subject(tmp_path, monkeypatch):
    import solspire.workspace_manager as workspace_mod

    monkeypatch.setattr(workspace_mod, "_DB_PATH", str(tmp_path / "workspace.db"))
    manager = workspace_mod.WorkspaceManager()

    workspace_a = manager.get_or_create("subject-a")
    workspace_b = manager.get_or_create("subject-b")

    assert workspace_a.id != workspace_b.id
    assert manager.get_for_subject("subject-a").id == workspace_a.id
    assert manager.get_for_subject("subject-b").id == workspace_b.id
    assert manager.count_for_subject("subject-a") == 1
    assert manager.count_for_subject("subject-b") == 1


def test_empty_subject_is_rejected(tmp_path, monkeypatch):
    import solspire.workspace_manager as workspace_mod

    monkeypatch.setattr(workspace_mod, "_DB_PATH", str(tmp_path / "workspace.db"))
    manager = workspace_mod.WorkspaceManager()

    try:
        manager.get_or_create("")
    except ValueError as exc:
        assert "subject" in str(exc).lower()
    else:
        raise AssertionError("empty canonical subject must be rejected")
