"""WEAVER-SCI-BOUNDARY-01 — SCI / SolSpire surface ownership topology.

SCI owns global operator discovery/navigation only.
SolSpire owns project/workspace context.
Weaver mutation remains K15→K3 only.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCI_PAGE = ROOT / "web/public_prism/src/pages/SpiralCommandInterface.tsx"
SCI_REG = ROOT / "web/public_prism/src/lib/sciCommandRegistry.ts"
APP = ROOT / "web/public_prism/src/App.tsx"
NAV = ROOT / "web/public_prism/src/components/ArkadiaNavigation.tsx"
SOL = ROOT / "web/public_prism/src/pages/SolSpireConsole.tsx"
DASH = ROOT / "web/public_prism/src/pages/ProjectDashboard.tsx"
NEXUS = ROOT / "web/public_prism/src/pages/NexusPage.tsx"
MATRIX = ROOT / "web/public_prism/src/pages/UniversalEchofeildMatrix.tsx"


def _r(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_sci_is_canonical_operator_shell():
    sci = _r(SCI_PAGE)
    reg = _r(SCI_REG)
    app = _r(APP)
    assert "SCI_DISCOVERY_WITHOUT_AUTHORITY" in sci
    assert "WEAVER-SCI-BOUNDARY-01" in sci
    assert "view === 'sci'" in app
    assert "SpiralCommandInterface" in app
    assert "routeView: 'solspire'" in reg
    assert "routeView: 'knowledge-os'" in reg


def test_solspire_owns_project_workspace_not_global_command():
    sol = _r(SOL)
    assert "WEAVER-SCI-BOUNDARY-01" in sol
    assert "PROJECT/WORKSPACE" in sol or "project/workspace" in sol.lower()
    assert "ProjectDashboard" in sol
    assert "SCI_DISCOVERY_WITHOUT_AUTHORITY" not in sol


def test_weaver_lives_under_project_dashboard():
    dash = _r(DASH)
    assert "function WeaverPanel" in dash
    assert "tab === 'weaver'" in dash or "WeaverPanel" in dash


def test_sci_does_not_duplicate_project_execution():
    sci = _r(SCI_PAGE)
    reg = _r(SCI_REG)
    assert "execute_patch(" not in sci
    assert "run_transaction(" not in sci
    assert "createPassSpec" not in sci
    assert "createPatchApproval" not in sci
    assert "SCI REGISTRY != AUTHORIZATION" in reg or "Does NOT grant authorization" in reg


def test_no_second_k3_path_in_sci_or_registry():
    sci = _r(SCI_PAGE)
    reg = _r(SCI_REG)
    assert "run_transaction(" not in sci
    assert "run_transaction(" not in reg


def test_product_nav_is_not_operator_authority():
    nav = _r(NAV)
    assert "WEAVER-SCI-BOUNDARY-01" in nav
    assert "operator" in nav.lower() or "SCI" in nav
    assert "view: 'sci'" in nav


def test_novanet_and_matrix_preserved():
    app = _r(APP)
    assert "view === 'novanet'" in app
    assert "NexusPage" in app
    assert NEXUS.is_file()
    assert MATRIX.is_file()
    assert "export default function UniversalEchofeildMatrix" in _r(MATRIX)


def test_nexus_novanet_alias_intact():
    app = _r(APP)
    assert "v === 'nexus' ? 'novanet'" in app or "=== 'nexus' ? 'novanet'" in app


def test_ownership_map_present_in_registry():
    reg = _r(SCI_REG)
    for domain in ("SCI", "SolSpire", "Knowledge", "Weaver", "Governance", "Execution", "Verification", "System"):
        assert domain in reg
