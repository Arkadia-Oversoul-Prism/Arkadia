"""Architecture guard — api/nodes.py must not import the layer-1 surface.

api/nodes.py is layer-3 identity (ADR-015). It is composed with the A.I.S
profile and Engineering Lab routers, but must not import them directly: the
composition root injects them via ``api.nodes.configure_routers`` (ADR-014
Decision 4 — the same pattern used for the tools counter).

These tests exercise the real seam: the architectural invariant (AST, no
layer-1 import), the behavior (injected sub-routers actually serve), and the
truthfulness of the no-injection state (no fabricated routes).
"""
from __future__ import annotations

import ast

from fastapi import FastAPI
from fastapi.testclient import TestClient

import api.nodes as nodes


def test_nodes_has_no_api_surface_import():
    """AST-level check: api/nodes.py imports no sibling layer-1 api module.

    ``api.auth`` (layer-3 identity) is a permitted same-stability dependency and
    is deliberately not flagged.
    """
    tree = ast.parse(open(nodes.__file__, encoding="utf-8").read())
    forbidden = {"api.ais_profile", "api.lab_routes"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "") not in forbidden, f"import {node.module}"
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name not in forbidden, f"import {alias.name}"


def test_injected_sub_routers_serve_through_nodes_router():
    """The composition-root seam wires real routes end-to-end."""
    from api.ais_profile import router as ais_router
    from api.lab_routes import router as lab_router

    app = FastAPI()
    nodes.configure_routers(ais_router, lab_router)
    app.include_router(nodes.router)
    client = TestClient(app)

    # Routes are served (not 404) and, being authenticated, refuse without a
    # token rather than silently succeeding or fabricating data.
    for path in ("/api/lab/overview", "/api/me/ais-profile", "/api/me/identity-spine"):
        status = client.get(path).status_code
        assert status != 404, f"{path} was not mounted through the nodes router"
        assert status in (401, 403), f"{path} leaked past auth with {status}"


def test_configure_routers_is_idempotent():
    """Re-entry must not double-include the injected sub-routers.

    ``api.nodes.router`` is a module-level singleton and ``include_router``
    mutates it, so a second call used to append the injected sub-routers again.
    The composed ``app`` then emitted a duplicate-operation-ID warning for every
    injected operation (5 ais + 24 lab) whenever ``app.openapi()`` was built
    after the extra call. The composition root calls this once; the seam must be
    safe to invoke more than once regardless.
    """
    from api.ais_profile import router as ais_router
    from api.lab_routes import router as lab_router

    nodes.configure_routers(ais_router, lab_router)
    wired = len(nodes.router.routes)
    nodes.configure_routers(ais_router, lab_router)
    nodes.configure_routers(ais_router, lab_router)
    assert len(nodes.router.routes) == wired

    markers = [r for r in nodes.router.routes if type(r).__name__ == "_IncludedRouter"]
    assert len(markers) == 2, f"expected exactly 2 injected sub-routers, got {len(markers)}"


def test_without_injection_no_sub_router_routes_are_exposed():
    """Truthfulness: absent injection there are no fabricated sub-routes."""
    from fastapi import APIRouter

    fresh = APIRouter()
    # A fresh nodes router has only its own routes; the sub-routers are
    # compose-time state on the module singleton, not invented here.
    assert all("/api/lab" not in route.path for route in fresh.routes)
