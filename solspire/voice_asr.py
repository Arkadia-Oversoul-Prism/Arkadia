"""Arkadia Voice — ASR provider abstraction (Phase 3).

One canonical interface, replaceable providers:

    ASRProvider.transcribe(audio, options) -> Transcript

    TestProvider    deterministic, fully local — tests / development / demos / CI
    LocalProvider   an actually-installed local engine, if the runtime has one
    NAtlasProvider  the official N-ATLAS integration boundary (env-configured)
    CloudProvider   the repository's already-approved Gemini provider family

Provider states: AVAILABLE / UNAVAILABLE / MISCONFIGURED / FAILED.

Rules this module obeys:
  * No endpoint, credential, or model is fabricated. N-ATLAS reads only
    ``NATLAS_TRANSCRIBE_URL`` / ``NATLAS_API_KEY`` / ``NATLAS_MODEL`` from the
    environment; with them absent the provider reports
    ``UNAVAILABLE / OFFICIAL_ACCESS_NOT_CONFIGURED`` — never a made-up URL.
  * No secret is ever returned to a caller. Statuses expose configuration
    *names*, never values.
  * All provider I/O is server-side. The browser only ever sends audio bytes
    to the Arkadia backend.
  * Only providers whose status is AVAILABLE may be selected.
"""
from __future__ import annotations

import importlib.util
import json
import logging
import os
import tempfile
from dataclasses import asdict, dataclass
from typing import Any, Protocol, runtime_checkable

from solspire.voice_contracts import ProviderState, Transcript, new_id, utc_now

logger = logging.getLogger("solspire.voice_asr")

#: Environment variable names (documented in docs/voice/ASR_PROVIDERS.md).
ENV_NATLAS_URL = "NATLAS_TRANSCRIBE_URL"
ENV_NATLAS_KEY = "NATLAS_API_KEY"
ENV_NATLAS_MODEL = "NATLAS_MODEL"
ENV_GEMINI_KEYS = ("GEMINI_API_KEY", "GOOGLE_API_KEY")
ENV_PROVIDER_SELECT = "ARKADIA_VOICE_ASR_PROVIDER"

#: Selection priority when no provider is explicitly requested/configured.
#: Explicitly configured N-ATLAS wins (somebody wired it on purpose), then the
#: repository-approved cloud provider, then a local engine, then the always-
#: available deterministic TestProvider.
DEFAULT_PRIORITY: tuple[str, ...] = ("natlas", "cloud", "local", "test")


class ASRError(Exception):
    """Provider failure carrying a canonical Voice error state."""

    def __init__(self, state: str, detail: str) -> None:
        super().__init__(detail)
        self.state = state
        self.detail = detail


@dataclass
class ProviderInfo:
    name: str
    state: str
    reason: str
    model: str
    config_source: str
    recognized: bool  # False ⇒ the provider does not claim speech recognition

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@runtime_checkable
class ASRProvider(Protocol):
    """Canonical provider interface. Every provider conforms to this shape."""

    name: str

    def status(self) -> ProviderInfo: ...

    def transcribe(self, audio: bytes, options: dict[str, Any]) -> Transcript: ...


def _language(options: dict[str, Any], default: str = "en") -> str:
    lang = str(options.get("language") or default).strip()
    return lang or default


# ── TestProvider ─────────────────────────────────────────────────────────────

class TestProvider:
    """Deterministic, fully local provider for tests, development, demos, CI.

    It does **not** recognize speech and never claims to. The canonical text is
    supplied by the caller through ``options["transcript_hint"]`` (the same
    contract a deterministic ASR fixture obeys); provenance records
    ``recognized: false`` so the chain stays truthful. Without a hint it returns
    an empty transcript, which the pipeline surfaces as TRANSCRIPT_EMPTY —
    it never invents words.
    """

    name = "test"

    def status(self) -> ProviderInfo:
        return ProviderInfo(
            name=self.name,
            state=ProviderState.AVAILABLE.value,
            reason="deterministic local provider for tests, development and CI",
            model="deterministic-v1",
            config_source="builtin",
            recognized=False,
        )

    def transcribe(self, audio: bytes, options: dict[str, Any]) -> Transcript:
        hint = str(options.get("transcript_hint") or "")
        text = Transcript.normalize(hint)
        return Transcript(
            text=text,
            language=_language(options),
            confidence=None,
            provider=self.name,
            model="deterministic-v1",
            timestamp=utc_now(),
            audio_hash=str(options.get("audio_hash") or ""),
            provenance={
                "recognized": False,
                "mode": "supplied_transcript",
                "audio_bytes": len(audio or b""),
                "note": "TestProvider returns the supplied canonical transcript; "
                        "it performs no speech recognition.",
            },
        )


