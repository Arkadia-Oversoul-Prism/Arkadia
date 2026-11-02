"""Serve Arkadia's single user-facing application from the canonical FastAPI origin.

There is ONE application shell: the Arkadia Console in ``web/arkadia_console``. It
owns the origin-root SPA and every route the product declares — including the
operator surface at ``/operator`` and the external N-ATLaS tester at
``/n-atlas-lab`` (with ``/n-atlas-tester`` reconciled to it as an alias). Those are
*surface routes of one build*, not mounts of a second application.

Two frontends are not served:

* the retired Prism UI, archived under ``archive/frontend/arkadia-prism``;
* the former standalone operator application (``web/console``). Its capabilities
  were migrated into the canonical application's route hierarchy, so it is no
  longer built into the image and no longer mounted here. The source is retained in
  the tree so the retirement remains reversible; nothing in this module reads it.

Reserved prefixes are therefore backend namespaces only. ``/operator`` and the
N-ATLaS routes used to be listed here because a second bundle answered them; now
that the canonical SPA answers them, reserving them would make the SPA's own
surface routes fall through to the API and 404 on a hard load.
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
)


def configure_frontends(app: FastAPI, repo_root: str | Path | None = None) -> None:
    """Mount the one built frontend without shadowing backend routes.

    Missing build output is reported by omission rather than silently serving a
    different application's index. The Docker build is responsible for producing
    ``web/arkadia_console/dist`` before this function is called.
    """
    root = Path(repo_root).resolve() if repo_root else Path(__file__).resolve().parents[1]
    console_app_dist = root / "web" / "arkadia_console" / "dist"

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
