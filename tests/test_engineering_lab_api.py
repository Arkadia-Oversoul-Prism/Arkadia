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
    "/api/lab/engineering/sessions/{session_id}/transition",
    "/api/lab/engineering/automations",
    "/api/lab/engineering/automations/{automation_id}/state",
    "/api/lab/engineering/voice/resolve",
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
    assert "require_auth" in dependency_names


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
