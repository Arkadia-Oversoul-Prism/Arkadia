"""Regression contract for GOV-01 conditional Weaver merge delegation."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "docs/control-plane/parallel-ui/SHARED-CONTRACTS.md"
DIRECTIVE = ROOT / "docs/control-plane/overnight/PRISM-UI-RECONCILIATION.md"
AGENTS = ROOT / "AGENTS.md"


def test_governance_docs_agree_on_conditional_weaver_merge_authority():
    shared, directive, agents = (p.read_text(encoding="utf-8") for p in (SHARED, DIRECTIVE, AGENTS))
    for content in (shared, directive, agents):
        assert "GOV-01" in content
        assert "M1–M13" in content or "M1-M13" in content
        assert "branch protection" in content.lower()
        assert "human" in content.lower() and "approval" in content.lower()
    assert "They may not merge any PR" not in directive
    assert "no merge/deploy/acceptance by agents" not in shared
    assert "Weaver may merge an existing candidate only" in agents
    assert "OpenHands and other agents do not inherit this authority" in agents


def test_human_only_boundaries_and_lane_ownership_are_preserved():
    shared, directive, agents = (p.read_text(encoding="utf-8") for p in (SHARED, DIRECTIVE, AGENTS))
    for content in (shared, directive, agents):
        assert "K15/K3" in content
        assert "acceptance" in content.lower()
        assert "production" in content.lower()
    assert all(f"Workstream {n}" in shared for n in range(1, 5))
    assert "one-open-PR-per-lane" in shared or "one open PR per lane" in shared


def test_gov01_cannot_authorize_its_own_merge():
    shared, directive, agents = (p.read_text(encoding="utf-8") for p in (SHARED, DIRECTIVE, AGENTS))
    for content in (shared, directive, agents):
        assert "GOV-01 itself" in content or "amendment itself" in content
        assert "human-reviewed and human-merged" in content
