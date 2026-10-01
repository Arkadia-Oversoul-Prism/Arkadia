"""The deployment guide's route table must describe the app that is actually served.

`DEPLOYMENT_GUIDE.md` advertised a legacy route set (`/status`, `/oracle`, `/threads`,
`/arkadia/corpus`, `/arkadia/refresh`) that does not exist on `api.main:app` — the app
`entrypoint.sh` runs. Every one of them answers `404` in production, so the document
contradicted the deployed contract. These tests pin the table to the served OpenAPI
schema so the two cannot drift apart again.

`/health` is deliberately *not* in the retired set: it is a genuine two-state path
(absent on `main`, restored as a `/api/heartbeat` projection by PR #154) and is governed
by `test_health_route_documentation_matches_the_served_app` instead.
"""

import re
from pathlib import Path

import pytest

GUIDE = Path(__file__).resolve().parents[1] / "DEPLOYMENT_GUIDE.md"

# Legacy paths the guide used to advertise that the app has never served. The table must
# not resurrect them, and they must stay absent from `api.main:app`.
RETIRED_LEGACY_ROUTES = {
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


def test_health_route_documentation_matches_the_served_app() -> None:
    """`/health` is a two-state path (absent on main, restored by PR #154).

    Whichever state holds, the guide must say the matching thing: a served `/health`
    has to appear in the table, and an absent `/health` must not be advertised as
    probeable. This keeps the guard correct under either merge order instead of
    turning `main` red when #154 lands.
    """
    served = _served_routes()
    documented = _documented_routes()
    guide_text = GUIDE.read_text(encoding="utf-8")

    if ("GET", "/health") in served:
        assert ("GET", "/health") in documented, (
            "/health is served but the guide's table does not list it"
        )
        assert "is **not** served by this app" not in guide_text, (
            "/health is served but the guide still says it returns 404"
        )
    else:
        assert ("GET", "/health") not in documented, (
            "/health is not served but the guide's table advertises it"
        )
        assert "is **not** served by this app" in guide_text, (
            "/health is not served but the guide does not warn that it 404s"
        )
