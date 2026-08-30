"""Frontend projection contracts for SG-03 path and activity runtime consumption."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "web" / "public_prism" / "src"
PAGE = SRC / "pages" / "SpiralGrovePage.tsx"
CHAMBER = SRC / "components" / "spiral-grove" / "CapabilityChamber.tsx"
CATALOG = SRC / "data" / "spiralGroveCatalog.ts"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_page_projects_learning_path_for_selected_capability() -> None:
    page = read(PAGE)
    assert "learningPathFor(selected.id, selectedState)" in page
    assert "learningPath={learningPath}" in page


def test_chamber_consumes_learning_path_projection() -> None:
    chamber = read(CHAMBER)
    assert "GroveLearningPathProjection" in chamber
    assert "learningPath: GroveLearningPathProjection | null" in chamber
    assert 'data-testid="learning-path-panel"' in chamber
    assert "pathIds.map" in chamber
    assert "learningPath?.capability_ids" in chamber


def test_activity_contract_supports_all_eight_work_kinds() -> None:
    catalog = read(CATALOG)
    for kind in ("research", "writing", "build", "reflection", "presentation", "field", "creative", "collaborative"):
        assert kind in catalog
    assert "LearningActivityKind" in catalog
    assert "GroveLearningActivityWorkSurface" in catalog
    assert "estimated_minutes: number" in catalog
    assert "deliverable: string" in catalog
    assert "tools: string[]" in catalog
    assert "work_surface: GroveLearningActivityWorkSurface" in catalog


def test_activity_runtime_maps_capabilities_to_explicit_work_modes() -> None:
    catalog = read(CATALOG)
    assert "function activityKindFor(capability: GroveCapability): LearningActivityKind" in catalog
    assert "const blueprint = ACTIVITY_BLUEPRINTS[kind]" in catalog
    assert "work_surface: { mode:" in catalog


def test_chamber_renders_activity_runtime_metadata() -> None:
    chamber = read(CHAMBER)
    assert "activity.work_surface" in chamber
    assert "activity.estimated_minutes" in chamber
    assert "activity.deliverable" in chamber
    assert "activity.tools.join" in chamber
    assert "surface.prompt_label" in chamber
    assert "surface.placeholder" in chamber
    assert "surface.artifact_type" in chamber


def test_path_projection_preserves_downstream_evidence_boundary() -> None:
    catalog = read(CATALOG)
    chamber = read(CHAMBER)
    assert "completion: 'evidence_required'" in catalog
    assert "Evidence is separate." in chamber
    assert "Assessment and learner capability-state updates require a future explicit downstream stage." in chamber
    assert "does not autonomously generate exercises" in catalog
    assert "generateExercise" not in chamber
    assert "createEvidence" not in chamber


def test_path_projection_uses_existing_registry_capability_ids() -> None:
    catalog = read(CATALOG)
    assert "const target = AIS_CAPABILITIES.find(item => item.id === capabilityId)" in catalog
    assert "const prerequisites = prerequisitesFor(capabilityId)" in catalog
    assert "capability_ids: capabilityIds" in catalog
