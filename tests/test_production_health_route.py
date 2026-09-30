"""Gate 2 — production health route provenance.

The deployment contract pointed at a health endpoint that did not exist:

  * ``api/rate_limit.EXEMPT_PREFIXES`` exempts ``/health`` from rate limiting;
  * ``DEPLOYMENT_GUIDE.md`` and ``UPTIMEROBOT_SETUP.md`` direct operators to
    probe it;
  * ``api/main.py`` declared no such route, and ``git log -S`` shows it never did.

The operational consequence was live: ``GET /health`` on the Render service
returned **404**, so any monitor configured from the repository's own
documentation would report the service down.

These tests assert the invariant rather than the incident — that the exemption
list and the operator documentation bind to a route that actually exists — and
that ``/health`` is a *projection* of the canonical ``/api/heartbeat`` signal
rather than a second, independently-drifting liveness authority.

They run against the real composed FastAPI application through ``TestClient``,
as ``tests/test_m02_reasomate_truth.py`` does.
"""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app
from api.rate_limit import EXEMPT_PREFIXES

ROOT = Path(__file__).resolve().parents[1]
DEPLOYMENT_GUIDE = ROOT / "DEPLOYMENT_GUIDE.md"

CANONICAL_LIVENESS = "/api/heartbeat"
PRODUCTION_HEALTH = "/health"


def _declared_paths() -> set[str]:
    """Every path the composed application actually serves."""
    return set(app.openapi()["paths"])


def test_health_route_is_declared() -> None:
    """The route the deployment contract points at must exist."""
    paths = _declared_paths()
    assert PRODUCTION_HEALTH in paths, (
        f"{PRODUCTION_HEALTH} is not served by the application; every exemption "
        f"and operator instruction that names it is pointing at a 404"
    )


def test_rate_limit_exemption_binds_to_a_real_route() -> None:
    """An exemption for a non-existent *application* path is a silent contract violation.

    This is the regression: ``/health`` was exempted and documented while no
    route served it, so a monitor built from the repository's own instructions
    reported the service down.

    Scope note: only prefixes naming an application surface can be adjudicated
    here. ``/docs``, ``/redoc``, ``/openapi`` are FastAPI built-ins and
    ``/assets``, ``/favicon`` are static mounts — Starlette serves them outside
    the OpenAPI schema, so their absence from ``paths`` is correct, not a defect.
    """
    framework_or_static = ("/docs", "/redoc", "/openapi", "/assets", "/favicon")
    paths = _declared_paths()
    unbound = [
        p
        for p in EXEMPT_PREFIXES
        if p not in framework_or_static and not any(x.startswith(p) for x in paths)
    ]
    assert unbound == [], f"rate-limit exemptions binding to nothing: {unbound}"


def test_health_returns_200_and_is_a_projection_of_the_canonical_signal() -> None:
    """``/health`` mirrors ``/api/heartbeat``; it does not define its own status.

    The status is compared by value, never hardcoded, so this test stays green
    if the canonical signal changes and fails if the two ever disagree.
    """
    client = TestClient(app)
    health = client.get(PRODUCTION_HEALTH)
    heartbeat = client.get(CANONICAL_LIVENESS)

    assert health.status_code == 200
    assert heartbeat.status_code == 200
    assert health.json()["status"] == heartbeat.json()["status"], (
        "the production health status has drifted from the canonical liveness signal"
    )


def test_health_surface_is_bounded() -> None:
    """``/health`` exposes liveness only — no resonance, no internals.

    A monitor endpoint is unauthenticated by necessity, so it must not become a
    channel for detail the canonical signal does not already publish.
    """
    client = TestClient(app)
    body = client.get(PRODUCTION_HEALTH).json()
    assert set(body) == {"status", "path"}
    assert body["path"] == PRODUCTION_HEALTH


def test_operator_documentation_binds_to_the_declared_route() -> None:
    """Documentation that names ``/health`` must be matched by the route.

    Guards the other direction of the same defect: the contract and the code
    cannot drift apart again without this failing.
    """
    guide = DEPLOYMENT_GUIDE.read_text(encoding="utf-8")
    assert PRODUCTION_HEALTH in guide, "DEPLOYMENT_GUIDE.md no longer names the health route"
    assert PRODUCTION_HEALTH in _declared_paths()
