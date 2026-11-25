"""A router that fails to import must fail a test, not vanish behind a warning.

``api/main.py`` mounts twelve routers inside ``try: ... except Exception:``
handlers that log a warning and continue. That fail-open shape is deliberate —
one broken optional surface must not take the whole application down — but it
means a failed import produces a *healthy-looking* application whose surface is
gone: ``/health`` still answers, every other router still answers, and the only
signal is one WARNING line in the boot log.

Nothing asserted the composed surface. ``tests/test_solspire_route_composition.py``
builds its own ``FastAPI()`` and includes the SolSpire router directly, so it
passes whether or not ``api.main`` mounted it; a test that imports a router
module directly fails on an import error, which is a different property from
"the composition root mounted what it declared".

This module binds the composition root instead: every fail-open mount must carry
its routes on the real ``app``. The mount list is derived from ``api/main.py`` by
AST rather than restated here, so a new fail-open mount is judged by the same
rule without editing this file.
"""
from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

from fastapi.routing import APIRoute
from starlette.routing import Match

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "api" / "main.py"


def _fail_open_mounts(source: str) -> list[tuple[str, str]]:
    """``(include_variable, module)`` for every mount that fails open.

    A mount fails open when its ``include_router`` call sits in a ``try`` whose
    handlers never ``raise``. A mount whose handler re-raises already breaks boot
    on a failed import, so it needs no guard here.
    """
    mounts: list[tuple[str, str]] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Try):
            continue
        if any(isinstance(stmt, ast.Raise) for handler in node.handlers for stmt in ast.walk(handler)):
            continue
        imported = {
            alias.asname or alias.name: stmt.module
            for stmt in node.body
            if isinstance(stmt, ast.ImportFrom) and stmt.module
            for alias in stmt.names
        }
        for stmt in node.body:
            for call in ast.walk(stmt):
                if not (
                    isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Attribute)
                    and call.func.attr == "include_router"
                    and call.args
                    and isinstance(call.args[0], ast.Name)
                ):
                    continue
                variable = call.args[0].id
                if variable in imported:
                    mounts.append((variable, imported[variable]))
    return mounts


def _leaf_routes(routes) -> list[tuple[tuple[str, ...], str]]:
    """Every ``(methods, path)`` a router declares, including nested includes."""
    leaves: list[tuple[tuple[str, ...], str]] = []
    for route in routes:
        path = getattr(route, "path", None)
        if isinstance(route, APIRoute) and path:
            methods = tuple(sorted(m for m in route.methods if m not in ("HEAD", "OPTIONS")))
            leaves.append((methods, path))
            continue
        inner = getattr(route, "original_router", None)
        if inner is not None:
            prefix = getattr(getattr(route, "include_context", None), "prefix", "") or ""
            leaves.extend((methods, prefix + sub) for methods, sub in _leaf_routes(inner.routes))
            continue
        if hasattr(route, "routes"):
            leaves.extend(_leaf_routes(route.routes))
    return leaves


def _reachable(app, path: str, method: str) -> bool:
    scope = {"type": "http", "method": method, "path": path, "headers": []}
    for route in app.routes:
        try:
            matched, _ = route.matches(scope)
        except Exception:
            continue
        if matched == Match.FULL:
            return True
    return False


def _missing_leaf_routes(app, router) -> list[str]:
    missing = []
    for methods, path in _leaf_routes(router.routes):
        for method in methods or ("GET",):
            if not _reachable(app, path, method):
                missing.append(f"{method} {path}")
    return missing


_SYNTHETIC_SWALLOWING = """
try:
    from pkg.a import router as _a_router
    app.include_router(_a_router)
except Exception as _a_err:
    logger.warning(f"[A] mount skipped: {_a_err}")
"""

_SYNTHETIC_LOUD = """
try:
    from pkg.b import router as _b_router
    app.include_router(_b_router)
except Exception:
    raise
"""


def test_the_extractor_finds_a_swallowing_mount():
    assert _fail_open_mounts(_SYNTHETIC_SWALLOWING) == [("_a_router", "pkg.a")]


def test_the_extractor_ignores_a_loud_mount():
    assert _fail_open_mounts(_SYNTHETIC_LOUD) == []


def test_every_fail_open_mount_carries_its_routes_on_the_composed_app():
    from api.main import app

    mounts = _fail_open_mounts(MAIN.read_text(encoding="utf-8"))
    assert len(mounts) >= 8, (
        f"the mount extractor found only {len(mounts)} fail-open mounts ({mounts}); "
        f"either api/main.py changed shape or the extractor broke"
    )
    assert "solspire.console_router" in [module for _, module in mounts], (
        "the SolSpire console mount is the largest fail-open surface and must be in the derived set"
    )

    failures = []
    for variable, module in mounts:
        missing = _missing_leaf_routes(app, importlib.import_module(module).router)
        if missing:
            failures.append(f"{module} ({variable}): {len(missing)} unreachable, e.g. {missing[:3]}")

    assert not failures, (
        "these routers are mounted inside a swallowing try/except but are NOT reachable "
        "on the composed app, so their import failed and only a WARNING recorded it:\n  "
        + "\n  ".join(failures)
    )


def test_a_skipped_mount_boots_a_healthy_app_with_the_surface_missing(monkeypatch):
    """The defect this guard exists for, executed rather than asserted.

    Blocking the SolSpire console import must still produce an app (the mount is
    fail-open), leave ``/health`` answering, and be *visible* to the detector
    above. The module is reloaded again afterwards, or every later test in the
    session would inherit a degraded application.
    """
    import api.main as main_module

    router = importlib.import_module("solspire.console_router").router
    assert _missing_leaf_routes(main_module.app, router) == [], (
        "the mount is already degraded before the control ran"
    )

    monkeypatch.setitem(sys.modules, "solspire.console_router", None)
    degraded = importlib.reload(main_module)
    try:
        assert _reachable(degraded.app, "/health", "GET"), (
            "a fail-open mount must leave the rest of the application serving"
        )
        missing = _missing_leaf_routes(degraded.app, router)
        assert missing, "a skipped mount was invisible to the detector"
    finally:
        monkeypatch.undo()
        importlib.reload(main_module)

    assert _missing_leaf_routes(main_module.app, router) == [], (
        "the control did not restore the composed app"
    )
