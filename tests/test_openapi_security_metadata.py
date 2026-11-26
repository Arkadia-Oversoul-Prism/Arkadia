"""Regression tests for explicit, operation-level OpenAPI security metadata."""
from fastapi import APIRouter, Depends, FastAPI, Request

from api.openapi_security import install_openapi_security

#: Stands in for the env var the real sovereign-gated handlers consult.
SOVEREIGN_KEY = "configured"


async def require_auth():
    return {"uid": "test"}


async def get_current_user():
    return None


def test_every_operation_has_explicit_security_and_boundary_metadata():
    app = FastAPI()

    @app.get("/public")
    async def public():
        return {"ok": True}

    @app.get("/protected", dependencies=[Depends(require_auth)])
    async def protected():
        return {"ok": True}

    @app.get("/optional", dependencies=[Depends(get_current_user)])
    async def optional():
        return {"ok": True}

    install_openapi_security(app)
    schema = app.openapi()
    operations = [
        operation
        for path_item in schema["paths"].values()
        for method, operation in path_item.items()
        if method in {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
    ]

    assert len(operations) == 3
    assert all("security" in operation for operation in operations)
    assert all("x-arkadia-auth-boundary" in operation for operation in operations)
    assert "FirebaseBearer" in schema["components"]["securitySchemes"]


def test_required_and_optional_identity_are_not_conflated():
    app = FastAPI()

    @app.get("/protected", dependencies=[Depends(require_auth)])
    async def protected():
        return {"ok": True}

    @app.get("/optional", dependencies=[Depends(get_current_user)])
    async def optional():
        return {"ok": True}

    install_openapi_security(app)
    schema = app.openapi()
    protected = schema["paths"]["/protected"]["get"]
    optional = schema["paths"]["/optional"]["get"]

    assert protected["security"] == [{"FirebaseBearer": []}]
    assert optional["security"] == [{"FirebaseBearer": []}, {}]
    assert protected["x-arkadia-auth-boundary"]["classification"] == "firebase_bearer"
    assert optional["x-arkadia-auth-boundary"]["classification"] == "optional_firebase_bearer"


def test_sovereign_access_is_marked_as_stronger_than_identity():
    async def require_sovereign():
        return {"uid": "test", "access_level": 3}

    app = FastAPI()

    @app.get("/sovereign", dependencies=[Depends(require_sovereign)])
    async def sovereign():
        return {"ok": True}

    install_openapi_security(app)
    operation = app.openapi()["paths"]["/sovereign"]["get"]
    assert operation["security"] == [{"FirebaseBearer": []}]
    assert operation["x-arkadia-auth-boundary"]["minimum_access_level"] == 3


def test_sovereign_header_detection_is_case_insensitive():
    """A header name is case-insensitive, so the detector must be too.

    Measured on the canonical deployment at `fd0a4fdc`: `GET /api/orders` and
    `GET /api/ims/inquiries` returned 403 to an anonymous caller while the served
    document declared them `anonymous_no_auth_guard`, because the handlers spell
    the header `x-sovereign-key` and the detector matched `X-Sovereign-Key`.
    """
    app = FastAPI()

    @app.get("/lowercase")
    async def lowercase(request: Request):
        key = request.headers.get("x-sovereign-key", "")
        if not SOVEREIGN_KEY or key != SOVEREIGN_KEY:
            return {"refused": True}
        return {"key": key}

    @app.get("/mixed")
    async def mixed(request: Request):
        key = request.headers.get("X-Sovereign-Key", "")
        if not SOVEREIGN_KEY or key != SOVEREIGN_KEY:
            return {"refused": True}
        return {"key": key}

    install_openapi_security(app)
    schema = app.openapi()
    for path in ("/lowercase", "/mixed"):
        operation = schema["paths"][path]["get"]
        assert operation["security"] == [{"SovereignKeyHeader": []}], path
        assert (
            operation["x-arkadia-auth-boundary"]["classification"] == "sovereign_key_header"
        ), path


def test_sovereign_detector_negative_control_requires_the_header():
    """Naming only the env var is not a header gate, and must stay anonymous."""
    app = FastAPI()

    @app.get("/env-only")
    async def env_only():
        return {"configured": bool("SOVEREIGN_KEY")}

    install_openapi_security(app)
    operation = app.openapi()["paths"]["/env-only"]["get"]
    assert operation["security"] == []
    assert operation["x-arkadia-auth-boundary"]["classification"] == "anonymous_no_auth_guard"


def test_commune_thread_routes_declare_the_identity_they_enforce():
    """Every Arkana thread operation must declare the bearer it refuses without.

    The module refused anonymous callers with 401 while declaring `security: []`,
    so the served contract advertised a public surface that did not exist.
    """
    from api.main import app

    schema = app.openapi()
    expected = {
        ("get", "/api/commune/threads"),
        ("post", "/api/commune/threads"),
        ("get", "/api/commune/threads/{thread_uuid}"),
        ("patch", "/api/commune/threads/{thread_uuid}"),
        ("get", "/api/commune/threads/{thread_uuid}/messages"),
    }
    declared = {
        (method, path)
        for path, item in schema["paths"].items()
        if path.startswith("/api/commune/threads")
        for method in item
    }
    assert declared == expected, f"thread surface changed: {declared ^ expected}"
    for method, path in sorted(expected):
        operation = schema["paths"][path][method]
        assert operation["security"] == [{"FirebaseBearer": []}], f"{method} {path}"
        assert (
            operation["x-arkadia-auth-boundary"]["classification"] == "firebase_bearer"
        ), f"{method} {path}"


def test_thread_declaration_negative_control_the_detector_discriminates():
    """The same detector must call the pre-repair shape anonymous.

    A helper that refuses anonymous callers is not a FastAPI dependency, so it
    declares nothing. This is the shape the thread routes had, and it proves the
    assertion above is not trivially true.
    """
    app = FastAPI()
    router = APIRouter()

    def _identity(request: Request) -> str:
        if not request.headers.get("authorization"):
            raise RuntimeError("Authentication required")
        return "uid"

    @router.get("/undeclared")
    async def undeclared(request: Request):
        return {"uid": _identity(request)}

    app.include_router(router)
    install_openapi_security(app)
    operation = app.openapi()["paths"]["/undeclared"]["get"]
    assert operation["security"] == []
    assert operation["x-arkadia-auth-boundary"]["classification"] == "anonymous_no_auth_guard"
