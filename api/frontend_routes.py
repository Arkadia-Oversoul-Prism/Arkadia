"""Serve Arkadia's user-facing applications from the canonical FastAPI origin.

The primary Arkadia experience is the Arkadia Console in web/arkadia_console.
The reconciled operator console is mounted at /operator, while the focused
N-ATLaS tester remains reachable at its established direct routes. All routes
share the same origin, service, backend, and authorization boundary.

The retired Prism UI is archived under archive/frontend/arkadia-prism and is no
longer served or built.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


_RESERVED_PREFIXES = (
    "/api",
    "/solspire",
    "/health",
    "/openapi.json",
    "/docs",
    "/redoc",
    "/static",
    "/operator",
    "/n-atlas-lab",
    "/n-atlas-tester",
)


def configure_frontends(app: FastAPI, repo_root: str | Path | None = None) -> None:
    """Mount built frontends without shadowing backend routes.

    Missing build output is reported by omission rather than silently serving a
    different application's index. The Docker build is responsible for producing
    both dist directories before this function is called.
    """
    root = Path(repo_root).resolve() if repo_root else Path(__file__).resolve().parents[1]
    console_app_dist = root / "web" / "arkadia_console" / "dist"
    operator_dist = root / "web" / "console" / "dist"

    if operator_dist.is_dir() and (operator_dist / "index.html").is_file():
        operator_assets = operator_dist / "assets"
        if operator_assets.is_dir():
            app.mount(
                "/operator/assets",
                StaticFiles(directory=str(operator_assets)),
                name="operator-assets",
            )

        async def operator_index() -> FileResponse:
            return FileResponse(operator_dist / "index.html")

        app.add_api_route("/operator", operator_index, methods=["GET"], include_in_schema=False)
        app.add_api_route("/operator/", operator_index, methods=["GET"], include_in_schema=False)
        app.add_api_route("/operator/{path:path}", operator_index, methods=["GET"], include_in_schema=False)
        app.add_api_route("/n-atlas-lab", operator_index, methods=["GET"], include_in_schema=False)
        app.add_api_route("/n-atlas-lab/", operator_index, methods=["GET"], include_in_schema=False)
        app.add_api_route("/n-atlas-tester", operator_index, methods=["GET"], include_in_schema=False)
        app.add_api_route("/n-atlas-tester/", operator_index, methods=["GET"], include_in_schema=False)

    if console_app_dist.is_dir() and (console_app_dist / "index.html").is_file():
        console_app_assets = console_app_dist / "assets"
        if console_app_assets.is_dir():
            app.mount(
                "/assets",
                StaticFiles(directory=str(console_app_assets)),
                name="arkadia-assets",
            )

        async def console_app_index() -> FileResponse:
            return FileResponse(console_app_dist / "index.html")

        async def console_app_route(path: str) -> FileResponse:
            requested = "/" + path.strip("/")
            if any(
                requested == prefix or requested.startswith(prefix + "/")
                for prefix in _RESERVED_PREFIXES
            ):
                raise HTTPException(status_code=404, detail="Route not found")

            # Serve root-level public files (icons, manifest, robots.txt) without
            # turning an unknown API/backend path into a successful SPA response.
            candidate = (console_app_dist / path).resolve()
            if candidate != console_app_dist and console_app_dist in candidate.parents and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(console_app_dist / "index.html")

        # api.main owns GET / so browser requests can receive the SPA while
        # non-browser health probes keep their historical JSON response. In
        # isolated tests or other apps, provide the root route if it is absent.
        has_root_get = any(
            getattr(route, "path", None) == "/"
            and "GET" in (getattr(route, "methods", None) or set())
            for route in app.routes
        )
        if not has_root_get:
            app.add_api_route("/", console_app_index, methods=["GET"], include_in_schema=False)
        app.add_api_route("/{path:path}", console_app_route, methods=["GET"], include_in_schema=False)
