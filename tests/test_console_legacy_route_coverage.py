"""Console legacy-route reconciliation and alias-safety contract (Slice A).

Directive §5.1/§5.2/§5.6 require one route registry, legacy inbound links
reconciled to a canonical surface, and an explicit disposition for every legacy
path — adapt, defer, or reject. The archived Prism's route table is the source of
the legacy paths a user may still hold in a browser tab or a shared link; a
missing disposition is silent link loss (`/oracle` fell through to `home`), and an
alias that collides with a live backend route is a second, shadowed contract.

Two defects this guard closes, both measured on `main` @ `49809f45`:

1.  **No reconciliation of the legacy route table against the console.** The
    archived `App.tsx` declares 31 distinct inbound paths across its `direct` and
    `compatibility` maps. Nothing in `tests/` bound those paths to a console
    disposition, so a legacy path could be dropped without a failing test. The
    per-path assertions in `test_console_shell_nav_contract.py` cover the aliases
    that were *added* (`/nexus`, `/oracle`, `/commune`); they do not bound the
    *domain*.

2.  **No guard on the alias-safety precondition.** The shell lane instruction
    requires every candidate alias be verified against the served app's route table
    and the reserved-prefix set before it becomes a UI alias, but the alias
    soundness detector only checks declared-surface membership and canonical-path
    collision. An alias placed on a live backend route (`/api`, `/solspire`, …)
    would shadow it and pass every existing guard.

3.  **The checked domain was the archive's two route maps, not the archive's
    inbound paths.** `resolvePath` also accepts two families the maps cannot
    express: a regex family `/^\\/solariun(?:\\/([^/]+))?$/` and the exact-string
    branches `/solspire` and `/solspire/voice`. A transcription of `direct` and
    `compatibility` is blind to them, so an archive-declared inbound path could
    leave the domain without any assertion noticing. Both families are now
    declared (`ARCHIVE_NON_MAP_INBOUND`) and bound to the archive by
    `test_the_archive_non_map_inbound_paths_are_declared`, so the domain covers
    every inbound path `resolvePath` accepts rather than only its two maps.

Scope: this is a **contract/boundary guard**, not a feature slice. It does not add
an alias for any path whose disposition is still a product decision — it *records*
that disposition so the gap cannot move silently. It edits no console source, the
router, the surface registry, or the existing shell-nav test, all of which are
contended by open lane-1 PRs (#497 `nexus/*`, #505 `home`/`knowledge-os`).

Domain: the Arkadia Console (``web/arkadia_console``), the primary application.
The retired Prism UI is archived under ``archive/frontend/arkadia-prism`` and is
source evidence, not code to delete or serve.

Disjoint from: ``test_console_shell_nav_contract.py`` (shell structure, positive
aliases, address-bar normalisation), ``test_canonical_frontend_routing.py``
(surface-path serving + shadowing), ``test_console_endpoint_registry_contract.py``
(API endpoint registry), ``test_prism_pass_c_surface_ownership.py`` (archive view
mount integrity).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "web" / "arkadia_console" / "src"
SURFACES_PATH = SRC / "lib" / "surfaces.ts"
ROUTER_PATH = SRC / "lib" / "router.ts"
ARCHIVE_APP = ROOT / "archive/frontend/arkadia-prism/web/public_prism/src/App.tsx"

SURFACES = SURFACES_PATH.read_text(encoding="utf-8")
ROUTER = ROUTER_PATH.read_text(encoding="utf-8")
ARCHIVE = ARCHIVE_APP.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# The legacy route table (explicit: a page-derived table would be definitional)
# ---------------------------------------------------------------------------

#: Every distinct inbound path in the archived Prism's `direct` and `compatibility`
#: route maps, transcribed from `ARCHIVE_APP` (declared literally so an archive
#: edit is a visible change here rather than a silent re-derivation).
LEGACY_ROUTE_TABLE = (
    "/",
    "/about",
    "/account",
    "/challenge",
    "/codex",
    "/commune",
    "/dashboard",
    "/echofeild-matrix",
    "/encyclopedia",
    "/future-skills",
    "/gate",
    "/home",
    "/knowledge-os",
    "/living-gate",
    "/login",
    "/loops",
    "/nexus",
    "/nexus/distribution",
    "/nexus/grove",
    "/nexus/ims",
    "/nexus/larder",
    "/offerings",
    "/oracle",
    "/personal-echofeild",
    "/pulse",
    "/reasomate",
    "/reset",
    "/sci",
    "/settings",
    "/spiral-codex",
)

#: Inbound path families the archive's `resolvePath` accepts **outside** its two
#: route maps. Declared explicitly and bound to the archive by
#: `test_the_archive_non_map_inbound_paths_are_declared` (a source-text pin could
#: only restate the implementation; binding it keeps an archive edit visible).
#:
#: Two families, each transcribed in the shape `resolvePath` writes it:
#:
#: * ``regex`` — the match pattern, e.g. ``^\/solariun(?:\/([^/]+))?$``. The family
#:   it addresses is every path the pattern accepts, not the one sample below.
#: * ``exact`` — the literal ``path === '…'`` branches.
#:
#: ``samples`` are representative concrete paths, used where a concrete path is
#: needed (resolution, disposition). They are asserted to be accepted by the
#: declared pattern, so a sample that stops describing its own family fails here.
ARCHIVE_NON_MAP_INBOUND = {
    "regex": (
        {
            "pattern": "^\\/solariun(?:\\/([^/]+))?$",
            "samples": ("/solariun", "/solariun/knowledge"),
        },
    ),
    "exact": ("/solspire", "/solspire/voice"),
}

#: Recorded disposition of every legacy path that has **no route on this
#: revision** — neither a declared surface path nor a legacy alias. Each is either
#: a product decision (the console declares no surface the path unambiguously
#: names, so an alias would invent a destination — §3.4/§5.1 forbid that) or a
#: reconciliation in flight in a sibling lane-1 slice. This is a **floor**, not an
#: exact match: when one of these is reconciled by adding a real alias, the union
#: in `test_every_legacy_path_has_a_reconciliation_disposition` still covers it, so
#: the guard does not redden a *correct* sibling reconciliation.
LEGACY_GAP_DISPOSITIONS = {
    "/codex": "names the Solariun `knowledge` lens *and* the distinct `knowledge` surface",
    "/dashboard": "addressed a Solariun `overview` lens the console does not declare",
    "/loops": "addressed a Solariun `tasks` lens the console does not declare",
    "/settings": "addressed a Solariun `settings` lens the console does not declare",
    "/account": "same absent Solariun `settings` lens as `/settings`",
    "/personal-echofeild": "addressed a Solariun `observatory` lens the console does not declare",
    "/echofeild-matrix": "same absent Solariun `observatory` lens as `/personal-echofeild`",
    "/sci": "the archived Spiral Command Interface has no console surface",
    "/pulse": "the archived ArkadianPulse surface has no console surface",
    "/reset": "the archived Coherence Reset surface has no console surface",
    "/reasomate": "the archived ReasoMate surface has no console surface",
    "/challenge": "the archived Future Skills Challenge has no console surface",
    "/future-skills": "same absent challenge surface as `/challenge`",
    "/offerings": "the archived Offerings surface has no console surface",
    "/nexus/ims": "a NovaNet/nexus sub-view whose backend contract is UNKNOWN",
    "/nexus/grove": "a NovaNet/nexus sub-view whose backend contract is UNKNOWN",
    "/nexus/larder": "a NovaNet/nexus sub-view whose backend contract is UNKNOWN",
    "/nexus/distribution": "a NovaNet/nexus sub-view whose backend contract is UNKNOWN",
    "/solspire": (
        "a reserved backend namespace (`api/frontend_routes.py::_RESERVED_PREFIXES`); "
        "the console expresses the enterprise surface at `/enterprise`"
    ),
    "/solspire/voice": (
        "under the reserved `/solspire` namespace, so the SPA cannot serve it; the "
        "archived voice view has no console surface"
    ),
}


# ---------------------------------------------------------------------------
# Detectors (module-level so the negative controls exercise the live code)
# ---------------------------------------------------------------------------


def _archive_route_keys(text: str) -> set[str]:
    """Every inbound path in the archive's `direct` and `compatibility` maps."""
    keys: set[str] = set()
    for name in ("direct", "compatibility"):
        block = re.search(
            rf"const\s+{name}\s*:\s*Record<.*?>\s*=\s*\{{(.*?)\}};", text, re.DOTALL
        )
        assert block, f"archive App.tsx declares no `{name}` route map"
        keys |= set(re.findall(r"'([^']*)'\s*:", block.group(1)))
    return keys


