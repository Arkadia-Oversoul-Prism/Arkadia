from pathlib import Path

from solspire import enterprise_router, workspace_manager


def test_enterprise_onboarding_is_generic_and_subject_bound(tmp_path: Path, monkeypatch):
    db = tmp_path / "enterprise.db"
    monkeypatch.setattr(enterprise_router, "_DB_PATH", str(db))
    monkeypatch.setattr(workspace_manager, "_DB_PATH", str(db))

    manager = enterprise_router.EnterpriseManager()
    enterprise = manager.create(subject_ref="subject-a", display_name="Acme Operating Company")
    assert enterprise.display_name == "Acme Operating Company"
    assert enterprise.onboarding_step == 1
    assert enterprise.lifecycle == "ONBOARDING"

    enterprise = manager.save_step(
        subject_ref="subject-a",
        enterprise_id=enterprise.enterprise_id,
        step=1,
        data={"display_name": "Acme Operating Company", "legal_name": "Acme Ltd"},
    )
    assert enterprise.legal_name == "Acme Ltd"

    enterprise = manager.save_step(
        subject_ref="subject-a",
        enterprise_id=enterprise.enterprise_id,
        step=5,
        data={"currency": "NGN", "budget_total": 1_000_000, "allocations": []},
    )
    assert enterprise.operating_context["budget_total"] == 1_000_000

    dashboard = manager.dashboard(subject_ref="subject-a", enterprise_id=enterprise.enterprise_id)
    assert dashboard["enterprise"]["name"] == "Acme Operating Company"
    assert dashboard["financial"]["budget_total"] == 1_000_000
    assert dashboard["financial"]["committed"] == "UNKNOWN"

    assert manager.list(subject_ref="subject-b") == []
