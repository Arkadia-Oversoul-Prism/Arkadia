from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "web/public_prism/src/App.tsx"
FRAME = ROOT / "web/public_prism/src/components/ExperienceConsolidationFrame.tsx"
CSS = ROOT / "web/public_prism/src/components/experience-consolidation.css"
MAP = ROOT / "docs/architecture/SOLARIUN_EXPERIENCE_CONSOLIDATION_01_MAP.md"


def test_area_a_novanet_is_bound_to_shared_experience_shell():
    src = APP.read_text()
    assert 'surface="NovaNet"' in src
    assert "<NovaNetPage />" in src
    assert "ExperienceConsolidationFrame" in src


def test_area_b_solariun_workspace_is_bound_to_shared_experience_shell():
    src = APP.read_text()
    assert 'surface="Solariun"' in src
    assert "<SolSpireConsole" in src
    assert "/solspire" in src


def test_area_c_solspire_substrate_uses_existing_search_and_context_grammar():
    src = FRAME.read_text()
    assert "searchKnowledge" in src
    assert "Knowledge OS search only" in src
    assert "No universal object index" in src
    assert "ACTIVITY ≠ PROVENANCE" in src
    assert "Existing repository components + existing APIs" in src


def test_area_d_spiral_command_is_bound_to_existing_sci_surface():
    app = APP.read_text()
    sci = (ROOT / "web/public_prism/src/pages/SpiralCommandInterface.tsx").read_text()
    assert 'surface="Spiral Command"' in app
    assert "<SpiralCommandInterface" in app
    assert "'/sci': {view:'sci'}" in app
    assert "SCI_DISCOVERY_WITHOUT_AUTHORITY" in sci
    assert "does not authorize" in sci.lower() or "not authorization" in sci.lower()
    assert "K15" in sci and "K3" in sci


def test_responsive_composition_and_inspector_exist():
    css = CSS.read_text()
    frame = FRAME.read_text()
    assert "@media (max-width: 920px)" in css
    assert "@media (max-width: 600px)" in css
    assert 'data-testid="experience-inspector"' in frame
    assert 'data-testid="experience-context-bar"' in frame


def test_forbidden_architecture_not_introduced():
    frame = FRAME.read_text()
    assert "CREATE TABLE" not in frame.upper()
    assert "graph db" not in frame.lower()
    assert "intent schema" not in frame.lower()
    assert "auto_build" not in frame.lower()
    assert "run_transaction" not in frame.lower()
    assert "WorkEvent" not in frame
    assert "K15 -> K3" not in frame


def test_preimplementation_map_is_present_and_bounded():
    mapping = MAP.read_text()
    for area in ["NovaNet", "Solariun Workspace", "SolSpire substrate", "Spiral Command"]:
        assert area in mapping
    assert "Recursive endpoint/component/data mapping" in mapping
    assert "Merge: human_only" in mapping
    assert "Deploy: human_only" in mapping
