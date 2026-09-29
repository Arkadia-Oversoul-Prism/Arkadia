"""MVP2-08 — Spiral Command Interface foundation invariants.

SCI_DISCOVERY_WITHOUT_AUTHORITY:
  SCI may discover and route. It must not become an authorization or mutation authority.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCI_PAGE = ROOT / "web" / "public_prism" / "src" / "pages" / "SpiralCommandInterface.tsx"
SCI_REG = ROOT / "web" / "public_prism" / "src" / "lib" / "sciCommandRegistry.ts"
APP = ROOT / "web" / "public_prism" / "src" / "App.tsx"
NAV = ROOT / "web" / "public_prism" / "src" / "components" / "ArkadiaNavigation.tsx"
DASHBOARD = ROOT / "web" / "public_prism" / "src" / "pages" / "ProjectDashboard.tsx"
MATRIX = ROOT / "web" / "public_prism" / "src" / "pages" / "UniversalEchofeildMatrix.tsx"
NOVANET = ROOT / "web" / "public_prism" / "src" / "pages" / "NovaNetPage.tsx"
NEXUS = ROOT / "web" / "public_prism" / "src" / "pages" / "NexusPage.tsx"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_sci_files_exist():
    assert SCI_PAGE.is_file()
    assert SCI_REG.is_file()


def test_sci_renders_canonical_command_categories():
    reg = _read(SCI_REG)
    page = _read(SCI_PAGE)
    for cat in (
        "Overview",
        "Projects",
        "Knowledge",
        "Weaver",
        "Governance",
        "Execution",
        "Verification",
        "System",
    ):
        assert cat in reg or cat in page
    assert "SCI_CATEGORIES" in reg
    assert "sci-command-rail" in page
    assert "spiral-command-interface" in page


def test_existing_weaver_surface_reachable_via_registry():
    reg = _read(SCI_REG)
    assert "sci.weaver" in reg
    assert "routeView: 'solspire'" in reg
    assert "WeaverPanel" in _read(DASHBOARD)


def test_existing_solspire_surface_reachable():
    reg = _read(SCI_REG)
    app = _read(APP)
    assert "routeView: 'solspire'" in reg
    assert "view === 'solspire'" in app
    assert "SolSpireConsole" in app


def test_existing_knowledge_surface_reachable():
    reg = _read(SCI_REG)
    app = _read(APP)
    assert "routeView: 'knowledge-os'" in reg
    assert "view === 'knowledge-os'" in app


def test_capability_metadata_is_descriptive_only():
    reg = _read(SCI_REG)
    page = _read(SCI_PAGE)
    assert "Descriptive UI metadata only" in reg or "descriptive" in reg.lower()
    assert "Does NOT grant authorization" in reg or "not grant" in reg.lower()
    assert "SCI_DISCOVERY_WITHOUT_AUTHORITY" in page
    assert "SCI navigation" in page


def test_sci_does_not_directly_invoke_k3():
    page = _read(SCI_PAGE)
    reg = _read(SCI_REG)
    combined = page + reg
    assert "execute_patch(" not in page
    assert "run_transaction(" not in page
    assert "No SCI" in page or "does not call K3" in combined.lower()


def test_sci_does_not_create_passspec_authority():
    page = _read(SCI_PAGE)
    reg = _read(SCI_REG)
    assert "No PassSpec or PatchApproval authority is created in SCI" in reg or (
        "PassSpec" in reg and "authority is created" in reg
    )
    assert "createPassSpec" not in page
    assert "new PassSpec" not in page


def test_sci_does_not_create_patchapproval_authority():
    page = _read(SCI_PAGE)
    assert "createPatchApproval" not in page
    assert "new PatchApproval" not in page


def test_execution_remains_backend_authorized():
    reg = _read(SCI_REG)
    assert "Backend governance" in reg or "backend-authorized" in reg.lower() or "backend remains" in reg.lower()
    assert "governed" in reg.lower() or "K15" in reg


def test_locked_and_not_available_vocabulary_present():
    reg = _read(SCI_REG)
    page = _read(SCI_PAGE)
    for marker in ("LOCKED", "NOT_AVAILABLE", "NOT_IMPLEMENTED", "DISABLED", "PROPOSAL_ONLY"):
        assert marker in reg or marker in page


def test_no_autonomous_mutation_path():
    reg = _read(SCI_REG)
    page = _read(SCI_PAGE)
    combined = page + reg
    assert "DISABLED" in reg
    assert "autonomous" in combined.lower()
    assert "git push" not in page
    assert "git commit" not in page


def test_nexus_novanet_canonical_routing_intact():
    app = _read(APP)
    assert "v === 'nexus' ? 'novanet'" in app or "=== 'nexus' ? 'novanet'" in app
    assert "view === 'novanet'" in app
    assert "view === 'nexus'" not in app
    assert "NexusPage" in app
    assert NOVANET.is_file()
    assert NEXUS.is_file()


def test_universal_echofeild_matrix_intact():
    assert MATRIX.is_file()
    text = _read(MATRIX)
    assert "Universal Echofeild" in text or "Echofeild" in text
    assert "export default function UniversalEchofeildMatrix" in text


def test_sci_wired_into_app_and_nav():
    app = _read(APP)
    nav = _read(NAV)
    assert "SpiralCommandInterface" in app
    assert "view === 'sci'" in app
    assert "| 'sci'" in app
    assert "view: 'sci'" in nav


def test_weaver_lifecycle_vocabulary_not_invented():
    reg = _read(SCI_REG)
    for stage in (
        "PROJECT",
        "KNOWLEDGE",
        "OBJECTIVE",
        "SCOPE",
        "EVIDENCE",
        "ANALYSIS",
        "PLAN",
        "CHANGESET",
        "PATCH",
        "REVIEW",
        "PASSSPEC",
        "PATCH APPROVAL",
        "K15",
        "K3",
        "VERIFICATION",
    ):
        assert stage in reg
