#!/usr/bin/env python3
"""Read-only HTTP/OpenAPI/auth reconciliation for Arkadia's canonical Render service."""
from __future__ import annotations
import argparse, json, os, sys, time, urllib.error, urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ORIGIN = "https://arkadia-qzu4.onrender.com"
FRONTEND_ROUTES = [
    "/", "/oracle", "/solariun", "/solariun/opportunity-radar",
    "/operator", "/operator/", "/n-atlas-lab", "/n-atlas-tester",
]
OPTIONAL_ROUTES = ["/health", "/api/heartbeat"]
PROTECTED_ROUTE = "/api/operator/security-verification"
METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}

def inventory(spec: dict[str, Any]) -> list[str]:
    return sorted({
        f"{method.upper()} {path}"
        for path, ops in spec.get("paths", {}).items()
        for method in ops
        if method.lower() in METHODS
    })

def fetch(url: str, token: str | None = None, accept: str = "application/json") -> dict[str, Any]:
    headers = {"User-Agent": "Arkadia-Render-Reconciliation/1.0", "Accept": accept}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read()
            return {"status": r.status, "content_type": r.headers.get("Content-Type", ""),
                    "bytes": len(body), "body": body, "final_url": r.geturl()}
    except urllib.error.HTTPError as e:
        body = e.read()
        return {"status": e.code, "content_type": e.headers.get("Content-Type", ""),
                "bytes": len(body), "body": body, "final_url": e.geturl()}
    except Exception as e:
        return {"status": 0, "content_type": "", "bytes": 0, "body": b"",
                "error_type": type(e).__name__}

def as_json(body: bytes) -> Any:
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None

def local_inventory() -> list[str]:
    sys.path.insert(0, str(ROOT))
    from api.main import app
    return inventory(app.openapi())

