"""Contract tests for the read-only deployment version endpoint (ADR-016).

The endpoint must report an allowlisted projection only: never a secret,
credential, token, or arbitrary environment value. It must also fail closed to
an explicit ``unknown`` state when no revision metadata is present, rather than
inventing a revision.

Hardened after PR #392 review: absence, placeholder, and invalid values are
classified identically by the endpoint and by
``scripts/version_reconciliation.py`` (both via ``kernel.revision_identity``),
a non-revision value is never echoed back, and two disagreeing valid revision
sources are reported as an explicit conflict instead of being resolved silently
by precedence.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.version_routes import _REVISION_ENV_VARS, resolve_build_metadata, router
from kernel.revision_identity import PLACEHOLDER_TOKENS

_EXPECTED_KEYS = {
    "schema",
    "service",
    "read_only",
    "canonical_deployment",
    "source_revision",
    "revision_source",
    "revision_conflict",
    "revision_sources",
    "build_time",
    "metadata_present",
    "verification_note",
}

_BAKED = "f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8"
_PROVIDER = "ba3c7b574e704f6cc73393fa63e867ee2a9aa719"

# Every value the endpoint must refuse to treat as a revision. Covers the
# documented placeholder tokens plus case- and whitespace-padded variants.
_PLACEHOLDER_VARIANTS = sorted(
    PLACEHOLDER_TOKENS
    | {token.upper() for token in PLACEHOLDER_TOKENS if token}
    | {f"  {token}  " for token in PLACEHOLDER_TOKENS if token}
    | {"\tunknown\n", "UnKnOwN", "None ", " N/A"}
)


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
    monkeypatch.setenv("ARKADIA_SOURCE_REVISION", _BAKED)
    monkeypatch.setenv("ARKADIA_BUILD_TIME", "2026-10-10T00:00:00Z")

    response = _client().get("/api/version")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_revision"] == _BAKED
    assert payload["revision_source"] == "ARKADIA_SOURCE_REVISION"
    assert payload["build_time"] == "2026-10-10T00:00:00Z"
    assert payload["metadata_present"] is True
    assert payload["revision_conflict"] is False
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
    assert payload["revision_conflict"] is False


def test_version_prefers_explicit_revision_when_provider_absent(monkeypatch):
    """Precedence still holds when only one source supplies a usable revision."""
    _clear_revision_env(monkeypatch)
    monkeypatch.setenv("ARKADIA_SOURCE_REVISION", _BAKED)

    payload = resolve_build_metadata()

    assert payload["source_revision"] == _BAKED
    assert payload["revision_source"] == "ARKADIA_SOURCE_REVISION"
    assert payload["revision_conflict"] is False


def test_version_uses_provider_commit_when_explicit_revision_absent(monkeypatch):
    """The Dockerfile default (ARG/ENV empty) must fall through to the provider commit."""
    _clear_revision_env(monkeypatch)
    monkeypatch.setenv("ARKADIA_SOURCE_REVISION", "")
    monkeypatch.setenv("RENDER_GIT_COMMIT", _PROVIDER)

    payload = resolve_build_metadata()

    assert payload["source_revision"] == _PROVIDER
    assert payload["revision_source"] == "RENDER_GIT_COMMIT"
    assert payload["metadata_present"] is True
    assert payload["revision_conflict"] is False
    assert payload["revision_sources"]["ARKADIA_SOURCE_REVISION"]["status"] == "absent"


@pytest.mark.parametrize("value", _PLACEHOLDER_VARIANTS)
def test_version_never_reports_a_placeholder_as_metadata(monkeypatch, value):
    _clear_revision_env(monkeypatch)
    monkeypatch.setenv("ARKADIA_SOURCE_REVISION", value)

    payload = resolve_build_metadata()

    assert payload["metadata_present"] is False
    assert payload["source_revision"] == "unknown"
    assert payload["revision_source"] == "none"
    assert payload["revision_sources"]["ARKADIA_SOURCE_REVISION"]["status"] in {"absent", "placeholder"}
    assert payload["revision_sources"]["ARKADIA_SOURCE_REVISION"]["value"] is None


def test_version_reports_conflict_between_two_valid_disagreeing_sources(monkeypatch):
    """A baked revision that disagrees with the provider commit is a diagnosable conflict."""
    _clear_revision_env(monkeypatch)
    monkeypatch.setenv("ARKADIA_SOURCE_REVISION", _BAKED)
    monkeypatch.setenv("RENDER_GIT_COMMIT", _PROVIDER)

    payload = resolve_build_metadata()

    assert payload["revision_conflict"] is True
    # Precedence selects the baked value, but precedence is not proof it is correct.
    assert payload["source_revision"] == _BAKED
    assert payload["revision_source"] == "ARKADIA_SOURCE_REVISION"
    # Both sources' provenance is preserved so the conflict is diagnosable.
    assert payload["revision_sources"]["ARKADIA_SOURCE_REVISION"]["value"] == _BAKED
    assert payload["revision_sources"]["RENDER_GIT_COMMIT"]["value"] == _PROVIDER


def test_version_reports_no_conflict_when_sources_agree(monkeypatch):
    _clear_revision_env(monkeypatch)
    monkeypatch.setenv("ARKADIA_SOURCE_REVISION", _BAKED)
    monkeypatch.setenv("RENDER_GIT_COMMIT", _BAKED)

    payload = resolve_build_metadata()

    assert payload["revision_conflict"] is False
    assert payload["source_revision"] == _BAKED


def test_version_falls_back_to_provider_when_explicit_revision_is_not_a_sha(monkeypatch):
    """An invalid baked value is not echoed, is not a revision, and does not block the provider."""
    _clear_revision_env(monkeypatch)
    monkeypatch.setenv("ARKADIA_SOURCE_REVISION", "release-candidate-tag")
    monkeypatch.setenv("RENDER_GIT_COMMIT", _PROVIDER)

    payload = resolve_build_metadata()

    assert payload["source_revision"] == _PROVIDER
    assert payload["revision_source"] == "RENDER_GIT_COMMIT"
    assert payload["revision_sources"]["ARKADIA_SOURCE_REVISION"]["status"] == "invalid"
    assert payload["revision_sources"]["ARKADIA_SOURCE_REVISION"]["value"] is None


def test_version_reports_unknown_when_no_source_is_usable(monkeypatch):
    """Placeholder and invalid values together must not be smoothed into a revision."""
    _clear_revision_env(monkeypatch)
    monkeypatch.setenv("ARKADIA_SOURCE_REVISION", "N/A")
    monkeypatch.setenv("RENDER_GIT_COMMIT", "not-a-sha")

    payload = resolve_build_metadata()

    assert payload["source_revision"] == "unknown"
    assert payload["revision_source"] == "none"
    assert payload["metadata_present"] is False
    assert payload["revision_conflict"] is False


def test_version_does_not_echo_non_revision_values(monkeypatch):
    """A misconfigured revision variable is classified, never echoed verbatim."""
    _clear_revision_env(monkeypatch)
    sentinel = "sentinel-not-a-revision-identifier"
    monkeypatch.setenv("ARKADIA_SOURCE_REVISION", sentinel)

    response = _client().get("/api/version")

    assert response.status_code == 200
    assert sentinel not in response.text


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
