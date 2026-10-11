from fastapi import FastAPI
from fastapi.testclient import TestClient
from pathlib import Path

from api.frontend_routes import configure_frontends


def _write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_canonical_frontend_routes_share_one_origin_and_preserve_backend(tmp_path):
    console_app = tmp_path / "web" / "arkadia_console" / "dist"
    operator = tmp_path / "web" / "console" / "dist"
    _write(console_app / "index.html", "<html>ARKADIA-CONSOLE-APP</html>")
    _write(console_app / "assets" / "console.js", "console-asset")
    _write(console_app / "arkadia-mark.svg", "<svg>mark</svg>")
    _write(operator / "index.html", "<html>ARKADIA-OPERATOR-APP</html>")
    _write(operator / "assets" / "operator.js", "operator-asset")

    app = FastAPI()

    @app.get("/api/known")
    async def known_api():
        return {"ok": True}

    configure_frontends(app, tmp_path)
    client = TestClient(app)

    # The primary application is the Arkadia Console, served at the root.
    assert client.get("/").text == "<html>ARKADIA-CONSOLE-APP</html>"
    assert client.get("/solariun/opportunity-radar").text == "<html>ARKADIA-CONSOLE-APP</html>"
    assert client.get("/arkana").text == "<html>ARKADIA-CONSOLE-APP</html>"
    assert client.get("/assets/console.js").text == "console-asset"
    assert client.get("/arkadia-mark.svg").text == "<svg>mark</svg>"

    # The reconciled operator console remains mounted at /operator.
    assert client.get("/operator").text == "<html>ARKADIA-OPERATOR-APP</html>"
    assert client.get("/operator/inspector").text == "<html>ARKADIA-OPERATOR-APP</html>"
    assert client.get("/operator/assets/operator.js").text == "operator-asset"
    assert client.get("/n-atlas-tester").text == "<html>ARKADIA-OPERATOR-APP</html>"

    assert client.get("/api/known").json() == {"ok": True}
    assert client.get("/api/unknown").status_code == 404
    assert client.get("/solspire/not-a-real-route").status_code == 404


def test_frontend_mounts_are_omitted_when_build_output_is_missing(tmp_path):
    app = FastAPI()
    configure_frontends(app, tmp_path)
    client = TestClient(app)

    assert client.get("/api/missing").status_code == 404


# ── every declared console surface must be servable on the FastAPI origin ────
#
# The CP10 browser gate drives the Vite dev server (port 5000), which serves the
# SPA for *every* path and therefore cannot detect a surface path that collides
# with a reserved backend namespace. On the canonical FastAPI origin such a path
# falls through to the API and returns raw JSON (404 from the SPA handler's
# reserved-prefix guard, or a backend handler's own status). A hard load or
# refresh of that route is broken even though client-side navigation masks it.
# This binds each declared surface path to the served SPA deterministically.
import re as _re

from api.frontend_routes import _RESERVED_PREFIXES

_CONSOLE_SURFACES = (
    Path(__file__).resolve().parents[1] / "web" / "arkadia_console" / "src" / "lib" / "surfaces.ts"
)


def _declared_console_paths() -> list[str]:
    text = _CONSOLE_SURFACES.read_text(encoding="utf-8")
    return _re.findall(r'path: "([^"]+)"', text)


def test_every_console_surface_path_is_served_as_the_spa(tmp_path):
    _write(tmp_path / "web" / "arkadia_console" / "dist" / "index.html", "<html>ARKADIA-CONSOLE-APP</html>")
    app = FastAPI()
    configure_frontends(app, tmp_path)
    client = TestClient(app)

    paths = _declared_console_paths()
    assert paths, "no console surface paths were declared -- the guard would be vacuous"
    for path in paths:
        r = client.get(path, headers={"Accept": "text/html,application/xhtml+xml"})
        assert r.status_code == 200, f"surface path {path} is not served (status {r.status_code})"
        assert r.text == "<html>ARKADIA-CONSOLE-APP</html>", (
            f"surface path {path} did not resolve to the console SPA -- it collides "
            f"with a reserved backend namespace or a backend handler. Body: {r.text[:80]!r}"
        )


def test_console_surface_paths_avoid_reserved_namespaces():
    """The negative control: a surface declared on a reserved prefix is exactly the
    defect the guard above prevents. Pin the reserved list and prove a colliding
    path is rejected, so the guard cannot be disarmed by editing surfaces.ts
    alone."""
    for path in _declared_console_paths():
        for prefix in _RESERVED_PREFIXES:
            assert not (path == prefix or path.startswith(prefix + "/")), (
                f"console surface path {path} collides with reserved backend prefix {prefix}"
            )
    # The detector would flag the pre-repair path.
    colliding = "/solspire"
    assert any(colliding == p or colliding.startswith(p + "/") for p in _RESERVED_PREFIXES)


# ── a declared surface must not be shadowed by a real backend handler ────────
#
# The reserved-prefix list is a static denylist. A surface can also be broken by
# a *real, non-reserved* backend route: FastAPI matches that handler before the
# SPA catch-all, so the route returns raw JSON instead of the console. The test
# above cannot see this -- it registers no backend handlers. This guard scans the
# real `api.main` route table, so a surface added on top of any existing handler
# (for example `/health`) is caught rather than shipping as a raw-JSON response.
from starlette.routing import Match as _Match


def _routes_shadowing(surface_path: str, routes) -> list[str]:
    """Return the non-SPA route paths that would handle a GET for ``surface_path``."""
    scope = {"type": "http", "method": "GET", "path": surface_path, "headers": []}
    shadowing = []
    for route in routes:
        path = getattr(route, "path", None)
        if path in ("/", "/{path:path}"):
            continue  # the SPA mount owns these
        try:
            matched, _ = route.matches(scope)
        except Exception:
            continue
        if matched == _Match.FULL:
            shadowing.append(path or getattr(route, "path_format", "?"))
    return shadowing


def test_console_surface_paths_are_not_shadowed_by_a_backend_route():
    """Each declared surface must reach the SPA, not a backend handler. On the
    canonical origin a shadowing handler wins the match and the surface serves
    raw JSON -- the exact failure the reserved-prefix test alone would miss."""
    from api.main import app as canonical_app

    routes = list(canonical_app.routes)
    for path in _declared_console_paths():
        shadowing = _routes_shadowing(path, routes)
        assert not shadowing, (
            f"console surface path {path} is shadowed by backend route(s) {shadowing}; "
            f"it would serve raw JSON instead of the console SPA"
        )


def test_shadowing_detector_flags_a_non_reserved_backend_route():
    """Negative control: the detector must flag a surface placed on a real,
    non-reserved handler. `/health` is not in the reserved list, so only this
    route-table scan can catch it."""
    from fastapi import FastAPI as _FastAPI

    probe = _FastAPI()

    @probe.get("/dashboard")
    async def _dashboard():
        return {"backend": "json"}

    assert _routes_shadowing("/dashboard", list(probe.routes)) == ["/dashboard"]
    # A path with no handler is not shadowed -- the detector is not trivially true.
    assert _routes_shadowing("/enterprise", list(probe.routes)) == []