# ── LocalProvider ────────────────────────────────────────────────────────────

#: Local engines this adapter actually implements. Detection without an
#: implementation would be a fake integration, so the two are kept identical.
_LOCAL_ENGINES = ("faster_whisper", "whisper")


def _detect_local_engine() -> str | None:
    for engine in _LOCAL_ENGINES:
        try:
            if importlib.util.find_spec(engine) is not None:
                return engine
        except Exception:  # pragma: no cover - defensive
            continue
    return None


class LocalProvider:
    """Local speech recognition, only when the runtime actually has an engine.

    No dependency stack is installed by Arkadia Voice: if neither
    ``faster-whisper`` nor openai ``whisper`` is importable, this provider
    reports UNAVAILABLE with an explicit reason instead of pretending.
    """

    name = "local"
    model_name = os.environ.get("ARKADIA_LOCAL_ASR_MODEL", "base")

    def _engine(self) -> str | None:
        return _detect_local_engine()

    def status(self) -> ProviderInfo:
        engine = self._engine()
        if engine is None:
            return ProviderInfo(
                name=self.name,
                state=ProviderState.UNAVAILABLE.value,
                reason="LOCAL_ASR_ENGINE_NOT_INSTALLED (faster-whisper / whisper)",
                model=self.model_name,
                config_source="runtime-probe",
                recognized=False,
            )
        return ProviderInfo(
            name=self.name,
            state=ProviderState.AVAILABLE.value,
            reason=f"local engine available: {engine}",
            model=self.model_name,
            config_source="runtime-probe",
            recognized=True,
        )

    def transcribe(self, audio: bytes, options: dict[str, Any]) -> Transcript:
        engine = self._engine()
        if engine is None:
            raise ASRError(
                "ASR_UNAVAILABLE",
                "LOCAL_ASR_ENGINE_NOT_INSTALLED — no local ASR engine is importable",
            )
        suffix = ".wav"
        mime = str(options.get("mime") or "").lower()
        if "ogg" in mime:
            suffix = ".ogg"
        elif "mpeg" in mime or "mp3" in mime:
            suffix = ".mp3"
        elif "webm" in mime:
            suffix = ".webm"
        path = ""
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as fh:
                fh.write(audio or b"")
                path = fh.name
            if engine == "faster_whisper":
                from faster_whisper import WhisperModel  # type: ignore

                model = WhisperModel(self.model_name)
                segments, info = model.transcribe(path, language=_language(options))
                segments = list(segments)
                text = Transcript.normalize(" ".join(s.text for s in segments))
                confidences = [
                    pow(2.718281828, s.avg_logprob) for s in segments
                    if getattr(s, "avg_logprob", None) is not None
                ]
                confidence = (
                    round(sum(confidences) / len(confidences), 4)
                    if confidences else None
                )
                language = getattr(info, "language", None) or _language(options)
            else:  # openai whisper
                import whisper  # type: ignore

                model = whisper.load_model(self.model_name)
                result = model.transcribe(path, language=_language(options))
                text = Transcript.normalize(str(result.get("text") or ""))
                confidence = None  # whisper exposes no per-utterance confidence
                language = str(result.get("language") or _language(options))
        except ASRError:
            raise
        except Exception as exc:
            logger.warning("[ASR:local] transcription failed: %s", exc)
            raise ASRError("ASR_FAILED", f"local ASR failed: {exc}") from exc
        finally:
            if path:
                try:
                    os.unlink(path)
                except OSError:  # pragma: no cover
                    pass
        return Transcript(
            text=text,
            language=language,
            confidence=confidence,
            provider=self.name,
            model=self.model_name,
            timestamp=utc_now(),
            audio_hash=str(options.get("audio_hash") or ""),
            provenance={
                "recognized": True,
                "engine": engine,
                "model": self.model_name,
                "location": "server-side local engine",
            },
        )


# ── NAtlasProvider ───────────────────────────────────────────────────────────

