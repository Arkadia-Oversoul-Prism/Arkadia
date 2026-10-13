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


def _without_ts_comments(source: str) -> str:
    """Mask TS/JS comments without removing hashes inside strings or JSX classes."""
    out = []
    i = 0
    quote = None
    while i < len(source):
        char = source[i]
        if quote is not None:
            out.append(char)
            if char == "\\" and i + 1 < len(source):
                out.append(source[i + 1])
                i += 2
                continue
            if char == quote:
                quote = None
            i += 1
            continue
        if char in ("'", '"', "`"):
            quote = char
            out.append(char)
            i += 1
            continue
        if source.startswith("//", i):
            end = source.find("\n", i)
            if end == -1:
                break
            out.append("\n")
            i = end + 1
            continue
        if source.startswith("/*", i):
            end = source.find("*/", i + 2)
            if end == -1:
                break
            out.append("\n" * source[i:end + 2].count("\n"))
            i = end + 2
            continue
        out.append(char)
        i += 1
    return "".join(out)


def _hex_colour_literals(sources: dict[str, str]) -> list[tuple[str, str]]:
    """Hex colour literals in TS/TSX source, excluding comments.

    Design tokens live in ``tailwind.config.js`` (one shared palette) and
    ``index.css``; a page-local hex is styling drift, the defect Slice A exists
    to remove. Comments may mention pull-request numbers such as `#493`; those
    are not colour declarations and must not trip the detector.
    """
    pattern = re.compile(r"#[0-9A-Fa-f]{3,8}\b")
    return [
        (name, src)
        for name, src in sources.items()
        if pattern.search(_without_ts_comments(src))
    ]


def _ts_sources() -> dict[str, str]:
    return {
        str(p.relative_to(ROOT)): p.read_text(encoding="utf-8")
        for p in sorted(SRC.rglob("*.ts*"))
    }


def _opening_tag_at(src: str, start: int) -> tuple[str, str] | None:
    """``(tag_name, tag_text)`` for the JSX opening tag beginning at ``start``.

    Scans to the matching ``>`` while tracking brace depth and string quotes, so
    a ``=>`` inside a JSX expression container does not terminate the tag (a
    naive ``<[^>]*>`` match would cut the attribute list in half and hide the
    handler it is looking for).
    """
    m = re.match(r"<([A-Za-z][A-Za-z0-9.]*)", src[start:])
    if not m:
        return None
    i, depth, quote = start + 1, 0, None
    while i < len(src):
        c = src[i]
        if quote:
            if c == quote:
                quote = None
        elif c in "\"'`":
            quote = c
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == ">" and depth == 0:
            return m.group(1), src[start : i + 1]
        i += 1
    return None


def _elements_carrying_testid(src: str) -> list[tuple[str, str]]:
    """Every JSX element whose opening tag carries a ``data-testid``."""
    found = []
    for m in re.finditer(r"data-testid=", src):
        start = src.rfind("<", 0, m.start())
        if start == -1:
            continue
        tag = _opening_tag_at(src, start)
        if tag is not None and "data-testid=" in tag[1]:
            found.append(tag)
    return found


LENS_CONTROL_TESTID = re.compile(r"-lens-")


def _decorative_lens_controls(sources: dict[str, str]) -> list[str]:
    """Lens controls that cannot navigate — the decorative control §4 forbids.

    A per-lens testid marks something the user is meant to operate. If it is not
    a ``<button>`` carrying an ``onClick`` it does nothing. The strip *container*
    (``...-lenses``) carries no per-lens testid and is not a control, so it is
    deliberately out of scope.
    """
    defects = []
    for name, src in sources.items():
        for tag_name, tag_text in _elements_carrying_testid(src):
            if not LENS_CONTROL_TESTID.search(tag_text):
                continue
            if tag_name != "button" or "onClick" not in tag_text:
                defects.append(f"{name}: <{tag_name}> {tag_text[:70]!r}")
    return defects


def _lens_testid_owners(sources: dict[str, str]) -> list[str]:
    """Files that declare a per-lens testid — the lens strip's owner(s)."""
    return [
        name
        for name, src in sources.items()
        if any(LENS_CONTROL_TESTID.search(t) for _, t in _elements_carrying_testid(src))
    ]


SKIP_TARGET = 'id="main-content"'


def _skip_link_tag(shell_text: str) -> str | None:
    """The opening tag of the skip-to-content link, or None."""
    i = shell_text.find('data-testid="skip-to-content"')
    if i == -1:
        return None
    start = shell_text.rfind("<", 0, i)
    if start == -1:
        return None
    tag = _opening_tag_at(shell_text, start)
    return tag[1] if tag else None


