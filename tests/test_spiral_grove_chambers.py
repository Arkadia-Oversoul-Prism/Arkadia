from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "web" / "public_prism" / "src"
PAGE = SRC / "pages" / "SpiralGrovePage.tsx"
CHAMBER = SRC / "components" / "spiral-grove" / "CapabilityChamber.tsx"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_capability_map_enters_a_capability_chamber():
    page = read(PAGE)
    chamber = read(CHAMBER)
    assert "CapabilityChamber" in page
    assert "openCapability" in page
    assert "onEnter={() => openCapability(capability.id)}" in page
    assert 'data-testid="capability-chamber"' in chamber


def test_chamber_exposes_required_operating_context():
    chamber = read(CHAMBER)
    for label in (
        "What this capability means",
        "Current learner state",
        "Prerequisites",
        "Knowledge OS sources",
        "Your next move",
    ):
        assert label in chamber


def test_chamber_does_not_invoke_autonomous_generation_or_adjudication():
    chamber = read(CHAMBER)
    assert "SG-03 activity contract" in chamber
    assert "Evidence is separate." in chamber
    assert "generateExercise" not in chamber
    assert "createEvidence" not in chamber
    assert "mutate learner capability state" in chamber


def test_chamber_uses_typed_capability_and_learner_state():
    chamber = read(CHAMBER)
    assert "GroveCapability" in chamber
    assert "LearnerCapabilityState" in chamber
    assert "prerequisites: GroveCapability[]" in chamber


def test_learning_activity_exposes_a_real_work_surface():
    chamber = read(CHAMBER)
    assert "GroveLearningActivity" in chamber
    assert 'data-testid="learning-activity"' in chamber
    assert 'data-testid="activity-action"' in chamber
    assert 'data-testid="learning-activity-work-surface"' in chamber
    assert 'data-testid="activity-draft"' in chamber
    assert 'data-testid="save-activity-draft"' in chamber


def test_learning_activity_persistence_is_local_progress_only():
    chamber = read(CHAMBER)
    assert "arkadia.spiral-grove.activity-draft.v1:" in chamber
    assert "localStorage" in chamber
    assert "Saved locally" in chamber
    assert "does not change your learner capability state" in chamber


def test_page_keeps_knowledge_os_boundary_explicit():
    page = read(PAGE)
    assert "Knowledge OS remains the canonical source-backed knowledge authority" in page