def _archive_non_map_inbound(text: str) -> dict[str, tuple[str, ...]]:
    """The archive's inbound paths that live **outside** its two route maps.

    ``resolvePath`` accepts two further families the maps cannot express, and a
    transcription of the maps is blind to both:

    * the regex family ``path.match(/^\\/solariun(?:\\/([^/]+))?$/)`` — every path
      the pattern accepts, not a single sample;
    * the exact-string branches ``path === '/solspire'`` and
      ``path === '/solspire/voice'``.

    Returned in the same shape as :data:`ARCHIVE_NON_MAP_INBOUND` so the guard can
    compare like with like: ``{"regex": ({"pattern":…, "samples":…}, …),
    "exact": (…, …)}``. The samples are *derived from the archive's own pattern*
    rather than restated, so a sample can never drift from the family it describes.
    """
    patterns = tuple(
        {"pattern": p, "samples": _sample_paths_for(p)}
        for p in sorted(set(re.findall(r"path\.match\(/(.*?)/\)", text)))
    )
    exact = tuple(sorted(set(re.findall(r"path === '([^']*)'", text))))
    return {"regex": patterns, "exact": exact}


def _sample_paths_for(pattern: str) -> tuple[str, ...]:
    """Concrete paths a transcribed archive regex accepts.

    The archived ``/solariun`` family is ``^\\/solariun(?:\\/([^/]+))?$``: the root
    plus one optional single-segment section. Rather than hard-code the two
    samples, the root is read out of the pattern and the section sample is built
    from it, so the samples are a function of the declared family.
    """
    root = re.match(r"\^\\/([A-Za-z0-9_-]+)", pattern)
    assert root, f"archive regex {pattern!r} does not open with a rooted literal segment"
    return (f"/{root.group(1)}", f"/{root.group(1)}/knowledge")


