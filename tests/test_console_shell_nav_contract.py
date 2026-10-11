"""Console shell / navigation / design-system contract (Slice A).

Directive §5 and §9 require that a route/suffix or shell decision be *explicit
and regression-protected*, and that one global navigation model and one router
survive reconciliation. These are source-level contracts over
``web/arkadia_console`` — this repository's frontend-test convention — and each
detector carries a negative control so it cannot be disarmed by editing the
console source alone.

Domain: the Arkadia Console (``web/arkadia_console``), the primary application.
The retired Prism UI is archived under ``archive/frontend/arkadia-prism`` and is
not built or served.

The assertions here are deliberately disjoint from the existing guards:
``test_canonical_frontend_routing.py`` (reserved prefixes + backend-route
shadowing), ``test_aeas05_canonical_frontend_acceptance.py`` (auth threshold +
CP10 gate testids) and ``test_frontend_arkadia_console_rebuild_01.py`` (archive
preservation). This file covers what none of them do: one navigation model, one
router/surface declaration, no hardcoded deployment origin, no page-local colour
literals, and surface -> composition-root wiring.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "web" / "arkadia_console"
SRC = CONSOLE / "src"
SURFACES_PATH = SRC / "lib" / "surfaces.ts"
ROUTER_PATH = SRC / "lib" / "router.ts"
SHELL_PATH = SRC / "components" / "Shell.tsx"
APP_PATH = SRC / "App.tsx"
APPCONFIG_PATH = SRC / "lib" / "apiConfig.ts"
INDEX_CSS_PATH = SRC / "index.css"
TAILWIND_PATH = CONSOLE / "tailwind.config.js"

SURFACES = SURFACES_PATH.read_text(encoding="utf-8")
ROUTER = ROUTER_PATH.read_text(encoding="utf-8")
SHELL = SHELL_PATH.read_text(encoding="utf-8")
APP = APP_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Detectors (module-level so the negative controls exercise the same code the
# live assertions use — a detector that is only proven on synthetic input, or
# only on the live tree, proves nothing about the other).
# ---------------------------------------------------------------------------


def _declared_surface_ids(text: str) -> list[str]:
    """The ids in the ``SurfaceId`` union of surfaces.ts."""
    union = re.search(r"export type SurfaceId\s*=\s*(.*?);", text, re.DOTALL)
    assert union, "surfaces.ts declares no SurfaceId union"
    return re.findall(r'"([^"]+)"', union.group(1))


def _declared_paths(text: str) -> list[str]:
    return re.findall(r'path: "([^"]+)"', text)


def _composition_root_surface_ids(text: str) -> set[str]:
    """The surface ids App.tsx switches on.

    The composition root dispatches on ``switch (route.surface)``. A declared
    surface with no case silently renders the default — a blank surface with no
    type error and no test failure. This is the detector for that class.
    """
    return set(re.findall(r'case "([^"]+)":', text))


def _hardcoded_origins(sources: dict[str, str]) -> list[tuple[str, str]]:
    """Absolute deployment origins in frontend source.

    ``http://``/``https://`` URL *literals* are deployment origins. Relative
    imports and type references contain no scheme, so they are unaffected. The
    canonical API base is resolved at runtime (``apiConfig.ts``); a hardcoded
    origin is the second-API-base defect directive §5.5 forbids.
    """
    pattern = re.compile(r"""["'`]https?://""")
    return [(name, src) for name, src in sources.items() if pattern.search(src)]


def _hex_colour_literals(sources: dict[str, str]) -> list[tuple[str, str]]:
    """Hex colour literals in TS/TSX source.

    Design tokens live in ``tailwind.config.js`` (one shared palette) and
    ``index.css``; a page-local hex is styling drift, the defect Slice A exists
    to remove.
    """
    pattern = re.compile(r"#[0-9A-Fa-f]{3,8}\b")
    return [(name, src) for name, src in sources.items() if pattern.search(src)]


def _ts_sources() -> dict[str, str]:
    return {
        str(p.relative_to(ROOT)): p.read_text(encoding="utf-8")
        for p in sorted(SRC.rglob("*.ts*"))
    }


# ---------------------------------------------------------------------------
# One navigation model, one router/surface declaration
# ---------------------------------------------------------------------------


def test_navigation_model_is_declared_exactly_once():
    """One global navigation model: the shell renders the surface table, and no
    other component owns a navigation list (directive §5.1, §4 Slice A)."""
    nav_modules = [name for name in _ts_sources() if "NAV_SURFACES" in _ts_sources()[name]]
    assert nav_modules == [str(SHELL_PATH.relative_to(ROOT))], (
        f"the navigation model must live only in Shell.tsx; found {nav_modules}"
    )
    assert "NAV_SURFACES = SURFACES.filter" in SHELL, (
        "the shell must derive navigation from the surface table, not a second list"
    )