class NAtlasProvider:
    """Official N-ATLAS integration boundary.

    The endpoint and credentials come exclusively from the environment
    (``NATLAS_TRANSCRIBE_URL``, ``NATLAS_API_KEY``, optional ``NATLAS_MODEL``).
    With official access absent — as it is in this repository today — the
    provider is configured but reports:

        status = UNAVAILABLE
        reason = OFFICIAL_ACCESS_NOT_CONFIGURED

    No N-ATLAS URL, host, or credential is invented anywhere in this file.
    """

    name = "natlas"

    @staticmethod
    def _config() -> tuple[str, str, str]:
        url = os.environ.get(ENV_NATLAS_URL, "").strip()
        key = os.environ.get(ENV_NATLAS_KEY, "").strip()
        model = os.environ.get(ENV_NATLAS_MODEL, "").strip()
        return url, key, model

    def status(self) -> ProviderInfo:
        url, key, model = self._config()
        if not url or not key:
            return ProviderInfo(
                name=self.name,
                state=ProviderState.UNAVAILABLE.value,
                reason="OFFICIAL_ACCESS_NOT_CONFIGURED",
                model=model or "unset",
                config_source=f"env:{ENV_NATLAS_URL},{ENV_NATLAS_KEY}",
                recognized=True,
            )
        return ProviderInfo(
            name=self.name,
            state=ProviderState.AVAILABLE.value,
            reason="official endpoint configured via environment",
            model=model or "official-default",
            config_source=f"env:{ENV_NATLAS_URL},{ENV_NATLAS_KEY}",
            recognized=True,
        )

    def transcribe(self, audio: bytes, options: dict[str, Any]) -> Transcript:
        url, key, model = self._config()
        if not url or not key:
            raise ASRError(
                "ASR_UNAVAILABLE",
                "OFFICIAL_ACCESS_NOT_CONFIGURED — N-ATLAS endpoint/credentials "
                f"absent from {ENV_NATLAS_URL} / {ENV_NATLAS_KEY}",
            )
        mime = str(options.get("mime") or "audio/webm") or "audio/webm"
        try:
            import httpx

            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    url,
                    headers={"Authorization": f"Bearer {key}"},
                    files={"file": ("voice.ogg", audio, mime)},
                    data={
                        "language": _language(options),
                        **({"model": model} if model else {}),
                    },
                )
                response.raise_for_status()
                body = response.json()
        except Exception as exc:
            logger.warning("[ASR:natlas] request failed: %s", exc)
            raise ASRError("ASR_FAILED", f"N-ATLAS transcription failed: {exc}") from exc

        if not isinstance(body, dict):
            raise ASRError("ASR_FAILED", "N-ATLAS returned a non-object response")
        # The official response contract must be confirmed when access exists;
        # until then both conventional keys are accepted and nothing else is assumed.
        text = Transcript.normalize(str(body.get("text") or body.get("transcript") or ""))
        raw_confidence = body.get("confidence")
        try:
            confidence = float(raw_confidence) if raw_confidence is not None else None
        except (TypeError, ValueError):
            confidence = None
        return Transcript(
            text=text,
            language=str(body.get("language") or _language(options)),
            confidence=confidence,
            provider=self.name,
            model=str(body.get("model") or model or "official-default"),
            timestamp=utc_now(),
            audio_hash=str(options.get("audio_hash") or ""),
            provenance={
                "recognized": True,
                "endpoint": "configured-official-endpoint",
                "http_status": 200,
            },
        )


# ── CloudProvider (repository-approved provider family) ──────────────────────

class CloudProvider:
    """Cloud ASR through the provider family this repository already approves.

    ``providers/gemini.py`` is Arkadia's primary LLM provider and resolves its
    key from ``GEMINI_API_KEY`` / ``GOOGLE_API_KEY``. This adapter reuses that
    exact convention (model default ``gemini-2.0-flash``). With no key present
    it reports UNAVAILABLE — the pipeline never depends on it.
    """

    name = "cloud"
    model_name = os.environ.get("ARKADIA_CLOUD_ASR_MODEL", "gemini-2.0-flash")

    @staticmethod
    def _key() -> str | None:
        for env in ENV_GEMINI_KEYS:
            value = os.environ.get(env, "").strip()
            if value:
                return value
        return None

    def status(self) -> ProviderInfo:
        key = self._key()
        spec = importlib.util.find_spec("google.generativeai")
        if spec is None:
            return ProviderInfo(
                name=self.name,
                state=ProviderState.MISCONFIGURED.value,
                reason="google-generativeai is not importable in this runtime",
                model=self.model_name,
                config_source="runtime-probe",
                recognized=True,
            )
        if key is None:
            return ProviderInfo(
                name=self.name,
                state=ProviderState.UNAVAILABLE.value,
                reason=f"API key not configured ({'/'.join(ENV_GEMINI_KEYS)})",
                model=self.model_name,
                config_source=f"env:{'/'.join(ENV_GEMINI_KEYS)}",
                recognized=True,
            )
        return ProviderInfo(
            name=self.name,
            state=ProviderState.AVAILABLE.value,
            reason="configured via the repository's approved Gemini provider family",
            model=self.model_name,
            config_source=f"env:{'/'.join(ENV_GEMINI_KEYS)}",
            recognized=True,
        )

    def transcribe(self, audio: bytes, options: dict[str, Any]) -> Transcript:
        status = self.status()
        if status.state != ProviderState.AVAILABLE.value:
            raise ASRError("ASR_UNAVAILABLE", f"cloud ASR unavailable: {status.reason}")
        import base64

        try:
            import google.generativeai as genai  # type: ignore

            genai.configure(api_key=self._key())
            mime = str(options.get("mime") or "audio/webm") or "audio/webm"
            model = genai.GenerativeModel(self.model_name)
            result = model.generate_content(
                [
                    "Transcribe this audio exactly. Return ONLY the transcript text, "
                    "no commentary, no quotes.",
                    {"mime_type": mime, "data": base64.b64encode(audio).decode()},
                ],
                generation_config={"temperature": 0.0},
            )
            text = Transcript.normalize(getattr(result, "text", "") or "")
        except Exception as exc:
            logger.warning("[ASR:cloud] transcription failed: %s", exc)
            raise ASRError("ASR_FAILED", f"cloud ASR failed: {exc}") from exc
        return Transcript(
            text=text,
            language=_language(options),
            confidence=None,  # the API returns no honest per-utterance confidence
            provider=self.name,
            model=self.model_name,
            timestamp=utc_now(),
            audio_hash=str(options.get("audio_hash") or ""),
            provenance={
                "recognized": True,
                "engine": "gemini-generative",
                "model": self.model_name,
                "location": "server-side cloud call",
            },
        )


