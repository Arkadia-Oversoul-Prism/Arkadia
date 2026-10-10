#!/usr/bin/env python3
"""Read-only production route inventory for the canonical Render runtime.

Never sends mutation verbs. It inventories every OpenAPI method/path, probes
safe GET routes, and records the limits of the available authorization matrix.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

BASE = os.environ.get("ARKADIA_PRODUCTION_ORIGIN", "https://arkadia-qzu4.onrender.com").rstrip("/")
OUT = Path(os.environ.get("ARKADIA_PROBE_OUTPUT", "artifacts/canonical-render-runtime"))
OUT.mkdir(parents=True, exist_ok=True)
TIMEOUT = 18
LOW_PRIVILEGE_TOKEN = os.environ.get("ARKADIA_PROBE_LOW_PRIVILEGE_BEARER", "").strip()


def request(path: str, headers: dict[str, str] | None = None) -> dict:
    url = BASE + path
    req = urllib.request.Request(url, headers={"User-Agent": "Arkadia-Canonical-Runtime-Probe/1.0", **(headers or {})})
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            body = response.read(2_000_000)
            return {
                "url": url, "status": response.status,
                "content_type": response.headers.get("Content-Type", ""),
                "bytes_read": len(body), "elapsed_ms": round((time.monotonic() - started) * 1000),
                "location": response.headers.get("Location"),
                "body_preview": body[:160].decode("utf-8", "replace"),
            }
    except urllib.error.HTTPError as error:
        body = error.read(1000)
        return {
            "url": url, "status": error.code,
            "content_type": error.headers.get("Content-Type", ""),
            "bytes_read": len(body), "elapsed_ms": round((time.monotonic() - started) * 1000),
            "location": error.headers.get("Location"),
            "body_preview": body[:160].decode("utf-8", "replace"),
        }
    except Exception as error:
        return {
            "url": url, "status": None, "error_type": type(error).__name__,
            "error": str(error)[:240],
            "elapsed_ms": round((time.monotonic() - started) * 1000),
        }


def classify(status: int | None) -> str:
    if status is None:
        return "failing_or_unreachable"
    if status in (401, 403):
        return "protected"
    if status == 404 or status == 410:
        return "absent"
    if status >= 500:
        return "failing"
    if 200 <= status < 300:
        return "reachable"
    if 300 <= status < 400:
        return "redirected"
    if status in (400, 405, 422):
        return "route_reachable_request_shape_rejected"
    return "needs_review"


def probe_path(path: str) -> str:
    # Give path parameters a harmless sentinel; never send query data or bodies.
    return re.sub(r"\{[^/{}]+\}", "probe-id", path)


report = {
    "captured_at": datetime.now(timezone.utc).isoformat(),
    "origin": BASE,
    "mode": "read_only_get_probes; no mutation verbs invoked",
    "baseline": {},
    "openapi": {},
    "endpoint_inventory": [],
    "frontend_routes": {},
    "authorization_matrix": {},
    "limitations": [],
}

for path in ("/", "/health", "/api/version", "/openapi.json", "/operator", "/solariun/opportunity-radar", "/n-atlas-lab", "/n-atlas-tester"):
    result = request(path, {"Accept": "text/html" if path in ("/", "/operator", "/solariun/opportunity-radar", "/n-atlas-lab", "/n-atlas-tester") else "application/json"})
    result["classification"] = classify(result.get("status"))
    report["frontend_routes" if path in ("/", "/operator", "/solariun/opportunity-radar", "/n-atlas-lab", "/n-atlas-tester") else "baseline"][path] = result

openapi_result = request("/openapi.json", {"Accept": "application/json"})
if openapi_result.get("status") != 200:
    report["openapi"] = {"classification": classify(openapi_result.get("status")), "response": openapi_result}
    report["limitations"].append("OpenAPI document unavailable; route inventory cannot be reconciled.")
    (OUT / "production-route-inventory.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"result": "BLOCKED", "reason": "OpenAPI capture unavailable", "status": openapi_result.get("status")}, indent=2))
    sys.exit(2)

try:
    with urllib.request.urlopen(BASE + "/openapi.json", timeout=TIMEOUT) as response:
        schema = json.loads(response.read(8_000_000))
except Exception as error:
    report["limitations"].append("OpenAPI response could not be decoded: " + type(error).__name__)
    (OUT / "production-route-inventory.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    sys.exit(2)

paths = schema.get("paths", {})
report["openapi"] = {
    "classification": "reachable",
    "title": schema.get("info", {}).get("title"),
    "version": schema.get("info", {}).get("version"),
    "path_count": len(paths),
    "operation_count": sum(1 for item in paths.values() for method in item if method.lower() in {"get", "post", "put", "patch", "delete", "options", "head"}),
    "response": openapi_result,
}
probe_jobs = []
all_entries = []
for path, item in sorted(paths.items()):
    for method, operation in sorted(item.items()):
        method = method.lower()
        if method not in {"get", "post", "put", "patch", "delete", "options", "head"}:
            continue
        entry = {
            "method": method.upper(), "path": path,
            "operation_id": operation.get("operationId"),
            "tags": operation.get("tags", []),
            "security_declared": bool(operation.get("security", schema.get("security", []))),
            "probe": "not_probed_non_get_method",
        }
        all_entries.append(entry)
        if method == "get":
            entry["probe"] = "GET"
            probe_jobs.append((entry, probe_path(path)))

# Bounded concurrency keeps a full production inventory from serially waiting on
# every slow/missing route. The probes remain read-only and capped at 12 workers.
with ThreadPoolExecutor(max_workers=12) as pool:
    futures = [(entry, pool.submit(request, path, {"Accept": "application/json"})) for entry, path in probe_jobs]
    for entry, future in futures:
        response = future.result()
        # Retry slow read-only GETs once; a transient timeout is not enough to
        # conclude that an endpoint is broken.
        if response.get("status") is None:
            response = request(path, {"Accept": "application/json"})
            response["retry_after_timeout"] = True
        entry["response"] = response
        entry["classification"] = classify(response.get("status"))
        # OpenAPI proves this path/method is registered. A 404 carrying a
        # resource-level "not found" detail means the sentinel record is absent,
        # not that the router itself is absent.
        if response.get("status") == 404 and "not found" in (response.get("body_preview") or "").lower():
            entry["classification"] = "resource_not_found_route_present"
for entry in sorted(all_entries, key=lambda e: (e["path"], e["method"])):
    report["endpoint_inventory"].append(entry)

# Authorization probes exercise the actual deployed Express/FastAPI boundary.
# No credentials are printed or written into the artifact.
auth_path = "/api/operator/security-verification"
auth = {
    "anonymous_no_authorization_header": request(auth_path),
    "malformed_bearer_token": request(auth_path, {"Authorization": "Bearer invalid-production-probe-token"}),
}
for name, result in list(auth.items()):
    result["classification"] = classify(result.get("status"))
if LOW_PRIVILEGE_TOKEN:
    result = request(auth_path, {"Authorization": "Bearer " + LOW_PRIVILEGE_TOKEN})
    result["classification"] = classify(result.get("status"))
    auth["valid_low_privilege_identity"] = result
    auth["valid_low_privilege_token_source"] = "configured CI secret; token value withheld"
else:
    auth["valid_low_privilege_identity"] = {
        "classification": "not_tested",
        "reason": "ARKADIA_PROBE_LOW_PRIVILEGE_BEARER is not configured; a valid low-privilege Firebase ID token is required to distinguish unauthorized from unauthenticated."
    }
report["authorization_matrix"] = auth
if not LOW_PRIVILEGE_TOKEN:
    report["limitations"].append("Unauthorized (valid identity with insufficient privileges) is NOT TESTED; only anonymous and malformed-bearer behavior can be observed without a valid low-privilege identity token.")

(OUT / "production-route-inventory.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
summary = {
    "result": "CAPTURED",
    "origin": BASE,
    "main_openapi_path_count": report["openapi"]["path_count"],
    "openapi_operation_count": report["openapi"]["operation_count"],
    "get_routes_probed": sum(1 for x in report["endpoint_inventory"] if x["probe"] == "GET"),
    "classifications": {},
    "auth_matrix": {k: v.get("classification", classify(v.get("status"))) for k, v in auth.items()},
    "artifact": str(OUT / "production-route-inventory.json"),
    "limitations": report["limitations"],
}
for entry in report["endpoint_inventory"]:
    if "classification" in entry:
        summary["classifications"][entry["classification"]] = summary["classifications"].get(entry["classification"], 0) + 1
print(json.dumps(summary, indent=2))
