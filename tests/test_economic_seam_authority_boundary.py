"""Conformance pin for the economic-seam authority boundary.

The sovereign economic-seam surface was merged by `f9ced6b6` ("Expose sovereign
economic seam scan in canonical Opportunity Radar") on top of `2a8f3c32`
("Repair economic seam provider evidence paths"). Its stated contract is a
*sovereign-only* scan: the UI hides the action behind `isSovereign`
(`access_level >= 3`), but hiding a button is not an authority boundary — the
boundary is the server dependency.

Before this file, no test reached `api.economic_seam_routes` at all: the only
suite that touched economic seams (`tests/test_market_data.py`) drives
`engine._scan_*` helpers directly and never constructs the router, so the
authority gate on `POST /api/economic-seams/scan` and `POST
/api/economic-seams/assess` was unpinned. A later refactor could swap
`require_sovereign` for `require_auth` — silently widening a sovereign mutation
surface to any authenticated node — without reddening the suite.

These are source-level + structural assertions in the repo's existing style.
The file carries negative controls: a detector that returns a constant would
be self-satisfying, so each control proves the detector fires on the weakened
form it claims to detect.
"""

from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

import api.auth as auth
import api.economic_seam_routes as esr
from api.auth import require_auth, require_sovereign


# ---------------------------------------------------------------------------
# Detector — resolves the auth callable a route depends on.
# ---------------------------------------------------------------------------

def _auth_dependency(routes, path: str, method: str):
    """Return the first security/auth dependency callable on a route, else None."""
    for route in routes:
        route_path = getattr(route, "path", None)
        methods = getattr(route, "methods", None) or set()
        if route_path == path and method.upper() in {m.upper() for m in methods}:
            dependant = getattr(route, "dependant", None)
            if dependant is None:
                return None
            for dep in dependant.dependencies:
                if dep.call in (require_auth, require_sovereign):
                    return dep.call
            return None
    return None


def _routes_app() -> FastAPI:
    app = FastAPI()
    app.include_router(esr.router)
    return app


# ---------------------------------------------------------------------------
# Structural pin: the mutation endpoints must depend on require_sovereign.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "path,method",
    [
        ("/api/economic-seams/scan", "POST"),
        ("/api/economic-seams/assess", "POST"),
    ],
)
def test_mutation_endpoints_depend_on_require_sovereign(path, method):
    assert _auth_dependency(esr.router.routes, path, method) is require_sovereign


@pytest.mark.parametrize(
    "path,method",
    [
        ("/api/economic-seams/status", "GET"),
        ("/api/economic-seams/opportunities", "GET"),
    ],
)
def test_read_endpoints_depend_on_require_auth_not_sovereign(path, method):
    dep = _auth_dependency(esr.router.routes, path, method)
    assert dep is require_auth


def test_detector_is_not_self_satisfying():
    """Negative control: the detector must distinguish a weakened gate.

    A route built with `Depends(require_auth)` instead of `Depends(require_sovereign)`
    must be reported as `require_auth` — otherwise
    `test_mutation_endpoints_depend_on_require_sovereign` could not detect a
    widened boundary.
    """
    probe = FastAPI()

    @probe.post("/weakened")
    async def _weakened(user: dict = Depends(require_auth)):  # noqa: ANN001
        return {}

    assert _auth_dependency(probe.routes, "/weakened", "POST") is require_auth
    assert _auth_dependency(probe.routes, "/weakened", "POST") is not require_sovereign


def test_detector_resolves_sovereign_when_present():
    """Positive control: the detector reports require_sovereign when it is the gate."""
    probe = FastAPI()

    @probe.post("/hardened")
    async def _hardened(user: dict = Depends(require_sovereign)):  # noqa: ANN001
        return {}

    assert _auth_dependency(probe.routes, "/hardened", "POST") is require_sovereign


# ---------------------------------------------------------------------------
# Behavioural pin: the live gate rejects before the mutation runs.
# ---------------------------------------------------------------------------

def test_scan_without_credentials_is_rejected(monkeypatch):
    """No token -> 401, and `scan_once` (the mutating action) is never invoked."""
    called = {"n": 0}
    monkeypatch.setattr(esr, "scan_once", lambda: called.__setitem__("n", called["n"] + 1) or {})

    response = TestClient(_routes_app()).post("/api/economic-seams/scan")

    assert response.status_code == 401
    assert called["n"] == 0


def test_scan_rejects_authenticated_non_sovereign(monkeypatch):
    """An authenticated node below access_level 3 must not reach the mutation.

    Negative control for the boundary: the fake user IS authenticated
    (`get_current_user` returns a real profile) but not sovereign, so a
    `require_auth`-only gate would let the request through. This must fail
    closed with 403 and must not call `scan_once`.
    """
    called = {"n": 0}
    monkeypatch.setattr(esr, "scan_once", lambda: called.__setitem__("n", called["n"] + 1) or {})

    async def _non_sovereign(request):  # noqa: ANN001
        return {"uid": "node-1", "access_level": 1}

    monkeypatch.setattr(auth, "get_current_user", _non_sovereign)

    response = TestClient(_routes_app()).post(
        "/api/economic-seams/scan", headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == 403
    assert called["n"] == 0


def test_scan_allows_sovereign_and_returns_scan_result(monkeypatch):
    """Positive control: a sovereign actor reaches the action and gets its result."""
    payload = {"sources": ["cbn_fx"], "records": 3}

    async def _sovereign(request):  # noqa: ANN001
        return {"uid": "sovereign-1", "access_level": 3}

    monkeypatch.setattr(auth, "get_current_user", _sovereign)
    monkeypatch.setattr(esr, "scan_once", lambda: payload)

    response = TestClient(_routes_app()).post(
        "/api/economic-seams/scan", headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == 200
    assert response.json() == payload