def wait_for_revision(origin: str, expected: str, attempts: int = 40) -> dict[str, Any]:
    last = {"verdict": "BLOCKED"}
    for attempt in range(1, attempts + 1):
        r = fetch(origin + "/api/version")
        payload = as_json(r.get("body", b""))
        if r["status"] == 200 and isinstance(payload, dict):
            actual = payload.get("source_revision")
            if payload.get("revision_conflict") is True:
                last = {"verdict": "CONFLICT", "attempt": attempt}
            elif actual == expected:
                return {"verdict": "MATCH", "reported_revision": actual, "attempts": attempt}
            else:
                last = {"verdict": "MISMATCH_OR_UNKNOWN", "reported_revision": actual, "attempt": attempt}
        else:
            last = {"verdict": "BLOCKED", "http_status": r["status"], "attempt": attempt}
        time.sleep(15)
    return last

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--origin", default=os.environ.get("RENDER_CANONICAL_URL", DEFAULT_ORIGIN))
    parser.add_argument("--expected-revision", default=os.environ.get("GITHUB_SHA"))
    parser.add_argument("--wait-for-revision", action="store_true")
    args = parser.parse_args()
    origin = args.origin.rstrip("/")
    outdir = ROOT / "artifacts" / "render-production"
    outdir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "schema": "arkadia.render-production-reconciliation/v1",
        "origin": origin, "expected_revision": args.expected_revision or "NOT_PROVIDED",
        "checks": {}, "open_loops": [],
    }

    if args.wait_for_revision and args.expected_revision:
        identity = wait_for_revision(origin, args.expected_revision)
    else:
        r = fetch(origin + "/api/version")
        payload = as_json(r.get("body", b""))
        actual = payload.get("source_revision") if isinstance(payload, dict) else None
        identity = {
            "verdict": "CONFLICT" if isinstance(payload, dict) and payload.get("revision_conflict") else
                       "MATCH" if args.expected_revision and actual == args.expected_revision else
                       "OBSERVED" if isinstance(actual, str) and len(actual) == 40 else "UNKNOWN",
            "http_status": r["status"], "reported_revision": actual,
        }
    report["checks"]["deployment_identity"] = identity
    if identity.get("verdict") not in {"MATCH", "OBSERVED"}:
        report["open_loops"].append("Live revision is not verified against the expected source revision.")

    r = fetch(origin + "/openapi.json")
    spec = as_json(r.get("body", b""))
    report["checks"]["openapi_http"] = {
        "status": r["status"], "content_type": r["content_type"],
        "bytes": r["bytes"], "valid_json_object": isinstance(spec, dict),
    }
    if isinstance(spec, dict):
        (outdir / "openapi.json").write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        live = inventory(spec)
        report["checks"]["live_inventory"] = {
            "path_count": len(spec.get("paths", {})), "operation_count": len(live), "operations": live,
        }
        try:
            source = local_inventory()
            only_live, only_source = sorted(set(live)-set(source)), sorted(set(source)-set(live))
            report["checks"]["source_inventory_comparison"] = {
                "source_path_count": len({x.split(" ",1)[1] for x in source}),
                "source_operation_count": len(source), "only_live": only_live, "only_source": only_source,
                "verdict": "MATCH" if not only_live and not only_source else "DIFF",
            }
            if only_live or only_source:
                report["open_loops"].append("Live OpenAPI operations differ from the checked-out source inventory.")
        except Exception as e:
            report["checks"]["source_inventory_comparison"] = {"verdict": "BLOCKED", "error_type": type(e).__name__}
            report["open_loops"].append("Could not generate the local source OpenAPI inventory.")
    else:
        report["open_loops"].append("Live /openapi.json is unavailable or not valid JSON.")

    routes = {}
    for path in FRONTEND_ROUTES:
        r = fetch(origin + path, accept="text/html")
        html = "text/html" in r["content_type"].lower()
        routes[path] = {"status": r["status"], "content_type": r["content_type"],
                        "bytes": r["bytes"], "html": html,
                        "verdict": "PASS" if r["status"] == 200 and html else "FAIL"}
    for path in OPTIONAL_ROUTES:
        r = fetch(origin + path)
        routes[path] = {"status": r["status"], "content_type": r["content_type"],
                        "bytes": r["bytes"],
                        "verdict": "PASS" if r["status"] == 200 else "ABSENT" if r["status"] == 404 else "FAIL"}
    report["checks"]["http_routes"] = routes
    if any(v["verdict"] == "FAIL" for v in routes.values()):
        report["open_loops"].append("A required frontend route failed HTTP/HTML verification.")

    anon = fetch(origin + PROTECTED_ROUTE)
    invalid = fetch(origin + PROTECTED_ROUTE, token="invalid-test-token-not-a-credential")
    auth = {
        "anonymous": {"status": anon["status"], "verdict": "PASS" if anon["status"] in {401,403} else "FAIL"},
        "invalid_bearer": {"status": invalid["status"], "verdict": "PASS" if invalid["status"] in {401,403} else "FAIL"},
    }
    token = os.environ.get("ARKADIA_PROBE_NON_SOVEREIGN_BEARER", "").strip()
    if token:
        r = fetch(origin + PROTECTED_ROUTE, token=token)
        auth["authenticated_non_sovereign"] = {"status": r["status"], "verdict": "PASS" if r["status"] in {401,403} else "FAIL"}
    else:
        auth["authenticated_non_sovereign"] = {"verdict": "NOT_CONFIGURED"}
        report["open_loops"].append("Live authenticated-but-unauthorized test needs a valid non-sovereign Firebase test token.")
    token = os.environ.get("ARKADIA_PROBE_SOVEREIGN_BEARER", "").strip()
    if token:
        r = fetch(origin + PROTECTED_ROUTE, token=token)
        payload = as_json(r.get("body", b""))
        auth["authorized_sovereign"] = {
            "status": r["status"], "result": payload.get("result") if isinstance(payload, dict) else None,
            "verdict": "PASS" if r["status"] == 200 and isinstance(payload, dict) else "FAIL",
        }
    else:
        auth["authorized_sovereign"] = {"verdict": "NOT_CONFIGURED"}
        report["open_loops"].append("Live authorized-role test needs a valid sovereign Firebase test token.")
    report["checks"]["authorization_matrix"] = auth

    (outdir / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    fail = identity.get("verdict") not in {"MATCH", "OBSERVED"}
    fail = fail or report.get("checks", {}).get("source_inventory_comparison", {}).get("verdict") != "MATCH"
    fail = fail or any(v["verdict"] == "FAIL" for v in routes.values())
    fail = fail or any(v["verdict"] == "FAIL" for v in auth.values())
    return 1 if fail else 0

if __name__ == "__main__":
    raise SystemExit(main())
