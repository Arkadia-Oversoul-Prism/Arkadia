"""WEAVER-W4 — operator validation + SolSpire project bridge."""
from __future__ import annotations

import base64
import json
import os
import tempfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from weaver.capabilities import capability_summary, list_capabilities
from weaver.operator_validation import run_all_scenarios, run_scenario
from solspire.weaver_bridge import project_analyze, project_weaver_context


def test_capability_registry_read_only():
    caps = list_capabilities()
    assert any(c["name"] == "engineering_analysis" for c in caps)
    mut = [c for c in caps if c.get("mutation")]
    assert mut and all(c["authority_level"] == "MUTATION" for c in mut)
    s = capability_summary()
    assert "Not authorization" in s["note"] or "not authorization" in s["note"].lower()


def test_operator_validation_scenarios():
    r = run_all_scenarios()
    assert r["mutation"] is False
    assert r["authority"] == "NONE"
    assert r["ok"] is True
    assert len(r["results"]) >= 5


def test_project_context_does_not_authorize():
    proj = {"id": "p1", "name": "Alpha", "owner": "u1", "status": "active"}
    ctx = project_weaver_context(proj)
    assert ctx["authorization"]["Execution"] == "LOCKED"
    assert ctx["authorization"]["PassSpec"] == "NONE"
    out = project_analyze(
        proj,
        "Investigate execution routing",
        affected_paths=["weaver/execution.py"],
    )
    assert out["executed"] is False
    assert out["authorization"]["Execution"] == "LOCKED"
    assert out["authorization"]["PatchApproval"] == "NONE"
    assert out["project_context"]["project_id"] == "p1"


def test_solspire_weaver_routes_owner_isolation():
    tmp = tempfile.mkdtemp(prefix="w4_sol_")
    os.environ["SOLSPIRE_PROJECTS_DB"] = os.path.join(tmp, "db.sqlite")
    os.environ.setdefault("SOLSPIRE_DATA_DIR", tmp)

    import solspire.project_manager as pm_mod
    import solspire.project_store as store_mod
    from solspire.console_router import router as solspire_router

    pm_mod._DB_PATH = store_mod._DB_PATH = os.environ["SOLSPIRE_PROJECTS_DB"]
    app = FastAPI()
    app.include_router(solspire_router)

    def _b64(d):
        return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()

    def token(uid):
        return f"{_b64({'alg': 'none'})}.{_b64({'user_id': uid, 'email': f'{uid}@t.dev'})}.s"

    def headers(uid):
        return {"Authorization": f"Bearer {token(uid)}"}

    with TestClient(app) as c:
        r = c.post("/solspire/projects", json={"name": "W4A"}, headers=headers("user-a"))
        assert r.status_code == 200, r.text
        pid = r.json()["project"]["id"]

        r = c.get(f"/solspire/projects/{pid}/weaver/capabilities", headers=headers("user-a"))
        assert r.status_code == 200
        assert "capabilities" in r.json()

        r = c.post(
            f"/solspire/projects/{pid}/weaver/analyze",
            json={"objective": "Map execution", "affected_paths": ["weaver/execution.py"]},
            headers=headers("user-a"),
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["executed"] is False
        assert body["authorization"]["Execution"] == "LOCKED"

        # Cross-user: 404, no leak
        r = c.get(f"/solspire/projects/{pid}/weaver/capabilities", headers=headers("user-b"))
        assert r.status_code == 404

        r = c.post(
            f"/solspire/projects/{pid}/weaver/analyze",
            json={"objective": "x"},
            headers=headers("user-b"),
        )
        assert r.status_code == 404

        r = c.get(f"/solspire/projects/{pid}/weaver/knowledge-summary", headers=headers("user-a"))
        assert r.status_code == 200
        assert r.json()["authorization"]["Execution"] == "LOCKED"


def test_no_mutation_imports_in_bridge():
    import solspire.weaver_bridge as b
    import weaver.operator_validation as ov
    for mod in (b, ov):
        for name in ("write_file", "commit_and_push", "apply_patch", "run_transaction", "execute_patch"):
            assert not hasattr(mod, name)
