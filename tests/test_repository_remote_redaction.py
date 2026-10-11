from __future__ import annotations

import subprocess

import pytest

from lab.observatory.git import _redact_remote_url, repository_state


@pytest.mark.parametrize(
    ("remote", "expected"),
    [
        (
            "https://alice:synthetic-token@example.invalid/Arkadia/repo.git",
            "https://example.invalid/Arkadia/repo.git",
        ),
        (
            "ssh://deploy:synthetic-token@example.invalid:2222/Arkadia/repo.git",
            "ssh://example.invalid:2222/Arkadia/repo.git",
        ),
        ("https://example.invalid/Arkadia/repo.git", "https://example.invalid/Arkadia/repo.git"),
        ("git@example.invalid:Arkadia/repo.git", "example.invalid:Arkadia/repo.git"),
        ("https://example.invalid/path?contact=alice@example.invalid", "https://example.invalid/path?contact=alice@example.invalid"),
    ],
)
def test_remote_userinfo_is_removed_without_rewriting_safe_remotes(remote: str, expected: str):
    assert _redact_remote_url(remote) == expected


def test_malformed_credential_bearing_remote_fails_closed():
    value = _redact_remote_url("https://alice:synthetic-token@")
    assert "alice" not in (value or "")
    assert "synthetic-token" not in (value or "")


def test_repository_state_never_exposes_remote_userinfo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "remote",
            "add",
            "origin",
            "https://alice:synthetic-token@example.invalid/Arkadia/repo.git",
        ],
        check=True,
    )

    state = repository_state(str(tmp_path))

    assert state["remote"] == "https://example.invalid/Arkadia/repo.git"
    assert "alice" not in repr(state)
    assert "synthetic-token" not in repr(state)
