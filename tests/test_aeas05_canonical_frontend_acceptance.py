"""AEAS-05 — Canonical Frontend Acceptance guards.

The console transition is only acceptable if its protected surfaces are actually
gated, its sign-in surface is the one the CP10 browser gate drives, and the
Gate-2 observation binds each marker reading to the application it measured.

These are source-level contracts, matching this repository's frontend-test
convention. They are the pre-deployment half of AEAS-05: they must pass before a
production cutover may be claimed.
"""
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
    unauthenticated deep-link loop may still probe ``/solspire/*`` to prove it
    leaks nothing; what matters is that the authenticated observation targets the
    console surface."""
    assert "navigate_lab" in WORKFLOW
    lab_region = WORKFLOW.split("phase='navigate_lab'", 1)[1].split("phase=", 1)[0]
    assert "/engineering-lab'" in lab_region or "/engineering-lab\"" in lab_region
    assert "/solspire/engineering-lab" not in lab_region


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
