"""AEAS-05 — Canonical Frontend Acceptance guards.

The console transition is only acceptable if its protected surfaces are actually
gated, its sign-in surface is the one the CP10 browser gate drives, and the
Gate-2 observation binds each marker reading to the application it measured.

These are source-level contracts, matching this repository's frontend-test
convention. They are the pre-deployment half of AEAS-05: they must pass before a
production cutover may be claimed.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "web" / "arkadia_console"
SURFACES = (CONSOLE / "src" / "lib" / "surfaces.ts").read_text(encoding="utf-8")
APP = (CONSOLE / "src" / "App.tsx").read_text(encoding="utf-8")
SIGNIN = CONSOLE / "src" / "pages" / "SignInPage.tsx"
WORKFLOW = (ROOT / ".github" / "workflows" / "sg-02-fe-2-v.yml").read_text(encoding="utf-8")
GATE2 = (ROOT / "scripts" / "gate2_production_observation.py").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Protected surfaces are gated
# ---------------------------------------------------------------------------


def test_protected_surfaces_declare_requires_auth():
    """Every product surface that reads a protected contract must declare it, so
    the gate is a property of the surface table rather than of each page."""
    for surface in ("solariun", "engineering-lab", "solspire", "knowledge", "weaver"):
        idx = SURFACES.index(f'id: "{surface}"')
        window = SURFACES[idx : idx + 200]
        assert "requiresAuth: true" in window, f"surface '{surface}' is not declared protected"


def test_app_renders_a_threshold_for_protected_surfaces_without_an_identity():
    """The negative control: an unauthenticated visitor must not render the
    protected page content. The gate is the app composition root's job."""
    assert "AuthThreshold" in APP
    assert "def.requiresAuth && !isAuthenticated" in APP
    # The threshold is not cosmetic -- it names the boundary and offers sign-in.
    assert "Sign in to continue" in APP
    assert 'href="/login"' in APP


def test_sign_in_surface_carries_the_cp10_gate_testids():
    """The CP10 browser gate drives this exact form. If the testids drift, the
    automated acceptance gate can no longer exercise the real sign-in path."""
    assert SIGNIN.is_file(), "the console has no sign-in page for the acceptance gate to drive"
    body = SIGNIN.read_text(encoding="utf-8")
    for testid in ("tab-signin", "input-email-signin", "input-password-signin", "button-signin"):
        assert f'data-testid="{testid}"' in body, f"sign-in page lost {testid}"


def test_sign_in_has_no_development_bypass():
    """There is no anonymous/local login path: when Firebase is not configured the
    form is not offered at all."""
    body = SIGNIN.read_text(encoding="utf-8")
    assert "firebaseConfigured" in body
    assert "Authentication is not configured" in body


def test_login_is_reachable_but_not_a_navigation_surface():
    assert 'path: "/login"' in SURFACES
    assert "nav: false" in SURFACES


# ---------------------------------------------------------------------------
# The CP10 browser gate observes the console, not the retired Prism strings
# ---------------------------------------------------------------------------


def test_cp10_gate_is_bound_to_the_console_threshold():
    """The gate previously pinned retired Prism copy (``Enter the enterprise
    layer.``). It must assert the console's own threshold copy instead."""
    threshold_region = WORKFLOW.split("const UNAUTH_THRESHOLD", 1)[1].split(";", 1)[0]
    assert "Enter the enterprise layer." not in threshold_region
    assert "Sign in to continue" in threshold_region


def test_cp10_gate_authenticated_lens_targets_a_console_route():
    """The authenticated lens step must resolve the console's own Lab route. The
    unauthenticated route loop probes the console's SolSpire surface (now
    ``/enterprise``) to prove it leaks nothing; what matters is that the
    authenticated observation targets the console surface."""
    assert "navigate_lab" in WORKFLOW
    lab_region = WORKFLOW.split("phase='navigate_lab'", 1)[1].split("phase=", 1)[0]
    assert "/engineering-lab'" in lab_region or "/engineering-lab\"" in lab_region
    assert "/solspire/engineering-lab" not in lab_region


