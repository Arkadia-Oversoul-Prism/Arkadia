"""EDEN-SOLSPIRE-01 — Eden Food Systems enterprise instantiation."""
from pathlib import Path

from solspire import enterprise_router, workspace_manager


def test_eden_pilot_instantiates_on_existing_enterprise_substrate(tmp_path: Path, monkeypatch):
    db = tmp_path / "eden_enterprise.db"
    monkeypatch.setattr(enterprise_router, "_DB_PATH", str(db))
    monkeypatch.setattr(workspace_manager, "_DB_PATH", str(db))

    manager = enterprise_router.EnterpriseManager()
    enterprise = manager.instantiate_eden_food_systems(subject_ref="architect-subject")

    assert enterprise.display_name == "Eden Food Systems"
    assert enterprise.lifecycle == "READY_FOR_OPERATIONS"
    assert enterprise.onboarding_step == 7
    assert enterprise.pilot_workload["workload_id"] == "EDEN-PILOT-CYCLE-01"
    assert enterprise.pilot_workload["capital_ngn"] == 1_000_000
    assert len(enterprise.workstreams) == 7
    assert {ws["id"] for ws in enterprise.workstreams} == {
        "D01", "D02", "D03", "D04", "D05", "D06", "D07"
    }
    assert all(ws.get("status") == "UNASSIGNED" for ws in enterprise.workstreams)
    assert enterprise.operating_context["budget_total"] == 1_000_000
    assert enterprise.operating_context["currency"] == "NGN"
    assert len(enterprise.operating_context["allocations"]) == 8
    assert sum(a["amount"] for a in enterprise.operating_context["allocations"]) == 1_000_000
    assert enterprise.week_one["week"] == 1
    assert "monday" in enterprise.week_one["days"]
    assert any(m["role"] == "Chief of Operations" and m["status"] == "UNASSIGNED" for m in enterprise.members)

    dashboard = manager.dashboard(subject_ref="architect-subject", enterprise_id=enterprise.enterprise_id)
    assert dashboard["enterprise"]["name"] == "Eden Food Systems"
    assert dashboard["financial"]["budget_total"] == 1_000_000
    assert dashboard["financial"]["committed"] == "UNKNOWN"
    assert dashboard["financial"]["spent"] == "UNKNOWN"
    assert dashboard["financial"]["remaining"] == "UNKNOWN"
    assert len(dashboard["control"]["workstreams"]) == 7
    assert "truthfulness" in dashboard

    # Subject isolation: other subjects cannot see this enterprise
    assert manager.list(subject_ref="other-subject") == []


def test_eden_template_route_is_registered():
    paths = {getattr(route, "path", "") for route in enterprise_router.router.routes}
    assert any(p.endswith("/workspaces/templates/eden-food-systems") for p in paths)


def test_no_parallel_eden_authority_primitives_introduced():
    src = Path(enterprise_router.__file__).read_text()
    assert "run_k3" not in src
    assert "K15" not in src
    assert "CREATE TABLE IF NOT EXISTS eden_" not in src
