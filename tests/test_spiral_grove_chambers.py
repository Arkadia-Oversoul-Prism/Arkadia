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
    assert "enterChamber" in page
    assert "onEnter={() => enterChamber(capability.id)}" in page
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


def test_chamber_does_not_invoke_learning_path_engine():
    chamber = read(CHAMBER)
    assert "Learning Path Engine: downstream SG-03" in chamber
    assert "generateExercise" not in chamber
    assert "createEvidence" not in chamber


def test_chamber_uses_typed_capability_and_learner_state():
    chamber = read(CHAMBER)
    assert "GroveCapability" in chamber
    assert "LearnerCapabilityState" in chamber
    assert "prerequisites: GroveCapability[]" in chamber


def test_page_keeps_knowledge_os_boundary_explicit():
    page = read(PAGE)
    assert "Knowledge OS remains the canonical source-backed knowledge authority" in page
