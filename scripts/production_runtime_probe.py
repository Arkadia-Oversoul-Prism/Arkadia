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


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Return 3xx responses as observations instead of following Location."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_without_redirects(path: str) -> dict:
    url = BASE + path
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Arkadia-Codex-Anomaly-Probe/1.0", "Accept": "application/json"},
    )
    opener = urllib.request.build_opener(NoRedirectHandler())
    started = time.monotonic()
    try:
        with opener.open(req, timeout=TIMEOUT) as response:
            body = response.read(200_000)
            headers = response.headers
            return {
                "requested_url": url,
                "response_url": response.geturl(),
                "status": response.status,
                "location": headers.get("Location"),
                "request_id": headers.get("X-Request-ID") or headers.get("X-Correlation-ID") or headers.get("Traceparent"),
                "request_id_headers": {
                    key: headers.get(key)
                    for key in ("X-Request-ID", "X-Correlation-ID", "Traceparent", "CF-Ray", "X-Render-Origin-Server")
                    if headers.get(key)
                },
                "elapsed_ms": round((time.monotonic() - started) * 1000),
                "content_type": headers.get("Content-Type", ""),
                "body_preview": body[:300].decode("utf-8", "replace"),
                "redirect_followed": False,
            }
    except urllib.error.HTTPError as error:
        body = error.read(200_000)
        headers = error.headers
        return {
            "requested_url": url,
            "response_url": error.geturl(),
            "status": error.code,
            "location": headers.get("Location"),
            "request_id": headers.get("X-Request-ID") or headers.get("X-Correlation-ID") or headers.get("Traceparent"),
            "request_id_headers": {
                key: headers.get(key)
                for key in ("X-Request-ID", "X-Correlation-ID", "Traceparent", "CF-Ray", "X-Render-Origin-Server")
                if headers.get(key)
            },
            "elapsed_ms": round((time.monotonic() - started) * 1000),
            "content_type": headers.get("Content-Type", ""),
            "body_preview": body[:300].decode("utf-8", "replace"),
            "redirect_followed": False,
        }
    except Exception as error:
        return {
            "requested_url": url,
            "response_url": None,
            "status": None,
            "location": None,
            "request_id": None,
            "request_id_headers": {},
            "elapsed_ms": round((time.monotonic() - started) * 1000),
            "error_type": type(error).__name__,
            "error": str(error)[:300],
            "redirect_followed": False,
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

# Focused anomaly capture: never follow a redirect for either path. Keep the
# Location, response/request identifiers, elapsed time, and actual response URL.
report["targeted_anomaly_probe"] = {
    "method": "GET",
    "redirect_policy": "follow_redirects=false",
    "results": {
        "/api/codex": request_without_redirects("/api/codex"),
        "/solspire/workspace": request_without_redirects("/solspire/workspace"),
    },
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
# Resolve dynamically registered route functions back to the APIRouter passed
# by their registration site. Example: register_eden_ops_02_routes(router) is
# defined in a separate module, but its target router carries the caller's
# /enterprise prefix and is itself mounted below /solspire.
router_prefixes_by_file: dict[str, dict[str, str]] = {}
registration_source_by_name: dict[str, str] = {}
for source_root in source_roots:
    if not source_root.exists():
        continue
    for source_file in source_root.rglob("*.py"):
        if any(part in {"archive", "tests", "__pycache__"} for part in source_file.parts):
            continue
        try:
            tree = ast.parse(source_file.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        local_prefixes: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                value = node.value
                if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "APIRouter":
                    prefix = next((kw.value.value for kw in value.keywords
                                   if kw.arg == "prefix" and isinstance(kw.value, ast.Constant)
                                   and isinstance(kw.value.value, str)), "")
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    for target in targets:
                        if isinstance(target, ast.Name):
                            local_prefixes[target.id] = prefix
        router_prefixes_by_file[str(source_file)] = local_prefixes
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    if alias.name.startswith("register_") and alias.name.endswith("_routes"):
                        registration_source_by_name[alias.asname or alias.name] = str(
                            Path(*node.module.split(".")).with_suffix(".py")
                        )

dynamic_prefix_by_file: dict[str, str] = {}
for source_root in source_roots:
    if not source_root.exists():
        continue
    for caller_file in source_root.rglob("*.py"):
        if any(part in {"archive", "tests", "__pycache__"} for part in caller_file.parts):
            continue
        try:
            tree = ast.parse(caller_file.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            function_name = node.func.id
            target_file = registration_source_by_name.get(function_name)
            if not target_file or not node.args or not isinstance(node.args[0], ast.Name):
                continue
            target_router = node.args[0].id
            local_prefix = router_prefixes_by_file.get(str(caller_file), {}).get(target_router)
            if local_prefix is None:
                continue
            composed = "/".join(part.strip("/") for part in (
                "solspire" if str(caller_file).startswith("solspire/") else "",
                local_prefix,
            ) if part.strip("/"))
            dynamic_prefix_by_file[target_file] = "/" + composed if composed else ""

source_keys = set()
composed_source_declarations = []
for item in source_declarations:
    path = item["path"]
    source_file = item["file"]
    if source_file in dynamic_prefix_by_file:
        prefix = dynamic_prefix_by_file[source_file]
        path = "/" + "/".join(part.strip("/") for part in (prefix, path) if part.strip("/"))
        item["composition"] = "dynamic_registration_site"
        item["composed_path"] = path
    elif source_file.startswith("solspire/") and not path.startswith("/solspire"):
        path = "/solspire" + path
        item["composition"] = "solspire_parent_router"
        item["composed_path"] = path
    else:
        item["composition"] = "local_router_or_app"
        item["composed_path"] = path
    composed_source_declarations.append({**item, "path": path})
    source_keys.add((item["method"], path))

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
    "source_declarations": composed_source_declarations,
    "dynamic_registration_prefixes": dynamic_prefix_by_file,
    "comparison_status": "router_aware_nested_and_dynamic_registration_composition",
    "limitation": "Static AST analysis composes SolSpire's parent prefix and statically identifiable register_*_routes(router) registrations. Remaining unmatched entries require source-level review and are not automatically classified as absent.",
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
