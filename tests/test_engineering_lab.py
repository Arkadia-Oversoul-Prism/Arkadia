from __future__ import annotations

from pathlib import Path

from lab.observatory.repository import discover_files
from lab.observatory.snapshot import module_map, route_map
from lab.trajectory.commits import classify_commit, trajectory_model
from lab.canon.loader import load_canon
from lab.graph.relationships import relates
from lab.patterns.structural import detect_patterns


def test_file_discovery_excludes_secret_and_generated_dirs(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "src" / "main.py").write_text("import os\n", encoding="utf-8")
    (tmp_path / ".env").write_text("SECRET=x\n", encoding="utf-8")
    (tmp_path / "node_modules" / "x.js").write_text("x", encoding="utf-8")
    paths = {x["path"] for x in discover_files(str(tmp_path))}
    assert "src/main.py" in paths
    assert ".env" not in paths
    assert "node_modules/x.js" not in paths


def test_python_import_and_route_discovery(tmp_path: Path):
    api = tmp_path / "api"
    api.mkdir()
    (api / "routes.py").write_text(
        "from fastapi import APIRouter\nrouter=APIRouter()\n@router.get('/x')\ndef x(): return {}\n",
        encoding="utf-8",
    )
    modules = module_map(str(tmp_path))
    routes = route_map(str(tmp_path))
    assert modules[0]["kind"] == "router"
    assert modules[0]["imports"] == ["fastapi"]
    assert routes == [{"method":"GET","path":"/x","module":"api/routes.py","handler":"x","auth_boundary":"unknown"}]


def test_trajectory_churn_and_classification():
    commits = [
        {"sha":"2","message":"fix: repair kernel","files_changed":["kernel/jobs.py"]},
        {"sha":"1","message":"feat: add kernel","files_changed":["kernel/jobs.py"]},
        {"sha":"0","message":"refactor kernel","files_changed":["kernel/jobs.py"]},
    ]
    assert classify_commit("fix: repair kernel", ["kernel/jobs.py"])[0] == "fix"
    model = trajectory_model(commits)
    assert model["high_churn"][0]["path"] == "kernel/jobs.py"


def test_canon_loader_is_explicit_and_provenanced(tmp_path: Path):
    (tmp_path / "AGENTS.md").write_text("Human approval is required.\n", encoding="utf-8")
    result = load_canon(str(tmp_path))
    assert result["loaded"] is True
    assert result["sources"][0]["classification"] == "GOVERNANCE"
    assert result["sources"][0]["provenance"]["source_file"] == "AGENTS.md"


def test_relationship_has_provenance():
    rel = relates("commit:1", "modifies", "module:kernel/jobs.py", source="git", evidence=["1", "kernel/jobs.py"], provenance={"git_commit":"1"})
    assert rel.provenance["git_commit"] == "1"
    assert "kernel/jobs.py" in rel.evidence


def test_parallel_execution_pattern_is_evidence_based():
    patterns = detect_patterns([], [], [], [
        {"id":"execution:kernel"}, {"id":"execution:weaver"}
    ], {"high_churn":[]}, {"files":[]})
    assert any(p["type"] == "parallel execution paths" for p in patterns)
    assert all(p["evidence"] for p in patterns)