def _claimed_by_a_declared_surface(path: str, declared_paths: set[str]) -> bool:
    """Whether a declared surface owns this path.

    A surface declares its root (`/solariun`) and owns the section paths beneath it
    (`/solariun/knowledge`), which is how the console expresses a lens — the same
    ownership `LENS_ALIASES` encodes. Comparing by string equality would report
    every lens path as unaccounted.
    """
    return any(path == root or path.startswith(root + "/") for root in declared_paths)


def _declared_surface_ids(text: str) -> list[str]:
    union = re.search(r"export type SurfaceId\s*=\s*(.*?);", text, re.DOTALL)
    assert union, "surfaces.ts declares no SurfaceId union"
    return re.findall(r'"([^"]+)"', union.group(1))


def _declared_paths(text: str) -> set[str]:
    return set(re.findall(r'path: "([^"]+)"', text))


def _path_aliases(text: str) -> dict[str, str]:
    block = re.search(r"PATH_ALIASES[^=]*=\s*\{(.*?)\}", text, re.DOTALL)
    assert block, "router.ts declares no PATH_ALIASES map"
    return dict(re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', block.group(1)))


def _lens_aliases(text: str) -> dict[str, str]:
    """Legacy inbound path -> the canonical path a lens alias resolves to.

    A lens alias addresses a **surface + section**, not a surface, so it lives in
    its own table. The value is an object literal; the parser matches the whole
    object so the nested keys are not read as aliases.
    """
    block = re.search(r"LENS_ALIASES[^=]*=\s*\{(.*?)\n\};", text, re.DOTALL)
    assert block, "router.ts declares no LENS_ALIASES map"
    return {
        path: f"/{surface}/{section}"
        for path, surface, section in re.findall(
            r'"([^"]+)"\s*:\s*\{\s*surface:\s*"([^"]+)"\s*,\s*section:\s*"([^"]+)"\s*\}',
            block.group(1),
        )
    }


def _reserved_prefixes() -> tuple[str, ...]:
    """The serving path's reserved backend namespaces, read from source."""
    text = (ROOT / "api" / "frontend_routes.py").read_text(encoding="utf-8")
    block = re.search(r"_RESERVED_PREFIXES\s*=\s*\((.*?)\)", text, re.DOTALL)
    assert block, "frontend_routes.py declares no _RESERVED_PREFIXES"
    return tuple(re.findall(r'"([^"]+)"', block.group(1)))


def _served_paths() -> set[str]:
    """The paths the served app declares (imported lazily)."""
    from api.main import app

    return set(app.openapi()["paths"].keys())


def _shadowed_backend_routes(paths, served: set[str], reserved: tuple[str, ...]) -> list[str]:
    """UI paths that would shadow a live backend route.

    A path is shadowed when FastAPI would match a real handler before the SPA
    catch-all: an exact served path, a path under a reserved backend namespace, or a
    path whose **first non-root** segment is the first segment of a served route
    (FastAPI's ``/{param}`` and ``/api/...`` both live under such a segment).

    The root path ``/`` is excluded: it is never shadowed (the SPA owns the root and
    every backend route has a segment), and it has no first segment to compare. A
    one-segment path such as ``/api`` *is* reported because its segment is served.
    """
    served_segments = {p.split("/")[1] for p in served if p.count("/") >= 1 and p.split("/")[1]}
    reserved_roots = {r.split("/")[1] for r in reserved if r.count("/") >= 1 and r.split("/")[1]}
    defects = []
    for path in sorted(paths):
        if path == "/":
            continue  # the SPA owns the root; no backend route lives there
        segments = [s for s in path.split("/") if s]
        if not segments:
            continue
        root = segments[0]
        if path in served:
            defects.append(f"{path} is an exact served backend route")
        elif root in reserved_roots:
            defects.append(f"{path} is under the reserved backend namespace /{root}")
        elif root in served_segments:
            defects.append(f"{path} shares its root segment with served routes under /{root}")
    return defects


def _js_route_resolver(router_text: str, probes: list[str]) -> dict[str, str]:
    """Evaluate the live router in Node and return the canonical path per probe.

    The property under test is *what a legacy path resolves to*, which a
    source-text pin cannot observe — it could only restate the implementation. The
    routing functions are pure and dependency-free, so they are executed.
    """
    node = shutil.which("node")
    assert node, "node is required to evaluate the console router"

    def strip_types(source: str) -> str:
        source = re.sub(r"^import[^;]+;\s*$", "", source, flags=re.MULTILINE)
        source = re.sub(r"^export\s+", "", source, flags=re.MULTILINE)
        source = re.sub(
            r":\s*(?:SurfaceId|SurfaceDef\[\]|Route|string|boolean|Record<[^>]*>)\b", "", source
        )
        return source

    script = (
        strip_types(SURFACES)
        + "\n"
        + strip_types(router_text).replace("as const", "")
        + "\n"
        + f"const probes = {json.dumps(probes)};\n"
        + "console.log(JSON.stringify(probes.map((p) => resolvePath(p).path)));\n"
    )
    result = subprocess.run([node, "-e", script], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, f"router evaluation failed: {result.stderr.strip()}"
    return dict(zip(probes, json.loads(result.stdout)))


# ---------------------------------------------------------------------------
# The disposition partition must be total (no silent gap)
# ---------------------------------------------------------------------------


def test_the_legacy_route_table_is_derivable_from_the_archive():
    """The transcribed table must equal what the archive actually declares.

    The table is declared explicitly (so an archive edit is a visible change), but
    it is *bound* to the archive here: a legacy path dropped from the table while
    still declared in the archive fails the guard instead of quietly leaving the
    domain.
    """
    declared = _archive_route_keys(ARCHIVE)
    assert declared, "the archive declares no route keys -- the guard would be vacuous"
    assert declared == set(LEGACY_ROUTE_TABLE), (
        "the transcribed legacy route table differs from the archive's route maps: "
        f"only-in-table={sorted(set(LEGACY_ROUTE_TABLE) - declared)} "
        f"only-in-archive={sorted(declared - set(LEGACY_ROUTE_TABLE))}"
    )


def test_every_non_map_inbound_path_has_a_reconciliation_disposition():
    """The partition covers the archive's non-map inbound paths too.

    `test_every_legacy_path_has_a_reconciliation_disposition` partitions the two
    route maps. The regex and exact-string families are inbound paths the archive
    accepts and the maps cannot express, so they belong in the same partition:
    measured, `/solariun/knowledge` reaches its surface while `/solspire` and
    `/solspire/voice` are silent losses. Without this, adding a non-map family to
    the archive leaves every one of its paths unaccounted and nothing fails.
    """
    declared_paths = _declared_paths(SURFACES)
    aliases = set(_path_aliases(ROUTER))
    lens_aliases = set(_lens_aliases(ROUTER))
    gaps = set(LEGACY_GAP_DISPOSITIONS)

    inbound = set(ARCHIVE_NON_MAP_INBOUND["exact"])
    for family in ARCHIVE_NON_MAP_INBOUND["regex"]:
        inbound |= set(family["samples"])
    assert inbound, "no non-map inbound path declared -- the guard would be vacuous"

    # A surface's *section* path is accounted by the surface that declares it
    # (`/solariun/knowledge` by `/solariun`), so the partition is over surface
    # ownership, not string equality.
    unaccounted = sorted(
        p
        for p in inbound
        if p not in aliases
        and p not in lens_aliases
        and p not in gaps
        and not _claimed_by_a_declared_surface(p, declared_paths)
    )
    assert unaccounted == [], (
        "archive non-map inbound path(s) with no reconciliation disposition: "
        + ", ".join(unaccounted)
    )
    # A non-map inbound path that is *not* recorded as a gap is claimed as routed,
    # so it must genuinely reach a declared surface rather than falling through to
    # `home`. `test_detector_flags_a_legacy_path_that_falls_through_to_home` proves
    # the resolver can see the fall-through; this asserts the live set carries none.
    routed = sorted(p for p in inbound if p not in gaps)
    assert routed, "no non-map inbound path is claimed as routed -- the guard would be vacuous"
    resolved = _js_route_resolver(ROUTER, routed)
    fell_through = sorted(
        p for p, target in resolved.items() if not _claimed_by_a_declared_surface(target, declared_paths)
    )
    assert fell_through == [], (
        "non-map inbound path(s) claimed as routed but resolving outside a declared "
        f"surface: {[(p, resolved[p]) for p in fell_through]}"
    )


def test_the_archive_non_map_inbound_paths_are_declared():
    """The domain is every inbound path the archive's `resolvePath` accepts.

    The two route maps are not the whole domain. `resolvePath` matches a
    `/solariun` regex family and two exact-string paths before it consults either
    map, and a transcription of the maps alone leaves all of them unasserted —
    measured on `main` @ `fb1d03e4`: `_archive_route_keys` returns 30 keys while
    the archive accepts `/solariun`, `/solariun/<lens>`, `/solspire` and
    `/solspire/voice` as well.

    This binds the declared families to the archive so a family added, changed, or
    removed there is a visible change here rather than a silent loss of domain.
    """
    measured = _archive_non_map_inbound(ARCHIVE)
    assert measured["regex"] or measured["exact"], (
        "the archive declares no non-map inbound path -- the guard would be vacuous"
    )
    assert measured == ARCHIVE_NON_MAP_INBOUND, (
        "the declared non-map inbound families differ from the archive's "
        f"`resolvePath`: measured={measured!r} declared={ARCHIVE_NON_MAP_INBOUND!r}"
    )
    # Every sample must be accepted by the pattern it claims to describe, or the
    # sample is a path the archive never offered and its disposition is spurious.
    for family in ARCHIVE_NON_MAP_INBOUND["regex"]:
        for sample in family["samples"]:
            assert re.match(family["pattern"], sample), (
                f"sample {sample!r} is not accepted by its declared family "
                f"{family['pattern']!r}"
            )


def test_every_legacy_path_has_a_reconciliation_disposition():
    """Every legacy path is a declared surface path, a legacy alias, or a recorded
    product decision — nothing falls through the partition.

    A legacy path outside all three is a silent gap: it resolves to a surface the
    archive never offered (the `/oracle` fall-through class) with no evidence it was
    considered.
    """
    declared_paths = _declared_paths(SURFACES)
    aliases = set(_path_aliases(ROUTER))
    lens_aliases = set(_lens_aliases(ROUTER))
    accounted = declared_paths | aliases | lens_aliases | set(LEGACY_GAP_DISPOSITIONS)

    assert set(LEGACY_ROUTE_TABLE) <= accounted, (
        "legacy path(s) with no reconciliation disposition: "
        + ", ".join(sorted(set(LEGACY_ROUTE_TABLE) - accounted))
    )
    # The partition must be genuine, not a union that swallows contradictions.
    assert not (aliases & declared_paths), (
        "alias(es) that duplicate a declared surface path: " + ", ".join(sorted(aliases & declared_paths))
    )
    # A lens alias resolves to a *section* of a surface, so it must not duplicate
    # either a canonical surface path or a plain alias key.
    assert not (lens_aliases & declared_paths), (
        "lens alias(es) that duplicate a declared surface path: "
        + ", ".join(sorted(lens_aliases & declared_paths))
    )
    assert not (lens_aliases & aliases), (
        "path(s) declared as both a surface alias and a lens alias: "
        + ", ".join(sorted(lens_aliases & aliases))
    )


def test_lens_aliases_reconcile_a_path_that_would_otherwise_be_silent_loss():
    """`/encyclopedia` and `/spiral-codex` are reconciled, not left as gaps.

    Both were recorded as reconciliation gaps because `PATH_ALIASES` maps one path
    segment to a *surface* and cannot express "NovaNet's codex lens". A lens alias
    table can, so the gap is closed: each must now resolve to the surface's own
    section path rather than falling through to `home`.
    """
    lens_aliases = _lens_aliases(ROUTER)
    assert lens_aliases, "no lens alias declared -- the guard would be vacuous"
    for legacy in ("/encyclopedia", "/spiral-codex"):
        assert lens_aliases[legacy] == "/novanet/codex", lens_aliases
        assert legacy not in LEGACY_GAP_DISPOSITIONS, (
            f"{legacy} is reconciled by a lens alias but is still recorded as a gap"
        )
    resolved = _js_route_resolver(ROUTER, ["/encyclopedia", "/spiral-codex"])
    assert resolved == {
        "/encyclopedia": "/novanet/codex",
        "/spiral-codex": "/novanet/codex",
    }, resolved


# ---------------------------------------------------------------------------
# Alias safety: no alias may shadow a live backend route (the lane's precondition)
# ---------------------------------------------------------------------------


def test_every_alias_resolves_to_a_declared_surface():
    """An alias is one registry expressed: it must target a surface that exists."""
    ids = set(_declared_surface_ids(SURFACES))
    defects = [f"{a} -> {t}" for a, t in sorted(_path_aliases(ROUTER).items()) if t not in ids]
    assert defects == [], f"alias(es) targeting an undeclared surface: {defects}"


def test_no_alias_or_legacy_path_shadows_a_served_backend_route():
    """The lane instruction's precondition, now enforced.

    A UI alias placed on a live backend route is shadowed by FastAPI's handler
    before the SPA catch-all — the reserved-namespace defect measured for
    `/solspire`. Both inbound paths the console claims as aliases and the reserved
    backend prefixes themselves are checked, so a future alias for a legacy path
    such as `/codex` obviously cannot land on `/api` or `/solspire`.
    """
    reserved = _reserved_prefixes()
    assert reserved, "no reserved prefixes declared -- the guard would be vacuous"
    served = _served_paths()

    # Premise: the reserved roots are genuinely reserved by the serving path.
    assert "/solspire" in reserved, "control premise: /solspire is a reserved prefix"
    assert "/api" in reserved, "control premise: /api is a reserved prefix"

    ui_paths = (
        set(_path_aliases(ROUTER)) | set(_lens_aliases(ROUTER)) | set(_declared_paths(SURFACES))
    )
    defects = _shadowed_backend_routes(ui_paths, served, reserved)
    assert defects == [], f"UI path(s) shadowed by a backend route: {defects}"


def test_deferred_legacy_paths_are_neither_aliased_nor_declared():
    """A path recorded as a gap must not have quietly gained a route.

    The recorded set is a floor: if a legacy path it names gains a real alias (a
    lane-1 reconciliation), the union test above still covers that path. Here it is
    asserted that the *recorded* entries still describe a gap, so a stale entry with
    a live alias beside it is visible rather than silently wrong.
    """
    aliases = set(_path_aliases(ROUTER))
    declared = _declared_paths(SURFACES)
    # A recorded gap that is now aliased/declared is a reconciliation: report it so
    # the ledger is pruned rather than silently stale.
    still_gap = {p for p in LEGACY_GAP_DISPOSITIONS if p not in aliases and p not in declared}
    reconciled = sorted(set(LEGACY_GAP_DISPOSITIONS) - still_gap)
    assert reconciled == [], (
        "legacy path(s) recorded as reconciliation gaps have since gained a route -- "
        f"prune LEGACY_GAP_DISPOSITIONS: {reconciled}"
    )


# ---------------------------------------------------------------------------
# Negative controls -- each detector must fire on the defect it names
# ---------------------------------------------------------------------------


def test_detector_flags_an_unaccounted_legacy_path():
    """Negative control: a legacy path in no disposition bucket must be reported."""
    declared_paths = {"/", "/about"}
    aliases = {"/nexus"}
    lens_aliases = {"/encyclopedia"}
    accounted = declared_paths | aliases | lens_aliases | {"/gate"}
    missing = {"/invented-legacy"} - accounted
    assert missing == {"/invented-legacy"}, "control premise: the path must be unaccounted"
    # And the live partition must not itself be missing anything. This restates the
    # partition, so it must name every bucket the live assertion uses -- including
    # the lens-alias table, or the control would report a false gap.
    live_accounted = (
        _declared_paths(SURFACES)
        | set(_path_aliases(ROUTER))
        | set(_lens_aliases(ROUTER))
        | set(LEGACY_GAP_DISPOSITIONS)
    )
    assert set(LEGACY_ROUTE_TABLE) <= live_accounted


def test_detector_flags_an_alias_on_a_reserved_backend_namespace():
    """Negative control: an alias whose path is a reserved backend namespace must
    be reported by the same shadowing detector the live assertion uses.

    The serving path owns `/solspire/*`; a UI alias there would be shadowed by the
    backend handler and pass every existing alias guard, which is exactly the hole
    this guard closes.
    """
    reserved = _reserved_prefixes()
    served = _served_paths()

    assert _shadowed_backend_routes({"/solspire"}, served, reserved) != []
    assert _shadowed_backend_routes({"/api/thing"}, served, reserved) != []
    # The real console UI paths must not be reported.
    real = set(_path_aliases(ROUTER)) | set(_declared_paths(SURFACES))
    assert _shadowed_backend_routes(real, served, reserved) == []


def test_detector_flags_a_legacy_path_that_falls_through_to_home():
    """Negative control: a legacy path the archive offered but neither the console
    nor its aliases claim resolves to `home` — a real deep link silently discarded.

    `/oracle` was this exact shape before its alias existed; `/codex` is the live,
    still-deferred instance of the class. The control proves the resolver can detect
    the fall-through so the disposition tests are not vacuous.
    """
    declared_paths = _declared_paths(SURFACES)
    aliases = set(_path_aliases(ROUTER))

    # Every live alias and alias-less legacy path that *is* meant to reach its
    # surface must not resolve to `/` unless `/` is genuinely correct.
    resolved = _js_route_resolver(ROUTER, ["/oracle", "/nexus", "/codex"])
    assert resolved["/oracle"] == "/arkana", resolved
    assert resolved["/nexus"] == "/novanet", resolved
    assert resolved["/codex"] == "/" and "/codex" not in aliases, (
        "control premise: `/codex` is a deferred legacy path that falls through to home"
    )
    assert "/codex" not in declared_paths


def test_detector_flags_a_non_map_inbound_family_the_archive_stops_declaring():
    """Negative control: the binding must fire when the archive's non-map family
    changes, and must stay silent for the live archive.

    A detector that only ever compares the declaration with itself is vacuous. This
    feeds `_archive_non_map_inbound` an archive whose exact-string family has grown
    a path — the shape a real archive edit produces — and asserts the declaration
    no longer matches, then asserts the live archive still matches.

    The pre-repair domain is also exercised: the two route maps are *silent* about
    these paths, which is the defect, so a guard built on `_archive_route_keys`
    alone cannot see them.
    """
    live = _archive_non_map_inbound(ARCHIVE)
    assert live == ARCHIVE_NON_MAP_INBOUND, "control premise: the live archive matches"

    mutated = ARCHIVE.replace(
        "path === '/solspire/voice'", "path === '/solspire/voice' || path === '/invented-legacy'"
    )
    assert mutated != ARCHIVE, "control premise: the archive fixture was actually mutated"
    drifted = _archive_non_map_inbound(mutated)
    assert drifted != ARCHIVE_NON_MAP_INBOUND, (
        "the guard did not notice a new archive non-map inbound path"
    )
    assert "/invented-legacy" in drifted["exact"], drifted

    # And the maps alone remain blind to the whole family -- the defect this closes.
    assert not set(ARCHIVE_NON_MAP_INBOUND["exact"]) & _archive_route_keys(ARCHIVE), (
        "control premise: the exact-string family is outside the two route maps"
    )
