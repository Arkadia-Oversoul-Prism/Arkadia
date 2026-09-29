import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "web/public_prism/src/App.tsx"
FRAME = ROOT / "web/public_prism/src/components/ExperienceConsolidationFrame.tsx"
CSS = ROOT / "web/public_prism/src/components/experience-consolidation.css"
MAP = ROOT / "docs/architecture/SOLARIUN_EXPERIENCE_CONSOLIDATION_01_MAP.md"
# Area C owners per the map ("Existing data/runtime": searchKnowledge over
# Knowledge OS groups; existing Arkana context pack UI). The substrate grammar
# moved out of the frame wrapper into the components that actually own it, so
# the assertions follow it there rather than pinning the wrapper's prose.
SOLSPIRE = ROOT / "web/public_prism/src/components/solspire/SolSpireExperience.tsx"
CANONICAL_CSS = ROOT / "web/public_prism/src/components/solspire/solspire-canonical.css"
DASHBOARD = ROOT / "web/public_prism/src/pages/ProjectDashboard.tsx"


def test_area_a_novanet_is_bound_to_shared_experience_shell():
    src = APP.read_text()
    assert 'surface="NovaNet"' in src
    assert "<NovaNetPage />" in src
    assert "ExperienceConsolidationFrame" in src


def test_area_b_solariun_workspace_is_bound_to_shared_experience_shell():
    src = APP.read_text()
    assert 'surface="Solariun"' in src
    assert "<SolariunConsole" in src
    assert "/solariun" in src
    assert "<SolSpireConsole" in src


def test_area_c_solspire_substrate_uses_existing_search_and_context_grammar():
    """Area C must reuse the existing search/context substrate, not a parallel one.

    The grammar is asserted where it now lives: the Solariun workspace component
    (federated search + honest coverage copy, reusing `searchKnowledge` from
    `lib/knowledgeApi`) and the project inspector that owns the activity/provenance
    distinction. The frame stays a wrapper, so it must *not* grow that grammar.
    """
    solspire = SOLSPIRE.read_text()
    dashboard = DASHBOARD.read_text()
    frame = FRAME.read_text()

    assert "searchKnowledge" in solspire  # existing Knowledge OS client, reused
    assert "No universal object index" in solspire
    assert "COVERAGE (honest)" in solspire
    # ACTIVITY is named as its own epistemic layer, explicitly not provenance proof.
    assert re.search(r"ACTIVITY \(project_events\)", dashboard)
    assert "provenance proof" in dashboard.lower()
    # The composition wrapper must not become a second search/context substrate.
    assert "searchKnowledge" not in frame
    assert "No universal object index" not in frame


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
    canonical_css = CANONICAL_CSS.read_text()
    solspire = SOLSPIRE.read_text()
    dashboard = DASHBOARD.read_text()

    # Transition-surface composition stays responsive at the frame breakpoints.
    assert "@media (max-width: 920px)" in css
    assert "@media (max-width: 600px)" in css
    # Responsive canonical chrome (sidebar/context bar/bottom rail collapse).
    assert "@media (max-width: 700px)" in canonical_css
    assert ".solspire-context-bar" in canonical_css
    assert ".solspire-mobile-bottom" in canonical_css
    # The inspector is the real epistemic activity/provenance panel.
    assert 'data-testid="solariun-epistemic-inspector"' in dashboard
    # The context bar is the canonical Solariun context grammar in the workspace.
    assert "solspire-context-bar" in solspire
    # The frame itself must not re-implement shell chrome/inspector placeholders.
    frame = FRAME.read_text()
    assert 'data-testid="experience-inspector"' not in frame
    assert 'data-testid="experience-context-bar"' not in frame


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
    # Markdown emphasis is presentation; assert the decision, not its formatting.
    merge_line = next(line for line in mapping.splitlines() if "Merge:" in line)
    deploy_line = next(line for line in mapping.splitlines() if "Deploy:" in line)
    assert "human_only" in merge_line
    assert "human_only" in deploy_line

