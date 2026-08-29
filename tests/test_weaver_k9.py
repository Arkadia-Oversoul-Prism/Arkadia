"""WEAVER-K9 — evidence-bound analysis proofs."""
from __future__ import annotations

import subprocess

from weaver.analysis import (
    AnalysisResultKind,
    analyze_objective,
    analysis_to_plan,
)
from weaver.pass_spec import PassSpec
from weaver.plan import PlanError
import weaver.analysis as analysis_mod


def _repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "README").write_text("x")
    (tmp_path / "weaver").mkdir()
    (tmp_path / "weaver" / "x.py").write_text("#")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()


def _spec(head, **kw):
    base = dict(
        pass_id="K9",
        objective="analyze",
        base_sha=head,
        allowed_paths=["weaver/"],
        forbidden_paths=["api/"],
        non_goals=["product"],
    )
    base.update(kw)
    return PassSpec(**base)


def test_no_pass_spec_read_only(tmp_path):
    _repo(tmp_path)
    a = analyze_objective("inspect weaver modules", repo_root=str(tmp_path))
    assert a.authorization["current_pass_authorized"] is False
    assert a.result_kind == AnalysisResultKind.ANALYSIS_READY.value
    assert a.repository["head_sha"]


def test_facts_inferences_unknowns(tmp_path):
    _repo(tmp_path)
    a = analyze_objective("x", repo_root=str(tmp_path))
    assert a.evidence["facts"]
    assert a.evidence["inferences"]
    assert a.evidence["unknowns"]
    assert all(f["kind"] == "FACT" for f in a.evidence["facts"])


def test_out_of_scope_paths(tmp_path):
    head = _repo(tmp_path)
    a = analyze_objective(
        "change api",
        pass_spec=_spec(head),
        affected_path_hints=["api/main.py"],
        repo_root=str(tmp_path),
    )
    assert a.result_kind in (
        AnalysisResultKind.PROTECTED_BOUNDARY_CONFLICT.value,
        AnalysisResultKind.BLOCKED.value,
    )


def test_forbidden_paths(tmp_path):
    head = _repo(tmp_path)
    a = analyze_objective(
        "x",
        pass_spec=_spec(head),
        affected_path_hints=["api/auth.py"],
        repo_root=str(tmp_path),
    )
    assert a.result_kind == AnalysisResultKind.PROTECTED_BOUNDARY_CONFLICT.value


def test_plan_subordinate_to_spec(tmp_path):
    head = _repo(tmp_path)
    a = analyze_objective(
        "improve weaver",
        pass_spec=_spec(head),
        affected_path_hints=["weaver/x.py"],
        repo_root=str(tmp_path),
    )
    assert a.result_kind == AnalysisResultKind.ANALYSIS_READY.value
    p = analysis_to_plan(a, _spec(head))
    assert p.approved is False


def test_no_execute_apis():
    for name in ("write_file", "commit_and_push", "run_transaction", "execute_approved_proposal"):
        assert not hasattr(analysis_mod, name)


def test_continuation_state_recorded(tmp_path):
    _repo(tmp_path)
    a = analyze_objective("x", repo_root=str(tmp_path))
    assert a.continuation_state in ("CURRENT", "STALE", "MISSING", "INVALID")


def test_protected_product_in_objective(tmp_path):
    head = _repo(tmp_path)
    a = analyze_objective(
        "rewrite SolSpire console",
        pass_spec=_spec(head),
        repo_root=str(tmp_path),
    )
    assert a.result_kind == AnalysisResultKind.PROTECTED_BOUNDARY_CONFLICT.value
