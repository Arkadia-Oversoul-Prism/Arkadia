"""R2 — SolSpire direct GitHub mutation closure invariants."""
from __future__ import annotations

import inspect


def test_github_tool_no_longer_performs_contents_api_writes():
    import solspire.tools_github as gh

    src = inspect.getsource(gh)
    assert "httpx.put(" not in src
    assert "contents_url" not in src
    assert "base64.b64encode" not in src
    assert "commit_file" not in gh.__all__


def test_legacy_commit_file_fails_closed_without_network_write():
    import solspire.tools_github as gh

    result = gh.commit_file(
        "Arkadia-Oversoul-Prism",
        "Arkadia",
        "example.txt",
        "must not be written",
        "test",
        "main",
    )
    assert result["ok"] is False
    assert result["code"] == "MUTATION_DISABLED"
    assert "K15" in result["error"] and "K3" in result["error"]


def test_read_only_github_surface_remains_exported():
    import solspire.tools_github as gh

    assert set(gh.__all__) == {"list_repos", "get_tree", "read_file", "get_repo_info"}
