from pathlib import Path

from solspire import enterprise_router
from solspire import workspace_manager
from solspire import pulse_manager, synthesis_manager


def test_eden_bootstrap_is_idempotent_and_seeds_week1(monkeypatch, tmp_path: Path):
    db = tmp_path / "eden.db"
    monkeypatch.setattr(enterprise_router, "_DB_PATH", str(db))
    monkeypatch.setattr(workspace_manager, "_DB_PATH", str(db))
    monkeypatch.setattr(pulse_manager, "_DB_PATH", str(db))
    monkeypatch.setattr(synthesis_manager, "_DB_PATH", str(db))
    manager = enterprise_router.EdenEnterpriseManager()

    first = manager.bootstrap(subject_ref="test-subject")
    second = manager.bootstrap(subject_ref="test-subject")

    assert first["workspace"]["enterprise_id"] == second["workspace"]["enterprise_id"]
    dashboard = manager.dashboard(subject_ref="test-subject")

    assert dashboard["product"]["name"] == "Eden Food Systems"
    assert dashboard["product"]["tier"] == "ENTERPRISE"
    assert dashboard["product"]["authority_effect"].startswith("DESCRIPTIVE_ONLY")
    assert dashboard["money"][0]["value"] == 1_000_000
    assert dashboard["commercial"][0]["epistemic_status"] == "UNKNOWN"
    assert len(dashboard["operations"]["workstreams"]) == 8
    assert len(dashboard["operations"]["week1_tasks"]) == 17
    assert dashboard["truthfulness"]["unknown_policy"] == "UNKNOWN is preserved when no governed source exists."
