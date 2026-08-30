from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "web/public_prism/src/pages/FutureSkillsChallenge.tsx"
LIVING_GATE = ROOT / "web/public_prism/src/pages/LivingGate.tsx"


def test_w9_lab_persists_anonymous_progress_and_writes_canonical_handoff():
    source = LAB.read_text()
    assert "sessionStorage" in source
    assert "arkadia.ais.future-skills-challenge.v1" in source
    assert "arkadia.ais.diagnostic-handoff.v1" in source
    assert "source: 'future-skills-lab'" in source
    assert "challengeVersion: 2" in source


def test_w9_lab_completion_hands_off_without_manual_operator_intervention():
    source = LAB.read_text()
    assert "setComplete(true)" in source
    assert "onNavigate('gate')" in source
    assert "AUTO_HANDOFF_MS" in source
    assert 'data-testid="challenge-auto-handoff"' in source
    assert "Let's map what you can actually do." in source


def test_w9_lab_and_diagnostic_share_the_same_handoff_contract():
    lab = LAB.read_text()
    gate = LIVING_GATE.read_text()
    assert "HANDOFF_KEY = 'arkadia.ais.diagnostic-handoff.v1'" in lab
    assert "HANDOFF_KEY = 'arkadia.ais.diagnostic-handoff.v1'" in gate
    assert "source === 'future-skills-lab'" in gate
    assert "profileFromHandoff(initialHandoff)" in gate


def test_w9_does_not_introduce_a_second_authentication_store():
    source = LAB.read_text()
    assert "firebase" not in source.lower()
    assert "createUser" not in source
    assert "signIn" not in source
    assert "AuthProvider" not in source
