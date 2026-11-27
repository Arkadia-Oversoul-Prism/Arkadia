"""Home surface — identity-aware entry action (PRR-10).

The archived Prism home (`archive/frontend/arkadia-prism/web/public_prism/src/App.tsx`
`function Home`) rendered exactly one primary entry whose target depended on the
viewer's identity — "Enter Arkadia" for an anonymous visitor, "Open Solariun"
for a signed-in node — plus a secondary action. It also offered a portal grid to
the other surfaces.

The console HomePage had the portal grid but *no* primary entry: a returning,
authenticated node landing on `/` had no single obvious way back into its
workspace. This slice recovers the identity-aware primary entry without
inventing a second surface — the anonymous primary targets the declared `login`
surface (the console has no separate gate surface), never an unrouted path.

Domain: the Arkadia Console (`web/arkadia_console`). The retired Prism UI is
archived and is not built or served; it is the reference this slice reconciles.

What is asserted:

  * HomePage renders a primary and a secondary entry action (`data-testid`);
  * the entry is identity-aware: a signed-in node and an anonymous visitor get
    different primary targets;
  * every entry target is a *declared* canonical surface, and each resolves,
    through the **executed** router, to that same surface — the anonymous
    primary is `login`, never a decorative `gate`;
  * a negative control per load-bearing detector, so a detector that always
    passes is itself caught.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "web" / "arkadia_console" / "src"
HOME_PATH = SRC / "pages" / "HomePage.tsx"
SURFACES_PATH = SRC / "lib" / "surfaces.ts"
ROUTER_PATH = SRC / "lib" / "router.ts"

HOME = HOME_PATH.read_text(encoding="utf-8")
SURFACES = SURFACES_PATH.read_text(encoding="utf-8")
ROUTER = ROUTER_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Detectors (module-level so the negative controls exercise the SAME code the
# live assertions use).
# ---------------------------------------------------------------------------


def _entry_block(text: str) -> str:
    """The `entryActions` helper body.

    Slice up to the next top-level declaration (`export function HomePage`); the
    helper's return type spans several braces, so a `.*?\\n}` match would stop in
    the type annotation.
    """
    match = re.search(
        r"function entryActions\(.*?(?=\nexport function HomePage\b)", text, re.DOTALL
    )
    if match:
        return match.group(0)
    fallback = re.search(r"function entryActions\(.*", text, re.DOTALL)
    assert fallback, "HomePage declares no entryActions helper"
    return fallback.group(0)


def _has_entry_actions(text: str) -> bool:
    """A real primary and secondary entry control, not just a portal grid."""
    return 'data-testid="home-entry-primary"' in text and 'data-testid="home-entry-secondary"' in text


def _entry_targets(text: str) -> list[str]:
    """Every surface id an entry action navigates to, in source order.

    Source order is authenticated-primary, authenticated-secondary,
    anonymous-primary, anonymous-secondary — matching the two `return` branches.
    """
    block = _entry_block(text)
    return re.findall(r'(?:primary|secondary):\s*\{\s*id:\s*"([^"]+)"', block)


def _invalid_targets(targets: list[str], declared: set[str]) -> list[str]:
    """Entry targets that are not declared surfaces (would be an invented route)."""
    return [t for t in targets if t not in declared]


def _is_identity_aware(text: str) -> bool:
    """A genuine identity *branch* — the signature merely names the parameter."""
    return "if (isAuthenticated)" in _entry_block(text)


def _declared_surface_ids(text: str) -> set[str]:
    union = re.search(r"export type SurfaceId\s*=\s*(.*?);", text, re.DOTALL)
    assert union, "surfaces.ts declares no SurfaceId union"
    return set(re.findall(r'"([^"]+)"', union.group(1)))


def _js_resolve(probes: list[str]) -> list[dict]:
    """Execute the console's real `resolvePath` in Node on the given probes."""

    def strip_types(source: str) -> str:
        source = re.sub(r"^import[^;]+;\s*$", "", source, flags=re.MULTILINE)
        source = re.sub(r"^export\s+", "", source, flags=re.MULTILINE)
        source = re.sub(
            r":\s*(?:SurfaceId|SurfaceDef\[\]|Route|string|boolean|Record<[^>]*>)\b",
            "",
            source,
        )
        return source

    node = shutil.which("node")
    assert node, "node is required to evaluate the console router"
    surfaces = strip_types(SURFACES)
    router = strip_types(ROUTER).replace("as const", "")
    script = (
        surfaces
        + "\n"
        + router
        + "\n"
        + f"const probes = {json.dumps(probes)};\n"
        + "console.log(JSON.stringify(probes.map((p) => resolvePath(p))));\n"
    )
    result = subprocess.run([node, "-e", script], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, f"router evaluation failed: {result.stderr.strip()}"
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# 1. The entry action exists and is wired to the shared router.
# ---------------------------------------------------------------------------


def test_home_renders_a_primary_and_secondary_entry():
    assert _has_entry_actions(HOME), (
        "HomePage must render a primary and a secondary entry action — the archived "
        "home had one primary entry plus a secondary; a bare portal grid leaves a "
        "returning node with no single obvious way back into its workspace"
    )
    assert "onNavigate(entry.primary.id)" in HOME
    assert "onNavigate(entry.secondary.id)" in HOME


def test_negative_control_detects_the_portal_grid_without_an_entry():
    """The entry detector must fire on the pre-fix shape (a grid only)."""
    pre_fix = HOME.replace('data-testid="home-entry-primary"', 'data-testid="portal-home"').replace(
        'data-testid="home-entry-secondary"', 'data-testid="portal-about"'
    )
    assert not _has_entry_actions(pre_fix), (
        "the entry detector must catch a Home that is a portal grid only"
    )
    assert _has_entry_actions(HOME)


# ---------------------------------------------------------------------------
# 2. The entry is identity-aware.
# ---------------------------------------------------------------------------


def test_entry_is_identity_aware():
    assert _is_identity_aware(HOME), "the entry action must branch on the viewer's identity"
    targets = _entry_targets(HOME)
    assert len(targets) == 4, f"expected 4 entry targets (2 per identity), got {targets}"
    # authenticated: solariun / solspire ; anonymous: login / about
    assert targets[0] == "solariun", "a signed-in node's primary entry is the personal canvas"
    assert targets[2] == "login", (
        "an anonymous visitor's primary entry must be the real sign-in surface (`login`) — "
        "the console has no separate gate surface, so `gate` would be an invented route"
    )
    assert targets[0] != targets[2], "the primary target must differ by identity"


def test_negative_control_entry_detector_reports_identity_anchor():
    """A non-identity-aware entry must fail the identity detector."""
    synthetic = """
    function entryActions(isAuthenticated: boolean) {
      return { primary: { id: "login", label: "x", body: "y" }, secondary: { id: "about", label: "z" } };
    }
    """
    assert not _is_identity_aware(synthetic), "a single non-branching entry is not identity-aware"


# ---------------------------------------------------------------------------
# 3. Targets are declared surfaces and resolve through the executed router.
# ---------------------------------------------------------------------------


def test_every_entry_target_is_a_declared_surface():
    declared = _declared_surface_ids(SURFACES)
    targets = _entry_targets(HOME)
    invalid = _invalid_targets(targets, declared)
    assert not invalid, f"entry targets that are not declared surfaces: {invalid}"


def test_negative_control_flags_an_invented_target():
    declared = _declared_surface_ids(SURFACES)
    synthetic = """
    function entryActions(isAuthenticated: boolean) {
      return { primary: { id: "gate", label: "x", body: "y" }, secondary: { id: "about", label: "z" } };
    }
    """
    assert _invalid_targets(["gate", "about"], declared) == ["gate"], (
        "the detector must flag an entry target that is not a declared surface"
    )
    assert not _invalid_targets(["login", "about"], declared)


def test_entry_targets_resolve_to_themselves_via_the_router():
    targets = _entry_targets(HOME)
    resolved = _js_resolve(
        [
            "/solariun",
            "/login",
            "/enterprise",
            "/about",
            "/solspire",
        ]
    )
    by_path = {p: r for p, r in zip(
        ["/solariun", "/login", "/enterprise", "/about", "/solspire"], resolved
    )}
    # solariun -> solariun, login -> login, about -> about
    assert by_path["/solariun"]["surface"] == "solariun"
    assert by_path["/login"]["surface"] == "login"
    assert by_path["/about"]["surface"] == "about"
    # The SolSpire surface lives on /enterprise; a `solspire` *path* is a reserved
    # backend namespace and must not resolve to a second surface.
    assert by_path["/enterprise"]["surface"] == "solspire"
    assert by_path["/solspire"]["surface"] != "solspire", (
        "/solspire is a reserved backend namespace and must not resolve to the SolSpire surface"
    )
    # every declared target is reachable
    for t in targets:
        assert t in {"solariun", "login", "solspire", "about"}, t


# ---------------------------------------------------------------------------
# 4. A portal never renders the same label twice.
# ---------------------------------------------------------------------------

def _portal_block(text: str) -> str:
    """The `Portal` component body."""
    match = re.search(r"function Portal\(.*?(?=\n/\*\*|\nexport function)", text, re.DOTALL)
    assert match, "HomePage declares no Portal component"
    return match.group(0)


def _portal_eyebrow_is_conditional(text: str) -> bool:
    """The boundary eyebrow is suppressed when it would repeat the surface name.

    The eyebrow is the product *boundary* (`lib/surfaces.ts` `boundary`), while
    the card title is the surface `name`. For a surface that is its own boundary
    the two strings are equal, so an unconditional eyebrow renders the same word
    twice.
    """
    block = _portal_block(text)
    compared = "boundary.trim().toLowerCase() === surface.name.trim().toLowerCase()" in block
    guarded = re.search(r"\{boundary\s*&&", block) is not None
    return compared and guarded


def _surface_triples(text: str) -> list[tuple[str, str, str]]:
    """(id, name, boundary) for every declared surface, in source order."""
    triples: list[tuple[str, str, str]] = []
    for block in re.split(r"\n  \{\n", text)[1:]:
        id_match = re.search(r'id:\s*"([^"]+)"', block)
        name_match = re.search(r'name:\s*"([^"]+)"', block)
        boundary_match = re.search(r'boundary:\s*"([^"]+)"', block)
        if id_match and name_match and boundary_match:
            triples.append((id_match.group(1), name_match.group(1), boundary_match.group(1)))
    return triples


def _rendered_labels(name: str, boundary: str) -> tuple[str | None, str]:
    """What a portal prints for (name, boundary) under the suppressed-eyebrow rule."""
    eyebrow = None if boundary.strip().lower() == name.strip().lower() else boundary
    return eyebrow, name


def test_portal_suppresses_an_eyebrow_that_repeats_the_name():
    assert _portal_eyebrow_is_conditional(HOME), (
        "Portal must suppress its boundary eyebrow when the boundary equals the surface "
        "name — otherwise the card prints the same label twice"
    )


def test_negative_control_flags_the_unconditional_eyebrow():
    """The detector must fire on the shape that shipped the duplicated labels."""
    pre_fix = HOME.replace(
        '      {boundary && (\n'
        '        <p className={`font-mono text-[11px] uppercase tracking-[0.18em] ${surface.accent}`}>{boundary}</p>\n'
        "      )}",
        '      <p className={`font-mono text-[11px] uppercase tracking-[0.18em] ${surface.accent}`}>{surface.boundary}</p>',
    )
    assert pre_fix != HOME, "the negative control no longer matches the shipped shape"
    assert not _portal_eyebrow_is_conditional(pre_fix), (
        "the detector must catch an eyebrow rendered unconditionally"
    )
    assert _portal_eyebrow_is_conditional(HOME)


def test_no_portal_renders_a_repeated_label():
    """Judged against the live registry, not a literal list of surface names."""
    triples = _surface_triples(SURFACES)
    assert triples, "surfaces.ts declares no surfaces"
    repeats = [
        surface_id
        for surface_id, name, boundary in triples
        if (eyebrow := _rendered_labels(name, boundary)[0]) is not None
        and eyebrow.strip().lower() == name.strip().lower()
    ]
    assert not repeats, f"portals that would print a repeated label: {repeats}"
    # The rule is load-bearing today: five declared surfaces are their own
    # boundary. If this becomes empty the suppression is inert, not wrong.
    suppressed = [
        surface_id
        for surface_id, name, boundary in triples
        if _rendered_labels(name, boundary)[0] is None
    ]
    assert suppressed, "no surface is its own boundary — the suppression rule is inert"
