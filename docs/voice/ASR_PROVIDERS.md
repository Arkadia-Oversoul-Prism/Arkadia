# Arkadia Voice — ASR Providers

**Status:** IMPLEMENTED. Provider configuration is env-driven only. No
provider endpoint, key, or model is fabricated anywhere in this repository.

---

## 1. Provider protocol

`solspire/voice_asr.py` defines:

```python
class ASRProvider(Protocol):
    name: str
    def status() -> ProviderInfo        # truthfulness probe (no network calls)
    def transcribe(audio, options) -> Transcript
```

`ProviderInfo = {name, state, reason, model, config_source, recognized}`:

- `state` — `AVAILABLE | UNAVAILABLE | MISCONFIGURED` (truthful, probed).
- `recognized` — whether the provider actually recognizes speech. The test
  provider returns `False`; the UI shows "not a recognizer" accordingly.
- `config_source` — where configuration came from (`env:<NAME>` / `local`),
  never the secret value.
- `reason` — human explanation when not `AVAILABLE`.

Errors raise `ASRError(state, detail)`; `ingest` converts them into persisted
voice events with `error_state` (evidence survives negatives).

---

## 2. The four providers

| Provider | State in this deployment | Configuration (env names only) | Notes |
|---|---|---|---|
| **test** | `AVAILABLE` | none | Deterministic: returns `options["transcript_hint"]` verbatim. `recognized=False`, `confidence=None`. Used by tests, the smoke harness and the console's typed fallback path. |
| **local** | `UNAVAILABLE` (`LOCAL_ASR_ENGINE_NOT_INSTALLED`) unless a faster-whisper/whisper engine is installed | optional local model dir | Probes the engine at status time; transcribes to a temp file when installed. |
| **natlas** | `UNAVAILABLE` (`OFFICIAL_ACCESS_NOT_CONFIGURED`) in this environment | `NATLAS_TRANSCRIBE_URL`, `NATLAS_API_KEY`, `NATLAS_MODEL` | Env-config only. If the URL is absent, the provider reports UNAVAILABLE with the official-access reason; **no default URL, host, or model name is invented**. `rg -i "n-atlas|natlas"` over the pre-implementation repo returned 0 hits — there was no existing integration to reuse. |
| **cloud** | `UNAVAILABLE`/`MISCONFIGURED` when no key is set (this environment has no keys set) | `GEMINI_API_KEY` or `GOOGLE_API_KEY`; model `gemini-2.0-flash` | Gemini-family speech transcription. |

Env keys present in this workspace: **none** (`freebuff-env list` → empty),
so N-ATLAS and cloud correctly report unavailable/misconfigured states. These
are expected, truthful states — not bugs.

---

## 3. Selection rules (`select_provider`)

1. **Explicit request** (form field `provider=` or env `ARKADIA_VOICE_ASR_PROVIDER`):
   the named provider is used **only if it is `AVAILABLE`**; otherwise the
   request fails loudly with `ASR_UNAVAILABLE` (HTTP 503) and the provider's
   reason. **Never silent substitution** — an operator who asked for N-ATLAS
   must not silently receive another engine's transcript.
2. **Default priority**: `natlas → cloud → local → test`. The chain falls
   through unavailable providers and lands on `test`, so a fresh checkout
   still works end-to-end with a deterministic transcript.

`GET /solspire/voice/providers` returns
`{providers: [...], default_priority, selection_env, requested_env}` —
configuration names only; no secret is ever echoed (verified by
`tests/test_voice_asr.py`).

---

## 4. Transcript contract

```python
Transcript = {text, provider, model, confidence, recognized, provenance}
```

- `text` — exact provider output; empty → `TRANSCRIPT_EMPTY` (422) with a
  persisted ERROR stage.
- `provenance` — surfaced in the UI as "Transcript & provenance" alongside
  the event's `audio_hash` (sha256 of the stored bytes), mime, size and
  duration; audio can be replayed from
  `GET /solspire/voice/events/{id}/audio` with header
  `X-Arkadia-Audio-SHA256` for independent comparison.

---

## 5. Enabling a real provider

1. Set the env names listed above in the project's Keys/Environment UI
   (never committed to `.env` in the repository).
2. Re-open `/solspire/voice` → **Providers** panel; the provider must read
   `AVAILABLE` with `config_source = env:<NAME>`.
3. Optionally pin it with `ARKADIA_VOICE_ASR_PROVIDER=<name>`; if the pin
   cannot be honored, ingest returns 503 instead of substituting.

Until then the console truthfully shows `UNAVAILABLE · OFFICIAL_ACCESS_NOT_CONFIGURED`
for N-ATLAS, and the test provider carries the end-to-end chain.
