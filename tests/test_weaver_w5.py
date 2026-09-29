"""WEAVER-W5 — Project Knowledge OS + workbench."""
from __future__ import annotations

import base64
import json

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from solspire.project_knowledge import (
    build_derived_graph,
    build_knowledge_summary,
    build_project_context_for_weaver,
)
from solspire.weaver_bridge import project_analyze
import solspire.project_knowledge as pk
import solspire.weaver_bridge as wb


def test_knowledge_summary_structure():
    s = build_knowledge_summary("nonexistent-project")
    assert s["project_id"] == "nonexistent-project"
    assert "sources" in s
    assert s["embeddings"]["status"] == "NOT_AVAILABLE"
    assert s["authorization"]["Execution"] == "LOCKED"


def test_derived_graph_provenance():
    g = build_derived_graph("p-x")
    # build_derived_graph is a compatibility wrapper for the bounded semantic
    # graph projection, whose canonical kind is DERIVED_BOUNDED_SEMANTIC.
    assert g["kind"] == "DERIVED_BOUNDED_SEMANTIC"
    assert g["nodes"][0]["type"] == "Project"
    assert all(e.get("classification") for e in g["edges"]) or g["edges"] == []


def test_context_not_auth():
    ctx = build_project_context_for_weaver({"id": "p1", "name": "N", "owner_uid": "u"})
    assert ctx["authorization"]["Execution"] == "LOCKED"
    assert ctx["authorization"]["PassSpec"] == "NONE"


def test_analyze_with_context_locked():
    out = project_analyze(
        {"id": "p1", "name": "N"},
        "Investigate execution",
        affected_paths=["weaver/execution.py"],
    )
    assert out["executed"] is False
    assert out["authorization"]["Execution"] == "LOCKED"
    assert out["project_context"]["authorization"]["Execution"] == "LOCKED" or out["authorization"]["PatchApproval"] == "NONE"


def test_no_mutation_on_modules():
    for mod in (pk, wb):
        for name in ("write_file", "apply_patch", "commit_and_push", "execute_patch", "run_transaction"):
            assert not hasattr(mod, name)


def test_http_knowledge_isolation(monkeypatch, tmp_path):
    # Environment control lives here, not at import time: pytest imports every
    # module before running any test, so an import-time override stays in force
    # for the whole session and repoints the shared project DB for later modules.
    db_path = str(tmp_path / "db.sqlite")
    monkeypatch.setenv("SOLSPIRE_PROJECTS_DB", db_path)
    monkeypatch.setenv("SOLSPIRE_DATA_DIR", str(tmp_path))

    import solspire.project_manager as pm_mod
    import solspire.project_store as store_mod
    from solspire.console_router import router

    monkeypatch.setattr(pm_mod, "_DB_PATH", db_path)
    monkeypatch.setattr(store_mod, "_DB_PATH", db_path)
    app = FastAPI()
    app.include_router(router)

    def b64(d):
        return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()

    def headers(uid):
        return {"Authorization": f"Bearer {b64({'alg':'none'})}.{b64({'user_id': uid})}.s"}

    with TestClient(app) as c:
        r = c.post("/solspire/projects", json={"name": "W5"}, headers=headers("ua"))
        assert r.status_code == 200
        pid = r.json()["project"]["id"]
        r = c.get(f"/solspire/projects/{pid}/knowledge", headers=headers("ua"))
        assert r.status_code == 200
        assert r.json()["embeddings"]["status"] == "NOT_AVAILABLE"
        r = c.get(f"/solspire/projects/{pid}/knowledge/graph", headers=headers("ua"))
        assert r.status_code == 200
        assert r.json()["kind"] == "DERIVED_BOUNDED_SEMANTIC"
        r = c.get(f"/solspire/projects/{pid}/knowledge", headers=headers("ub"))
        assert r.status_code == 404
        r = c.post(
            f"/solspire/projects/{pid}/weaver/analyze",
            json={"objective": "x", "affected_paths": ["weaver/execution.py"]},
            headers=headers("ua"),
        )
        assert r.status_code == 200
        assert r.json()["authorization"]["Execution"] == "LOCKED"
