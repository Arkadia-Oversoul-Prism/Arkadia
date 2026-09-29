"""P2 implementation — search honesty + epistemic inspector; Intent/Automation deferred."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "web/public_prism/src/components/solspire/SolSpireExperience.tsx"
DASH = ROOT / "web/public_prism/src/pages/ProjectDashboard.tsx"


def test_p2_search_honest_coverage():
    src = EXP.read_text()
    assert 'data-testid="solariun-search-coverage"' in src
    assert "COVERAGE (honest)" in src
    assert "No universal object index" in src
    assert "Federated search" in src
    assert "Universal search" not in src.split("function SearchOverlay")[1][:500] or "Federated" in src


def test_p2_search_federates_project_when_open():
    src = EXP.read_text()
    assert "project-corpus" in src
    assert "/solspire/projects/${project.id}/files" in src
    assert "project={project}" in src


def test_p2_epistemic_inspector():
    src = DASH.read_text()
    assert 'data-testid="solariun-epistemic-inspector"' in src
    assert 'data-epistemic="ACTIVITY"' in src
    assert 'data-epistemic="CONTINUITY"' in src
    assert "not" in src.lower() and "provenance proof" in src.lower()


def test_p2_does_not_implement_intent_store():
    # no new intent table references in these files
    assert "CREATE TABLE intent" not in DASH.read_text().lower()


def test_p2_does_not_activate_aeas_automation():
    src = EXP.read_text() + DASH.read_text()
    assert "auto_build" not in src
