from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "web/public_prism/src/pages/ProjectDashboard.tsx"
CANVAS = ROOT / "web/public_prism/src/components/solspire/ArcanaWeaverCanvas.tsx"
NAV = ROOT / "web/public_prism/src/components/solspire/SolSpireExperience.tsx"


def test_arcana_weaver_fuses_project_canvas_weaver_and_arkana_runtime():
    canvas = CANVAS.read_text(encoding="utf-8")
    dashboard = DASH.read_text(encoding="utf-8")
    nav = NAV.read_text(encoding="utf-8")

    assert "SolariunInteractionCanvas" in canvas
    assert "ArkanaCommune" in canvas
    assert "ProjectAgenticCanvas" in canvas
    assert "projectContextId={project.id}" in canvas
    assert 'data-testid="arcana-weaver-canvas"' in canvas
    assert "ArcanaWeaverCanvas" in dashboard
    assert "(tab === 'weaver' || tab === 'canvas')" in dashboard
    assert "label: 'Arcana Weaver'" in dashboard
    assert "label:'Arcana Weaver'" in nav
