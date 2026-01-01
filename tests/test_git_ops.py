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
    calls = []

    def fake_run(cmd, capture_output=False, text=False, check=True):
        calls.append(cmd)
        # simulate staged files, commit and push succeed
        if cmd[:4] == ["git", "diff", "--staged", "--name-only"]:
            return DummyCompleted(stdout="file.txt\n")
        return DummyCompleted(stdout="", returncode=0)

    monkeypatch.setenv('REPO_ROOT', '.')
    monkeypatch.setattr(subprocess, 'run', fake_run)
    ok = git_ops.commit_and_push("msg", paths=["."], meta={'engine_cycle': 5})
    assert ok is True
    # verify commit message contained metadata (ts and engine_cycle)
    commit_cmds = [c for c in calls if len(c) >= 3 and c[0] == 'git' and c[1] == 'commit']
    assert commit_cmds
    commit_cmd = commit_cmds[-1]
    # find -m value
    assert '-m' in commit_cmd
    mindex = commit_cmd.index('-m')
    full_msg = commit_cmd[mindex + 1]
    assert 'ts=' in full_msg
    assert 'engine_cycle=5' in full_msg


def test_commit_and_push_allowed_extensions_refused(monkeypatch, tmp_path):
    # Attempt to commit a .txt file when only .py is allowed should be refused
    def fake_run(cmd, capture_output=False, text=False, check=True):
        # if diff --staged, return our .txt file
        if cmd[:4] == ["git", "diff", "--staged", "--name-only"]:
            return DummyCompleted(stdout="evil.txt\n")
        return DummyCompleted(stdout="", returncode=0)

    monkeypatch.setenv('REPO_ROOT', str(tmp_path))
    monkeypatch.setenv('COMMIT_FILE_EXT_WHITELIST', '.py')
    # create file for size calculation
    file = tmp_path / "evil.txt"
    file.write_text("hello")
    monkeypatch.setattr(subprocess, 'run', fake_run)
    ok = git_ops.commit_and_push("msg", paths=[str(file)])
    assert ok is False


def test_commit_and_push_max_size_refused(monkeypatch, tmp_path):
    # create a big file and attempt to commit with low max size
    big_file = tmp_path / 'big.bin'
    big_file.write_bytes(b"0" * 200)

    def fake_run(cmd, capture_output=False, text=False, check=True):
        if cmd[:4] == ["git", "diff", "--staged", "--name-only"]:
            return DummyCompleted(stdout=f"{big_file.name}\n")
        return DummyCompleted(stdout="", returncode=0)

    monkeypatch.setenv('REPO_ROOT', str(tmp_path))
    monkeypatch.setenv('REPO_MAX_COMMIT_SIZE', '100')
    monkeypatch.setattr(subprocess, 'run', fake_run)
    ok = git_ops.commit_and_push("msg", paths=[str(big_file)])
    assert ok is False
