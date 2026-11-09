"""Engineering Lab API boundary guards.

EL-01 -> EL-10 gives the Lab governed hands: it may execute bounded work inside
a sandbox and record Lab state (sessions, runs, evidence, artifacts,
automations). It must never gain a *repository mutation path* or an *authority
path*. These guards encode that stronger invariant.

History: v0.1 asserted the router was entirely read-only (all GET). That was the
correct seal for the observational Lab. With the authorized EL substrate the
router now exposes Lab-state write endpoints, so the guard is sharpened from
"no writes at all" to "no repository/authority mutation" — which is the
boundary that must actually hold.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import yaml
from starlette.requests import Request

import api.lab_routes as lab_routes
from api.lab_routes import router

#: Substrings that would indicate a repository-mutation or authority surface.
FORBIDDEN_SURFACE_MARKERS = (
    "merge",
    "deploy",
    "production",
    "force-push",
    "force_push",
    "push",
    "k15",
    "k3",
    "provenance",
    "authority",
    "credential",
    "secret",
)

#: The complete set of mutating endpoints the Lab is permitted to expose. Every
#: one operates on *Lab state*, never on the repository. Adding an entry here is
#: a deliberate, reviewable act.
ALLOWED_MUTATION_ENDPOINTS = {
    "/api/lab/engineering/agents",
    "/api/lab/engineering/sessions",
    "/api/lab/engineering/sessions/{session_id}/authorize",
    "/api/lab/engineering/sessions/{session_id}/execute",
    "/api/lab/engineering/sessions/{session_id}/run-agent",
    "/api/lab/engineering/sessions/{session_id}/transition",
    "/api/lab/engineering/automations",
    "/api/lab/engineering/automations/{automation_id}/state",
    "/api/lab/engineering/voice/resolve",
    # The anonymous tester-session endpoint grants only a short-lived N-ATLaS
    # run capability; the run endpoint writes only the Lab session/run/evidence
    # records and remains subject-authenticated.
    "/api/lab/engineering/n-atlas/test-session",
    "/api/lab/engineering/n-atlas/run",
}


def test_lab_router_authentication_is_scoped_to_the_declared_natlas_public_paths(monkeypatch):
    routes = {route.path: route for route in router.routes}
    assert "/api/lab/overview" in routes
    assert routes["/api/lab/overview"].methods == {"GET"}

    dependency_names = {
        getattr(getattr(dep, "dependency", None), "__name__", "")
        for dep in router.dependencies
    }
    assert "require_lab_auth" in dependency_names
    assert lab_routes._PUBLIC_NATLAS_PATHS == {
        "/api/lab/engineering/n-atlas/catalog",
        "/api/lab/engineering/n-atlas/test-session",
    }

    calls = []

    async def require_auth_spy(request):
        calls.append(request.url.path)
        return {"uid": "test-subject"}

    def request_for(path: str) -> Request:
        return Request({
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": path,
            "raw_path": path.encode("utf-8"),
            "query_string": b"",
            "headers": [],
            "client": ("test", 1234),
            "server": ("test", 80),
        })

    monkeypatch.setattr(lab_routes, "require_auth", require_auth_spy)

    async def exercise_auth_boundary():
        for public_path in lab_routes._PUBLIC_NATLAS_PATHS:
            await lab_routes.require_lab_auth(request_for(public_path))
        assert calls == [], "only the two declared N-ATLaS paths may bypass account auth"

        protected_path = "/api/lab/engineering/overview"
        await lab_routes.require_lab_auth(request_for(protected_path))
        assert calls == [protected_path], "all other Lab routes must pass through require_auth"

    asyncio.run(exercise_auth_boundary())

    run_route = routes["/api/lab/engineering/n-atlas/run"]
    route_dependency_names = {
        getattr(getattr(dep, "dependency", None), "__name__", "")
        for dep in run_route.dependencies
    }
    assert "require_auth" in route_dependency_names


def test_lab_route_has_no_repository_mutation_surface():
    """No route may touch the repository, authority, provenance, or credentials."""
    for route in router.routes:
        path = route.path.lower()
        for marker in FORBIDDEN_SURFACE_MARKERS:
            assert marker not in path, (
                f"lab route '{route.path}' exposes a forbidden surface '{marker}'"
            )


def test_lab_mutation_endpoints_are_exactly_the_lab_state_set():
    """Every mutating endpoint must be a known Lab-state operation."""
    mutating = {
        route.path for route in router.routes if not (route.methods <= {"GET"})
    }
    assert mutating == ALLOWED_MUTATION_ENDPOINTS, (
        "the set of mutating Lab endpoints changed; review it against the "
        "no-repository-mutation boundary"
    )


def test_lab_has_no_merge_or_deploy_operation():
    """The substrate must never expose a merge/deploy operation."""
    from lab.engineering_lab.contracts import FORBIDDEN_OPERATIONS, HUMAN_ONLY

    assert "merge" in FORBIDDEN_OPERATIONS
    assert "production_deploy" in FORBIDDEN_OPERATIONS
    assert "MERGE" in HUMAN_ONLY
    assert "PRODUCTION_DEPLOY" in HUMAN_ONLY


def test_agent_loop_route_is_authenticated_and_bounded():
    routes = {route.path: route for route in router.routes}
    path = "/api/lab/engineering/sessions/{session_id}/run-agent"
    assert path in routes
    route = routes[path]
    assert route.methods == {"POST"}
    assert route.dependencies or router.dependencies
    from api.lab_routes import AgentLoopBody
    assert AgentLoopBody(objective="inspect", max_turns=1).max_turns == 1
    try:
        AgentLoopBody(objective="inspect", max_turns=9)
    except Exception:
        pass
    else:
        raise AssertionError("max_turns above 8 must be rejected by request validation")



def test_cp10_a_lab_test_gate_fails_on_pytest_failure():
    """The focused Lab boundary suite must be a required CI step, not best-effort."""
    workflow_path = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "sg-02-fe-2-v.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["validate"]["steps"]
    lab_step = next(step for step in steps if step.get("name") == "CP10-A Lab tests")

    assert lab_step.get("continue-on-error") is not True
    assert "set -o pipefail" in lab_step["run"]
