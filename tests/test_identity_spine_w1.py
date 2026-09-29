from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_ais_profile_exposes_canonical_identity_spine():
    src = read("api/ais_profile.py")
    assert '_SPINE_KEY = "identity_spine"' in src
    assert '@router.get("/api/me/identity-spine")' in src
    assert 'load_user_profile_store(user["uid"])' in src
    assert 'relational_index' in src
    assert 'capability' in src


def test_node_entry_is_ais_signup_not_a_separate_diagnostic_route():
    src = read("web/public_prism/src/pages/NodeEntry.tsx")
    assert "WELCOME TO ARKADIA" in src
    assert "Let's form your node." in src
    assert "Form my node" in src
    assert "/api/me/ais-profile" in src
    assert "AIS_CAPABILITIES" in src
    assert "GROVE_DOMAINS" in src


def test_personal_field_places_master_profile_at_its_root():
    src = read("web/public_prism/src/pages/UniversalEchofeildMatrix.tsx")
    assert "import MasterProfile from './MasterProfile';" in src
    assert "<MasterProfile />" in src
    assert "Personal Codex · EchoField" in src


def test_master_profile_is_longitudinal_and_non_destructive():
    src = read("web/public_prism/src/pages/MasterProfile.tsx")
    assert "/api/me/identity-spine" in src
    assert "Capability Baseline · Spiral Grove" in src
    assert "Relational Index" in src
    assert "Continuity" in src
    assert "The seed remains provenance" in src
