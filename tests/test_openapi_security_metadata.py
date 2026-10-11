"""Regression tests for explicit, operation-level OpenAPI security metadata."""
from fastapi import Depends, FastAPI

from api.openapi_security import install_openapi_security


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
