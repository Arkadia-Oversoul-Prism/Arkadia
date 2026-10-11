"""Full-app OpenAPI security reconciliation gate.

This imports the real composed FastAPI app, so router-level dependencies and mounted
operations are inspected rather than a synthetic subset alone.
"""
from api.main import app


def test_all_composed_operations_have_adjudicated_security_boundaries():
    schema = app.openapi()
    methods = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
    operations = [
        (method.upper(), path, operation)
        for path, path_item in schema.get("paths", {}).items()
        for method, operation in path_item.items()
        if method.lower() in methods
    ]
    missing_security = [
        f"{method} {path}" for method, path, op in operations if "security" not in op
    ]
    missing_boundary = [
        f"{method} {path}" for method, path, op in operations
        if not isinstance(op.get("x-arkadia-auth-boundary"), dict)
    ]
    unreviewed = [
        f"{method} {path}: {op['x-arkadia-auth-boundary']}"
        for method, path, op in operations
        if op.get("x-arkadia-auth-boundary", {}).get("review_required")
    ]
    assert not missing_security, f"Operations missing explicit security: {missing_security}"
    assert not missing_boundary, f"Operations missing boundary metadata: {missing_boundary}"
    assert not unreviewed, (
        f"{len(unreviewed)} operations still require auth-boundary adjudication:\n"
        + "\n".join(unreviewed)
    )
