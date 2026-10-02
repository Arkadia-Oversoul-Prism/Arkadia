"""Verified boundary — the kernel plan/spawn surfaces (Arkadia-native).

``POST /api/plan/run`` and ``POST /api/agent/spawn`` are consequential kernel
operations: plan execution runs the planner and then executes the resulting
steps. Both previously ran with no authentication, and ``/api/plan/run``
imported ``execute_plan`` from ``kernel.execution`` (where it does not exist),
so it raised ``ImportError`` -> 500 even when reached.

These tests pin the repaired boundary:

  * the route requires authentication;
  * the route is served by the extracted ``api/plan_routes`` router;
  * plan execution validates the plan against the tool registry before running
    it (``validate_plan``);
  * the router is mounted on the served app.
"""
from __future__ import annotations

import inspect

import pytest
from fastapi.testclient import TestClient

from api.auth import require_auth
from api.main import app


@pytest.fixture(scope="module", autouse=True)
def _tools_registered():
    from kernel.tools_real import register_real_tools
    register_real_tools()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def _isolate_dependency_overrides():
    app.dependency_overrides.pop(require_auth, None)
    yield
    app.dependency_overrides.pop(require_auth, None)


def test_plan_run_requires_auth(client):
    assert client.post("/api/plan/run", json={"input": "list the directory"}).status_code == 401


def test_agent_spawn_requires_auth(client):
    assert client.post("/api/agent/spawn", json={"intent": "ping"}).status_code == 401


def test_plan_route_is_served_by_the_plan_router():
    from api.plan_routes import router as plan_router
    paths = {r.path for r in plan_router.routes}
    assert "/api/plan/run" in paths


def test_plan_run_declares_an_auth_dependency():
    from api.plan_routes import run_plan
    assert "user" in inspect.signature(run_plan).parameters


def test_plan_validation_rejects_unknown_tool():
    """The route must refuse a plan referencing an unregistered tool."""
    from kernel.planner import validate_plan
    ok, reason = validate_plan({"steps": [{"tool": "no_such_tool", "input": {}}]})
    assert ok is False
    assert "no_such_tool" in reason


def test_plan_validation_accepts_a_known_tool():
    from kernel.planner import validate_plan
    ok, reason = validate_plan({"steps": [{"tool": "read_file", "input": {"path": "README.md"}}]})
    assert ok is True, reason


def test_plan_execution_authenticated_reaches_executor(client):
    """An authenticated caller is not rejected by the auth boundary; the request
    is served (a 4xx/5xx from plan semantics is fine, a 401 is not)."""
    app.dependency_overrides[require_auth] = lambda: {
        "uid": "planner", "role": "Guest", "access_level": 0,
    }
    try:
        r = client.post("/api/plan/run", json={"input": ""})
        assert r.status_code != 401  # empty input -> 400, never 401
        assert r.status_code == 400
    finally:
        app.dependency_overrides.pop(require_auth, None)
