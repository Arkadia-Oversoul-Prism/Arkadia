"""Operator surface convergence guard (ARK-UI-CONVERGENCE-001).

The operator console used to be a **second React application**: its own
`react-router-dom` `BrowserRouter` with a `/operator` basename and an
`isStandaloneLab` branch, its own `/operator` + `/n-atlas-lab` + `/n-atlas-tester`
mounts in `api/frontend_routes.py`, its own build stage in the `Dockerfile`, and
its own stylesheet. `/operator` answering 200 therefore proved nothing about how
many routing authorities existed.

This module binds the three claims that migration makes, and keeps them separable:

1. **Source convergence** — the operator views are sections of the canonical
   application's one router, reachable by the canonical surface registry.
2. **Build convergence** — the retired application is absent from every
   executable line of the Dockerfile and from the serving path.
3. **Route authority** — nested addressing is *opt-in* per surface, so adding the
   operator's `/operator/boundary/<id>` shape does not silently widen what every
   other surface accepts.

`/operator` returning 200 is deliberately NOT treated as evidence of any of these:
it is exactly what bothbefore and after this change answer.
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
APP_PATH = SRC / "App.tsx"
OPERATOR_PAGE = SRC / "pages" / "OperatorPage.tsx"
DOCKERFILE = ROOT / "Dockerfile"
FRONTEND_ROUTES = ROOT / "api" / "frontend_routes.py"

SURFACES = SURFACES_PATH.read_text(encoding="utf-8")
ROUTER = ROUTER_PATH.read_text(encoding="utf-8")
APP = APP_PATH.read_text(encoding="utf-8")
PAGE = OPERATOR_PAGE.read_text(encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# Detectors (module level, so the negative controls exercise the live code)
# ─────────────────────────────────────────────────────────────────────────────

def _strip_types(source: str) -> str:
    """Strip the TS syntax the router resolver does not need, for Node."""
    source = re.sub(r"^import[^;]+;\s*$", "", source, flags=re.MULTILINE)
    source = re.sub(r"^export\s+", "", source, flags=re.MULTILINE)
    source = re.sub(
        r":\s*(?:SurfaceId|SurfaceDef\[\]|Route|string|boolean|Record<[^>]*>)\b", "", source
    )
    return source.replace("as const", "")


def _resolve(probes: list[str]) -> dict[str, dict]:
    """Execute the real router and report each probe's full resolution.

    The property under test is *what a path resolves to* — surface, section and
    param — which a source-text pin can only restate. The routing functions are
    pure and dependency-free, so they are run.
    """
    node = shutil.which("node")
    assert node, "node is required to evaluate the console router"
    script = (
        _strip_types(SURFACES)
        + "\n"
        + _strip_types(ROUTER)
        + "\n"
        + f"const probes = {json.dumps(probes)};\n"
        + "console.log(JSON.stringify(probes.map((p) => {\n"
        + "  const r = resolvePath(p);\n"
        + "  return [p, r.path, r.surface, r.section ?? null, r.param ?? null,"
        + " resolvePath(r.path).path];\n"
        + "})));\n"
    )
    result = subprocess.run([node, "-e", script], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, f"router evaluation failed: {result.stderr.strip()}"
    keys = ("path", "surface", "section", "param", "reread")
    return {row[0]: dict(zip(keys, row[1:])) for row in json.loads(result.stdout)}


def _declared_surface_ids(text: str = SURFACES) -> set[str]:
    union = re.search(r"export type SurfaceId\s*=\s*(.*?);", text, re.DOTALL)
    assert union, "surfaces.ts declares no SurfaceId union"
    return set(re.findall(r'"([^"]+)"', union.group(1)))


def _declared_surface_paths(text: str = SURFACES) -> set[str]:
    return set(re.findall(r'path: "([^"]+)"', text))


def _sections_without_a_view(page: str) -> list[str]:
    """Lens ids the surface lists but never composes.

    A section in the strip that no branch renders is a control that navigates to
    an address the surface cannot draw — the decorative-control class this
    repository already treats as a defect.
    """
    block = re.search(r"const SECTIONS = \[(.*?)\];", page, re.DOTALL)
    assert block, "OperatorPage declares no SECTIONS list"
    ids = re.findall(r'id: "([^"]+)"', block.group(1))
    cases = set(re.findall(r'case "([^"]+)":', page))
    return [s for s in ids if s not in cases]


def _executable_lines(text: str) -> list[str]:
    """Dockerfile instructions, excluding comments and blanks."""
    return [
        line
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


# ─────────────────────────────────────────────────────────────────────────────
# 1. Source convergence — the surface is the canonical app's, not a second app
# ─────────────────────────────────────────────────────────────────────────────

def test_the_operator_surface_is_declared_in_the_one_registry():
    ids = _declared_surface_ids()
    assert "operator" in ids, "the operator surface is not declared in surfaces.ts"
    assert "n-atlas" in ids, "the N-ATLaS surface is not declared in surfaces.ts"
    # A second declaration of the same path would be a second route authority.
    paths = re.findall(r'path: "([^"]+)"', SURFACES)
    assert len(paths) == len(set(paths)), f"duplicate surface path: {paths}"
    assert "/operator" in _declared_surface_paths()
    assert "/n-atlas-lab" in _declared_surface_paths()


def test_both_migrated_surfaces_are_composed_in_the_app_root():
    """A declared surface with no `case` renders the default page."""
    for surface in ("operator", "n-atlas"):
        assert re.search(rf'case "{surface}":\s*\n\s*return <\w+', APP), (
            f"App.tsx has no composition case for the {surface} surface"
        )


def test_every_operator_section_has_a_composed_view():
    assert _sections_without_a_view(PAGE) == [], (
        "the operator surface lists a section it never renders: "
        f"{_sections_without_a_view(PAGE)}"
    )


def _without_ts_comments(source: str) -> str:
    """Drop block and line comments.

    The migrated modules *document* the router they no longer use, so a bare
    substring search would report the documentation as the defect — the
    mention-vs-execution confusion this repository has already been bitten by.
    """
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?m)^\s*//.*$", "", source)


def test_the_operator_page_does_not_own_a_router():
    """One routing authority: the surface must not parse the pathname or mount a
    second history."""
    assert "window.location" not in PAGE, "OperatorPage parses the location directly"
    assert not re.search(r"""from\s+["']react-router""", _without_ts_comments(PAGE)), (
        "OperatorPage depends on a second router"
    )
    # The migrated view modules must not carry the retired router either.
    offenders = [
        str(p.relative_to(ROOT))
        for p in (SRC / "operator").rglob("*.ts*")
        if re.search(r"""from\s+["']react-router""", _without_ts_comments(p.read_text(encoding="utf-8")))
    ]
    assert offenders == [], f"the retired router is still imported in {offenders}"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Route authority — nested addressing is opt-in, and the migrated paths hold
