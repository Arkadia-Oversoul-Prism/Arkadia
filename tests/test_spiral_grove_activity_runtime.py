"""SG-04 Learning Activity Runtime contract tests.

These tests intentionally validate the architectural boundary through the
frontend projection. Runtime state is learner work only; evidence, assessment,
and learner capability-state mutation remain downstream.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "web" / "public_prism" / "src"
RUNTIME = SRC / "components" / "spiral-grove" / "ActivityRuntime.tsx"
CHAMBER = SRC / "components" / "spiral-grove" / "CapabilityChamber.tsx"
GROVE_PAGE = SRC / "pages" / "SpiralGrovePage.tsx"
NEXUS_PAGE = SRC / "pages" / "NexusPage.tsx"
CATALOG = SRC / "data" / "spiralGroveCatalog.ts"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_runtime_exists_and_is_explicitly_bounded() -> None:
    runtime = read(RUNTIME)
    assert "SG-04 bounded learner-work runtime" in runtime
    assert "localStorage" in runtime
    assert "activity-runtime" in runtime
    assert "does not submit evidence" in runtime
    assert "does not" in runtime and "mutate learner capability state" in runtime


def test_runtime_has_local_draft_and_completion_state() -> None:
    runtime = read(RUNTIME)
    assert "arkadia.spiral-grove.activity-runtime-draft.v1:" in runtime
    assert "arkadia.spiral-grove.activity-runtime-complete.v1:" in runtime
    assert "activity-runtime-save" in runtime
    assert "activity-runtime-complete" in runtime
    assert "activity-runtime-reopen" in runtime


def test_runtime_is_mounted_by_the_capability_chamber() -> None:
    chamber = read(CHAMBER)
    assert "import ActivityRuntime from './ActivityRuntime'" in chamber
    assert "<ActivityRuntime activity={activity} />" in chamber
    assert "learningPath" in chamber
    assert "activities" in chamber


def test_all_eight_activity_kinds_have_explicit_blueprints() -> None:
    catalog = read(CATALOG)
    for kind in (
        "research",
        "writing",
        "build",
        "reflection",
        "presentation",
        "field",
        "creative",
        "collaborative",
    ):
        assert f"{kind}: {{" in catalog
    assert "const ACTIVITY_BLUEPRINTS" in catalog
    assert "function activityKindFor" in catalog


def test_runtime_does_not_cross_the_evidence_boundary() -> None:
    runtime = read(RUNTIME)
    assert "createEvidence" not in runtime
    assert "submitEvidence" not in runtime
    assert "assess" not in runtime
    assert "LearnerCapabilityState" not in runtime
    assert "Evidence submission" in runtime
    assert "assessment" in runtime


def test_chamber_preserves_sg03_downstream_boundary() -> None:
    chamber = read(CHAMBER)
    assert "SG-03 activity contract" in chamber
    assert "Evidence submission, assessment, and capability-state updates remain separate downstream stages." in chamber
    assert "generateExercise" not in chamber
    assert "createEvidence" not in chamber


def test_spiral_grove_uses_the_nexus_canonical_header() -> None:
    page = read(GROVE_PAGE)
    nexus = read(NEXUS_PAGE)
    assert "candidate.style.display = 'none'" not in page
    assert "duplicate.style.display = ''" not in page
    assert "data-sg-duplicate-header" not in page
    assert "while (cursor?.parentElement" not in page
    assert "activeTab === 'university' ? 'The Spiral Grove'" in nexus
    assert "activeTab === 'university' && <SpiralGrovePage />" in nexus
    assert "<h1" not in page
    assert "The Spiral Grove" not in page
