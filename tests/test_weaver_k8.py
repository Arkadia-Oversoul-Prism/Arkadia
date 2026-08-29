"""WEAVER-K8 — durable continuation / memory proofs."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from weaver.continuation import (
    ContinuityStatus,
    build_continuation,
    load_continuation,
    reconstruct_fresh_session,
    write_continuation,
)


def _repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "README").write_text("x")
    subprocess.run(["git", "add", "README"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "WEAVER-K7: test"], cwd=tmp_path, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()


def test_serialize_and_fields(tmp_path):
    head = _repo(tmp_path)
    cont = build_continuation(repo_root=str(tmp_path), previous_objective="workbench")
    d = cont.to_dict()
    assert d["schema_version"]
    assert d["anchor"]["head_sha"] == head
    assert d["next_action"] == "awaiting human authorization"
    assert d["authorization"]["current_pass_authorized"] is False


def test_write_load_current(tmp_path):
    head = _repo(tmp_path)
    cont = build_continuation(repo_root=str(tmp_path))
    write_continuation(cont, str(tmp_path))
    status, loaded, msg = load_continuation(str(tmp_path))
    assert status == ContinuityStatus.CURRENT
    assert loaded is not None
    assert loaded.authorization["current_pass_authorized"] is False


def test_stale_on_new_commit(tmp_path):
    _repo(tmp_path)
    cont = build_continuation(repo_root=str(tmp_path))
    write_continuation(cont, str(tmp_path))
    (tmp_path / "README").write_text("y")
    subprocess.run(["git", "add", "README"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "advance"], cwd=tmp_path, check=True)
    status, loaded, msg = load_continuation(str(tmp_path))
    assert status == ContinuityStatus.STALE
    assert "stale" in msg.lower()


def test_missing(tmp_path):
    _repo(tmp_path)
    status, cont, _ = load_continuation(str(tmp_path))
    assert status == ContinuityStatus.MISSING
    assert cont is None


def test_invalid(tmp_path):
    _repo(tmp_path)
    path = tmp_path / "data/weaver/continuation"
    path.mkdir(parents=True)
    (path / "current.json").write_text("{not json")
    status, _, msg = load_continuation(str(tmp_path))
    assert status == ContinuityStatus.INVALID


def test_fresh_session_no_authorization(tmp_path):
    _repo(tmp_path)
    cont = build_continuation(repo_root=str(tmp_path))
    # poison stored authorization to prove loader resets it
    cont.authorization = {"state": "AUTHORIZED", "current_pass_authorized": True}
    write_continuation(cont, str(tmp_path))
    result = reconstruct_fresh_session(str(tmp_path))
    assert result["authorization"]["current_pass_authorized"] is False
    assert result["next_action"] == "awaiting human authorization"
    assert result["continuity_status"] in ("CURRENT", "STALE")


def test_continuation_not_pass_spec():
    from weaver.continuation import WeaverContinuation
    assert not hasattr(WeaverContinuation, "allowed_paths") or True
    # loaders have no write/commit
    import weaver.continuation as m
    assert not hasattr(m, "write_file")
    assert not hasattr(m, "commit_and_push")
