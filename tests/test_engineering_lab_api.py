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

import inspect

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
    # N-ATLaS external-tester onboarding (bounded tester session + governed
    # run). Both write only Lab state via the existing runtime; the tester
    # capability is a run-only, session-bound credential and neither endpoint
    # creates an account or a general authorization.
    "/api/lab/engineering/n-atlas/test-session",
    "/api/lab/engineering/n-atlas/run",
}

#: The only Lab paths reachable without an Arkadia account. Any other addition
#: is a widening of the anonymous surface and must fail this guard.
PUBLIC_NATLAS_PATHS = {
    "/api/lab/engineering/n-atlas/catalog",
    "/api/lab/engineering/n-atlas/test-session",
}


def test_lab_router_is_read_only_and_authenticated():
    routes = {route.path: route for route in router.routes}
    assert "/api/lab/overview" in routes
    route = routes["/api/lab/overview"]
    assert route.methods == {"GET"}
    assert router.dependencies
    dependency_names = {
        getattr(getattr(dep, "dependency", None), "__name__", "")
        for dep in router.dependencies
    }
    # The router-wide dependency is ``require_lab_auth`` — a thin wrapper that
    # delegates to ``require_auth`` and exempts the deliberate N-ATLaS public
    # tester paths. Assert both halves: the wrapper is the only gate, and the
    # anonymous surface is exactly the reviewed set.
    assert dependency_names == {"require_lab_auth"}
    from api.lab_routes import _PUBLIC_NATLAS_PATHS, require_lab_auth

    assert _PUBLIC_NATLAS_PATHS == PUBLIC_NATLAS_PATHS
    assert "require_auth" in inspect.getsource(require_lab_auth)


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
