"""One served application, one route authority (ARK-UI-CONVERGENCE-001).

Two React applications used to be packaged into the same image and answered from
the same origin: the primary Arkadia Console at `/`, and a standalone operator
console mounted at `/operator` plus `/n-atlas-lab` and `/n-atlas-tester`. That is
two routing authorities over one backend.

The operator's capabilities were migrated into the canonical application's route
hierarchy, so `/operator`, `/n-atlas-lab` and `/n-atlas-tester` are now *surface
routes of the one build*. This module binds that fact from both directions:

* positively — every migrated route is served, and by the canonical SPA;
* negatively — a `web/console/dist` tree present on disk is never served, so the
  retired shell cannot be reactivated by leaving a stale build output behind.

The negative direction is the load-bearing one: a positive assertion alone would
still pass if BOTH applications were mounted, which is exactly the state this
change removed.
"""
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pathlib import Path

from api.frontend_routes import configure_frontends


def _write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


SECOND_SHELL_MARKER = "<html>ARKADIA-RETIRED-OPERATOR-APP</html>"


def _write_second_shell(tmp_path):
    """A complete, servable build of the retired application.

    This is not decoration: it is the control that proves the retirement is real.
    Before this change the same tree was mounted at `/operator`, so a test that
    omitted it could not distinguish "migrated" from "still mounted".
    """
    retired = tmp_path / "web" / "console" / "dist"
    _write(retired / "index.html", SECOND_SHELL_MARKER)
    _write(retired / "assets" / "operator.js", "retired-operator-asset")
    return retired


def test_canonical_frontend_routes_share_one_origin_and_preserve_backend(tmp_path):
    console_app = tmp_path / "web" / "arkadia_console" / "dist"
    _write(console_app / "index.html", "<html>ARKADIA-CONSOLE-APP</html>")
    _write(console_app / "assets" / "console.js", "console-asset")
    _write(console_app / "arkadia-mark.svg", "<svg>mark</svg>")
    _write_second_shell(tmp_path)

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

    # The migrated operator surface is a route of THAT application.
    for route in (
        "/operator",
        "/operator/inspector",
        "/operator/boundary/approval-not-execution",
        "/n-atlas-lab",
        "/n-atlas-tester",
    ):
        response = client.get(route)
        assert response.text == "<html>ARKADIA-CONSOLE-APP</html>", (
            f"{route} did not resolve to the canonical application; got {response.text[:60]!r}"
        )

    # ...and the retired application is not served anywhere, even though a valid
    # build of it exists on disk.
    retired_paths = (
        "/operator",
        "/operator/inspector",
        "/n-atlas-lab",
        "/assets/operator.js",
        "/operator/assets/operator.js",
    )
    for route in retired_paths:
        response = client.get(route)
        assert SECOND_SHELL_MARKER not in response.text, (
            f"{route} served the retired operator application — the second shell is "
            "still mounted somewhere in the serving path"
        )
    # The SPA catch-all answers an unrouted path with the canonical index — the
    # documented behaviour — so the retired bundle's asset path is not a 404; it
    # is the canonical application. What matters is that it is never the retired
    # asset, which the loop above asserts for this same path.
    assert client.get("/operator/assets/operator.js").text == "<html>ARKADIA-CONSOLE-APP</html>"

    assert client.get("/api/known").json() == {"ok": True}
    assert client.get("/api/unknown").status_code == 404
    assert client.get("/solspire/not-a-real-route").status_code == 404


def test_retired_shell_alone_is_not_mounted(tmp_path):
    """With only the retired build present, nothing is served at its old routes.

    The mount is keyed on the canonical build, not on "some dist exists", so a
    leftover `web/console/dist` cannot resurrect the second shell on its own.
    """
    _write_second_shell(tmp_path)

    app = FastAPI()
    configure_frontends(app, tmp_path)
    client = TestClient(app)

    for route in ("/", "/operator", "/n-atlas-lab", "/n-atlas-tester"):
        response = client.get(route)
        assert SECOND_SHELL_MARKER not in response.text
    assert client.get("/operator").status_code == 404


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
    # The migrated operator and N-ATLaS surface paths must be in the declared set,
    # or this guard would keep passing after they were dropped from the registry.
    assert "/operator" in paths, "the operator surface is no longer declared"
    assert "/n-atlas-lab" in paths, "the N-ATLaS surface is no longer declared"
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


def test_operator_routes_are_no_longer_reserved_backend_namespaces():
    """`/operator` and the N-ATLaS routes are surface routes of the SPA now.

    They were reserved only because a second bundle answered them. Keeping them in
    the reserved set would make a hard load of the SPA's own surface routes 404 —
    the failure mode the reserved-prefix guard exists to prevent, inverted.
    """
    for path in ("/operator", "/n-atlas-lab", "/n-atlas-tester"):
        assert path not in _RESERVED_PREFIXES, (
            f"{path} is a declared surface route and must not be reserved against the SPA"
        )


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
