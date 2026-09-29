"""M05 — project files stay on existing corpus; rename/copy via store."""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_copy_file_in_store(tmp_path, monkeypatch):
    import solspire.project_store as ps
    # isolate sqlite if path configurable
    db = tmp_path / "t.db"
    if hasattr(ps, "_DB_PATH"):
        monkeypatch.setattr(ps, "_DB_PATH", str(db))
    elif hasattr(ps, "DB_PATH"):
        monkeypatch.setattr(ps, "DB_PATH", str(db))
    # ensure tables
    if hasattr(ps, "ensure_projects_table"):
        ps.ensure_projects_table()
    # create project row if needed
    pid = "proj-m05-test"
    try:
        from solspire import project_manager as pm
        if hasattr(pm, "ensure_projects_table"):
            pm.ensure_projects_table()
    except Exception:
        pass
    # minimal insert via create_file may need project - create_file only needs project_id string
    f = ps.create_file(pid, "note.md", "hello", "text/markdown")
    assert f["name"] == "note.md"
    c = ps.copy_file(f["id"])
    assert c["name"] == "note.md (copy)"
    assert c["id"] != f["id"]
    full = ps.get_file(c["id"])
    assert full and full["content"] == "hello"
    assert full["project_id"] == pid


def test_update_file_supports_rename(tmp_path, monkeypatch):
    import solspire.project_store as ps
    db = tmp_path / "t2.db"
    if hasattr(ps, "_DB_PATH"):
        monkeypatch.setattr(ps, "_DB_PATH", str(db))
    f = ps.create_file("p2", "a.txt", "x")
    ps.update_file(f["id"], "x", name="b.txt")
    got = ps.get_file(f["id"])
    assert got and got["name"] == "b.txt"


def test_frontend_files_use_project_api():
    dash = (ROOT / "web/public_prism/src/pages/ProjectDashboard.tsx").read_text()
    assert "/solspire/projects/${project.id}/files" in dash
    assert "renameFile" in dash
    assert "copyFile" in dash
    assert "Share ref" in dash or "shareRef" in dash
    assert "cross-project Move remains deferred" in dash


def test_copy_route_exists():
    router = (ROOT / "solspire/console_router.py").read_text()
    assert 'files/{file_id}/copy' in router


def test_no_parallel_filesystem_introduced():
    store = (ROOT / "solspire/project_store.py").read_text()
    assert "def copy_file" in store
    # still same project_files table path
    assert "project_files" in store
