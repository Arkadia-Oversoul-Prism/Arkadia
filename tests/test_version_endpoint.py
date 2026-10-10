"""Contract tests for the read-only deployment version endpoint (ADR-016).

The endpoint must report an allowlisted projection only: never a secret,
credential, token, or arbitrary environment value. It must also fail closed to
an explicit ``unknown`` state when no revision metadata is present, rather than
inventing a revision.
"""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.version_routes import _REVISION_ENV_VARS, resolve_build_metadata, router

_EXPECTED_KEYS = {
    "schema",
    "service",
    "read_only",
    "canonical_deployment",
    "source_revision",
    "revision_source",
    "build_time",
    "metadata_present",
    "verification_note",
}


def _clear_revision_env(monkeypatch) -> None:
    for name in _REVISION_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("ARKADIA_BUILD_TIME", raising=False)
    monkeypatch.delenv("ARKADIA_SERVICE", raising=False)


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_version_reports_revision_without_auth(monkeypatch):
    _clear_revision_env(monkeypatch)
    monkeypatch.setenv("ARKADIA_SOURCE_REVISION", "f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8")
    monkeypatch.setenv("ARKADIA_BUILD_TIME", "2026-10-10T00:00:00Z")

    response = _client().get("/api/version")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_revision"] == "f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8"
    assert payload["revision_source"] == "ARKADIA_SOURCE_REVISION"
    assert payload["build_time"] == "2026-10-10T00:00:00Z"
    assert payload["metadata_present"] is True
    assert payload["read_only"] is True
    assert payload["canonical_deployment"] == "one_reconciled_deployment"
    assert response.headers["cache-control"] == "no-store, max-age=0"
    assert set(payload) == _EXPECTED_KEYS


def test_version_fails_closed_to_unknown_when_metadata_absent(monkeypatch):
    _clear_revision_env(monkeypatch)

    payload = _client().get("/api/version").json()

    assert payload["source_revision"] == "unknown"
    assert payload["revision_source"] == "none"
    assert payload["build_time"] == "unknown"
    assert payload["metadata_present"] is False


def test_version_prefers_explicit_revision_over_provider_commit(monkeypatch):
    _clear_revision_env(monkeypatch)
    monkeypatch.setenv("ARKADIA_SOURCE_REVISION", "explicit-sha")
    monkeypatch.setenv("RENDER_GIT_COMMIT", "provider-sha")

    payload = resolve_build_metadata()

    assert payload["source_revision"] == "explicit-sha"
    assert payload["revision_source"] == "ARKADIA_SOURCE_REVISION"


def test_version_uses_provider_commit_when_explicit_revision_absent(monkeypatch):
    _clear_revision_env(monkeypatch)
    monkeypatch.setenv("RENDER_GIT_COMMIT", "provider-sha")

    payload = resolve_build_metadata()

    assert payload["source_revision"] == "provider-sha"
    assert payload["revision_source"] == "RENDER_GIT_COMMIT"


def test_version_does_not_leak_secrets_or_arbitrary_env(monkeypatch):
    _clear_revision_env(monkeypatch)
    secrets = {
        "GOOGLE_API_KEY": "sentinel-google-key",
        "SOVEREIGN_KEY": "sentinel-sovereign-key",
        "FIREBASE_SERVICE_ACCOUNT_JSON": "sentinel-service-account",
        "GITHUB_PERSONAL_ACCESS_TOKEN": "sentinel-gh-token",
        "DATABASE_URL": "sentinel-database-url",
    }
    for name, value in secrets.items():
        monkeypatch.setenv(name, value)

    response = _client().get("/api/version")

    assert response.status_code == 200
    assert set(response.json()) == _EXPECTED_KEYS
    for value in secrets.values():
        assert value not in response.text
