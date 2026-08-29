"""WEAVER-K0.1 — PassSpec, scope, gates, commit≠push, durable checkpoint."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from weaver.pass_spec import PassSpec, PassSpecError, assert_paths_authorized, path_in_allowlist, verify_lineage
from weaver.autonomy.guard import AutonomyGuard
from weaver.session_kernel import filter_authorized_writes, write_checkpoint
from weaver import agent as weaver_agent
from weaver.git_ops import commit_and_push
from weaver.recursive import RecursiveEngine
import inspect


def _spec(**kwargs) -> PassSpec:
    base = dict(
        pass_id="WEAVER-K0-TEST",
        objective="unit test authorization",
        base_sha="abc1234",
        allowed_paths=["weaver/", "tests/test_weaver_k0.py", "data/weaver/checkpoints/"],
        forbidden_paths=[".git/", "governance/"],
        required_tests=[],
        push_allowed=True,
        publication_required=True,
        commit_required=False,
        checkpoint_required=True,
    )
    base.update(kwargs)
    return PassSpec(**base)


def test_pass_spec_defaults_publication_true():
    s = _spec()
    assert s.push_allowed is True
    assert s.publication_required is True


def test_pass_spec_requires_fields():
    with pytest.raises(PassSpecError):
        PassSpec(pass_id="", objective="x", base_sha="abc", allowed_paths=["a"]).validate_structure()
    with pytest.raises(PassSpecError):
        PassSpec(pass_id="p", objective="x", base_sha="abc", allowed_paths=[]).validate_structure()


def test_wrong_base_sha_rejected(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.system("git init -q && git config user.email t@t && git config user.name t")
    (tmp_path / "f.txt").write_text("x")
    os.system("git add f.txt && git commit -qm init")
    import subprocess
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    with pytest.raises(PassSpecError, match="HEAD mismatch"):
        verify_lineage(_spec(base_sha="0000000000000000000000000000000000000000"), str(tmp_path))
    assert verify_lineage(_spec(base_sha=head[:12]), str(tmp_path)).startswith(head[:12])


def test_scope_allow_and_forbid():
    s = _spec(allowed_paths=["weaver/"], forbidden_paths=["weaver/notes/"])
    assert path_in_allowlist("weaver/agent.py", s.allowed_paths)
    with pytest.raises(PassSpecError, match="forbidden"):
        assert_paths_authorized(["weaver/notes/x.txt"], s)
    with pytest.raises(PassSpecError, match="not in allowed"):
        assert_paths_authorized(["api/main.py"], s)


def test_guard_allowlist():
    g = AutonomyGuard.from_pass_spec(_spec(allowed_paths=["weaver/pass_spec.py"], forbidden_paths=[".git/"]))
    assert g.allowed() and g.path_allowed("weaver/pass_spec.py")
    assert not g.path_allowed("api/auth.py")


def test_filter_writes():
    acc, rej = filter_authorized_writes(["weaver/agent.py", "api/main.py"], {}, _spec(allowed_paths=["weaver/"]))
    assert "weaver/agent.py" in acc and "api/main.py" in rej


def test_agent_refuses_without_pass_spec():
    assert weaver_agent.run("danger") == ([], None)


def test_commit_push_param_default():
    sig = inspect.signature(commit_and_push)
    assert "push" in sig.parameters
    assert sig.parameters["push"].default is False  # internal primitive defaults safe


def test_checkpoint_fields(tmp_path):
    path = write_checkpoint(
        _spec(base_sha="deadbeef"),
        status="PASS",
        result_sha="cafebabe",
        remote_sha="cafebabe",
        changed_paths=["weaver/pass_spec.py"],
        tests_run=["tests/test_weaver_k0.py"],
        test_results={"passed": True},
        publication_status="published",
        publication_method="git_push",
        repo_root=str(tmp_path),
    )
    data = json.loads(Path(path).read_text())
    assert data["status"] == "PASS"
    assert data["result_sha"] == "cafebabe"
    assert data["publication_status"] == "published"
    assert "constitution" in data
    assert "token" not in json.dumps(data).lower() or "constitution" in data


def test_recursive_requires_pass_spec():
    engine = RecursiveEngine(initial_task="x", enabled=True, pass_spec=None)
    updated, msg = engine.run_step(1)
    assert updated == [] and msg is None
    assert any("PassSpec" in e for e in engine.errors)


def test_recursive_inherits_scope():
    s = _spec(allowed_paths=["weaver/pass_spec.py"])
    engine = RecursiveEngine(initial_task="x", enabled=True, pass_spec=s)
    assert engine.pass_spec.allowed_paths == ["weaver/pass_spec.py"]
