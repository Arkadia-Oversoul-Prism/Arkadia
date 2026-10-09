"""Serve Arkadia's user-facing applications from the canonical FastAPI origin.

The primary Arkadia experience is the existing Solariun/Arkana application in
web/public_prism. The reconciled operator console is mounted at /operator, while
the focused N-ATLaS tester remains reachable at its established direct routes.
All routes share the same origin, service, backend, and authorization boundary.
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
    prism_dist = root / "web" / "public_prism" / "dist"
    console_dist = root / "web" / "console" / "dist"

    if console_dist.is_dir() and (console_dist / "index.html").is_file():
        console_assets = console_dist / "assets"
        if console_assets.is_dir():
            app.mount(
                "/operator/assets",
                StaticFiles(directory=str(console_assets)),
                name="operator-assets",
            )

        async def console_index() -> FileResponse:
            return FileResponse(console_dist / "index.html")

        app.add_api_route("/operator", console_index, methods=["GET"], include_in_schema=False)
        app.add_api_route("/operator/", console_index, methods=["GET"], include_in_schema=False)
        app.add_api_route("/operator/{path:path}", console_index, methods=["GET"], include_in_schema=False)
        app.add_api_route("/n-atlas-lab", console_index, methods=["GET"], include_in_schema=False)
        app.add_api_route("/n-atlas-lab/", console_index, methods=["GET"], include_in_schema=False)
        app.add_api_route("/n-atlas-tester", console_index, methods=["GET"], include_in_schema=False)
        app.add_api_route("/n-atlas-tester/", console_index, methods=["GET"], include_in_schema=False)

    if prism_dist.is_dir() and (prism_dist / "index.html").is_file():
        prism_assets = prism_dist / "assets"
        if prism_assets.is_dir():
            app.mount(
                "/assets",
                StaticFiles(directory=str(prism_assets)),
                name="arkadia-assets",
            )

        async def prism_index() -> FileResponse:
            return FileResponse(prism_dist / "index.html")

        async def prism_route(path: str) -> FileResponse:
            requested = "/" + path.strip("/")
            if any(
                requested == prefix or requested.startswith(prefix + "/")
                for prefix in _RESERVED_PREFIXES
            ):
                raise HTTPException(status_code=404, detail="Route not found")

            # Serve root-level public files (icons, manifest, robots.txt) without
            # turning an unknown API/backend path into a successful SPA response.
            candidate = (prism_dist / path).resolve()
            if candidate != prism_dist and prism_dist in candidate.parents and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(prism_dist / "index.html")

        # api.main owns GET / so browser requests can receive the SPA while
        # non-browser health probes keep their historical JSON response. In
        # isolated tests or other apps, provide the root route if it is absent.
        has_root_get = any(
            getattr(route, "path", None) == "/"
            and "GET" in (getattr(route, "methods", None) or set())
            for route in app.routes
        )
        if not has_root_get:
            app.add_api_route("/", prism_index, methods=["GET"], include_in_schema=False)
        app.add_api_route("/{path:path}", prism_route, methods=["GET"], include_in_schema=False)
