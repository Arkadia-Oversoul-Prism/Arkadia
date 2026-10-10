#!/usr/bin/env python3
"""Capture and reconcile the live canonical Render runtime against source OpenAPI.

Safe by design: only GET/OPTIONS probes are issued. No mutation endpoints are called.
Writes a complete OpenAPI path/method reconciliation plus representative UI/auth probes.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = os.environ.get("ARKADIA_CANONICAL_BASE_URL", "https://arkadia-qzu4.onrender.com").rstrip("/")
EXPECTED = os.environ.get("EXPECTED_REVISION", "").strip()
WAIT_FOR_REVISION = os.environ.get("WAIT_FOR_REVISION", "0") == "1"
OUT = Path(os.environ.get("RECONCILIATION_OUT", "artifacts/render-reconciliation"))
OUT.mkdir(parents=True, exist_ok=True)


def request(path: str, *, accept: str = "application/json", authorization: str | None = None,
            origin: str | None = None, method: str = "GET") -> dict:
    headers = {"Accept": accept, "User-Agent": "Arkadia-Render-Reconciliation/1.0"}
    if authorization is not None:
        headers["Authorization"] = authorization
    if origin is not None:
        headers["Origin"] = origin
    req = urllib.request.Request(BASE + path, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            body = response.read()
            return {"status": response.status, "content_type": response.headers.get("Content-Type", ""),
                    "allow_origin": response.headers.get("Access-Control-Allow-Origin"),
                    "body": body, "text": body.decode("utf-8", errors="replace")}
    except urllib.error.HTTPError as exc:
        body = exc.read()
        return {"status": exc.code, "content_type": exc.headers.get("Content-Type", ""),
                "allow_origin": exc.headers.get("Access-Control-Allow-Origin"),
                "body": body, "text": body.decode("utf-8", errors="replace")}
    except Exception as exc:
        return {"status": None, "content_type": "", "allow_origin": None,
                "body": b"", "text": "", "error": f"{type(exc).__name__}: {exc}"}


def write_json(name: str, value: object) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def methods(document: dict) -> dict[str, list[str]]:
    result = {}
    for path, path_item in document.get("paths", {}).items():
        result[path] = sorted(k.upper() for k, v in path_item.items()
                              if k.lower() in {"get", "post", "put", "patch", "delete", "options", "head", "trace"}
                              and isinstance(v, dict))
    return result


def source_openapi() -> dict:
    # Python sets sys.path[0] to scripts/ when this file is invoked by path.
    # Add the repository root explicitly so the canonical api package resolves.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    # Import the repository composition root, not a hand-maintained route list.
    os.environ.setdefault("ENVIRONMENT", "development")
    os.environ.setdefault("SOVEREIGN_KEY", "ci-only-nonproduction-placeholder")
    os.environ.setdefault("CORS_ALLOWED_ORIGINS", "https://arkadia-qzu4.onrender.com")
    from api.main import app
    return app.openapi()


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    source_doc = source_openapi()
    source_map = methods(source_doc)
    write_json("source-openapi.json", source_doc)
    write_json("source-endpoints.json", source_map)

    version = request("/api/version")
    if WAIT_FOR_REVISION:
        deadline = time.monotonic() + 1800
        while time.monotonic() < deadline:
            try:
                payload = json.loads(version["text"])
            except Exception:
                payload = {}
            if version["status"] == 200 and payload.get("source_revision") == EXPECTED:
                break
            time.sleep(15)
            version = request("/api/version")
    try:
        version_payload = json.loads(version["text"])
    except Exception:
        version_payload = {}

    live_doc_result = request("/openapi.json")
    try:
        live_doc = json.loads(live_doc_result["text"])
    except Exception:
        live_doc = {}
    live_map = methods(live_doc) if live_doc else {}
    write_json("live-openapi.json", live_doc if live_doc else {
        "http_status": live_doc_result["status"], "body": live_doc_result["text"],
        "error": live_doc_result.get("error")
    })
    write_json("live-endpoints.json", live_map)

    all_paths = sorted(set(source_map) | set(live_map))
    endpoint_rows = []
    for path in all_paths:
        source_methods = source_map.get(path, [])
        live_methods = live_map.get(path, [])
        endpoint_rows.append({
            "path": path,
            "source_methods": source_methods,
            "live_methods": live_methods,
            "verdict": ("MATCH" if source_methods == live_methods else
                        "SOURCE_ONLY" if not live_methods else
                        "LIVE_ONLY" if not source_methods else "METHOD_DRIFT")
        })
    write_json("endpoint-reconciliation.json", endpoint_rows)

    probes = {}
    for path, accept in [
        ("/", "text/html"),
        ("/operator", "text/html"),
        ("/n-atlas-lab", "text/html"),
        ("/n-atlas-tester", "text/html"),
        ("/solariun/opportunity-radar", "text/html"),
        ("/api/heartbeat", "application/json"),
        ("/api/version", "application/json"),
        ("/openapi.json", "application/json"),
        ("/api/__arkadia_reconciliation_missing_route__", "application/json"),
    ]:
        result = request(path, accept=accept)
        probes[path] = {k: v for k, v in result.items() if k not in {"body", "text"}}
        if path in {"/", "/operator", "/n-atlas-lab", "/n-atlas-tester", "/solariun/opportunity-radar"}:
            probes[path]["looks_like_html"] = "text/html" in result.get("content_type", "").lower() and "<html" in result.get("text", "").lower()
        if path in {"/api/heartbeat", "/api/version"}:
            try:
                probes[path]["json_body"] = json.loads(result.get("text", ""))
            except Exception:
                probes[path]["json_body"] = None

    auth_matrix = {}
    protected = "/api/operator/security-verification"
    for label, token in [("anonymous", None), ("invalid_bearer", "Bearer invalid.invalid.invalid")]:
        result = request(protected, authorization=token)
        auth_matrix[label] = {"path": protected, "status": result["status"],
                              "content_type": result["content_type"]}
    me_methods = live_map.get("/api/me", [])
    if "GET" in me_methods:
        for label, token in [("me_anonymous", None), ("me_invalid_bearer", "Bearer invalid.invalid.invalid")]:
            result = request("/api/me", authorization=token)
            auth_matrix[label] = {"path": "/api/me", "status": result["status"],
                                  "content_type": result["content_type"]}
    auth_matrix["authenticated_non_sovereign"] = {
        "path": protected, "status": "NOT_TESTED",
        "reason": "No production test identity with valid Firebase signature and non-sovereign access was provisioned; do not fabricate credentials."
    }

    retired_origin = request("/api/heartbeat", origin="https://arkadia-prism.vercel.app", method="OPTIONS")
    cors = {
        "retired_vercel_origin": "https://arkadia-prism.vercel.app",
        "preflight_status": retired_origin["status"],
        "access_control_allow_origin": retired_origin["allow_origin"],
        "verdict": "BLOCKED" if retired_origin["allow_origin"] else "NO_CROSS_ORIGIN_GRANT"
    }

    report = {
        "schema": "arkadia.render-reconciliation/v1",
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "canonical_origin": BASE,
        "expected_revision": EXPECTED or None,
        "revision_wait_required": WAIT_FOR_REVISION,
        "runtime_revision_probe": {"http_status": version["status"], "payload": version_payload,
                                   "error": version.get("error")},
        "openapi_http_status": live_doc_result["status"],
        "source_path_count": len(source_map),
        "live_path_count": len(live_map),
        "endpoint_counts": {
            verdict: sum(row["verdict"] == verdict for row in endpoint_rows)
            for verdict in ["MATCH", "SOURCE_ONLY", "LIVE_ONLY", "METHOD_DRIFT"]
        },
        "endpoints": endpoint_rows,
        "route_probes": probes,
        "authorization_matrix": auth_matrix,
        "retired_vercel_cors_probe": cors,
        "acceptance": "NOT_ACCEPTED",
        "acceptance_blockers": [
            "Authenticated non-sovereign behavior requires a provisioned test identity.",
            "HTTP path/method parity is not proof that every operation's business behavior is correct.",
            "Human production acceptance remains required."
        ],
    }
    write_json("runtime-report.json", report)
    print(json.dumps({k: report[k] for k in [
        "canonical_origin", "expected_revision", "runtime_revision_probe", "source_path_count",
        "live_path_count", "endpoint_counts", "route_probes", "authorization_matrix",
        "retired_vercel_cors_probe", "acceptance"
    ]}, indent=2))

    hard_failures = []
    if live_doc_result["status"] != 200 or not live_map:
        hard_failures.append("live /openapi.json was not readable")
    if WAIT_FOR_REVISION and version_payload.get("source_revision") != EXPECTED:
        hard_failures.append("running revision did not converge to expected GitHub SHA")
    if any(row["verdict"] != "MATCH" for row in endpoint_rows):
        hard_failures.append("live OpenAPI path/method inventory differs from source composition root")
    for path in ["/", "/operator", "/n-atlas-tester", "/solariun/opportunity-radar"]:
        if probes[path].get("status") != 200 or not probes[path].get("looks_like_html"):
            hard_failures.append(f"frontend route failed: {path}")
    for path in ["/api/heartbeat", "/api/version"]:
        if probes[path].get("status") != 200 or not probes[path].get("json_body"):
            hard_failures.append(f"JSON endpoint failed: {path}")
    if probes["/api/__arkadia_reconciliation_missing_route__"].get("status") != 404:
        hard_failures.append("unknown API path did not fail closed with 404")
    for key in ["anonymous", "invalid_bearer"]:
        if auth_matrix[key]["status"] not in {401, 403}:
            hard_failures.append(f"protected security endpoint did not deny {key} access")
    if hard_failures:
        print("RECONCILIATION_FAIL: " + "; ".join(hard_failures), file=sys.stderr)
        return 1
    print("RECONCILIATION_PASS_WITH_ACCEPTANCE_BLOCKERS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
