"""WEAVER-SCI-CONTRACT-01 - freeze SCI / SolSpire / Weaver surface contract.

Boundary freeze only. No product redesign. No new authority.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCI_REG = ROOT / "web/public_prism/src/lib/sciCommandRegistry.ts"
SCI_PAGE = ROOT / "web/public_prism/src/pages/SpiralCommandInterface.tsx"
APP = ROOT / "web/public_prism/src/App.tsx"
NAV = ROOT / "web/public_prism/src/components/ArkadiaNavigation.tsx"
SOL = ROOT / "web/public_prism/src/pages/SolSpireConsole.tsx"
DASH = ROOT / "web/public_prism/src/pages/ProjectDashboard.tsx"
NEXUS = ROOT / "web/public_prism/src/pages/NexusPage.tsx"
MATRIX = ROOT / "web/public_prism/src/pages/UniversalEchofeildMatrix.tsx"


def _r(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_surface_owner_type_and_contract_exported():
    reg = _r(SCI_REG)
    assert "export type SurfaceOwner" in reg
    assert "SURFACE_CONTRACT" in reg
    assert "SCI_REGISTRY_IS_DESCRIPTIVE_NOT_AUTHORIZING" in reg
    assert "WEAVER-SCI-CONTRACT-01" in reg
    for owner in ("product", "sci", "solspire", "weaver", "knowledge", "governance", "system"):
        assert f"'{owner}'" in reg or f'"{owner}"' in reg


def test_sci_is_discover_orient_navigate_observe_only():
    reg = _r(SCI_REG)
    sci = _r(SCI_PAGE)
    assert "discover" in reg
    assert "orient" in reg
    assert "navigate" in reg
    assert "observe" in reg
    for banned in ("createPassSpec", "createPatchApproval", "callK3", "callK15"):
        assert banned in reg
    assert "execute_patch(" not in sci
    assert "run_transaction(" not in sci
    assert "createPassSpec" not in sci
    assert "createPatchApproval" not in sci


def test_sci_routes_to_existing_surfaces_not_duplicates():
    reg = _r(SCI_REG)
    assert "routeView: 'solspire'" in reg
    assert "routeView: 'knowledge-os'" in reg
    assert "WeaverPanel lives inside ProjectDashboard" in reg or "ProjectDashboard" in reg


def test_solspire_is_workspace_not_second_sci():
    reg = _r(SCI_REG)
    sol = _r(SOL)
    assert "secondSci" in reg or "second SCI" in reg.lower() or "mustNot" in reg
    assert "ProjectDashboard" in sol
    assert "SCI_DISCOVERY_WITHOUT_AUTHORITY" not in sol


def test_weaver_is_project_scoped_k15_k3():
    reg = _r(SCI_REG)
    dash = _r(DASH)
    assert "project-scoped" in reg.lower() or "Project -> Weaver" in reg or "SCI -> SolSpire" in reg
    assert "K15" in reg and "K3" in reg
    assert "function WeaverPanel" in dash


def test_product_nav_distinct_from_operator_sci():
    reg = _r(SCI_REG)
    nav = _r(NAV)
    app = _r(APP)
    assert "product" in reg
    assert "NovaNet" in reg or "novanet" in app.lower()
    assert "view === 'sci'" in app
    assert "view === 'novanet'" in app
    assert "view: 'sci'" in nav
    assert "SCI_DISCOVERY_WITHOUT_AUTHORITY" not in nav


def test_registry_not_authorizing():
    reg = _r(SCI_REG)
    assert "SCI_REGISTRY_IS_DESCRIPTIVE_NOT_AUTHORIZING = true" in reg
    assert "Does NOT grant authorization" in reg or "DESCRIPTIVE" in reg


def test_governance_chain_unchanged_in_contract():
    reg = _r(SCI_REG)
    for step in ("PassSpec", "PatchApproval", "K15", "K3"):
        assert step in reg


def test_novanet_matrix_preserved():
    app = _r(APP)
    assert "NexusPage" in app
    assert NEXUS.is_file() and MATRIX.is_file()
    assert "export default function UniversalEchofeildMatrix" in _r(MATRIX)


def test_nexus_novanet_alias_intact():
    app = _r(APP)
    assert "v === 'nexus' ? 'novanet'" in app or "=== 'nexus' ? 'novanet'" in app
