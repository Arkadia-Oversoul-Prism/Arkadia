from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "web/public_prism/src/App.tsx"
CHALLENGE = ROOT / "web/public_prism/src/pages/FutureSkillsChallenge.tsx"
GATE = ROOT / "web/public_prism/src/pages/LivingGate.tsx"
AUTH = ROOT / "web/public_prism/src/contexts/AuthContext.tsx"
LOGIN = ROOT / "web/public_prism/src/pages/LoginPage.tsx"
AIS_PROFILE = ROOT / "api/ais_profile.py"
NODES = ROOT / "api/nodes.py"


def test_w9_public_entry_reaches_the_self_guided_lab():
    app = APP.read_text(encoding="utf-8")
    challenge = CHALLENGE.read_text(encoding="utf-8")
    assert "FutureSkillsChallenge" in app
    assert "'challenge'" in app
    assert 'data-testid="start-future-skills-challenge"' in challenge
    assert "Start the 60-minute challenge" in challenge


def test_w9_lab_is_self_service_and_keeps_progress_anonymous():
    challenge = CHALLENGE.read_text(encoding="utf-8")
    assert "sessionStorage" in challenge
    assert "arkadia.ais.future-skills-challenge.v1" in challenge
    assert "LIMIT_MS = 60 * 60 * 1000" in challenge
    assert "firebase" not in challenge.lower()
    assert "Knowledge OS" not in challenge


def test_w9_completed_lab_hands_off_its_actual_signals_to_diagnostic():
    challenge = CHALLENGE.read_text(encoding="utf-8")
    gate = GATE.read_text(encoding="utf-8")
    assert 'data-testid="challenge-to-diagnostic"' in challenge
    assert "onNavigate('gate')" in challenge
    assert "arkadia.ais.diagnostic-handoff.v1" in challenge
    assert "createDiagnosticHandoff" in challenge
    assert "readDiagnosticHandoff" in gate
    assert "profileFromHandoff" in gate
    assert "Fill the missing signals" in gate


def test_w9_diagnostic_can_finish_without_auth_and_then_offer_the_canonical_boundary():
    gate = GATE.read_text(encoding="utf-8")
    assert 'data-testid="bind-ais-profile"' in gate
    assert "Create free Arkadia profile" in gate
    assert "showAuth" in gate
    assert "LoginPage" in gate
    assert "sessionStorage" in gate


def test_w9_authentication_reuses_the_existing_arkadia_identity():
    auth = AUTH.read_text(encoding="utf-8")
    login = LOGIN.read_text(encoding="utf-8")
    assert "onAuthStateChanged" in auth
    assert "createUserWithEmailAndPassword" in auth
    assert "sendSignInLinkToEmail" in auth
    assert "useAuth" in login
    assert "node_key" in auth


def test_w9_authenticated_portfolio_attaches_to_the_same_uid():
    gate = GATE.read_text(encoding="utf-8")
    ais = AIS_PROFILE.read_text(encoding="utf-8")
    assert "Authorization: `Bearer ${user.idToken}`" in gate
    assert "/api/me/ais-profile" in gate
    assert "kind: 'portfolio'" in gate
    assert "Depends(require_auth)" in ais
    assert 'load_user_profile_store(user["uid"])' in ais


def test_w9_authenticated_identity_continues_into_grove():
    app = APP.read_text(encoding="utf-8")
    gate = GATE.read_text(encoding="utf-8")
    assert "onEnterSpiralGrove={() => handleNavigate('grove')}" in app
    assert 'data-testid="open-spiral-grove"' in gate
    assert "onGrove={onEnterSpiralGrove}" in gate
    assert "SpiralGrovePage" in app
    assert "view === 'grove'" in app


def test_w9_profile_storage_is_a_projection_not_a_second_identity_store():
    ais = AIS_PROFILE.read_text(encoding="utf-8")
    nodes = NODES.read_text(encoding="utf-8")
    gate = GATE.read_text(encoding="utf-8")
    challenge = CHALLENGE.read_text(encoding="utf-8")
    assert '"ais_capability_portfolio"' in ais
    assert "_profiles_dir" in ais
    assert "router.include_router(_ais_profile_router)" in nodes
    assert "createUserWithEmailAndPassword" not in gate
    assert "signInWithEmailAndPassword" not in gate
    assert "firebase" not in ais.lower()
    assert "firebase" not in challenge.lower()


def test_w9_loop_has_a_single_human_action_at_each_boundary():
    challenge = CHALLENGE.read_text(encoding="utf-8")
    gate = GATE.read_text(encoding="utf-8")
    assert "Think, research, design, prove, and explain" in challenge
    assert "Let’s map what you can actually do" in challenge
    assert "Create my capability portfolio" in gate
    assert "Enter Spiral Grove" in gate
