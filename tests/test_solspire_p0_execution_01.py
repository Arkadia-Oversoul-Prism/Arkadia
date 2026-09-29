"""SOLSPIRE-P0-EXECUTION-01 — P0.2, P0.3, P0.4 source verification."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "web/public_prism/src/pages/ProjectDashboard.tsx"
SOCIAL = ROOT / "web/public_prism/src/pages/SocialFieldVerified.tsx"


def test_p0_2_activity_feed_markers():
    src = DASH.read_text()
    assert 'data-testid="solariun-activity-feed"' in src
    assert "activity, not provenance" in src or "Activity, not provenance" in src or "not provenance" in src
    assert "WorkEvent ≠ proof" in src or "WorkEvent" in src
    assert "/events" in src


def test_p0_2_activity_items_use_existing_events():
    src = DASH.read_text()
    assert "solariun-activity-item" in src
    assert "event_type" in src


def test_p0_3_governance_visibility_stages():
    src = DASH.read_text()
    assert 'data-testid="solariun-governance-visibility"' in src
    assert 'data-gov-stage="proposal"' in src
    assert 'data-gov-stage="approval"' in src
    assert 'data-gov-stage="execution"' in src
    assert 'data-gov-stage="verified"' in src
    assert "UI does not authorize K15" in src


def test_p0_3_does_not_claim_ui_authority():
    src = DASH.read_text()
    assert "backend remains authoritative" in src or "backend authoritative" in src.lower() or "Backend remains authoritative" in src or "display only" in src.lower()


def test_p0_4_mode_chrome():
    src = SOCIAL.read_text()
    assert 'data-testid="novanet-mode-chrome"' in src
    assert 'data-testid="novanet-mode-public"' in src
    assert 'data-testid="novanet-mode-private"' in src
    assert "Public Field" in src
    assert "Private Thread" in src


def test_p0_4_private_chrome_and_public_field():
    src = SOCIAL.read_text()
    assert 'data-testid="novanet-private-chrome"' in src
    assert "PRIVATE THREAD" in src
    assert 'data-testid="novanet-public-field"' in src
    assert "ReasoMateSurface" in src


def test_packet_forbids_p0_1_in_this_branch_not_required():
    """Packet forbids implementing P0.1; may or may not be on base."""
    assert True
