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
    # SH-02 row 2 re-pin: the marketing tagline moved off the landing page.
    # The surface is now offer-led, so the copy is pinned to the live headline;
    # the two anchors it framed are still asserted below.
    #
    # Re-pinned again 2026-10-07 (gate-hygiene/landing-headline-repin-01): the
    # SH-02e pin above named a headline that `2b87e8e` (#276, canonical
    # Oversoul identity) then removed — a *source change* with no test-side
    # re-pin, so the assertion drifted red on main. Pin the live architecture
    # headline instead; the same two anchors it frames are asserted below.
    assert "One Prism. Many ways to work with it." in landing
    # The landing surface is still reachable and still its own mount point.
    assert 'data-testid="arkadia-home-landing"' in landing
    assert "Spiral Grove" in landing
    assert "SolSpire" in landing
    assert "NovaNet" in landing


def test_no_reset_or_old_likert_contract_in_primary_gate():
    source = read("web/public_prism/src/pages/LivingGate.tsx")
    assert "RESET_LYRICS" not in source
    assert "Strongly\\nDisagree" not in source
    assert "api/pulse/analyze" not in source
