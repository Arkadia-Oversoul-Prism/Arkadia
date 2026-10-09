import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

import api.auth as auth
from api.auth import require_sovereign
from api.operator_security_routes import router


def _client(user: dict) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_sovereign] = lambda: user
    return TestClient(app)


def test_security_attestation_uses_firebase_verifier_and_redacts(caplog, monkeypatch):
    secret_token = "test-only-sensitive-token"
    caller_uid = "test-caller-uid"
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setattr(auth, "_firebase_app", object(), raising=False)
    monkeypatch.setattr(auth, "_dev_mode", False, raising=False)
    monkeypatch.setattr(
        auth,
        "verify_firebase_token",
        lambda token: {"uid": caller_uid} if token == secret_token else None,
    )

    client = _client({"uid": caller_uid, "access_level": 3})
    with caplog.at_level(logging.INFO, logger="arkadia.operator_security"):
        response = client.get(
            "/api/operator/security-verification",
            headers={"Authorization": f"Bearer {secret_token}"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"] == "PASS"
    assert {check["id"]: check["status"] for check in payload["checks"]} == {
        "production_environment": "PASS",
        "firebase_admin_initialized": "PASS",
        "firebase_identity_verified": "PASS",
        "sovereign_authorization": "PASS",
    }
    assert response.headers["cache-control"] == "no-store, max-age=0"
    assert payload["run_id"] in caplog.text
    assert secret_token not in caplog.text
    assert caller_uid not in caplog.text
    assert secret_token not in response.text
    assert caller_uid not in response.text


def test_security_attestation_fails_closed_when_firebase_verification_missing(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setattr(auth, "_firebase_app", object(), raising=False)
    monkeypatch.setattr(auth, "_dev_mode", False, raising=False)
    monkeypatch.setattr(auth, "verify_firebase_token", lambda token: None)

    client = _client({"uid": "profile-uid", "access_level": 3})
    response = client.get(
        "/api/operator/security-verification",
        headers={"Authorization": "Bearer not-verified"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"] == "FAIL"
    statuses = {check["id"]: check["status"] for check in payload["checks"]}
    assert statuses["firebase_identity_verified"] == "FAIL"
