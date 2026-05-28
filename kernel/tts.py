"""
Arkadia TTS Engine — Edge TTS neural voices (primary) · Piper (local fallback)
Microsoft Neural voices: natural breath, pacing, and emotional range.
No API key required. Completely free.
"""
import asyncio
import io
import logging
import threading
from typing import Optional

logger = logging.getLogger("arkadia.tts")

# ── Voice catalogue ────────────────────────────────────────────────────────────
VOICES: dict[str, dict] = {
    "aria": {
        "id":          "en-US-AriaNeural",
        "name":        "Aria",
        "description": "Warm, expressive — primary Oracle voice",
        "gender":      "female",
        "accent":      "American",
    },
    "jenny": {
        "id":          "en-US-JennyNeural",
        "name":        "Jenny",
        "description": "Natural, clear American female",
        "gender":      "female",
        "accent":      "American",
    },
    "sonia": {
        "id":          "en-GB-SoniaNeural",
        "name":        "Sonia",
        "description": "British female — eloquent, composed",
        "gender":      "female",
        "accent":      "British",
    },
    "christopher": {
        "id":          "en-US-ChristopherNeural",
        "name":        "Christopher",
        "description": "Rich, warm American male",
        "gender":      "male",
        "accent":      "American",
    },
    "george": {
        "id":          "en-GB-GeorgeNeural",
        "name":        "George",
        "description": "British male — authoritative, warm",
        "gender":      "male",
        "accent":      "British",
    },
    "ryan": {
        "id":          "en-US-RyanNeural",
        "name":        "Ryan",
        "description": "Casual, approachable American male",
        "gender":      "male",
        "accent":      "American",
    },
}

DEFAULT_VOICE = "aria"

# Keep for backward compat
AVAILABLE_VOICES = {k: v["description"] for k, v in VOICES.items()}


# ── Speed → Edge TTS rate string ──────────────────────────────────────────────
def _speed_to_rate(speed: float) -> str:
    """Convert a 0.5–2.0 speed multiplier to Edge TTS '+N%' rate string."""
    pct = int(round((speed - 1.0) * 100))
    return f"+{pct}%" if pct >= 0 else f"{pct}%"


# ── Core synthesis ─────────────────────────────────────────────────────────────
async def _synthesize_edge(text: str, voice_id: str, rate: str) -> bytes:
    """Run Edge TTS and return raw MP3 bytes."""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice_id, rate=rate)
    chunks: list[bytes] = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            chunks.append(chunk["data"])
    if not chunks:
        raise RuntimeError("Edge TTS returned no audio data")
    return b"".join(chunks)


def synthesize(
    text: str,
    voice_key: str = DEFAULT_VOICE,
    speed: float = 1.0,
) -> tuple[bytes, str]:
    """
    Synthesize text and return (audio_bytes, media_type).
    Primary: Edge TTS (neural quality).
    Fallback: Piper local TTS (if edge_tts fails).
    """
    text = text.strip()[:4500]
    if not text:
        raise ValueError("text is empty")

    voice_info = VOICES.get(voice_key, VOICES[DEFAULT_VOICE])
    voice_id   = voice_info["id"]
    rate       = _speed_to_rate(max(0.5, min(2.0, speed)))

    # ── Primary: Edge TTS ──────────────────────────────────────────────────────
    try:
        loop = asyncio.new_event_loop()
        try:
            audio = loop.run_until_complete(
                _synthesize_edge(text, voice_id, rate)
            )
        finally:
            loop.close()
        logger.info(
            f"[TTS] Edge TTS: {voice_key} ({voice_id}) "
            f"speed={speed} → {len(audio)} bytes MP3"
        )
        return audio, "audio/mpeg"
    except Exception as e:
        logger.warning(f"[TTS] Edge TTS failed ({e}), trying Piper fallback…")

    # ── Fallback: Piper ────────────────────────────────────────────────────────
    try:
        from kernel._piper_fallback import piper_synthesize
        audio = piper_synthesize(text, speed)
        logger.info(f"[TTS] Piper fallback: {len(audio)} bytes WAV")
        return audio, "audio/wav"
    except Exception as e2:
        logger.error(f"[TTS] Piper fallback also failed: {e2}")
        raise RuntimeError(f"All TTS engines failed. Edge: {e}. Piper: {e2}")


# ── Backward-compat shims (used by main.py) ───────────────────────────────────

class _FakePiper:
    """Thin shim so old main.py startup code doesn't crash."""
    voice_name = None

    def is_ready(self) -> bool:
        return False

    def load_voice(self, _name: str = DEFAULT_VOICE) -> bool:
        return False


_fake_piper = _FakePiper()


def get_piper():
    return _fake_piper


def warm_up_piper(voice_name: str = DEFAULT_VOICE) -> dict:
    """No-op warmup — Edge TTS needs no warmup."""
    logger.info("[TTS] Edge TTS engine active — no warmup needed.")
    return {"engine": "edge_tts", "voice": voice_name, "engine_ready": True}
