from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_living_gate_is_capability_portfolio_onboarding():
    source = read("web/public_prism/src/pages/LivingGate.tsx")
    for marker in (
        "A.I.S Capability Portfolio",
        "Identity",
        "Capability Map",
        "Builds",
        "Evidence",
        "Projects",
        "Offer",
        "Credentials",
        "Growth Map",
        "open-spiral-grove",
        "arkadia.ais.capability-portfolio.v1",
    ):
        assert marker in source


def test_living_gate_uses_existing_spiral_grove_catalog():
    source = read("web/public_prism/src/pages/LivingGate.tsx")
    assert "../data/spiralGroveCatalog" in source
    assert "AIS_CAPABILITIES" in source
    assert "GROVE_DOMAINS" in source


def test_home_is_offer_led_and_keeps_arkadia_entry_points():
    source = read("web/public_prism/src/components/ArkadiaNavigation.tsx")
    landing = read("web/public_prism/src/pages/ArkadiaLandingPage.tsx")
    assert "ArkadiaLandingPage" in source
    assert "currentView === 'home'" in source
    assert "Learn. Build. Prove. Launch." in landing
    assert "button-home-ais-diagnostic" in landing
    assert "button-home-ais-diagnostic" in landing
    assert "Spiral Grove" in landing
    assert "SolSpire" in landing
    assert "NovaNet" in landing


def test_no_reset_or_old_likert_contract_in_primary_gate():
    source = read("web/public_prism/src/pages/LivingGate.tsx")
    assert "RESET_LYRICS" not in source
    assert "Strongly\\nDisagree" not in source
    assert "api/pulse/analyze" not in source
