"""Project canvas snapshots stay inside the server-derived read-only workspace."""
from pathlib import Path

from solspire import project_store
from solspire.project_canvas import prepare_project_workspace


def test_snapshot_materializes_only_safe_canonical_files(monkeypatch, tmp_path):
    rows = [
        {"id": "file-1", "name": "docs/plan.md"},
        {"id": "file-2", "name": "../escape.md"},
        {"id": "file-3", "name": "/tmp/escape.txt"},
        {"id": "file-4", "name": "."},
    ]
    content_by_id = {
        "file-1": {"id": "file-1", "project_id": "project-uuid", "content": "# Eden plan\n", "name": "docs/plan.md"},
        "file-2": {"id": "file-2", "project_id": "project-uuid", "content": "unsafe", "name": "../escape.md"},
        "file-3": {"id": "file-3", "project_id": "project-uuid", "content": "unsafe", "name": "/tmp/escape.txt"},
        "file-4": {"id": "file-4", "project_id": "project-uuid", "content": "unsafe", "name": "."},
    }
    monkeypatch.setattr(project_store, "list_files", lambda project_id: rows)
    monkeypatch.setattr(project_store, "get_file", lambda file_id: content_by_id.get(file_id))

    result = prepare_project_workspace("private-user", "project-uuid", base_root=tmp_path / "canvas")
    root = Path(result["root"])

    assert result["source"] == "canonical_project_files"
    assert result["read_only"] is True
    assert result["seeded_files"] == ["docs/plan.md"]
    assert len(result["skipped_files"]) == 3
    assert (root / "docs/plan.md").read_text() == "# Eden plan\n"
    assert not (tmp_path / "escape.md").exists()
    assert "private-user" not in str(root)
    assert "project-uuid" not in str(root)


def test_snapshot_refresh_removes_stale_files(monkeypatch, tmp_path):
    rows = [{"id": "file-1", "name": "one.txt"}]
    content_by_id = {"file-1": {"id": "file-1", "project_id": "p1", "content": "one"}}
    monkeypatch.setattr(project_store, "list_files", lambda project_id: rows)
    monkeypatch.setattr(project_store, "get_file", lambda file_id: content_by_id.get(file_id))

    first = prepare_project_workspace("u1", "p1", base_root=tmp_path / "canvas")
    root = Path(first["root"])
    assert (root / "one.txt").exists()

    rows[:] = [{"id": "file-2", "name": "two.txt"}]
    content_by_id["file-2"] = {"id": "file-2", "project_id": "p1", "content": "two"}
    second = prepare_project_workspace("u1", "p1", base_root=tmp_path / "canvas")

    assert second["root"] == first["root"]
    assert not (root / "one.txt").exists()
    assert (root / "two.txt").read_text() == "two"

def test_existing_lab_session_schema_migrates_project_ref_additively(monkeypatch, tmp_path):
    import sqlite3

    from lab.engineering_lab import store as store_module
    from lab.engineering_lab.models import AgentSession

    database = tmp_path / "lab.sqlite"
    connection = sqlite3.connect(database)
    connection.execute(
        """CREATE TABLE el_sessions (
            session_id TEXT PRIMARY KEY,
            subject_ref TEXT NOT NULL,
            workspace_ref TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            state TEXT NOT NULL,
            objective TEXT NOT NULL DEFAULT '',
            repository_ref TEXT,
            authorization_ref TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )"""
    )
    connection.commit()
    connection.close()
    monkeypatch.setattr(store_module, "_DB_PATH", str(database))

    store = store_module.EngineeringLabStore()
    assert store.list_sessions("subject-a") == []
    session = AgentSession(
        session_id="SES-project-test",
        subject_ref="subject-a",
        workspace_ref="workspace-a",
        agent_id="AGT-project-test",
        state="PROPOSED",
        objective="inspect project files",
        project_ref="project-a",
    )
    store.create_session(session)

    stored = store.get_session("SES-project-test", "subject-a")
    assert stored is not None
    assert stored["project_ref"] == "project-a"