# ─────────────────────────────────────────────────────────────────────────────

def test_migrated_operator_routes_resolve_to_themselves():
    resolved = _resolve(
        [
            "/operator",
            "/operator/inspector",
            "/operator/authority",
            "/operator/work",
            "/operator/mie-lab",
            "/operator/n-atlas",
            "/operator/security",
        ]
    )
    for path, got in resolved.items():
        assert got["surface"] == "operator", (path, got)
        assert got["path"] == path, f"{path} normalised to {got['path']}"
        assert got["reread"] == path, f"{path} is not idempotent: re-read {got['reread']}"


def test_boundary_instances_resolve_to_surface_section_and_param():
    """The nested shape carries all three components, not a flattened section."""
    worked = ("approval-not-execution", "execution-not-workevent",
              "workevent-not-evidence", "evidence-not-verification")
    resolved = _resolve([f"/operator/boundary/{w}" for w in worked])
    for w in worked:
        path = f"/operator/boundary/{w}"
        got = resolved[path]
        assert got["surface"] == "operator", (path, got)
        assert got["section"] == "boundary", (path, got)
        assert got["param"] == w, (path, got)
        assert got["path"] == path, (path, got)
        assert got["reread"] == path, f"{path} is not idempotent: re-read {got['reread']}"


def test_the_n_atlas_direct_routes_survive_as_aliases():
    """`/n-atlas-lab` is canonical; `/n-atlas-tester` is reconciled to it.

    Both were answered by the retired bundle, so an inbound tester link must keep
    resolving — to the *same* view on the same origin, not to `home`.
    """
    resolved = _resolve(["/n-atlas-lab", "/n-atlas-tester", "/n-atlas-tester/"])
    for path in ("/n-atlas-lab", "/n-atlas-tester", "/n-atlas-tester/"):
        assert resolved[path]["surface"] == "n-atlas", (path, resolved[path])
        assert resolved[path]["path"] == "/n-atlas-lab", (path, resolved[path])


RETIRED_APP = ROOT / "web" / "console" / "src" / "main.tsx"

#: Every view the retired operator application answered, frozen from its own route
#: table (`web/console/src/main.tsx`, basename `/operator`) at the baseline this
#: migration was cut from. Frozen rather than re-derived so the contract survives
#: the retired tree's deletion -- and compared against that tree while it still
#: exists, so the two cannot drift apart unnoticed.
LEGACY_OPERATOR_PATHS = (
    "/operator",
    "/operator/inspector",
    "/operator/boundary/approval-not-execution",
    "/operator/work",
    "/operator/authority",
    "/operator/mie-lab",
    "/operator/security-verification",
)


