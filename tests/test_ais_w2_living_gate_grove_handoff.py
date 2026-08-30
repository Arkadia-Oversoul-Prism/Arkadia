"""W2 — Living Gate A.I.S diagnostic → Spiral Grove handoff.

Static contract tests. No second diagnostic, catalogue, or learner-state system.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "web/public_prism/src/pages/LivingGate.tsx"
GROVE = ROOT / "web/public_prism/src/pages/SpiralGrovePage.tsx"
CATALOG = ROOT / "web/public_prism/src/data/spiralGroveCatalog.ts"
APP = ROOT / "web/public_prism/src/App.tsx"
NAV = ROOT / "web/public_prism/src/components/ArkadiaNavigation.tsx"


def _r(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_living_gate_defaults_to_diagnostic_not_reset():
    src = _r(GATE)
    assert re.search(
        r"useState<FlowStep>\(\s*initialMode === 'reset' \? 'reset' : 'diagnostic'\s*\)",
        src,
    ), "Living Gate must default to diagnostic entry"
    assert "useState<FlowStep>('reset')" not in src


def test_pulse_analyze_endpoint_preserved():
    src = _r(GATE)
    assert "/api/pulse/analyze" in src
    assert src.count("/api/pulse/analyze") >= 1


def test_spiral_grove_handoff_prop_and_cta():
    src = _r(GATE)
    assert "onEnterSpiralGrove" in src
    assert 'data-testid="open-spiral-grove"' in src
    assert "Open Spiral Grove" in src


def test_app_wires_grove_navigation():
    app = _r(APP)
    assert "onEnterSpiralGrove={() => handleNavigate('grove')}" in app
    assert "view === 'grove'" in app
    assert "SpiralGrovePage" in app


def test_no_second_capability_catalogue():
    grove = _r(GROVE)
    catalog = _r(CATALOG)
    assert "AIS_CAPABILITIES" in catalog
    assert "GROVE_DOMAINS" in catalog
    assert "INITIAL_LEARNER_STATES" in catalog
    assert "from '../data/spiralGroveCatalog'" in grove or 'from "../data/spiralGroveCatalog"' in grove
    assert not re.search(r"const\s+AIS_CAPABILITIES\s*=\s*\[", grove)


def test_homepage_untouched_in_app_home_function():
    app = _r(APP)
    assert "function Home(" in app
    assert "PortalDoor" in app


def test_nav_subtitle_describes_ais_onboarding():
    nav = _r(NAV)
    assert "A.I.S diagnostic" in nav
    assert "Reset - IMS - AIC - 5-Minute" not in nav


def test_no_firebase_persistence_in_gate():
    src = _r(GATE)
    assert "localStorage.setItem" not in src
    assert "sessionStorage" not in src


def test_ims_lineage_preserved():
    src = _r(GATE)
    assert "invitation" in src
    assert "Ready for the Full Map" in src
    assert "BookingStep" in src or "booking" in src