# ── Registry + selection ─────────────────────────────────────────────────────

_PROVIDERS: dict[str, ASRProvider] = {
    "test": TestProvider(),
    "local": LocalProvider(),
    "natlas": NAtlasProvider(),
    "cloud": CloudProvider(),
}


def list_providers() -> list[ProviderInfo]:
    """Status of every registered provider (names only — never secrets)."""
    return [_PROVIDERS[name].status() for name in _PROVIDERS]


def get_provider(name: str) -> ASRProvider | None:
    return _PROVIDERS.get((name or "").strip().lower())


def select_provider(requested: str | None = None) -> tuple[ASRProvider, ProviderInfo]:
    """Choose an AVAILABLE provider.

    Explicit selection (argument or ``ARKADIA_VOICE_ASR_PROVIDER``) must succeed
    or fail loudly: an unavailable explicitly-selected provider raises
    ASR_UNAVAILABLE instead of silently substituting another one. Only the
    default priority chain (natlas → cloud → local → test) falls through to the
    next candidate.
    """
    requested = (requested or "").strip().lower()
    env = os.environ.get(ENV_PROVIDER_SELECT, "").strip().lower()

    def _require(name: str) -> tuple[ASRProvider, ProviderInfo]:
        provider = _PROVIDERS.get(name)
        if provider is None:
            raise ASRError("ASR_UNAVAILABLE", f"unknown ASR provider '{name}'")
        info = provider.status()
        if info.state != ProviderState.AVAILABLE.value:
            raise ASRError(
                "ASR_UNAVAILABLE",
                f"requested provider '{name}' is {info.state}: {info.reason}",
            )
        return provider, info

    if requested:
        return _require(requested)
    if env:
        return _require(env)

    statuses: list[ProviderInfo] = []
    for name in DEFAULT_PRIORITY:
        provider = _PROVIDERS.get(name)
        if provider is None:
            continue
        info = provider.status()
        statuses.append(info)
        if info.state == ProviderState.AVAILABLE.value:
            logger.info("[ASR] selected provider=%s state=%s", info.name, info.state)
            return provider, info

    raise ASRError(
        "ASR_UNAVAILABLE",
        "no ASR provider is AVAILABLE: "
        + "; ".join(f"{s.name}={s.state}({s.reason})" for s in statuses),
    )


def provider_status_report() -> dict[str, Any]:
    """GET payload for /solspire/voice/providers — configuration names only."""
    return {
        "providers": [info.to_dict() for info in list_providers()],
        "default_priority": list(DEFAULT_PRIORITY),
        "selection_env": ENV_PROVIDER_SELECT,
        "requested_env": os.environ.get(ENV_PROVIDER_SELECT, "") or None,
    }


__all__ = [
    "ASRProvider",
    "ASRError",
    "ProviderInfo",
    "TestProvider",
    "LocalProvider",
    "NAtlasProvider",
    "CloudProvider",
    "list_providers",
    "get_provider",
    "select_provider",
    "provider_status_report",
    "ENV_NATLAS_URL",
    "ENV_NATLAS_KEY",
    "ENV_NATLAS_MODEL",
    "ENV_PROVIDER_SELECT",
]
