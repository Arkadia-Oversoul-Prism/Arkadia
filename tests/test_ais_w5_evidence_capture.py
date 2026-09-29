"""W5 — A.I.S Build → Proof evidence-capture contracts."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAMBER = ROOT / "web/public_prism/src/components/spiral-grove/CapabilityChamber.tsx"


def _r():
    return CHAMBER.read_text(encoding="utf-8")


def test_w5_has_explicit_evidence_submission_model():
    src = _r()
    assert "interface EvidenceSubmission" in src
    assert "activityId" in src
    assert "capabilityId" in src
    assert "pathId" in src
    assert "submittedAt" in src


def test_evidence_is_gated_by_activity_contract():
    src = _r()
    assert "activity.evidence_required" in src
    assert 'data-testid="evidence-capture"' in src
    assert 'data-testid="open-evidence-capture"' in src
    assert 'data-testid="submit-evidence"' in src


def test_evidence_can_reference_the_actual_artifact():
    src = _r()
    assert 'data-testid="evidence-summary"' in src
    assert 'data-testid="evidence-artifact-ref"' in src
    assert "artifactRef" in src


def test_evidence_submission_is_explicit_and_transient():
    src = _r()
    assert "sessionStorage.setItem(evidenceKey" in src
    assert "new Date().toISOString()" in src
    assert "no learner-state mutation" in src
    assert "firebase" not in src.lower()


def test_w5_preserves_sg03_local_work_boundary():
    src = _r()
    assert "activity-draft.v1" in src
    assert "local work/progress only" in src
    assert "learner capability state" in src
    assert "Knowledge OS remains the canonical, source-backed knowledge authority" in src
