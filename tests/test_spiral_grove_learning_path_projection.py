"""Frontend projection contracts for SG-03 path consumption."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "web" / "public_prism" / "src"
PAGE = SRC / "pages" / "SpiralGrovePage.tsx"
CHAMBER = SRC / "components" / "spiral-grove" / "CapabilityChamber.tsx"
CATALOG = SRC / "data" / "spiralGroveCatalog.ts"


def test_page_projects_learning_path_for_selected_capability() -> None:
    page = PAGE.read_text(encoding="utf-8")
    assert "learningPathFor(selected.id, selectedState)" in page
    assert "learningPath={learningPath}" in page


def test_chamber_consumes_learning_path_projection() -> None:
    chamber = CHAMBER.read_text(encoding="utf-8")
    assert "GroveLearningPathProjection" in chamber
    assert "learningPath: GroveLearningPathProjection | null" in chamber
    assert "data-testid=\"learning-path-panel\"" in chamber
    assert "learningPath.capability_ids.map" in chamber


def test_path_projection_preserves_sg03_boundary() -> None:
    catalog = CATALOG.read_text(encoding="utf-8")
    assert "completion: 'evidence_required'" in catalog
    assert "No exercise or evidence generation occurs here." in CHAMBER.read_text(encoding="utf-8")
    assert "generateExercise" not in CHAMBER.read_text(encoding="utf-8")
    assert "createEvidence" not in CHAMBER.read_text(encoding="utf-8")


def test_path_projection_uses_existing_registry_capability_ids() -> None:
    catalog = CATALOG.read_text(encoding="utf-8")
    assert "const target = AIS_CAPABILITIES.find(item => item.id === capabilityId)" in catalog
    assert "const prerequisites = prerequisitesFor(capabilityId)" in catalog
    assert "capability_ids: capabilityIds" in catalog
