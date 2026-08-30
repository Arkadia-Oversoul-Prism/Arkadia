from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "web/public_prism/src/contexts/AuthContext.tsx"
FIREBASE = ROOT / "web/public_prism/src/lib/firebase.ts"
LOGIN = ROOT / "web/public_prism/src/pages/LoginPage.tsx"
GATE = ROOT / "web/public_prism/src/pages/LivingGate.tsx"
CHALLENGE = ROOT / "web/public_prism/src/pages/FutureSkillsChallenge.tsx"
NODES = ROOT / "api/nodes.py"
AIS_PROFILE = ROOT / "api/ais_profile.py"


def test_w8_canonical_auth_is_firebase_and_node_profile_is_downstream():
    auth = AUTH.read_text(encoding="utf-8")
    firebase = FIREBASE.read_text(encoding="utf-8")
    login = LOGIN.read_text(encoding="utf-8")
    assert "onAuthStateChanged" in auth
    assert "createUserWithEmailAndPassword" in auth
    assert "sendSignInLinkToEmail" in auth
    assert "getAuth" in firebase
    assert "useAuth" in login
    assert "node_key" in auth


def test_w8_ais_projection_reuses_authenticated_uid():
    src = AIS_PROFILE.read_text(encoding="utf-8")
    nodes = NODES.read_text(encoding="utf-8")
    assert "Depends(require_auth)" in src
    assert 'load_user_profile_store(user["uid"])' in src
    assert "_profiles_dir" in src
    assert "router.include_router(_ais_profile_router)" in nodes
    assert "/api/me/ais-profile" in src


def test_w8_anonymous_lab_state_can_cross_the_auth_boundary():
    challenge = CHALLENGE.read_text(encoding="utf-8")
    gate = GATE.read_text(encoding="utf-8")
    assert "arkadia.ais.diagnostic-handoff.v1" in challenge
    assert "sessionStorage" in challenge
    assert "LoginPage" in gate
    assert "Create free Arkadia profile" in gate
    assert "Authorization: `Bearer ${user.idToken}`" in gate


def test_w8_diagnostic_portfolio_is_attached_to_the_same_identity():
    gate = GATE.read_text(encoding="utf-8")
    assert "kind: 'portfolio'" in gate
    assert "/api/me/ais-profile" in gate
    assert "user?.idToken" in gate
    assert "Your A.I.S profile is attached to your canonical Arkadia identity." in gate


def test_w8_no_second_authentication_or_identity_store_is_created():
    gate = GATE.read_text(encoding="utf-8")
    ais = AIS_PROFILE.read_text(encoding="utf-8")
    assert "firebase" not in ais.lower()
    assert "createUserWithEmailAndPassword" not in gate
    assert "signInWithEmailAndPassword" not in gate
    assert "FIREBASE_SERVICE_ACCOUNT_JSON" not in gate
    assert '"ais_capability_portfolio"' in ais
