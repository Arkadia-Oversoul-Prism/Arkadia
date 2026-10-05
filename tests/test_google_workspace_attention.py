from pathlib import Path

from api.google_workspace_routes import _state, _verify_state
import api.google_workspace_store as store


def test_oauth_state_round_trip(monkeypatch):
    monkeypatch.setenv("SOVEREIGN_KEY", "test-secret")
    state=_state("uid-1")
    assert _verify_state(state)=="uid-1"


def test_device_token_lifecycle(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("SOVEREIGN_KEY", "test-secret")
    monkeypatch.setattr(store, "_PATH", tmp_path / "google.json")
    store.save_device_token("uid-test","token-1")
    assert "token-1" in store.list_device_tokens("uid-test")
    store.revoke_device_token("uid-test","token-1")
    assert "token-1" not in store.list_device_tokens("uid-test")
