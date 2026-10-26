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

#: The router's own authentication guard. It delegates to ``require_auth`` for
#: every path outside ``_PUBLIC_NATLAS_PATHS``, so the router is authenticated by
#: default through this name rather than through ``require_auth`` directly.
ROUTER_AUTH_DEPENDENCY = "require_lab_auth"

#: The paths the router exempts from authentication. This records the *declared*
#: public surface; it does not approve it. A path appearing here is reachable
#: without any caller identity.
DECLARED_PUBLIC_PATHS = {
    "/api/lab/engineering/n-atlas/catalog",
}

#: The complete set of mutating endpoints the Lab is permitted to expose. Every
#: one operates on *Lab state*, never on the repository. Adding an entry here is
#: a deliberate, reviewable act.
#:
#: This set is the *approved* set. It is deliberately not widened to match
#: whatever the router currently exposes: an endpoint that mutates Lab state
#: outside this set is an unapproved authority path, and the guard below fails
#: until a human dispositions it. Editing this set is a disposition, not a fix.
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
}

#: Public authority endpoints that still lack a human disposition. The
#: test-session route was dispositioned to require authentication; this set
#: remains empty unless another unauthenticated authority path is introduced.
#: The shared provenance defect is tracked separately and remains unresolved.
UNDISPOSITIONED_PUBLIC_AUTHORITY_ENDPOINTS: set[str] = set()


def test_lab_router_is_read_only_and_authenticated():
    routes = {route.path: route for route in router.routes}
    assert "/api/lab/overview" in routes
    route = routes["/api/lab/overview"]
    assert route.methods == {"GET"}
    assert router.dependencies, "the Lab router must carry an authentication dependency"
    dependency_names = {
        getattr(getattr(dep, "dependency", None), "__name__", "")
        for dep in router.dependencies
    }
    # The router authenticates by default through its own guard, which delegates
    # to ``require_auth`` for every non-public path. Asserting the delegating
    # guard (not the delegatee) is what actually holds here.
    assert ROUTER_AUTH_DEPENDENCY in dependency_names, (
        f"the Lab router must authenticate through {ROUTER_AUTH_DEPENDENCY!r}; "
        f"found {sorted(dependency_names)}"
    )


def test_public_lab_paths_are_exactly_the_declared_set():
    """The router's auth exemptions must match the declared public surface.

    An exemption added to the router without being declared here would make a
    path anonymous silently. This asserts the two agree, in both directions.
    """
    from api.lab_routes import _PUBLIC_NATLAS_PATHS

    assert set(_PUBLIC_NATLAS_PATHS) == DECLARED_PUBLIC_PATHS, (
        "the router's public-path exemptions changed; declare them here and "
        "review each one against the authentication boundary"
    )


def test_public_authority_endpoints_are_dispositioned():
    """No unauthenticated endpoint may reach the authority-recording call.

    ``runtime.record_authorization`` stamps every record ``originated_by="human"``
    and the store rejects any other value, so a request that reaches it without a
    human identity yields a record whose provenance is not truthful. A public
    endpoint that creates a workspace, agent, session, authorization record, and
    a bearer token therefore bypasses the substrate's stated invariant one layer
    above the layer that declares it.

    This guard fails while such a path exists. Clearing it requires a human
    disposition of the endpoint — narrowing the public surface, requiring
    authentication, or stopping short of ``AUTHORIZED`` — not an edit to the
    allow-list.
    """
    assert not UNDISPOSITIONED_PUBLIC_AUTHORITY_ENDPOINTS, (
        "unauthenticated authority-path endpoints require human disposition "
        f"before this guard can pass: "
        f"{sorted(UNDISPOSITIONED_PUBLIC_AUTHORITY_ENDPOINTS)}"
    )


def test_natlas_test_session_requires_authenticated_identity_and_tracks_open_provenance_gap():
    """Stage 1b: the route is authenticated and uses verified caller identity.

    This source-level guard does not claim the shared provenance defect is fixed:
    record_authorization still stamps originated_by="human" independently of an
    actual authorization event. Boundary B remains open for separate design.
    """
    import ast
    from pathlib import Path

    source = Path(__file__).resolve().parents[1] / "api" / "lab_routes.py"
    source_text = source.read_text(encoding="utf-8")
    tree = ast.parse(source_text)
    handler = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "n_atlas_test_session"
    )

    user_arg = next(arg for arg in handler.args.args if arg.arg == "user")
    assert isinstance(user_arg.annotation, ast.Name) and user_arg.annotation.id == "dict"
    user_default = handler.args.defaults[-1]
    assert isinstance(user_default, ast.Call)
    assert isinstance(user_default.func, ast.Name) and user_default.func.id == "Depends"
    assert len(user_default.args) == 1
    assert isinstance(user_default.args[0], ast.Name)
    assert user_default.args[0].id == "require_auth"
    handler_text = ast.get_source_segment(source_text, handler)
    assert 'uid = user["uid"]' in handler_text
    assert 'natlas-tester-' not in handler_text

    # Preserve the evidence boundary: this stage does not repair shared provenance.
    runtime_source = (
        Path(__file__).resolve().parents[1] / "lab" / "engineering_lab" / "runtime.py"
    ).read_text(encoding="utf-8")
    assert '"originated_by": "human"' in runtime_source, (
        "the shared provenance implementation changed; re-audit Boundary B"
    )

def test_lab_route_has_no_repository_mutation_surface():
    """No route may touch the repository, authority, provenance, or credentials."""
    for route in router.routes:
        path = route.path.lower()
        for marker in FORBIDDEN_SURFACE_MARKERS:
            assert marker not in path, (
                f"lab route '{route.path}' exposes a forbidden surface '{marker}'"
            )


def test_lab_mutation_endpoints_are_exactly_the_lab_state_set():
    """Every mutating endpoint must be an *approved* Lab-state operation.

    This compares the router's live mutating surface against the approved set
    rather than restating it, so a newly added mutating endpoint fails here
    instead of passing unnoticed. It reports the delta in both directions: an
    endpoint present in the router but absent from the approved set is an
    unapproved authority path, and an approved entry the router no longer serves
    is stale.
    """
    mutating = {
        route.path for route in router.routes if not (route.methods <= {"GET"})
    }
    unapproved = sorted(mutating - ALLOWED_MUTATION_ENDPOINTS)
    stale = sorted(ALLOWED_MUTATION_ENDPOINTS - mutating)
    assert not unapproved, (
        "the Lab exposes mutating endpoints outside the approved Lab-state set; "
        "each one requires a human disposition before it may be approved: "
        f"{unapproved}"
    )
    assert not stale, (
        f"the approved mutating set names endpoints the router does not serve: {stale}"
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
