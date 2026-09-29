"""M03 — NovaNet public field vs private ReasoMate boundary."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOVANET = ROOT / "web/public_prism/src/pages/NovaNetPage.tsx"
FIELD = ROOT / "web/public_prism/src/pages/SocialFieldVerified.tsx"
REASOMATE = ROOT / "web/public_prism/src/components/ReasoMateSurface.tsx"
APP = ROOT / "web/public_prism/src/App.tsx"


def test_novanet_page_is_public_field_surface():
    assert "SocialFieldVerified" in NOVANET.read_text()


def test_public_field_markers_present():
    src = FIELD.read_text()
    assert 'data-testid="novanet-public-field"' in src
    assert 'data-testid="novanet-public-feed"' in src
    assert "PUBLIC FIELD" in src or "public field" in src.lower()


def test_novanet_reasomate_tab_uses_private_surface():
    src = FIELD.read_text()
    assert "ReasoMateSurface" in src
    assert 'data-testid="novanet-tab-reasomate"' in src
    # Must not mount only SocialMessenger as the private tab replacement
    assert "mode === \"reasomate\"" in src or "mode === 'reasomate'" in src
    assert "ReasoMateSurface" in src


def test_private_surface_still_marked():
    surface = REASOMATE.read_text()
    assert 'data-testid="reasomate-private-surface"' in surface
    assert "not the public field" in surface.lower() or "Private messenger" in surface


def test_public_feed_uses_transmissions_api():
    src = FIELD.read_text()
    assert "/api/transmissions" in src


def test_knowledge_os_not_imported_into_public_field():
    src = FIELD.read_text()
    assert "KnowledgeOS" not in src
    assert "knowledge-os" not in src.lower()


def test_app_routes_novanet_and_reasomate_distinct():
    app = APP.read_text()
    assert "view === 'novanet'" in app
    assert "view === 'reasomate'" in app
    assert "NovaNetPage" in app
    assert "ReasoMatePage" in app


def test_m03_does_not_touch_k15_k3_paths():
    """Sanity: this move's primary product file is the field surface only."""
    src = FIELD.read_text()
    assert "pass_spec" not in src
    assert "execute_patch" not in src