def _unrendered_legacy_views(page: str, resolved: dict[str, dict]) -> list[str]:
    """Legacy addresses that reach a section the surface composes no view for.

    The defect this names is a **rename without an alias**. The route still
    resolves to the right surface and the address bar still reads correctly, but
    the section id is one no branch matches, so the page falls to its "not a view
    of this surface" default and the view the link named is simply gone. A
    resolver-only check cannot see that: it is satisfied by the wrong destination.
    """
    cases = set(re.findall(r'case "([^"]+)":', page))
    missing = []
    for path, got in sorted(resolved.items()):
        if got["surface"] != "operator":
            missing.append(f"{path} resolves to {got['surface']!r}, not the operator surface")
        elif got["section"] is None:
            continue  # the surface's own root view
        elif got["section"] == "boundary" and got["param"]:
            continue  # rendered by BoundaryView and addressed by its param
        elif got["section"] not in cases:
            missing.append(f"{path} reaches section {got['section']!r}, which no branch renders")
    return missing


def test_every_retired_operator_route_still_reaches_a_composed_view():
    """Parity: no view the retired application served may be lost in the migration.

    Judged by resolution *and* composition, because those failed independently
    here: `/operator/security-verification` is a real address (a sidebar link,
    `Layout.tsx` item "07"), and after the migration it resolved to
    `section="security-verification"` while the page only composed `security`.
    The route answered 200; the view did not exist.
    """
    resolved = _resolve(list(LEGACY_OPERATOR_PATHS))
    unrendered = _unrendered_legacy_views(PAGE, resolved)
    assert unrendered == [], f"retired operator views are unreachable: {unrendered}"


def test_the_frozen_legacy_contract_matches_the_retired_route_table():
    """The frozen list is a record of the retired app, not an invention.

    Skipped by returning early once the tree is gone -- at that point the frozen
    tuple is the only surviving statement of what parity means.
    """
    if not RETIRED_APP.exists():
        return
    retired = set(re.findall(r'<Route path="([^"]+)"', RETIRED_APP.read_text(encoding="utf-8")))
    retired.discard("*")  # the catch-all is a redirect, not a view
    expected = set()
    for path in retired:
        if path.startswith("/n-atlas"):
            continue  # standalone tester routes, covered by their own alias test
        if path == "/":
            expected.add("/operator")
        elif ":id" in path:
            expected.add("/operator/boundary/approval-not-execution")
        else:
            expected.add("/operator" + path)
    assert expected == set(LEGACY_OPERATOR_PATHS), (
        "the retired route table and the frozen contract disagree: "
        f"missing {sorted(expected - set(LEGACY_OPERATOR_PATHS))}, "
        f"invented {sorted(set(LEGACY_OPERATOR_PATHS) - expected)}"
    )


def test_nested_addressing_is_opt_in_and_does_not_widen_other_surfaces():
    """The negative control for the router change itself.

    Adding the operator's three-segment shape must not make every surface accept
    one. `novanet` and `solariun` declare no `param`, so a deeper path still falls
    through to `home` exactly as it did before the shape existed.
    """
    resolved = _resolve(
        ["/novanet/a/b", "/solariun/a/b", "/arkana/x/y", "/invented", "/operator/not-a-view"]
    )
    assert resolved["/novanet/a/b"]["path"] == "/"
    assert resolved["/solariun/a/b"]["path"] == "/"
    assert resolved["/arkana/x/y"]["path"] == "/"
    assert resolved["/invented"]["path"] == "/"
    # An undeclared *section* is not an error: it resolves to the surface, whose
    # page renders an honest "not a view of this surface" state.
    assert resolved["/operator/not-a-view"]["surface"] == "operator"
    assert resolved["/operator/not-a-view"]["path"] == "/operator/not-a-view"


def test_only_the_operator_surface_declares_a_param():
    """The opt-in gate must stay narrow, and the declaration must be resolve-able."""
    declared = re.findall(r"id: \"([^\"]+)\",(.*?)\n  \}", SURFACES, re.DOTALL)
    with_param = sorted(sid for sid, body in declared if re.search(r"param: \"", body))
    assert with_param == ["operator"], f"unexpected surfaces accept a nested segment: {with_param}"
    assert re.search(r'param: "id"', SURFACES), "the param segment must be named"


# ─────────────────────────────────────────────────────────────────────────────
# 3. Build / runtime convergence — the retired shell is not activated
# ─────────────────────────────────────────────────────────────────────────────

