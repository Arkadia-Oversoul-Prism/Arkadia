from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "web/public_prism/src/pages/ProjectDashboard.tsx"
CANVAS = ROOT / "web/public_prism/src/components/solspire/ArkanaWeaverCanvas.tsx"
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
    assert "ArkanaWeaverCanvas" in dashboard
    # The merged canvas was mounted as `(tab === 'weaver' || tab === 'canvas')`, which
    # replaced the Weaver tab's governed lifecycle panel (WeaverPanel). Pin the mount
    # expression actually composed here instead of the discarded combined-condition form.
    assert "tab === 'canvas'" in dashboard
    assert "<ArkanaWeaverCanvas project={currentProject} />" in dashboard
    assert "<WeaverPanel project={currentProject} />" in dashboard
    assert "label: 'Arkana Weaver'" in dashboard
    assert "label:'Arkana Weaver'" in nav
