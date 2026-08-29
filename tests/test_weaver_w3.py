"""WEAVER-W3 — operator scoping UX proofs."""
from __future__ import annotations

import json
import threading
from http.client import HTTPConnection

from weaver.workbench_view import run_read_only_pipeline
from weaver.workbench_web import make_server
import weaver.workbench_web as wweb
import weaver.workbench_view as wview


def test_unscoped_visible():
    r = run_read_only_pipeline("Investigate Weaver without paths")
    assert r["scope"]["status"] == "UNSCOPED"
    assert r["scope"]["affected_paths"] == []
    assert r["authorization"]["Execution"] == "LOCKED"
    assert r["executed"] is False


def test_path_hints_reach_pipeline():
    r = run_read_only_pipeline(
        "Investigate execution routing",
        affected_paths=["weaver/execution.py", "weaver/transaction.py"],
        symbols=["execute_patch"],
    )
    assert r["scope"]["status"] in ("IN-SCOPE", "OPERATOR-SCOPED", "PLAN-SCOPED")
    assert "weaver/execution.py" in r["scope"]["affected_paths"]
    assert len(r.get("changeset", {}).get("files") or []) >= 1
    assert r["authorization"]["Execution"] == "LOCKED"
    assert r["authorization"]["PatchApproval"] == "NONE"
    # display-only passspec at most
    assert r["authorization"]["PassSpec"] in ("NONE", "DISPLAY_ONLY")


def test_pass_spec_display_does_not_authorize():
    r = run_read_only_pipeline(
        "scoped",
        affected_paths=["weaver/execution.py"],
        pass_spec_display={
            "pass_id": "FAKE",
            "allowed_paths": ["weaver/"],
            "forbidden_paths": ["api/"],
        },
    )
    assert r["authorization"]["Execution"] == "LOCKED"
    assert r["authorization"]["PatchApproval"] == "NONE"
    assert r["executed"] is False
    assert r["authorization"]["PassSpec"] == "DISPLAY_ONLY"


def test_http_analyze_with_paths():
    httpd = make_server("127.0.0.1", 0)
    host, port = httpd.server_address
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        c = HTTPConnection(host, port, timeout=60)
        payload = json.dumps(
            {
                "objective": "Map execution to K3",
                "affected_paths": ["weaver/execution.py"],
                "symbols": ["execute_patch"],
            }
        ).encode()
        c.request("POST", "/api/analyze", body=payload, headers={"Content-Type": "application/json"})
        r = c.getresponse()
        data = json.loads(r.read().decode())
        assert r.status == 200
        assert data["authorization"]["Execution"] == "LOCKED"
        assert data["scope"]["status"] != "UNSCOPED"
        assert data["executed"] is False
    finally:
        httpd.shutdown()


def test_no_mutation_apis():
    for name in ("write_file", "commit_and_push", "apply_patch", "run_transaction", "execute_patch"):
        assert not hasattr(wweb, name)
        assert not hasattr(wview, name)
