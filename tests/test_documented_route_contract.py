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

# The guide carries several two-column tables that are not endpoint tables (component
# owners, environment variables). A row is an endpoint row only when its first cell names
# HTTP methods; without this gate ``| `PORT` | `entrypoint.sh` |`` is read as the route
# ``entrypoint.sh`` and reported as documented-but-unserved.
HTTP_METHODS = frozenset(
    {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE", "CONNECT"}
)


def _is_endpoint_row(methods: str) -> bool:
    tokens = [token.strip().upper() for token in methods.split(",")]
    return bool(tokens) and all(token in HTTP_METHODS for token in tokens)


def _documented_routes(guide: Path | None = None) -> set[tuple[str, str]]:
    """Return {(METHOD, path)} parsed from the guide's endpoint table."""
    rows = _ROW.findall((guide or GUIDE).read_text(encoding="utf-8"))
    assert rows, "no endpoint table rows found in DEPLOYMENT_GUIDE.md"
    routes: set[tuple[str, str]] = set()
    for methods, path in rows:
        if not _is_endpoint_row(methods):
            continue
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


def test_non_endpoint_rows_are_not_read_as_routes() -> None:
    """A two-column table that names no HTTP method is not an endpoint table.

    `DEPLOYMENT_GUIDE.md` documents component owners and environment variables in the same
    `| cell | cell |` shape. Reading those as routes reports e.g. `entrypoint.sh` as a
    documented-but-unserved path, which is a defect in the extractor, not in the document.
    """
    rows = [
        "| `PORT` | `entrypoint.sh` |",
        "| `ELEVENLABS_API_KEY` | `kernel/tts.py` |",
        "| `GET` | `/api/heartbeat` |",
    ]
    assert [m for m, _ in (_ROW.match(row).groups() for row in rows)] == [
        "PORT",
        "ELEVENLABS_API_KEY",
        "GET",
    ]
    assert [_is_endpoint_row(_ROW.match(row).group("methods")) for row in rows] == [
        False,
        False,
        True,
    ]


def test_the_detector_still_flags_a_documented_route_the_app_does_not_serve(
    tmp_path,
) -> None:
    """Negative control: gating on HTTP methods must not silence a genuine defect."""
    planted = tmp_path / "guide.md"
    planted.write_text(
        "| Methods | Path |\n|---|---|\n"
        "| `GET` | `/api/heartbeat` |\n"
        "| `POST` | `/api/totally-unserved-probe` |\n"
        "| `PORT` | `entrypoint.sh` |\n",
        encoding="utf-8",
    )
    documented = _documented_routes(guide=planted)
    assert ("POST", "/api/totally-unserved-probe") in documented
    assert ("PORT", "entrypoint.sh") not in documented

    missing = sorted(documented - _served_routes())
    assert ("POST", "/api/totally-unserved-probe") in missing
