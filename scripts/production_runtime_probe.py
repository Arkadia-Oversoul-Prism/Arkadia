#!/usr/bin/env python3
"""Read-only production route inventory for the canonical Render runtime.

Never sends mutation verbs. It inventories every OpenAPI method/path, probes
safe GET routes, and records the limits of the available authorization matrix.
"""
from __future__ import annotations

import ast
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


def current_version() -> dict:
    try:
        with urllib.request.urlopen(BASE + "/api/version", timeout=TIMEOUT) as response:
            return json.loads(response.read(100_000))
    except Exception as error:
        return {"_error": type(error).__name__}


EXPECTED_REVISION = os.environ.get("GITHUB_SHA", "") if os.environ.get("GITHUB_EVENT_NAME") == "push" else ""
deployment_identity = {
    "expected_revision": EXPECTED_REVISION or None,
    "observed_revision": None,
    "status": "not_applicable_for_pull_request_probe" if not EXPECTED_REVISION else "waiting_for_render_deploy",
}
if EXPECTED_REVISION:
    deadline = time.monotonic() + 420
    while True:
        version = current_version()
        observed = version.get("source_revision") if isinstance(version, dict) else None
        deployment_identity["observed_revision"] = observed
        deployment_identity["version_payload"] = version
        if observed == EXPECTED_REVISION:
            deployment_identity["status"] = "matched"
            break
        if time.monotonic() >= deadline:
            deployment_identity["status"] = "mismatch_or_deploy_not_live_within_420_seconds"
            break
        time.sleep(20)


report = {
    "captured_at": datetime.now(timezone.utc).isoformat(),
    "deployment_identity": deployment_identity,
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

# Static source declaration inventory. Router prefixes declared in each module
# are composed locally. Cross-module include_router(prefix=...) composition is
# reported as a limitation rather than treated as proof of absence.
source_declarations = []
source_roots = [Path("api"), Path("solspire"), Path("kernel"), Path("providers"), Path("knowledge"), Path("lab"), Path("economic_seams")]
route_methods = {"get", "post", "put", "patch", "delete", "options", "head", "api_route"}
for source_root in source_roots:
    if not source_root.exists():
        continue
    for source_file in source_root.rglob("*.py"):
        if any(part in {"archive", "tests", "__pycache__"} for part in source_file.parts):
            continue
        try:
            module_ast = ast.parse(source_file.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        router_prefixes = {}
        for node in ast.walk(module_ast):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                value = node.value
                if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "APIRouter":
                    prefix = ""
                    for keyword in value.keywords:
                        if keyword.arg == "prefix" and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                            prefix = keyword.value.value
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    for target in targets:
                        if isinstance(target, ast.Name):
                            router_prefixes[target.id] = prefix
        for node in ast.walk(module_ast):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                    continue
                method = decorator.func.attr.lower()
                if method not in route_methods or not decorator.args:
                    continue
                route_value = decorator.args[0]
                if not isinstance(route_value, ast.Constant) or not isinstance(route_value.value, str):
                    continue
                receiver = decorator.func.value.id if isinstance(decorator.func.value, ast.Name) else "dynamic"
                prefix = router_prefixes.get(receiver, "") if receiver != "app" else ""
                route_path = "/" + "/".join(part for part in (prefix.strip("/"), route_value.value.strip("/")) if part)
                methods = [method.upper()]
                if method == "api_route":
                    for keyword in decorator.keywords:
                        if keyword.arg == "methods" and isinstance(keyword.value, (ast.List, ast.Tuple)):
                            methods = [e.value.upper() for e in keyword.value.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
                for verb in methods:
                    source_declarations.append({
                        "method": verb, "path": route_path,
                        "file": str(source_file), "function": node.name,
                        "router_variable": receiver,
                    })
source_keys = {(item["method"], item["path"]) for item in source_declarations}
for item in source_declarations:
    if item["file"].startswith("solspire/") and not item["path"].startswith("/solspire"):
        source_keys.add((item["method"], "/solspire" + item["path"]))

runtime_keys = {
    (method.upper(), path)
    for path, item in paths.items()
    for method in item
    if method.lower() in {"get", "post", "put", "patch", "delete", "options", "head"}
}
exact_matches = sorted(runtime_keys & source_keys)
runtime_unmatched = sorted(runtime_keys - source_keys)
source_unmatched = sorted(source_keys - runtime_keys)
report["source_inventory"] = {
    "static_route_declaration_count": len(source_declarations),
    "unique_method_path_count": len(source_keys),
    "exact_method_path_matches": len(exact_matches),
    "runtime_operations_without_exact_local_decorator_match": [
        {"method": method, "path": path} for method, path in runtime_unmatched[:500]
    ],
    "source_declarations_without_exact_runtime_match": [
        {"method": method, "path": path} for method, path in source_unmatched[:500]
    ],
    "source_declarations": source_declarations,
    "comparison_status": "exact_with_known_solspire_parent_prefix",
    "limitation": "Known SolSpire child-router prefix is composed explicitly. Any remaining unmatched entries require source-level review and are not automatically classified as absent.",
}
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
    "deployment_identity": report["deployment_identity"],
    "main_openapi_path_count": report["openapi"]["path_count"],
    "openapi_operation_count": report["openapi"]["operation_count"],
    "get_routes_probed": sum(1 for x in report["endpoint_inventory"] if x["probe"] == "GET"),
    "source_inventory": {
        "static_route_declarations": report["source_inventory"]["static_route_declaration_count"],
        "unique_method_paths": report["source_inventory"]["unique_method_path_count"],
        "exact_method_path_matches": report["source_inventory"]["exact_method_path_matches"],
        "runtime_unmatched_count": len(report["source_inventory"]["runtime_operations_without_exact_local_decorator_match"]),
        "source_unmatched_count": len(report["source_inventory"]["source_declarations_without_exact_runtime_match"]),
        "status": report["source_inventory"]["comparison_status"],
    },
    "classifications": {},
    "auth_matrix": {k: v.get("classification", classify(v.get("status"))) for k, v in auth.items()},
    "artifact": str(OUT / "production-route-inventory.json"),
    "limitations": report["limitations"],
}
for entry in report["endpoint_inventory"]:
    if "classification" in entry:
        summary["classifications"][entry["classification"]] = summary["classifications"].get(entry["classification"], 0) + 1
print(json.dumps(summary, indent=2))
if EXPECTED_REVISION and deployment_identity["status"] != "matched":
    sys.exit(3)