def test_cp10_gate_route_targets_a_declared_console_surface():
    """The browser gate must drive a route the console actually declares. A route
    the console does not serve is a phantom probe: on the Vite dev server every
    path returns 200, so the gate stays green while the canonical FastAPI origin
    would 404 that path. Bind the gate's first probe to the surface table."""
    import re

    declared = set(re.findall(r'path: "([^"]+)"', SURFACES))
    probe = re.search(r"const r0=await p\.goto\('http://127\.0\.0\.1:5000([^']*)'", WORKFLOW)
    assert probe, "the CP10 gate has no unauthenticated first probe"
    route = probe.group(1)
    assert route in declared, f"CP10 gate probes {route!r}, which is not a declared console surface"
    # The retired Prism SolSpire path was the reserved backend namespace; it must
    # not be probed as if it were a console surface.
    assert "/solspire" not in route


def test_cp10_gate_detector_would_flag_the_retired_copy():
    """Negative control: the retired Prism string is a real literal, so a gate
    restored to it would be caught by this guard's own assertion."""
    retired = "const UNAUTH_THRESHOLD='Enter the enterprise layer.';"
    assert "Enter the enterprise layer." in retired
    threshold_region = WORKFLOW.split("const UNAUTH_THRESHOLD", 1)[1].split(";", 1)[0]
    assert "Enter the enterprise layer." not in threshold_region


# ---------------------------------------------------------------------------
# The Gate-2 observation is bound to the app it measures
# ---------------------------------------------------------------------------


def test_gate2_declares_a_marker_list_per_frontend():
    """A console artifact scored against Prism literals reads 0 everywhere -- a
    category error, not a regression. Each frontend needs its own list."""
    assert "MARKER_APPS" in GATE2
    for app in ("arkadia-prism", "arkadia-console"):
        assert f'"{app}"' in GATE2
    # The console list carries a control literal that must be absent.
    console_block = GATE2.split('"arkadia-console": {', 1)[1].split("},", 1)[0]
    assert "Enter the enterprise layer." in console_block
    assert ", False," in console_block, "the console marker list has no control literal"


def test_gate2_scopes_the_marker_read_to_the_observed_app():
    """The read (``markers_in``) and the source check (``source_markers_present``)
    must take the observed app, so a Prism artifact is never scored as a console
    one or vice versa."""
    assert "markers_in(text, observed_app)" in GATE2
    assert "source_markers_present(observed_app)" in GATE2
    assert "observed_app = deployed_app if deployed_app in MARKER_APPS else None" in GATE2


def test_gate2_archived_prism_build_input_is_still_observable():
    """The Prism lineage must stay observable after the archive move; its build
    input is read under the archive location, not the removed path."""
    assert "archive/frontend/arkadia-prism/web/public_prism/" in GATE2


# ---------------------------------------------------------------------------
# The canonical browser smoke observes routes it can actually resolve
# ---------------------------------------------------------------------------

SMOKE = (ROOT / ".github" / "workflows" / "canonical-render-browser-smoke.yml").read_text(
    encoding="utf-8"
)
ROUTER = (CONSOLE / "src" / "lib" / "router.ts").read_text(encoding="utf-8")


def declared_surface_paths() -> set[str]:
    """Every path ``surfaces.ts`` declares, which is the only source of surfaces."""
    return set(re.findall(r'path:\s*"([^"]+)"', SURFACES))


def surface_paths_by_id() -> dict[str, str]:
    """`SurfaceId -> declared path`, read from the same table."""
    ids = [(m.start(), m.group(1)) for m in re.finditer(r'id:\s*"([^"]+)"', SURFACES)]
    paths: dict[str, str] = {}
    for index, (offset, surface_id) in enumerate(ids):
        end = ids[index + 1][0] if index + 1 < len(ids) else len(SURFACES)
        found = re.search(r'path:\s*"([^"]+)"', SURFACES[offset:end])
        if found:
            paths[surface_id] = found.group(1)
    return paths


def path_aliases() -> dict[str, str]:
    """`legacy path -> SurfaceId`, read from the router's own alias table."""
    body = ROUTER.split("export const PATH_ALIASES", 1)[1].split("};", 1)[0]
    return dict(re.findall(r'"([^"]+)":\s*"([^"]+)"', body))


