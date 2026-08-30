"""SG-04 Learning Activity Runtime contract tests."""
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
    assert "mutate learner capability state" in runtime


def test_runtime_persistence_uses_versioned_activity_scoped_records() -> None:
    runtime = read(RUNTIME)
    assert "STORAGE_VERSION = 1" in runtime
    assert "type DraftRecord" in runtime
    assert "type CompletionRecord" in runtime
    assert "activity_id: string" in runtime
    assert "activity_kind: LearningActivityKind" in runtime
    assert "updated_at: string" in runtime
    assert "completed_at: string" in runtime
    assert "JSON.stringify(record)" in runtime


def test_runtime_recovers_safely_from_invalid_persisted_state() -> None:
    runtime = read(RUNTIME)
    assert "try {" in runtime
    assert "catch { return '' }" in runtime
    assert "catch { return false }" in runtime
    assert "record.version !== STORAGE_VERSION" in runtime
    assert "record.activity_id !== activity.id" in runtime
    assert "record.activity_kind !== activity.kind" in runtime


def test_runtime_has_local_draft_and_completion_state() -> None:
    runtime = read(RUNTIME)
    assert "arkadia.spiral-grove.activity-runtime-draft.v1:" in runtime
    assert "arkadia.spiral-grove.activity-runtime-complete.v1:" in runtime
    assert "activity-runtime-save" in runtime
    assert "activity-runtime-complete" in runtime
    assert "activity-runtime-reopen" in runtime
    assert "writeDraft(draftKey, activity, draft)" in runtime
    assert "writeCompletion(completeKey, activity)" in runtime


def test_completion_requires_persisted_draft() -> None:
    runtime = read(RUNTIME)
    assert "if (!draft.trim()) return" in runtime
    assert "const draftSaved = writeDraft(draftKey, activity, draft)" in runtime
    assert "const completionSaved = draftSaved && writeCompletion(completeKey, activity)" in runtime


def test_runtime_handles_storage_unavailability_without_claiming_completion() -> None:
    runtime = read(RUNTIME)
    assert "storageAvailable" in runtime
    assert "Local storage unavailable" in runtime
    assert "disabled={!draft.trim() || !storageAvailable}" in runtime


def test_runtime_dispatches_all_eight_kinds_to_deterministic_renderers() -> None:
    runtime = read(RUNTIME)
    renderers = ("ResearchSurface", "WritingSurface", "BuildSurface", "ReflectionSurface", "PresentationSurface", "FieldSurface", "CreativeSurface", "CollaborativeSurface")
    for kind, renderer in zip(("research", "writing", "build", "reflection", "presentation", "field", "creative", "collaborative"), renderers):
        assert f"case '{kind}': return <{renderer}" in runtime
        assert f"function {renderer}" in runtime
        assert f'data-testid="activity-surface-{kind}"' in runtime


def test_runtime_is_mounted_by_the_capability_chamber() -> None:
    chamber = read(CHAMBER)
    assert "import ActivityRuntime from './ActivityRuntime'" in chamber
    assert "<ActivityRuntime activity={activity} />" in chamber
    assert "learningPath" in chamber
    assert "activities" in chamber


def test_all_eight_activity_kinds_have_explicit_blueprints() -> None:
    catalog = read(CATALOG)
    for kind in ("research", "writing", "build", "reflection", "presentation", "field", "creative", "collaborative"):
        assert f"{kind}: {{" in catalog
    assert "const ACTIVITY_BLUEPRINTS" in catalog
    assert "function activityKindFor" in catalog


def test_runtime_does_not_cross_the_evidence_boundary() -> None:
    runtime = read(RUNTIME)
    assert "createEvidence" not in runtime
    assert "submitEvidence" not in runtime
    assert "LearnerCapabilityState" not in runtime
    assert "perform assessment" in runtime
    assert "mutate learner capability state" in runtime


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
