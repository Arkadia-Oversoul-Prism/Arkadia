"""WEAVER-W2 — browser cockpit proofs (stdlib HTTP)."""
from __future__ import annotations

import json
import threading
from http.client import HTTPConnection

from weaver.workbench_web import make_server, HTML
import weaver.workbench_web as wweb


def test_html_contains_governance():
    assert "K3 ONLY" in HTML
    assert "READ-ONLY ANALYSIS" in HTML
    assert "EXECUTED" in HTML
    assert "FACTS" in HTML and "INFERENCES" in HTML and "UNKNOWN" in HTML


def test_server_observatory_and_analyze():
    httpd = make_server("127.0.0.1", 0)
    host, port = httpd.server_address
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        c = HTTPConnection(host, port, timeout=30)
        c.request("GET", "/api/observatory")
        r = c.getresponse()
        body = json.loads(r.read().decode())
        assert r.status == 200
        assert body["authority"]["Execution"] == "LOCKED"
        assert body["authority"]["PassSpec"] == "NONE"
        assert body["authority"]["Mutation path"] == "K3 ONLY"
        assert body["repository"]["head_sha"]

        c.request("GET", "/")
        r = c.getresponse()
        html = r.read().decode()
        assert r.status == 200
        assert "WEAVER COCKPIT" in html

        payload = json.dumps({"objective": "Explain Weaver architecture layers"}).encode()
        c.request("POST", "/api/analyze", body=payload, headers={"Content-Type": "application/json"})
        r = c.getresponse()
        data = json.loads(r.read().decode())
        assert r.status == 200
        assert data["executed"] is False
        assert data["authorization"]["Execution"] == "LOCKED"
        assert data["patch"]["EXECUTED"] is False
        assert "analysis" in data and "plan" in data

        c.request("GET", "/api/last")
        last = json.loads(c.getresponse().read().decode())
        assert last.get("objective")
    finally:
        httpd.shutdown()


def test_no_mutation_on_web_module():
    for name in ("write_file", "commit_and_push", "apply_patch", "run_transaction", "execute_patch"):
        assert not hasattr(wweb, name)
