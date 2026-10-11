"""Runtime regression test for the OpenAPI-representable forge credential."""
from fastapi.testclient import TestClient

from api import main


def test_forge_uses_the_declared_sovereign_header_not_a_body_secret(monkeypatch):
    monkeypatch.setattr(main, "SOVEREIGN_KEY", "test-sovereign-secret")
    monkeypatch.setattr(main, "GOOGLE_API_KEY", "test-provider-key")

    from api import key_pool
    monkeypatch.setattr(key_pool, "acquire_key", lambda: "test-provider-key")

    async def no_image(_prompt):
        return None

    monkeypatch.setattr(main, "_generate_image", no_image)
    client = TestClient(main.app)

    legacy_body_credential = client.post(
        "/api/forge",
        json={"sovereign_key": "test-sovereign-secret", "count": 0},
    )
    assert legacy_body_credential.status_code == 403

    header_credential = client.post(
        "/api/forge",
        headers={"X-Sovereign-Key": "test-sovereign-secret"},
        json={"count": 0},
    )
    assert header_credential.status_code == 200
