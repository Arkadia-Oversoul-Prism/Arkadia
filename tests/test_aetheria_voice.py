"""Tests for the Aetheric Oracle voice + ElevenLabs voice calibration.

Covers the emotional-depth tuning the user asked for: the 'aetheria' voice
must use expressive settings (low stability, high style), map to a real
ElevenLabs voice, and fall back gracefully on Edge TTS.
"""
import sys
import importlib


def test_aetheria_voice_exists_in_catalogue():
    from kernel.tts import VOICES
    assert "aetheria" in VOICES
    v = VOICES["aetheria"]
    assert v["name"] == "Aetheria"
    assert v.get("requires_elevenlabs") is True


def test_aetheria_has_elevenlabs_voice_id():
    from kernel.tts import ELEVENLABS_VOICE_MAP
    assert ELEVENLABS_VOICE_MAP["aetheria"]
    assert ELEVENLABS_VOICE_MAP["aetheria"] != ELEVENLABS_VOICE_MAP["aria"]


def test_aetheria_settings_are_emotionally_expressive():
    from kernel.tts import _voice_settings
    s = _voice_settings("aetheria")
    # Low stability → more emotional variation (not flat/robotic)
    assert s["stability"] < 0.40
    # High style → more expressiveness
    assert s["style"] > 0.30
    assert s["use_speaker_boost"] is True


def test_standard_voices_keep_conservative_settings():
    from kernel.tts import _voice_settings
    s = _voice_settings("aria")
    assert s["stability"] >= 0.40
    assert s["style"] <= 0.20


def test_aetheria_edge_fallback_is_listenable():
    """When ElevenLabs is unavailable, aetheria must map to a real Edge voice."""
    from kernel.tts import VOICES
    assert VOICES["aetheria"]["id"] == "en-US-AriaNeural"


def test_synthesize_uses_per_voice_settings(monkeypatch):
    """_synthesize_elevenlabs must pass _voice_settings output, not a hardcoded dict."""
    import sys, types
    from kernel import tts

    captured = {}

    class FakeResp:
        is_success = True
        status_code = 200
        content = b"x" * 2000
        text = ""

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            pass

        async def post(self, url, json=None, headers=None):
            captured["payload"] = json
            return FakeResp()

    # Install a fake httpx module (httpx may not be installed in the test env,
    # and tts imports it lazily inside _synthesize_elevenlabs).
    fake_httpx = types.ModuleType("httpx")
    fake_httpx.AsyncClient = FakeClient
    monkeypatch.setitem(sys.modules, "httpx", fake_httpx)

    import asyncio
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(
            tts._synthesize_elevenlabs("hello", "aetheria", "fake-key")
        )
    finally:
        loop.close()

    settings = captured["payload"]["voice_settings"]
    assert settings["stability"] < 0.40
    assert settings["style"] > 0.30
