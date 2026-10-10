"""Regression coverage for nested and dynamically registered SolSpire routes."""
from fastapi import FastAPI

from solspire.console_router import router as solspire_router


EXPECTED_COMPOSED_ROUTES = {
    ("POST", "/solspire/enterprise/workspaces/{enterprise_id}/members"),
    ("DELETE", "/solspire/enterprise/workspaces/{enterprise_id}/members/{handle}/desks/{desk}"),
    ("GET", "/solspire/enterprise/workspaces/{enterprise_id}/tasks"),
    ("PATCH", "/solspire/enterprise/workspaces/{enterprise_id}/tasks/{task_id}"),
    ("GET", "/solspire/enterprise/workspaces/{enterprise_id}/control-room"),
}


def test_dynamic_eden_ops_routes_are_present_at_composed_solspire_paths():
    """The generated OpenAPI schema must include every route after parent prefixes."""
    app = FastAPI()
    app.include_router(solspire_router)

    schema = app.openapi()
    actual = {
        (method.upper(), path)
        for path, path_item in schema.get("paths", {}).items()
        for method in path_item
        if method.lower() in {"get", "post", "put", "patch", "delete", "options", "head"}
    }

    missing = EXPECTED_COMPOSED_ROUTES - actual
    assert not missing, f"EDEN-OPS-02 routes missing from composed OpenAPI paths: {sorted(missing)}"