def _main_landmark_tag(shell_text: str) -> str | None:
    """The ``<main>`` tag carrying the skip-link target id, or None."""
    for m in re.finditer(r"<main\b", shell_text):
        tag = _opening_tag_at(shell_text, m.start())
        if tag is not None and SKIP_TARGET in tag[1]:
            return tag[1]
    return None


def _keyboard_landmark_defects(shell_text: str) -> list[str]:
    """Reasons the shell is not keyboard-reachable. Empty == reachable.

    Keyboard reachability has three parts that fail independently: the skip link
    must exist, it must target a landmark that actually exists, and that
    landmark must be programmatically focusable (``tabIndex=-1``) or the browser
    clears the hash without moving focus.
    """
    defects = []
    tag = _skip_link_tag(shell_text)
    if tag is None:
        defects.append("no skip-to-content link")
    elif 'href="#main-content"' not in tag:
        defects.append("skip link does not target #main-content")
    landmark = _main_landmark_tag(shell_text)
    if landmark is None:
        defects.append("no content landmark with id=main-content")
    elif "tabIndex" not in landmark:
        defects.append("content landmark is not focusable")
    return defects


FOCUS_ON_ROUTE = re.compile(
    r"useEffect\(\s*\(\)\s*=>\s*\{.*?\.focus\(\)\s*;?\s*\}\s*,\s*\[current\]\s*\)",
    re.DOTALL,
)


def _focus_bound_to_route(shell_text: str) -> bool:
    """True when focus is moved to the content landmark on a route change."""
    return bool(FOCUS_ON_ROUTE.search(shell_text))


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
# The address bar agrees with the rendered surface (directive §5.2)
# ---------------------------------------------------------------------------


