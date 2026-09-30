"""The deployment guide's route table must describe the app that is actually served.

`DEPLOYMENT_GUIDE.md` advertised a legacy route set (`/health`, `/status`, `/oracle`,
`/threads`, `/arkadia/corpus`, `/arkadia/refresh`) that does not exist on `api.main:app` —
the app `entrypoint.sh` runs. Every one of them answers `404` in production, so the
document contradicted the deployed contract. These tests pin the table to the served
OpenAPI schema so the two cannot drift apart again.
"""

import re
from pathlib import Path

import pytest

GUIDE = Path(__file__).resolve().parents[1] / "DEPLOYMENT_GUIDE.md"

# Routes the guide used to advertise. They are absent from the app; the table must not
# resurrect them without also registering them on `api.main:app`.
RETIRED_LEGACY_ROUTES = {
    "/health",
    "/status",
    "/oracle",
    "/threads",
    "/arkadia/corpus",
    "/arkadia/refresh",
}

_ROW = re.compile(r"^\|\s*`(?P<methods>[^`]+)`\s*\|\s*`(?P<path>[^`]+)`\s*\|", re.MULTILINE)


def _documented_routes() -> set[tuple[str, str]]:
    """Return {(METHOD, path)} parsed from the guide's endpoint table."""
    rows = _ROW.findall(GUIDE.read_text(encoding="utf-8"))
    assert rows, "no endpoint table rows found in DEPLOYMENT_GUIDE.md"
    routes: set[tuple[str, str]] = set()
    for methods, path in rows:
        for method in methods.split(","):
            routes.add((method.strip().upper(), path.strip()))
    return routes


def _served_routes() -> set[tuple[str, str]]:
    """Return {(METHOD, path)} from the served app's OpenAPI schema."""
    from api.main import app

    schema = app.openapi()
    routes: set[tuple[str, str]] = set()
    for path, operations in schema["paths"].items():
        for method in operations:
            routes.add((method.upper(), path))
    return routes


def test_every_documented_route_is_served() -> None:
    documented = _documented_routes()
    served = _served_routes()

    missing = sorted(documented - served)
    assert not missing, (
        "DEPLOYMENT_GUIDE.md documents routes the app does not serve: "
        + ", ".join(f"{m} {p}" for m, p in missing)
    )


def test_retired_legacy_routes_are_not_advertised() -> None:
    documented_paths = {path for _, path in _documented_routes()}
    resurrected = sorted(RETIRED_LEGACY_ROUTES & documented_paths)
    assert not resurrected, (
        "DEPLOYMENT_GUIDE.md advertises retired legacy routes that 404 in production: "
        + ", ".join(resurrected)
    )


def test_canonical_health_route_is_documented() -> None:
    # `/api/heartbeat` is the health check railway.json points at; it must stay visible.
    assert ("GET", "/api/heartbeat") in _documented_routes()


@pytest.mark.parametrize("path", sorted(RETIRED_LEGACY_ROUTES))
def test_retired_legacy_route_is_actually_absent_from_the_app(path: str) -> None:
    served_paths = {served_path for _, served_path in _served_routes()}
    assert path not in served_paths, (
        f"{path} is now served — remove it from RETIRED_LEGACY_ROUTES and document it"
    )
