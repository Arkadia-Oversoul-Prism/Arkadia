"""WEAVER-K11 — evidence-grounded engineering plan proofs."""
from __future__ import annotations

import subprocess

from weaver.engineering_plan import (
    build_engineering_plan,
    engineering_plan_to_k3,
    review_engineering_plan,
)
from weaver.pass_spec import PassSpec
from weaver.plan import PlanError
import weaver.engineering_plan as ep_mod


def _repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "weaver").mkdir()
    (tmp_path / "weaver" / "x.py").write_text("def f():\n    return 1\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text("import weaver.x\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()


def _spec(head, **kw):
    base = dict(
        pass_id="K11",
        objective="plan",
        base_sha=head,
        allowed_paths=["weaver/"],
        forbidden_paths=["api/"],
        non_goals=["product"],
    )
    base.update(kw)
    return PassSpec(**base)


def test_deterministic_plan(tmp_path):
    head = _repo(tmp_path)
    a = build_engineering_plan("improve x", pass_spec=_spec(head), affected_path_hints=["weaver/x.py"], repo_root=str(tmp_path))
    b = build_engineering_plan("improve x", pass_spec=_spec(head), affected_path_hints=["weaver/x.py"], repo_root=str(tmp_path))
    assert a.plan_id == b.plan_id
    assert a.affected_paths == b.affected_paths
    assert a.implementation_steps == b.implementation_steps


def test_facts_preserved(tmp_path):
    _repo(tmp_path)
    p = build_engineering_plan("x", repo_root=str(tmp_path))
    assert p.facts
    assert all(f.get("kind") == "FACT" for f in p.facts)
    assert p.authorization["current_pass_authorized"] is False
    assert p.approval["approved"] is False


def test_out_of_scope(tmp_path):
    head = _repo(tmp_path)
    p = build_engineering_plan(
        "touch api",
        pass_spec=_spec(head),
        affected_path_hints=["api/main.py"],
        repo_root=str(tmp_path),
    )
    assert p.scope_status == "OUT_OF_SCOPE"


def test_to_k3_rejects_out_of_scope(tmp_path):
    head = _repo(tmp_path)
    p = build_engineering_plan(
        "api",
        pass_spec=_spec(head),
        affected_path_hints=["api/main.py"],
        repo_root=str(tmp_path),
    )
    try:
        engineering_plan_to_k3(p, _spec(head))
        assert False, "expected PlanError"
    except PlanError as e:
        assert "OUT_OF_SCOPE" in str(e)


def test_to_k3_in_scope(tmp_path):
    head = _repo(tmp_path)
    p = build_engineering_plan(
        "weaver",
        pass_spec=_spec(head),
        affected_path_hints=["weaver/x.py"],
        repo_root=str(tmp_path),
    )
    k3 = engineering_plan_to_k3(p, _spec(head))
    assert k3.approved is False
    assert "weaver/x.py" in k3.proposed_files


def test_no_execute_api():
    for name in ("write_file", "commit_and_push", "run_transaction", "execute"):
        assert not hasattr(ep_mod, name)


def test_review_bundle(tmp_path):
    head = _repo(tmp_path)
    p = build_engineering_plan("obj", pass_spec=_spec(head), affected_path_hints=["weaver/"], repo_root=str(tmp_path))
    b = review_engineering_plan(p)
    assert "objective" in b
    assert b.get("approval") is False
