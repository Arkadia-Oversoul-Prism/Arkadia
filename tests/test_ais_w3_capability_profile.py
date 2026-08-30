from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTIC = ROOT / "web/public_prism/src/pages/AISCapabilityDiagnostic.tsx"
APP = ROOT / "web/public_prism/src/App.tsx"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_living_gate_uses_new_capability_diagnostic():
    source = read(APP)
    assert "AISCapabilityDiagnostic" in source
    assert "<AISCapabilityDiagnostic onEnterSpiralGrove={() => handleNavigate('grove')} />" in source
    assert "<LivingGate" in source


def test_diagnostic_uses_existing_grove_catalogue():
    source = read(DIAGNOSTIC)
    assert "AIS_CAPABILITIES" in source
    assert "GROVE_DOMAINS" in source
    assert "Choose up to three capability territories" in source
    assert "not a second catalogue" in source


def test_profile_contains_eight_requested_surfaces():
    source = read(DIAGNOSTIC)
    for marker in (
        "Identity · Who am I?",
        "Capability Map · What can I do?",
        "Builds · What have I created?",
        "Evidence · Can I demonstrate it?",
        "Projects · Where have I applied it?",
        "Offer · What value can I provide?",
        "Credentials · What have I demonstrated?",
        "Growth Map · What should I learn next?",
    ):
        assert marker in source


def test_profile_persists_without_inventing_backend_storage():
    source = read(DIAGNOSTIC)
    assert "arkadia.ais.capability-portfolio.v1" in source
    assert "localStorage.setItem" in source
    assert "ownerUid" in source


def test_grove_handoff_is_primary_profile_action():
    source = read(DIAGNOSTIC)
    assert "data-testid=\"portfolio-open-spiral-grove\"" in source
    assert "Open Spiral Grove" in source
    assert "Spiral Grove is where the capability gets developed, demonstrated and updated." in source
