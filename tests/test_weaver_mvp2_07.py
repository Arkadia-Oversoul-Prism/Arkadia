from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "web" / "public_prism" / "src" / "pages" / "ProjectDashboard.tsx"


def dashboard_text() -> str:
    return DASHBOARD.read_text(encoding="utf-8")


def test_weaver_panel_is_mounted_in_project_dashboard():
    text = dashboard_text()
    assert "function WeaverPanel" in text
    assert 'tab === \'weaver\'' in text
    assert '<WeaverPanel project={currentProject} />' in text


def test_operator_can_see_governed_lifecycle_states():
    text = dashboard_text()
    for marker in (
        "Lifecycle:",
        "PassSpec:",
        "Approval:",
        "Execution:",
        "verification:",
        "EXECUTION RESULT (backend-authoritative)",
    ):
        assert marker in text


def test_lock_reasons_are_visible_and_backend_authoritative():
    text = dashboard_text()
    assert "Execution locked" in text
    assert "lock_reasons" in text
    assert "Reason unavailable from backend" in text
    assert "Backend does not report K15_READY" in text


def test_proposal_approval_execution_verification_are_distinct():
    text = dashboard_text()
    assert "BIND PASSSPEC" in text
    assert "BIND PATCH APPROVAL" in text
    assert "EXECUTE (K15 PRECHECK)" in text
    assert "PROPOSED ≠ APPROVED ≠ EXECUTED ≠ VERIFIED" in text


def test_frontend_execute_requires_backend_k15_ready():
    text = dashboard_text()
    assert "disabled={busy || !k15Ready}" in text
    assert "if (!readiness?.k15_ready)" in text


def test_frontend_uses_existing_execution_routes_only():
    text = dashboard_text()
    for route in (
        "/execution/pass-spec",
        "/execution/approval",
        "/execution/readiness",
        "/execution",
    ):
        assert route in text
    assert "run_k3: false" in text


def test_frontend_does_not_call_k3_or_create_authorization():
    text = dashboard_text()
    assert "run_transaction" not in text
    assert "PassSpec" in text and "PatchApproval" in text
    assert "patch_spec_hash" not in text


def test_operator_surface_has_no_autonomous_execute_loop():
    text = dashboard_text()
    assert "onClick={executeGoverned}" in text
    assert "setInterval" not in text
    assert "setTimeout(() => executeGoverned" not in text
    assert "autoExecute" not in text


def test_browser_surface_remains_a_view_of_existing_runtime():
    text = dashboard_text()
    assert "backend-authoritative" in text
    assert "UI STATE ≠ AUTHORIZATION" in text
    assert "Mutation: K15 → K3 ONLY" in text
