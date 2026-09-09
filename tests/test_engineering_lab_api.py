from __future__ import annotations

from api.lab_routes import router


def test_lab_router_is_read_only_and_authenticated():
    routes = {route.path: route for route in router.routes}
    assert "/api/lab/overview" in routes
    route = routes["/api/lab/overview"]
    assert route.methods == {"GET"}
    assert router.dependencies
    dependency_names = {getattr(dep.call, "__name__", "") for dep in router.dependencies}
    assert "require_auth" in dependency_names


def test_lab_route_has_no_mutation_surface():
    assert all(route.methods <= {"GET"} for route in router.routes)
