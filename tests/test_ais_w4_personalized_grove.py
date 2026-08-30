"""W4 — A.I.S capability portfolio → personalized Spiral Grove path contracts."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROVE = ROOT / "web/public_prism/src/pages/SpiralGrovePage.tsx"


def _r():
    return GROVE.read_text(encoding="utf-8")


def test_grove_reads_the_existing_transient_portfolio():
    src = _r()
    assert "arkadia.ais.capability-portfolio.v1" in src
    assert "sessionStorage.getItem(PORTFOLIO_KEY)" in src
    assert "function readPortfolio" in src


def test_personalization_reuses_canonical_grove_registry():
    src = _r()
    assert "AIS_CAPABILITIES" in src
    assert "GROVE_DOMAINS" in src
    assert "function derivePersonalization" in src
    assert "item.name.toLowerCase() === value.toLowerCase()" in src


def test_personalized_path_has_explainable_start_action():
    src = _r()
    assert 'data-testid="personalized-grove-path"' in src
    assert 'data-testid="grove-recommended-action"' in src
    assert "Your Grove starting point" in src
    assert "Start here →" in src


def test_w4_does_not_add_persistence_or_authority():
    src = _r()
    assert "sessionStorage.setItem" not in src
    assert "firebase" not in src.lower()
    assert "Knowledge OS remains the canonical source-backed knowledge authority" in src


def test_grove_keeps_existing_learning_path_runtime():
    src = _r()
    assert "learningPathFor" in src
    assert "learningActivitiesFor" in src
    assert "prerequisitesFor" in src
    assert "CapabilityChamber" in src
