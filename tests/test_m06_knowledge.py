"""M06 — project knowledge uses existing APIs; no second Knowledge OS."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "web/public_prism/src/pages/ProjectDashboard.tsx"


def test_project_knowledge_markers():
    src = DASH.read_text()
    assert 'data-testid="solariun-project-knowledge"' in src
    assert "ONE KNOWLEDGE MODEL" in src


def test_knowledge_uses_project_apis():
    src = DASH.read_text()
    assert "/solspire/projects/${project.id}/knowledge" in src
    assert "/solspire/projects/${project.id}/files" in src


def test_knowledge_panel_does_not_import_second_os():
    # Panel is inline; ensure no alternate knowledge DB path
    src = DASH.read_text()
    panel = src[src.find("function KnowledgePanel"): src.find("function Files")]
    assert "indexedDB" not in panel.lower()
    assert "NOT_AVAILABLE" in panel or "embeddings" in panel.lower()
