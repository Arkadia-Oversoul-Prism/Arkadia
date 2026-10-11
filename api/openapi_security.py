"""OpenAPI security metadata derived from FastAPI's actual dependency graph.

The schema is descriptive, not an authorization engine. Route dependencies remain the
runtime authority. Every operation gets an explicit OpenAPI security field plus a
machine-readable x-arkadia-auth-boundary classification so CI can detect drift.
"""
from __future__ import annotations

from typing import Any, Iterable

from fastapi import FastAPI
from fastapi.routing import APIRoute

HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
BEARER_SCHEME = "FirebaseBearer"

# These are intentionally public entry points in the N-ATLaS tester flow. Their
# subsequent run token is path-scoped by api.auth.require_auth and must not grant
# authority to other routes.
PUBLIC_CAPABILITY_PATHS = {
    "/api/lab/engineering/n-atlas/test-session",
    "/api/lab/engineering/n-atlas/catalog",
}

def _dependency_callables(dependant: Any) -> Iterable[Any]:
    """Walk nested FastAPI dependencies, including router-level dependencies."""
    for item in getattr(dependant, "dependencies", ()) or ():
        yield item.call
        yield from _dependency_callables(item)

def _name(call: Any) -> str:
    return getattr(call, "__name__", call.__class__.__name__)

def _join_path(prefix: str, path: str) -> str:
    if not prefix:
        return path
    if path == prefix or path.startswith(prefix.rstrip("/") + "/"):
        return path
    return prefix.rstrip("/") + "/" + path.lstrip("/")


def _route_bindings(routes: Iterable[Any], prefix: str = "", inherited: tuple[Any, ...] = ()):
    """Flatten FastAPI's lazy included-router wrappers while preserving prefixes."""
    for item in routes:
        if isinstance(item, APIRoute):
            yield _join_path(prefix, item.path), item, inherited
            continue
        original_router = getattr(item, "original_router", None)
        if original_router is not None:
            context = getattr(item, "include_context", None)
            child_prefix = _join_path(prefix, getattr(context, "prefix", "") or "")
            child_dependencies = tuple(getattr(context, "dependencies", ()) or ())
            yield from _route_bindings(
                getattr(original_router, "routes", ()),
                child_prefix,
                inherited + child_dependencies,
            )
            continue
        nested = getattr(item, "routes", None)
        if nested:
            yield from _route_bindings(nested, prefix, inherited)


def _boundary(
    route: APIRoute, inherited_dependencies: tuple[Any, ...] = (), effective_path: str | None = None
) -> tuple[list[dict[str, list[Any]]], dict[str, Any]]:
    calls = list(_dependency_callables(route.dependant))
    inherited_calls = [
        getattr(dependency, "dependency", dependency)
        for dependency in inherited_dependencies
    ]
    names = {_name(call) for call in calls + inherited_calls}
    path = effective_path or route.path

    if path in PUBLIC_CAPABILITY_PATHS and "require_lab_auth" in names:
        return [], {
            "classification": "public_capability_entry",
            "runtime_guard": "require_lab_auth",
            "note": "Public entry only; subsequent capability is session- and path-scoped.",
        }

    if "require_sovereign" in names:
        return [{BEARER_SCHEME: []}], {
            "classification": "firebase_bearer_sovereign",
            "runtime_guard": "require_sovereign",
            "minimum_access_level": 3,
        }

    if "require_auth" in names or "require_lab_auth" in names or "require_project_owner" in names:
        return [{BEARER_SCHEME: []}], {
            "classification": "firebase_bearer",
            "runtime_guard": sorted(names.intersection({
                "require_auth", "require_lab_auth", "require_project_owner"
            })),
        }

    if "get_current_user" in names or "_get_current_user" in names:
        return [{BEARER_SCHEME: []}, {}], {
            "classification": "optional_firebase_bearer",
            "runtime_guard": "get_current_user",
        }

    # Inline checks (for example a body-held sovereign key or GitHub HMAC signature)
    # cannot safely be inferred from a dependency name. Mark them for explicit review
    # rather than falsely claiming Firebase bearer auth protects them.
    return [], {
        "classification": "public_or_inline_application_guard",
        "runtime_guard": None,
        "review_required": True,
    }

def install_openapi_security(app: FastAPI) -> None:
    """Install explicit per-operation security metadata on the completed application."""
    original_openapi = app.openapi

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        schema = original_openapi()
        schema.setdefault("components", {}).setdefault("securitySchemes", {})[BEARER_SCHEME] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "Firebase ID token",
            "description": "Firebase ID token verified by Arkadia's auth dependency.",
        }
        routes = {
            (effective_path, method.lower()): (route, inherited_dependencies)
            for effective_path, route, inherited_dependencies in _route_bindings(app.routes)
            for method in route.methods or ()
            if method.lower() in HTTP_METHODS
        }
        for path, path_item in schema.get("paths", {}).items():
            for method, operation in path_item.items():
                if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                    continue
                binding = routes.get((path, method.lower()))
                if binding is None:
                    operation["security"] = []
                    operation["x-arkadia-auth-boundary"] = {
                        "classification": "unmatched_openapi_operation",
                        "review_required": True,
                    }
                    continue
                route, inherited_dependencies = binding
                security, boundary = _boundary(route, inherited_dependencies, path)
                operation["security"] = security
                operation["x-arkadia-auth-boundary"] = boundary
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi  # type: ignore[method-assign]