def smoke_route_entries() -> list[dict[str, str]]:
    """The route table the smoke drives, as ``{path, resolvesTo}`` pairs."""
    body = SMOKE.split("const routes = [", 1)[1].split("];", 1)[0]
    entries = []
    for block in re.findall(r"\{(.*?)\}", body, re.S):
        path = re.search(r"path:\s*'([^']+)'", block)
        resolves = re.search(r"resolvesTo:\s*'([^']+)'", block)
        if path and resolves:
            entries.append({"path": path.group(1), "resolvesTo": resolves.group(1)})
    return entries


def is_declared_or_lens(path: str, declared: set[str]) -> bool:
    """True when ``path`` is a declared surface path or a declared lens of one."""
    return path in declared or any(
        path.startswith(d + "/") for d in declared if d != "/"
    )


def route_binding_findings(entries: list[dict[str, str]]) -> list[str]:
    """Findings for a smoke route table that cannot measure what it claims.

    A path the console does not declare falls through ``resolvePath`` to ``home``
    and still answers 200 with a full page, so a drifted route is invisible to a
    status/body check. Two shapes are therefore rejected: a path that resolves to
    nothing the console declares, and a legacy alias whose declared target
    disagrees with the one the router actually applies.
    """
    declared = declared_surface_paths()
    by_id = surface_paths_by_id()
    aliases = path_aliases()
    findings: list[str] = []
    for entry in entries:
        path, resolves = entry["path"], entry["resolvesTo"]
        if path == resolves:
            if not is_declared_or_lens(path, declared):
                findings.append(f"{path}: not a declared surface path or lens of one")
            continue
        if not is_declared_or_lens(resolves, declared):
            findings.append(
                f"{path}: resolves to {resolves}, which is not a declared surface "
                f"path or lens of one"
            )
            continue
        target = aliases.get(path)
        if target is None:
            findings.append(f"{path}: resolves elsewhere but is not a PATH_ALIASES key")
            continue
        expected = by_id.get(target)
        if expected != resolves:
            findings.append(
                f"{path}: alias target is {expected!r}, but the smoke expects {resolves!r}"
            )
    return findings


def test_smoke_routes_are_bound_to_declared_surfaces():
    entries = smoke_route_entries()
    assert len(entries) >= 7, f"the smoke drives only {len(entries)} routes"
    assert route_binding_findings(entries) == []


def test_smoke_route_detector_flags_the_pre_repair_shapes():
    """Negative control: the detector must redden on the defects it exists to catch.

    A route the console does not declare, and a legacy alias pointed at the wrong
    surface, are the two ways a row can look wired while measuring the fallback.
    """
    assert route_binding_findings(
        [
            {"path": "/", "resolvesTo": "/"},
            {"path": "/definitely-not-a-surface", "resolvesTo": "/definitely-not-a-surface"},
            {"path": "/oracle", "resolvesTo": "/n-atlas-lab"},
        ]
    ) == [
        "/definitely-not-a-surface: not a declared surface path or lens of one",
        "/oracle: alias target is '/arkana', but the smoke expects '/n-atlas-lab'",
    ]


def test_smoke_scores_the_fallback_and_names_the_deployed_revision():
    """A 200 with a full body is not evidence a route resolved, and the artifact
    must name the revision the deployment reported rather than the repository's."""
    assert "fell_back: finalPath !== route.resolvesTo" in SMOKE
    assert "!record.fell_back" in SMOKE, "the fallback is recorded but not scored"
    assert "deployed_revision: process.env.DEPLOYED_REVISION" in SMOKE
    assert "source_revision: process.env.GITHUB_SHA" not in SMOKE, (
        "the artifact must not label the observation with the repository SHA"
    )
    assert "steps.ready.outputs.observed_revision" in SMOKE


def test_smoke_readiness_requires_a_readable_deployment_revision():
    """The Render hibernation wake page is a 200 HTML body with no revision. A
    readiness check that accepts a bare 200 can smoke a loader and report PASS."""
    readiness = SMOKE.split("Wait for canonical Render readiness", 1)[1].split(
        "Install Playwright", 1
    )[0]
    assert "grep -Eq '^[0-9a-f]{40}$'" in readiness

