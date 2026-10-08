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
    src = read("web/public_prism/src/pages/NodeEntry.tsx")
    assert "WELCOME TO ARKADIA" in src
    # The A.I.S surface reads and writes the canonical capability portfolio. Pinning the
    # constant rather than the URL literal keeps this true when the transport moves to
    # `apiFetch`, which resolves the base URL itself (ADR: consumers do not resolve it).
    assert "AIS_PROFILE_PATH" in src
    assert "/api/me/ais-profile" in src
    assert "kind:'portfolio'" in src or "kind: 'portfolio'" in src
    assert "pulse" in src
    # SUPERSEDED PIN (measured at 24a00f85): this node previously demanded
    # "Let's form your node." / "Form my node" / "AIS_CAPABILITIES" / "GROVE_DOMAINS".
    # None was ever satisfiable — the diagnostic CTA copy was replaced by the current
    # A.I.S copy before the assertion landed, and NodeEntry never imported the Grove
    # catalogue. See tests/test_ais_w2_living_gate_grove_handoff.py, which escalates the
    # catalogue question as a product decision rather than auto-repairing it.


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
