import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_ais_profile_exposes_canonical_identity_spine():
    src = read("api/ais_profile.py")
    assert re.search(r"_SPINE_KEY\s*=\s*['\"]identity_spine['\"]", src)
    assert re.search(r"@router\.get\(\s*['\"]/api/me/identity-spine['\"]\s*\)", src)
    assert re.search(r"load_user_profile_store\(\s*user\[['\"]uid['\"]\]\s*\)", src)
    assert 'relational_index' in src
    assert 'capability' in src


def test_node_entry_is_ais_signup_not_a_separate_diagnostic_route():
    src = read("archive/frontend/arkadia-prism/web/public_prism/src/pages/NodeEntry.tsx")
    assert "WELCOME TO ARKADIA" in src
    # The surface must *define* the path it fetches. A reference without a definition
    # throws inside the mount try/catch, silently disabling the A.I.S read/write — so the
    # definition, not just the URL literal, is the assertion.
    assert re.search(r"const\s+AIS_PROFILE_PATH\s*=", src)
    assert "/api/me/ais-profile" in src
    assert "kind:'portfolio'" in src or "kind: 'portfolio'" in src
    assert "pulse" in src
    # SUPERSEDED PIN (measured at bb19aabd): this node demanded "Let's form your node." /
    # "Form my node" / "AIS_CAPABILITIES" / "GROVE_DOMAINS". The archived Prism source never
    # carried the first two (its copy is "Let's see what feels like you." / "See my shape →")
    # and never imported the Grove catalogue; that catalogue question stays escalated in
    # tests/test_ais_w2_living_gate_grove_handoff.py as a product decision.


def test_personal_field_places_master_profile_at_its_root():
    src = read("archive/frontend/arkadia-prism/web/public_prism/src/pages/UniversalEchofeildMatrix.tsx")
    assert "import MasterProfile from './MasterProfile';" in src
    assert "<MasterProfile />" in src
    assert "Personal Codex · EchoField" in src


def test_master_profile_is_longitudinal_and_non_destructive():
    src = read("archive/frontend/arkadia-prism/web/public_prism/src/pages/MasterProfile.tsx")
    assert "/api/me/identity-spine" in src
    assert "Capability Baseline · Spiral Grove" in src
    assert "Relational Index" in src
    assert "Continuity" in src
    assert "The seed remains provenance" in src
