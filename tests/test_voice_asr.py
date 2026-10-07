"""Arkadia Voice — Phase 3 ASR provider tests.

Proves that TestProvider, LocalProvider, NAtlasProvider and CloudProvider all
conform to the same canonical interface, that provider states are truthful,
that N-ATLAS requires official configuration (no fabricated endpoint, no
credentials needed in CI), and that selection never silently substitutes a
provider for an explicitly requested one.
"""
from __future__ import annotations

import pytest

from solspire.voice_asr import (
    ASRError,
    DEFAULT_PRIORITY,
    ENV_NATLAS_KEY,
    ENV_NATLAS_MODEL,
    ENV_NATLAS_URL,
    ENV_PROVIDER_SELECT,
    CloudProvider,
    LocalProvider,
    NAtlasProvider,
    TestProvider,
    get_provider,
    list_providers,
    provider_status_report,
    select_provider,
)
from solspire.voice_contracts import ProviderState

ALL_PROVIDERS = [TestProvider(), LocalProvider(), NAtlasProvider(), CloudProvider()]
AUDIO = b"\x1a\x45\xdfa-bytes"


def _clear_natlas(monkeypatch):
    monkeypatch.delenv(ENV_NATLAS_URL, raising=False)
    monkeypatch.delenv(ENV_NATLAS_KEY, raising=False)
    monkeypatch.delenv(ENV_NATLAS_MODEL, raising=False)


# ── interface conformance ────────────────────────────────────────────────────

@pytest.mark.parametrize("provider", ALL_PROVIDERS, ids=lambda p: p.name)
def test_every_provider_conforms_to_the_asr_interface(provider):
    assert isinstance(provider.name, str) and provider.name
    assert callable(getattr(provider, "status"))
    assert callable(getattr(provider, "transcribe"))

    info = provider.status()
    assert info.state in {s.value for s in ProviderState}
    assert info.reason, f"{provider.name} status must explain itself"
    assert info.model
    payload = info.to_dict()
    assert set(payload) == {"name", "state", "reason", "model", "config_source",
                            "recognized"}


@pytest.mark.parametrize("provider", ALL_PROVIDERS, ids=lambda p: p.name)
def test_provider_states_are_from_the_canonical_set(provider):
    assert provider.status().state in {s.value for s in ProviderState}


def test_registry_exposes_all_four_providers():
    names = {info.name for info in list_providers()}
    assert names == {"test", "local", "natlas", "cloud"}
    assert get_provider("test") is not None
    assert get_provider("nope") is None


# ── TestProvider ─────────────────────────────────────────────────────────────

def test_test_provider_is_available_and_deterministic():
    provider = TestProvider()
    assert provider.status().state == ProviderState.AVAILABLE.value
    first = provider.transcribe(AUDIO, {"transcript_hint": "Create a project",
                                        "audio_hash": "h"})
    second = provider.transcribe(AUDIO, {"transcript_hint": "Create a project",
                                         "audio_hash": "h"})
    assert first.text == second.text == "Create a project"
    assert first.provider == "test"
    assert first.audio_hash == "h"
    assert first.timestamp >= 0


def test_test_provider_does_not_claim_recognition():
    provider = TestProvider()
    assert provider.status().recognized is False
    transcript = provider.transcribe(AUDIO, {"transcript_hint": "hello"})
    assert transcript.provenance["recognized"] is False
    assert transcript.provenance["mode"] == "supplied_transcript"
    # No honest confidence exists for supplied text — it is never invented.
    assert transcript.confidence is None


def test_test_provider_without_hint_returns_empty_not_fabricated():
    transcript = TestProvider().transcribe(AUDIO, {})
    assert transcript.text == ""


def test_transcript_is_whitespace_normalized_by_provider():
    transcript = TestProvider().transcribe(AUDIO, {"transcript_hint": "  a   b \n c "})
    assert transcript.text == "a b c"


# ── N-ATLAS official boundary ────────────────────────────────────────────────

def test_natlas_without_official_access_is_unavailable(monkeypatch):
    _clear_natlas(monkeypatch)
    info = NAtlasProvider().status()
    assert info.state == ProviderState.UNAVAILABLE.value
    assert info.reason == "OFFICIAL_ACCESS_NOT_CONFIGURED"


def test_natlas_never_fabricates_an_endpoint(monkeypatch):
    _clear_natlas(monkeypatch)
    info = NAtlasProvider().status().to_dict()
    blob = str(info).lower()
    assert "http://" not in blob and "https://" not in blob
    # Status exposes configuration variable NAMES only — never values.
    assert info["config_source"] == f"env:{ENV_NATLAS_URL},{ENV_NATLAS_KEY}"


def test_natlas_transcribe_without_access_fails_explicitly(monkeypatch):
    _clear_natlas(monkeypatch)
    with pytest.raises(ASRError) as exc:
        NAtlasProvider().transcribe(AUDIO, {})
    assert exc.value.state == "ASR_UNAVAILABLE"
    assert "OFFICIAL_ACCESS_NOT_CONFIGURED" in exc.value.detail