def _js_route_resolver(router_text: str) -> dict:
    """Evaluate ``resolvePath``/``routeForSurface``/``SURFACES`` in Node.

    The routing functions are pure and dependency-free, so they can be executed
    rather than pattern-matched. That matters here: the property under test is
    *what path a given inbound pathname resolves to*, which a source-text pin
    cannot observe — it can only restate the implementation.
    """
    import json
    import shutil
    import subprocess

    node = shutil.which("node")
    assert node, "node is required to evaluate the console router"

    def strip_types(source: str) -> str:
        source = re.sub(r"^import[^;]+;\s*$", "", source, flags=re.MULTILINE)
        source = re.sub(r"^export\s+", "", source, flags=re.MULTILINE)
        source = re.sub(r":\s*(?:SurfaceId|SurfaceDef\[\]|Route|string|boolean|Record<[^>]*>)\b", "", source)
        return source

    surfaces = strip_types(SURFACES_PATH.read_text(encoding="utf-8"))
    # The registry object is `as const`; strip the assertion for plain JS.
    router = strip_types(router_text).replace("as const", "")
    probes = [
        "/nexus",
        "/novanet",
        "/nexus/",
        "/",
        "/about",
        "/invented",
        "/login/",
        "/solariun/knowledge",
        "/oracle",
        "/commune",
    ]
    script = (
        surfaces
        + "\n"
        + router
        + "\n"
        + f"const probes = {json.dumps(probes)};\n"
        + "console.log(JSON.stringify(probes.map((p) => resolvePath(p).path)));\n"
    )
    result = subprocess.run(
        [node, "-e", script],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"router evaluation failed: {result.stderr.strip()}"
    return dict(zip(probes, json.loads(result.stdout)))


def _normalises_on_load(router_text: str) -> bool:
    """True when the router writes a resolved canonical path back to the address bar.

    Comments are stripped first: the pre-repair control below is proven by
    *removing the call*, and a detector that also matched the call's name in a
    comment would report the repaired file as unrepaired (and the control as
    passing) — the mention-vs-execution confusion this guard exists to avoid.
    """
    code = re.sub(r"//[^\n]*", "", router_text)
    return bool(re.search(r"history\.replaceState\([^)]*canonical", code))


def test_the_router_normalises_the_address_bar_to_a_declared_surface_path():
    """Every inbound pathname must resolve to a *declared* surface path, or to a
    section of one, and the router must write that canonical path back.

    The archived Prism did this once on load (`App.tsx:102 history.replaceState`);
    the console rendered the right surface but left the address bar holding the
    inbound alias, so a copied link kept propagating a path no surface declares.
    A section path (`/solariun/knowledge`) is canonical for its own surface — it
    is `<declared surface path>/<section>`, not a second surface.
    """
    resolved = _js_route_resolver(ROUTER)
    declared = set(_declared_paths(SURFACES))

    def is_canonical(path: str) -> bool:
        if path in declared:
            return True
        return any(path.startswith(f"{base}/") for base in declared if base != "/")

    undeclared = sorted({p for p in resolved.values() if not is_canonical(p)})
    assert undeclared == [], (
        f"inbound pathname(s) resolve to a path no surface declares: {undeclared}"
    )
    assert resolved["/nexus"] == "/novanet", resolved
    assert resolved["/oracle"] == "/arkana", resolved
    assert resolved["/commune"] == "/arkana", resolved
    assert resolved["/invented"] == "/", resolved
    # A section path is already canonical: normalising it must not flatten it.
    assert resolved["/solariun/knowledge"] == "/solariun/knowledge", resolved

    assert _normalises_on_load(ROUTER), (
        "the router must write the canonical path back to the address bar on load"
    )
    assert re.search(r"window\.location\.pathname !== canonical", ROUTER), (
        "the normalisation must be conditional, so a canonical path is not rewritten"
    )


def test_detector_flags_a_router_that_leaves_the_inbound_path_in_the_address_bar():
    """Negative control: the pre-repair shape — a router that resolves a surface
    but never rewrites the address bar — must be reported."""
    stale = ROUTER.replace(
        'window.history.replaceState({}, "", canonical);', "void canonical;"
    )
    assert stale != ROUTER, "control did not mutate router.ts -- detector unproven"
    assert not _normalises_on_load(stale), (
        "the detector must report a router that never rewrites the address bar"
    )
    assert _normalises_on_load(ROUTER), "the repaired router must not be reported"


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


def test_oracle_and_commune_reconcile_to_the_arkana_surface():
    """The archived Prism routed the Oracle view to `/oracle` (`commune: '/oracle'`)
    and also accepted `/commune` directly, and its home surface sent the Oracle
    portal to `commune`. The console names that surface `arkana`, so both inbound
    paths must reconcile to it.

    Without the aliases, `resolvePath` fell through to `home` -- a real archived
    deep link silently landed on Home instead of the Oracle. The paths are
    asserted *distinct from* the declared surface paths here because the
    soundness detector above already rejects a collision.
    """
    aliases = _path_aliases(ROUTER)
    assert aliases.get("/oracle") == "arkana", aliases
    assert aliases.get("/commune") == "arkana", aliases
    for legacy in ("/oracle", "/commune"):
        assert legacy not in _declared_paths(SURFACES), (
            f"{legacy} is an alias, not a second surface"
        )
    assert _alias_defects(ROUTER, SURFACES) == []


def test_detector_flags_an_oracle_alias_that_falls_through_to_home():
    """Negative control: the pre-repair shape -- `/oracle` and `/commune` absent
    from the alias table -- must be reported, not silently accepted."""
    repaired = _js_route_resolver(ROUTER)
    assert repaired["/oracle"] == "/arkana", repaired

    stripped = re.sub(
        r'\n\s*"/oracle": "arkana",\n\s*"/commune": "arkana",', "", ROUTER
    )
    assert stripped != ROUTER, "control did not mutate router.ts -- detector unproven"
    assert _js_route_resolver(stripped)["/oracle"] == "/", (
        "the control must reproduce the pre-repair fall-through to home"
    )
    assert _js_route_resolver(stripped)["/commune"] == "/"


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
    # Issue references in comments are not CSS colours; keep the detector precise.
    comments_only = {'src/pages/X.tsx': '// Related PR #493\\nconst label = "Solariun";'}
    assert _hex_colour_literals(comments_only) == []


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


# ---------------------------------------------------------------------------
# No decorative controls (directive §4 Slice A)
# ---------------------------------------------------------------------------


def test_no_lens_control_is_decorative():
    """A lens the user can see must be operable. On `75bbd859` the NovaNet lens
    strip rendered ``<span data-testid="novanet-lens-…">`` pills with no
    ``onClick`` — the decorative control §4 forbids, which reads as navigation
    and does nothing."""
    defects = _decorative_lens_controls(_ts_sources())
    assert defects == [], f"decorative lens control(s): {defects}"


def test_the_lens_strip_is_declared_once():
    """One control per surface. A second lens strip in a page would be a second
    sub-view model — the same class as a second navigation owner."""
    owners = _lens_testid_owners(_ts_sources())
    assert owners == ["web/arkadia_console/src/components/SurfaceLenses.tsx"], (
        f"the lens strip must be declared only in SurfaceLenses.tsx; found {owners}"
    )


def test_every_lens_control_navigates_through_the_shared_router():
    """A lens is real navigation, not local state: it must call ``onNavigate``,
    which the composition root binds to the shared router's ``navigate``."""
    lenses = (SRC / "components" / "SurfaceLenses.tsx").read_text(encoding="utf-8")
    assert "onNavigate(surface, l.id)" in lenses, (
        "a lens must navigate to its own section through the shared router"
    )
    assert re.search(r"case \"novanet\":\s*\n\s*return <NovaNetPage[^>]*onNavigate=\{navigate\}", APP), (
        "App.tsx must bind the NovaNet surface's onNavigate to the router's navigate"
    )


def test_detector_flags_a_decorative_lens_control():
    """Negative control: the exact pre-repair shape (a span with a per-lens
    testid) must be reported, and the repaired button must not be."""
    stale = {
        "src/pages/X.tsx": (
            '<span\n  key={l.id}\n  data-testid={`novanet-lens-${l.id}`}\n'
            '  className="rounded px-3 py-1"\n>\n  {l.label}\n</span>'
        )
    }
    defects = _decorative_lens_controls(stale)
    assert len(defects) == 1 and "span" in defects[0], defects
    repaired = {
        "src/components/SurfaceLenses.tsx": (
            '<button\n  type="button"\n  onClick={() => onNavigate(surface, l.id)}\n'
            '  data-testid={`surface-lens-${l.id}`}\n>\n  {l.label}\n</button>'
        )
    }
    assert _decorative_lens_controls(repaired) == [], "a navigable lens must not be flagged"


def test_detector_reads_the_whole_tag_when_a_handler_contains_an_arrow():
    """The pre-repair shape with an inline ``=>`` handler is the harder case: a
    naive ``<[^>]*>`` match stops at the ``=>`` and cannot see the ``onClick``.
    The scanner must read the whole opening tag."""
    live = {
        "src/components/SurfaceLenses.tsx": (
            '<button\n  key={l.id}\n  type="button"\n'
            '  onClick={() => onNavigate(surface, l.id)}\n'
            '  data-testid={`surface-lens-${l.id}`}\n'
            '  className={section === l.id ? "bg-white/5 text-azure" : "text-white/40"}\n>\n'
            "  {l.label}\n</button>"
        )
    }
    tags = _elements_carrying_testid(live["src/components/SurfaceLenses.tsx"])
    assert len(tags) == 1, tags
    tag_name, tag_text = tags[0]
    assert tag_name == "button" and "onClick" in tag_text
    assert _decorative_lens_controls(live) == []


# ---------------------------------------------------------------------------
# Keyboard reachability of the shared shell (directive §4 Slice A, §9)
# ---------------------------------------------------------------------------


def test_shell_is_keyboard_reachable_through_a_skip_link():
    """A persistent navigation block precedes every surface, so a keyboard user
    must be able to jump past it. The skip link must target a real, focusable
    content landmark — a link to a missing or unfocusable target is decorative.
    """
    assert _keyboard_landmark_defects(SHELL) == [], _keyboard_landmark_defects(SHELL)
    # The skip link must be hidden until focused, not permanently visible or
    # permanently hidden (either would make it unusable or noisy).
    tag = _skip_link_tag(SHELL)
    assert "sr-only" in tag and "focus:not-sr-only" in tag, tag


def test_route_change_moves_focus_to_the_content_landmark():
    """A navigation moves the app to a new surface; focus must follow it, or a
    screen-reader/keyboard user stays parked in the nav of the surface they left.
    """
    assert _focus_bound_to_route(SHELL), (
        "Shell.tsx must focus the content landmark in a useEffect keyed on the "
        "current surface (the route change), not leave focus on the old surface"
    )


def test_detector_flags_a_skip_link_with_no_target_landmark():
    """Negative control: the exact pre-repair shape — a skip link whose target
    id does not exist in the shell — must be reported."""
    stale = SHELL.replace('id="main-content"', 'id="somewhere-else"')
    assert stale != SHELL, "control did not mutate Shell.tsx -- detector unproven"
    assert any("no content landmark" in d for d in _keyboard_landmark_defects(stale)), (
        _keyboard_landmark_defects(stale)
    )


def test_detector_flags_a_skip_link_pointing_at_the_wrong_target():
    """Negative control: a skip link that exists but points somewhere other than
    the focusable landmark is not a skip link."""
    stale = SHELL.replace('href="#main-content"', 'href="#content"')
    assert stale != SHELL, "control did not mutate Shell.tsx -- detector unproven"
    assert any("does not target" in d for d in _keyboard_landmark_defects(stale)), (
        _keyboard_landmark_defects(stale)
    )


def test_detector_flags_an_unfocusable_content_landmark():
    """Negative control: dropping ``tabIndex`` leaves the landmark unfocusable;
    the hash change would not move keyboard focus, so this must be reported."""
    stale = re.sub(r"\n\s*tabIndex=\{-1\}\n", "\n", SHELL, count=1)
    assert stale != SHELL, "control did not mutate Shell.tsx -- detector unproven"
    assert any("not focusable" in d for d in _keyboard_landmark_defects(stale)), (
        _keyboard_landmark_defects(stale)
    )


def test_detector_flags_focus_that_is_not_bound_to_the_route():
    """Negative control: a ``focus()`` call that does not re-run per surface is
    the defect — it focuses once and never follows later navigation."""
    stale = SHELL.replace("}, [current]);", "}, []);")
    assert stale != SHELL, "control did not mutate Shell.tsx -- detector unproven"
    assert not _focus_bound_to_route(stale)


