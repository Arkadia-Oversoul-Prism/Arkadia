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
        or op.get("x-arkadia-auth-boundary", {}).get("classification") == "unmatched_openapi_operation"
    ]
    invalid_declarations = [
        f"{method} {path}: {op.get('x-arkadia-auth-boundary')} / security={op.get('security')}"
        for method, path, op in operations
        if (
            op.get("x-arkadia-auth-boundary", {}).get("classification")
            in {"firebase_bearer", "firebase_bearer_sovereign", "sovereign_key_header", "github_webhook_hmac"}
            and not op.get("security")
        ) or (
            op.get("x-arkadia-auth-boundary", {}).get("classification")
            == "anonymous_no_auth_guard" and op.get("security") != []
        )
    ]
    assert not missing_security, f"Operations missing explicit security: {missing_security}"
    assert not missing_boundary, f"Operations missing boundary metadata: {missing_boundary}"
    assert not invalid_declarations, (
        "Security requirements disagree with the declared boundary:\n"
        + "\n".join(invalid_declarations)
    )
    assert not unreviewed, (
        f"{len(unreviewed)} operations still require auth-boundary adjudication:\n"
        + "\n".join(unreviewed)
    )
    # Inventory 331 -> 332 is a deliberate, reviewable act (AEAS-01 P0.3,
    # issue #590): the Engineering Lab gained a read-only repository
    # observation, `GET /api/lab/engineering/repository`. The count is pinned
    # *and* the operation is named, so the number can only move when the
    # operation it accounts for is actually present and adjudicated.
    repository_op = schema["paths"].get("/api/lab/engineering/repository", {}).get("get", {})
    assert repository_op, "the Lab repository observation is no longer served"
    assert repository_op.get("x-arkadia-auth-boundary", {}).get("classification") == "firebase_bearer"
    assert repository_op.get("security") == [{"FirebaseBearer": []}]
    # Inventory 332 -> 333 is the same reviewable act for ARKANA A2: the SSE
    # resonance stream (`202bc4e1`) was mounted on the composition root in
    # `a1fe177f`. Named here for the same reason as the entry above, so the
    # count cannot drift onto an operation nobody adjudicated.
    stream_op = schema["paths"].get("/api/commune/resonance/stream", {}).get("post", {})
    assert stream_op, "the A2 SSE resonance stream is no longer served"
    assert stream_op.get("x-arkadia-auth-boundary", {}).get("classification") == "optional_firebase_bearer"
    assert stream_op.get("security") == [{"FirebaseBearer": []}, {}]
    assert len(operations) == 333, f"Expected captured 333-operation inventory; got {len(operations)}"
    assert "FirebaseBearer" in schema["components"]["securitySchemes"]
    assert "SovereignKeyHeader" in schema["components"]["securitySchemes"]
    assert "GitHubWebhookHMAC" in schema["components"]["securitySchemes"]
    assert schema["paths"]["/api/forge"]["post"]["security"] == [{"SovereignKeyHeader": []}]
    assert schema["paths"]["/api/github/webhook"]["post"]["security"] == [{"GitHubWebhookHMAC": []}]