def test_shell_is_mounted_exactly_once():
    """A second shell mount would be a second navigation path. The composition
    root is the only place that mounts it."""
    importers = [name for name, src in _ts_sources().items() if "<Shell" in src]
    assert importers == [str(APP_PATH.relative_to(ROOT))], f"<Shell> is mounted in {importers}"


def test_router_module_owns_the_only_pathname_resolution():
    """One router: pathname -> surface resolution must live in router.ts only."""
    users = [
        name
        for name, src in _ts_sources().items()
        if "window.location.pathname" in src and name != str(ROUTER_PATH.relative_to(ROOT))
    ]
    assert users == [], f"pathname is parsed outside the shared router in {users}"


# ---------------------------------------------------------------------------
# Surfaces: declared -> routed -> composed
# ---------------------------------------------------------------------------


def test_every_surface_id_has_a_path_and_the_union_matches_the_table():
    ids = _declared_surface_ids(SURFACES)
    paths = _declared_paths(SURFACES)
    assert ids, "no surface ids declared -- the guard would be vacuous"
    assert len(paths) == len(ids), (
        f"surfaces.ts declares {len(ids)} ids but {len(paths)} paths; a surface "
        f"without a path cannot be routed"
    )
    assert len(set(paths)) == len(paths), f"duplicate surface path in surfaces.ts: {paths}"


def test_every_declared_surface_is_composed_in_the_app_root():
    """Every declared surface must be reachable in the composition root. A
    declared-but-unhandled surface renders the default page with no error."""
    declared = set(_declared_surface_ids(SURFACES))
    composed = _composition_root_surface_ids(APP)
    assert composed, "App.tsx has no surface switch -- the guard would be vacuous"
    missing = sorted(declared - composed)
    assert missing == [], (
        f"declared surface(s) {missing} have no case in App.tsx and would render the "
        f"default page instead of their own surface"
    )


# ---------------------------------------------------------------------------
# Legacy route aliases (directive §5.2/§5.6)
# ---------------------------------------------------------------------------


