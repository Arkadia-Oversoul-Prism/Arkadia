"""R2 — SolSpire mutation-path closure invariants."""
from __future__ import annotations


def test_direct_github_commit_is_truthfully_unavailable():
    from solspire.tools_github import commit_file

    result = commit_file(
        "Arkadia-Oversoul-Prism",
        "Arkadia",
        "README.md",
        "should never be written",
        "test: should never commit",
    )

    assert result["ok"] is False
    assert result["status"] == "NOT_AVAILABLE"
    assert result["mutation_path"] == "NONE"
    assert "Weaver" in result["error"]
    assert "K15" in result["error"]
    assert "K3" in result["error"]


def test_filesystem_write_is_allowed_outside_git_worktree(tmp_path, monkeypatch):
    import solspire.tools_fs as tools_fs

    monkeypatch.setattr(tools_fs, "_WORKSPACE", tmp_path.resolve())
    result = tools_fs.write_file("notes/example.txt", "workspace-only")

    assert result["ok"] is True
    assert (tmp_path / "notes/example.txt").read_text() == "workspace-only"


def test_filesystem_write_is_blocked_inside_git_worktree(tmp_path, monkeypatch):
    import solspire.tools_fs as tools_fs

    monkeypatch.setattr(tools_fs, "_WORKSPACE", tmp_path.resolve())
    (tmp_path / ".git").mkdir()

    result = tools_fs.write_file("src/example.py", "should never be written")

    assert result["ok"] is False
    assert result["status"] == "BLOCKED"
    assert result["mutation_path"] == "NONE"
    assert "Weaver" in result["error"]
    assert not (tmp_path / "src/example.py").exists()


def test_filesystem_delete_is_blocked_inside_git_worktree(tmp_path, monkeypatch):
    import solspire.tools_fs as tools_fs

    monkeypatch.setattr(tools_fs, "_WORKSPACE", tmp_path.resolve())
    (tmp_path / ".git").mkdir()
    target = tmp_path / "existing.txt"
    target.write_text("preserve")

    result = tools_fs.delete_file("existing.txt")

    assert result["ok"] is False
    assert result["status"] == "BLOCKED"
    assert result["mutation_path"] == "NONE"
    assert target.exists()


def test_r2_read_only_github_tools_remain_exported():
    from solspire import tools_github

    assert "list_repos" in tools_github.__all__
    assert "get_tree" in tools_github.__all__
    assert "read_file" in tools_github.__all__
    assert "commit_file" in tools_github.__all__

    # Compatibility seam is retained, but it is a fail-closed adapter rather
    # than an engineering mutation capability.
    assert "httpx.put" not in tools_github.commit_file.__code__.co_names