def test_natlas_is_configured_only_via_environment(monkeypatch):
    monkeypatch.setenv(ENV_NATLAS_URL, "https://configured.example/transcribe")
    monkeypatch.setenv(ENV_NATLAS_KEY, "ci-placeholder-not-a-real-credential")
    info = NAtlasProvider().status()
    assert info.state == ProviderState.AVAILABLE.value
    # CI never needs real credentials: this test only asserts configuration
    # handling and makes no network call.


# ── LocalProvider ────────────────────────────────────────────────────────────

def test_local_provider_without_engine_is_unavailable(monkeypatch):
    monkeypatch.setattr("solspire.voice_asr._detect_local_engine", lambda: None)
    info = LocalProvider().status()
    assert info.state == ProviderState.UNAVAILABLE.value
    assert "LOCAL_ASR_ENGINE_NOT_INSTALLED" in info.reason


def test_local_provider_without_engine_cannot_transcribe(monkeypatch):
    monkeypatch.setattr("solspire.voice_asr._detect_local_engine", lambda: None)
    with pytest.raises(ASRError) as exc:
        LocalProvider().transcribe(AUDIO, {})
    assert exc.value.state == "ASR_UNAVAILABLE"


def test_local_provider_reports_engine_failure_as_failed_state(monkeypatch):
    # Detection says an engine exists, but importing it blows up → ASR_FAILED.
    monkeypatch.setattr("solspire.voice_asr._detect_local_engine", lambda: "whisper")
    with pytest.raises(ASRError) as exc:
        LocalProvider().transcribe(AUDIO, {})
    assert exc.value.state == "ASR_FAILED"


# ── CloudProvider ────────────────────────────────────────────────────────────

def test_cloud_provider_is_not_available_without_a_key(monkeypatch):
    for key in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    info = CloudProvider().status()
    assert info.state in {ProviderState.UNAVAILABLE.value,
                          ProviderState.MISCONFIGURED.value}
    if info.state == ProviderState.UNAVAILABLE.value:
        assert "API key" in info.reason


def test_cloud_provider_transcribe_without_availability_fails_explicitly(monkeypatch):
    for key in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(ASRError) as exc:
        CloudProvider().transcribe(AUDIO, {})
    assert exc.value.state == "ASR_UNAVAILABLE"


# ── selection ────────────────────────────────────────────────────────────────

def test_default_priority_order_is_documented():
    assert DEFAULT_PRIORITY == ("natlas", "cloud", "local", "test")


def test_default_selection_returns_an_available_provider(monkeypatch):
    _clear_natlas(monkeypatch)
    for key in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv(ENV_PROVIDER_SELECT, raising=False)
    provider, info = select_provider()
    assert info.state == ProviderState.AVAILABLE.value
    assert provider.name == info.name


def test_explicit_request_for_unavailable_provider_fails_loudly(monkeypatch):
    _clear_natlas(monkeypatch)
    with pytest.raises(ASRError) as exc:
        select_provider("natlas")
    assert exc.value.state == "ASR_UNAVAILABLE"
    assert "natlas" in exc.value.detail


def test_selection_never_silently_substitutes_a_provider(monkeypatch):
    """Requesting N-ATLAS while it is unavailable must NOT return the test
    provider — no fake N-ATLAS compliance by silent substitution."""
    _clear_natlas(monkeypatch)
    try:
        select_provider("natlas")
    except ASRError:
        return
    raise AssertionError("selection silently substituted an available provider")


def test_unknown_provider_is_rejected():
    with pytest.raises(ASRError) as exc:
        select_provider("definitely-not-a-provider")
    assert exc.value.state == "ASR_UNAVAILABLE"
    assert "unknown ASR provider" in exc.value.detail


def test_env_selection_is_honoured_and_fails_loudly_when_unavailable(monkeypatch):
    _clear_natlas(monkeypatch)
    monkeypatch.setenv(ENV_PROVIDER_SELECT, "natlas")
    with pytest.raises(ASRError):
        select_provider()
    monkeypatch.setenv(ENV_PROVIDER_SELECT, "test")
    provider, info = select_provider()
    assert provider.name == "test" and info.state == ProviderState.AVAILABLE.value


def test_selecting_local_when_unavailable_does_not_fall_through(monkeypatch):
    monkeypatch.setattr("solspire.voice_asr._detect_local_engine", lambda: None)
    with pytest.raises(ASRError) as exc:
        select_provider("local")
    assert "LOCAL_ASR_ENGINE_NOT_INSTALLED" in exc.value.detail


# ── status report (browser payload) ──────────────────────────────────────────

def test_status_report_contains_no_secret_values(monkeypatch):
    _clear_natlas(monkeypatch)
    monkeypatch.setenv(ENV_NATLAS_URL, "https://secret-endpoint.example/t")
    monkeypatch.setenv(ENV_NATLAS_KEY, "super-secret-value")
    report = provider_status_report()
    blob = str(report)
    assert "super-secret-value" not in blob
    assert "secret-endpoint" not in blob
    assert report["selection_env"] == ENV_PROVIDER_SELECT
    names = {p["name"] for p in report["providers"]}
    assert names == {"test", "local", "natlas", "cloud"}