def _path_aliases(text: str) -> dict[str, str]:
    """The ``PATH_ALIASES`` map: legacy inbound path -> canonical SurfaceId."""
    block = re.search(r"PATH_ALIASES[^=]*=\s*\{(.*?)\}", text, re.DOTALL)
    assert block, "router.ts declares no PATH_ALIASES map"
    return dict(re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', block.group(1)))


def _alias_defects(router_text: str, surfaces_text: str) -> list[str]:
    """Reasons a declared alias would be wrong. Empty == every alias is sound."""
    aliases = _path_aliases(router_text)
    ids = set(_declared_surface_ids(surfaces_text))
    paths = set(_declared_paths(surfaces_text))
    defects = []
    for alias, target in sorted(aliases.items()):
        if target not in ids:
            defects.append(f"alias {alias!r} targets undeclared surface {target!r}")
        if alias in paths:
            defects.append(
                f"alias {alias!r} collides with the canonical path of a declared "
                f"surface -- an alias must not duplicate a real route"
            )
    return defects


def test_legacy_route_aliases_resolve_to_declared_surfaces_only():
    """A legacy path is an *alias*, never a second surface: it must resolve to a
    surface that is actually declared, and must not shadow a canonical path."""
    assert _path_aliases(ROUTER), (
        "no legacy alias declared -- if /nexus support was removed, delete this "
        "guard deliberately rather than letting it pass vacuously"
    )
    assert _alias_defects(ROUTER, SURFACES) == []


def test_nexus_is_an_alias_of_novanet_not_a_second_surface():
    """The archived Prism hub routed `novanet` to `/nexus`. Reconciliation keeps
    the inbound path working while owning exactly one canonical surface."""
    assert _path_aliases(ROUTER).get("/nexus") == "novanet"
    assert "/nexus" not in _declared_paths(SURFACES)


def test_detector_flags_an_alias_to_an_undeclared_surface():
    """Negative control: an alias pointing at a surface nobody declared is dead
    routing and must be reported."""
    broken = ROUTER.replace('"/nexus": "novanet"', '"/nexus": "retired-hub"')
    assert broken != ROUTER, "control did not mutate router.ts -- the detector is unproven"
    defects = _alias_defects(broken, SURFACES)
    assert any("undeclared surface" in d for d in defects), defects


def test_detector_flags_an_alias_that_shadows_a_canonical_path():
    """Negative control: an alias whose key is also a declared surface path would
    create the duplicate route §5.1 forbids."""
    shadowing = SURFACES.replace('path: "/arkana"', 'path: "/nexus"', 1)
    assert shadowing != SURFACES, "control did not mutate surfaces.ts -- the detector is unproven"
    defects = _alias_defects(ROUTER, shadowing)
    assert any("collides with the canonical path" in d for d in defects), defects


# ---------------------------------------------------------------------------
# No hardcoded deployment origin (directive §5.5)
# ---------------------------------------------------------------------------


def test_no_absolute_deployment_origin_in_console_source():
    """``apiConfig.ts`` resolves the API base at runtime; an absolute origin in
    source is a hardcoded fallback hostname / second API base."""
    offenders = _hardcoded_origins(_ts_sources())
    assert offenders == [], f"hardcoded deployment origin(s) in {[n for n, _ in offenders]}"
    assert "resolveBase" in APPCONFIG_PATH.read_text(encoding="utf-8"), (
        "apiConfig.ts must resolve the API base rather than embed it"
    )


# ---------------------------------------------------------------------------
# No page-local colour literals (directive §4 Slice A)
# ---------------------------------------------------------------------------


def test_design_tokens_are_not_bypassed_by_page_local_hex_literals():
    offenders = _hex_colour_literals(_ts_sources())
    assert offenders == [], f"hex colour literal(s) in {[n for n, _ in offenders]}"
    tailwind = TAILWIND_PATH.read_text(encoding="utf-8")
    for token in ("ink", "panel", "line", "gold", "emerald", "azure", "violet"):
        assert re.search(rf"\b{token}:", tailwind), f"tailwind token '{token}' is missing"
    index_css = INDEX_CSS_PATH.read_text(encoding="utf-8")
    # The shared field keeps its palette in index.css: the ink background and the
    # single aurora layer every surface sits on.
    assert "#080a11" in index_css.lower(), "index.css must carry the ink background token"
    assert ".aurora-bg" in index_css, "the single shared aurora field is defined in index.css"


# ---------------------------------------------------------------------------
# Negative controls — each detector must flag the defect it claims to detect.
# ---------------------------------------------------------------------------


def test_detector_flags_a_second_navigation_owner():
    """A second component with its own NAV list is exactly the defect. Feed the
    detector the real shell plus a synthetic second owner."""
    shell = SHELL_PATH.read_text(encoding="utf-8")
    sources = {str(SHELL_PATH.relative_to(ROOT)): shell, "src/components/GhostNav.tsx": "const NAV_SURFACES = [];"}
    owners = [name for name, src in sources.items() if "NAV_SURFACES" in src]
    assert len(owners) == 2, "the navigation detector cannot see a second owner"


def test_detector_flags_a_hardcoded_origin():
    """The pre-repair form of a hardcoded API base must be reported."""
    stale = {'src/lib/apiConfig.ts': 'const FALLBACK = "https://arkadia-ten.vercel.app";'}
    assert [n for n, _ in _hardcoded_origins(stale)] == ["src/lib/apiConfig.ts"]
    # A relative import carries no scheme and must NOT be flagged.
    clean = {'src/lib/x.ts': 'import { API_BASE } from "./apiConfig";'}
    assert _hardcoded_origins(clean) == []


def test_detector_flags_a_page_local_hex_literal():
    """A page-local hex is the styling drift Slice A removes."""
    stale = {'src/pages/X.tsx': '<span style={{ color: "#00D4AA" }} />'}
    assert [n for n, _ in _hex_colour_literals(stale)] == ["src/pages/X.tsx"]
    clean = {'src/pages/X.tsx': '<span className="text-emerald" />'}
    assert _hex_colour_literals(clean) == []


def test_detector_flags_a_declared_surface_with_no_composition_case():
    """A declared surface missing from the switch renders the default page. The
    detector must see the gap, and stay silent when the case is present."""
    surfaces = 'export type SurfaceId =\n  | "home"\n  | "ghost";\n'
    app_missing = 'switch (route.surface) {\n  case "home":\n    return <HomePage />;\n}'
    app_present = 'switch (route.surface) {\n  case "home":\n    return <HomePage />;\n  case "ghost":\n    return <GhostPage />;\n}'
    declared = set(_declared_surface_ids(surfaces))
    assert declared == {"home", "ghost"}
    assert declared - _composition_root_surface_ids(app_missing) == {"ghost"}
    assert declared - _composition_root_surface_ids(app_present) == set()