def test_the_dockerfile_does_not_build_the_retired_application():
    """Only instructions are judged; the header comment may name the retirement."""
    offenders = [line for line in _executable_lines(DOCKERFILE.read_text(encoding="utf-8"))
                 if "web/console" in line]
    assert offenders == [], f"the retired application is still built: {offenders}"


def test_the_serving_path_does_not_mount_the_retired_application():
    text = FRONTEND_ROUTES.read_text(encoding="utf-8")
    assert not re.search(r'"web"\s*/\s*"console"', text), (
        "api/frontend_routes.py still resolves the retired application's build output"
    )
    assert "operator_dist" not in text, "the retired operator mount still exists"
    # ...and the canonical application IS mounted.
    assert re.search(r'"web"\s*/\s*"arkadia_console"', text), (
        "the canonical application is no longer mounted"
    )


def test_operator_and_lab_paths_are_not_reserved_against_the_spa():
    """A surface route listed as reserved is a hard load that 404s."""
    text = FRONTEND_ROUTES.read_text(encoding="utf-8")
    block = re.search(r"_RESERVED_PREFIXES\s*=\s*\((.*?)\)", text, re.DOTALL)
    assert block, "frontend_routes.py declares no _RESERVED_PREFIXES"
    reserved = tuple(re.findall(r'"([^"]+)"', block.group(1)))
    for path in ("/operator", "/n-atlas-lab", "/n-atlas-tester"):
        assert path not in reserved, f"{path} is a surface route and must not be reserved"


# ─────────────────────────────────────────────────────────────────────────────
# Negative controls — each detector must fire on the defect it names
# ─────────────────────────────────────────────────────────────────────────────

def test_detector_flags_a_listed_section_with_no_view():
    """Control: removing a branch must be reported, or the detector is vacuous."""
    stale = PAGE.replace('case "mie-lab":', 'case "removed-view":')
    assert stale != PAGE, "control did not mutate OperatorPage.tsx -- detector unproven"
    assert _sections_without_a_view(stale) == ["mie-lab"]


def test_detector_flags_a_legacy_route_left_without_a_view():
    """Control: the exact historical defect must be reported, or the guard is vacuous.

    Removes the alias added for `/operator/security-verification` and asserts the
    detector names that view. Without this, deleting the guard's teeth would look
    like a passing test.
    """
    stale = PAGE.replace('case "security-verification":', "")
    assert stale != PAGE, "control did not mutate OperatorPage.tsx -- detector unproven"
    flagged = _unrendered_legacy_views(stale, _resolve(["/operator/security-verification"]))
    assert len(flagged) == 1 and "security-verification" in flagged[0], flagged


def test_detector_flags_a_dockerfile_that_still_builds_the_retired_app():
    """Control: the pre-change instruction must be reported."""
    stale = "COPY web/console/ ./web/console/\nRUN npm run build\n"
    assert [l for l in _executable_lines(stale) if "web/console" in l] == [
        "COPY web/console/ ./web/console/"
    ]


def test_detector_flags_a_reserved_surface_route():
    """Control: a surface route placed in the reserved set must be caught."""
    text = '_RESERVED_PREFIXES = (\n    "/api",\n    "/operator",\n)'
    block = re.search(r"_RESERVED_PREFIXES\s*=\s*\((.*?)\)", text, re.DOTALL)
    reserved = tuple(re.findall(r'"([^"]+)"', block.group(1)))
    assert "/operator" in reserved


def test_detector_flags_a_router_that_widens_nested_addressing():
    """Control: without the per-surface gate, every surface accepts a param.

    This reproduces the shape the gate prevents — the nested pattern matching
    regardless of whether the surface declared a `param` — and proves the
    negative-control assertion above is not trivially true.
    """
    stale = ROUTER.replace(
        'const surface = SURFACES.find((s) => s.path === `/${nested[1]}` && s.param);',
        "const surface = SURFACES.find((s) => s.path === `/${nested[1]}`);",
    )
    assert stale != ROUTER, "control did not mutate router.ts -- detector unproven"
    node = shutil.which("node")
    script = (
        _strip_types(SURFACES)
        + "\n"
        + _strip_types(stale)
        + "\n"
        + 'console.log(JSON.stringify(["/solariun/a/b", "/novanet/a/b"].map((p) => resolvePath(p).path)));\n'
    )
    result = subprocess.run([node, "-e", script], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    widened = json.loads(result.stdout)
    assert widened == ["/solariun/a/b", "/novanet/a/b"], (
        f"the control must reproduce the widened-addressability defect, got {widened}"
    )
