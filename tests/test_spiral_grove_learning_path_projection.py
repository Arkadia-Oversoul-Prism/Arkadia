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


def test_capability_selection_mounts_chamber() -> None:
    page = read(PAGE)
    assert "setChamberOpen(true)" in page
    assert "<CapabilityChamber" in page


def test_chamber_has_stable_visible_root() -> None:
    chamber = read(CHAMBER)
    assert 'data-testid="capability-chamber"' in chamber
    assert "<motion.section" in chamber
    assert "<h2" in chamber
    assert "capability.name" in chamber


def test_chamber_activity_projection_is_null_safe() -> None:
    chamber = read(CHAMBER)
    assert "activities?.activities?.[0] ?? null" in chamber
    assert "const surface = activity.work_surface ?? FALLBACK_SURFACE" in chamber
    assert "FALLBACK_SURFACE" in chamber
    assert "Array.isArray(learningPath?.capability_ids)" in chamber


def test_activity_runtime_supports_all_eight_work_modes() -> None:
    catalog = read(CATALOG)
    for kind in ("research", "writing", "build", "reflection", "presentation", "field", "creative", "collaborative"):
        assert kind in catalog
    assert "LearningActivityKind" in catalog
    assert "GroveLearningActivityWorkSurface" in catalog


def test_evidence_assessment_state_are_downstream() -> None:
    catalog = read(CATALOG)
    chamber = read(CHAMBER)
    assert "completion: 'evidence_required'" in catalog
    assert "Evidence submission, assessment, and capability-state updates remain separate downstream stages." in chamber
    assert "generateExercise" not in chamber
    assert "createEvidence" not in chamber
