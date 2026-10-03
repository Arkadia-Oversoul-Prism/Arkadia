from __future__ import annotations

import pytest

from solspire.project_execution_boundary import (
    BoundaryError,
    build_container_argv,
    require_reviewed_patch,
    safe_relative_path,
)


def test_container_defaults_deny_network_and_harden_process(tmp_path):
    argv = build_container_argv(
        image="registry.example/arkadia-agent:sha256-abc123",
        workspace=tmp_path,
        command=("/usr/bin/python", "-c", "print('ok')"),
    )
    assert "--network=none" in argv
    assert "--read-only" in argv
    assert "--cap-drop=ALL" in argv
    assert "--security-opt=no-new-privileges:true" in argv
    assert "--pids-limit" in argv and "128" in argv
    assert "--memory" in argv and "512m" in argv
    assert "--cpus" in argv and "1.0" in argv
    assert "--user" in argv and "65532:65532" in argv
    assert "shell" not in argv


def test_container_rejects_missing_workspace(tmp_path):
    with pytest.raises((BoundaryError, FileNotFoundError)):
        build_container_argv(
            image="agent:1", workspace=tmp_path / "missing", command=("true",)
        )


@pytest.mark.parametrize("path", ["../secret", "/etc/passwd", "a/../../secret", "C:/secret", ""])
def test_path_escape_is_rejected(path):
    with pytest.raises(BoundaryError):
        safe_relative_path(path)


def test_review_gate_rejects_unapproved_patch():
    with pytest.raises(BoundaryError, match="explicit human approval"):
        require_reviewed_patch(
            approved=False, expected_base_digest="abc", observed_base_digest="abc",
            changed_paths=("README.md",), allowed_paths=("README.md",),
        )


def test_review_gate_rejects_stale_base():
    with pytest.raises(BoundaryError, match="base changed"):
        require_reviewed_patch(
            approved=True, expected_base_digest="old", observed_base_digest="new",
            changed_paths=("README.md",), allowed_paths=("README.md",),
        )


def test_review_gate_rejects_paths_outside_approved_allowlist():
    with pytest.raises(BoundaryError, match="allowlist"):
        require_reviewed_patch(
            approved=True, expected_base_digest="same", observed_base_digest="same",
            changed_paths=("src/main.py", "secrets/token.txt"),
            allowed_paths=("src/main.py",),
        )


def test_review_gate_accepts_only_approved_current_patch():
    assert require_reviewed_patch(
        approved=True, expected_base_digest="same", observed_base_digest="same",
        changed_paths=("src/main.py",), allowed_paths=("src/main.py",),
    ) == ("src/main.py",)
