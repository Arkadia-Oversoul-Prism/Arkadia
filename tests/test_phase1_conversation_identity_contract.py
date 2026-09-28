"""Phase 1 — Arkana conversation identity contract."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "api" / "main.py"
ARKANA = ROOT / "web" / "public_prism" / "src" / "components" / "ArkanaCommune.tsx"
DASH = ROOT / "web" / "public_prism" / "src" / "pages" / "ProjectDashboard.tsx"


def test_resonance_returns_explicit_session_identity_fields():
    src = MAIN.read_text()
    assert '"session": session_kind' in src
    assert '"identity_kind": identity_kind' in src
    assert '"session_id": session_id or None' in src
    assert 'identity_kind = "authenticated"' in src
    assert 'identity_kind = "guest"' in src


def test_frontend_does_not_default_authenticated_turns_to_guest():
    src = ARKANA.read_text()
    assert "data.identity_kind" in src
    assert "isAuthenticated ? 'authenticated'" in src
    assert "Authenticated session · thread continuity via Knowledge OS" in src
    assert "Guest session · sign in for durable continuity" in src


def test_weaver_precheck_is_not_labeled_as_execute_only():
    src = DASH.read_text()
    assert "K15 PRECHECK (NOT EXECUTE)" in src
    assert "run_k3=false" in src
    assert "NOT MUTATION" in src
