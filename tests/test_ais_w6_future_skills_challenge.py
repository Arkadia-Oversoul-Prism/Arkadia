from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHALLENGE = ROOT / "web/public_prism/src/pages/FutureSkillsChallenge.tsx"
GATE = ROOT / "web/public_prism/src/pages/LivingGate.tsx"
APP = ROOT / "web/public_prism/src/App.tsx"


def test_w6_is_self_guided_and_timed():
    src = CHALLENGE.read_text(encoding="utf-8")
    assert "60-minute challenge" in src
    assert "LIMIT_MS = 60 * 60 * 1000" in src
    assert 'data-testid="challenge-timer"' in src
    assert "sessionStorage" in src


def test_w6_has_the_five_capability_signals():
    src = CHALLENGE.read_text(encoding="utf-8")
    for marker in ("THINK", "RESEARCH", "BUILD", "PROVE", "LAUNCH"):
        assert marker in src


def test_w6_completion_hands_off_to_ais_diagnostic():
    src = CHALLENGE.read_text(encoding="utf-8")
    assert 'data-testid="challenge-to-diagnostic"' in src
    assert "onNavigate('gate')" in src
    assert "ChallengeState" in src
    assert "completedAt" in src
    assert "arkadia.ais.diagnostic-handoff.v1" in src
    assert "createDiagnosticHandoff" in src


def test_w6_handoff_maps_practical_signals_without_persisting_identity():
    src = CHALLENGE.read_text(encoding="utf-8")
    assert "answers.solution" in src
    assert "answers.proof" in src
    assert "answers.problem" in src
    assert "answers.value" in src
    assert "researchSignal" in src
    assert "firebase" not in src.lower()
    assert "Knowledge OS" not in src


def test_living_gate_hydrates_the_existing_profile_from_the_handoff():
    src = GATE.read_text(encoding="utf-8")
    assert "arkadia.ais.diagnostic-handoff.v1" in src
    assert "readDiagnosticHandoff" in src
    assert "profileFromHandoff" in src
    assert "Research approach:" in src
    assert "Fill the missing signals" in src
    assert "sessionStorage.removeItem(HANDOFF_KEY)" in src


def test_w6_is_not_a_second_profile_or_persistent_identity_system():
    src = CHALLENGE.read_text(encoding="utf-8")
    assert "arkadia.ais.future-skills-challenge.v1" in src
    assert "firebase" not in src.lower()
    assert "Knowledge OS" not in src


def test_w6_is_reachable_from_the_existing_home_shell():
    src = APP.read_text(encoding="utf-8")
    assert "FutureSkillsChallenge" in src
    assert "'challenge'" in src
    assert 'data-testid="start-future-skills-challenge"' in CHALLENGE.read_text(encoding="utf-8")
