import subprocess
from unittest import mock
from weaver import git_ops


class DummyCompleted:
    def __init__(self, stdout="", returncode=0):
        self.stdout = stdout
        self.returncode = returncode


def test_commit_and_push_no_staged(monkeypatch):
    calls = []

    def fake_run(cmd, capture_output=False, text=False, check=True):
        calls.append(cmd)
        if cmd[:3] == ["git", "diff", "--staged"] or cmd[:3] == ["git", "diff", "--staged", "--name-only"]:
            return DummyCompleted(stdout="")
        return DummyCompleted(stdout="", returncode=0)

    monkeypatch.setenv('REPO_ROOT', '.')
    monkeypatch.setattr(subprocess, 'run', fake_run)
    ok = git_ops.commit_and_push("msg")
    assert ok is False


def test_commit_and_push_success(monkeypatch):
    def fake_run(cmd, capture_output=False, text=False, check=True):
        # simulate staged files, commit and push succeed
        if cmd[:4] == ["git", "diff", "--staged", "--name-only"]:
            return DummyCompleted(stdout="file.txt\n")
        return DummyCompleted(stdout="", returncode=0)

    monkeypatch.setenv('REPO_ROOT', '.')
    monkeypatch.setattr(subprocess, 'run', fake_run)
    ok = git_ops.commit_and_push("msg", paths=["."])
    assert ok is True
