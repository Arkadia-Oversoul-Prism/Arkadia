"""
Arkadia TTS Engine — Edge TTS neural voices (primary) · Piper (local fallback)
Microsoft Neural voices: natural breath, pacing, and emotional range.
No API key required. Completely free.

Cycle 17 addition: SSML emotion layer — intelligent pauses, emphasis on
Arkadia-domain terms, prosody shaping for Oracle delivery quality.
"""
import asyncio
import html
import logging
import re
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

# ── SSML emotion layer ─────────────────────────────────────────────────────────
#
# Terms that receive gentle spoken emphasis when the Oracle utters them.
# These are Arkadia-domain words — their weight deserves a beat.
_EMPHASIS_TERMS: list[str] = [
    "Arkadia", "ARKANA", "Oracle", "Spiral", "Nexus", "Codex",
    "sovereignty", "sovereign", "intelligence", "field",
    "coherence", "resonance", "transmission", "emergence",
    "consciousness", "awakening", "alignment", "living",
    "Grove", "Larder", "Pankshin", "Eden",
]

# Compiled once at import time
_EMPHASIS_RE = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in _EMPHASIS_TERMS) + r")\b",
    re.IGNORECASE,
)

def _build_ssml(text: str, voice_id: str, rate: str) -> str:
    """
    Convert plain text into SSML with:
      • Sentence-level pauses  (period / exclamation / question → 480 ms)
      • Em-dash / ellipsis pauses                               (350 ms)
      • Comma micro-pauses                                      (120 ms)
      • Gentle <emphasis> on Arkadia-domain terms
      • Prosody rate wrapped around everything
    """
    # Escape XML special chars first (we'll un-escape our own tags below)
    safe = html.escape(text, quote=False)

    # Sentence-ending punctuation → longer breath
    safe = re.sub(
        r'([.!?])\s+',
        lambda m: m.group(1) + '<break time="480ms"/> ',
        safe,
    )
    # Ellipsis → contemplative pause
    safe = re.sub(r'\.\.\.',  '<break time="600ms"/>', safe)
    # Em-dash → pause with rhythm
    safe = re.sub(r'\s*—\s*', ' <break time="320ms"/> ', safe)
    # Colon introducing a list or revelation
    safe = re.sub(r':\s+', ':<break time="200ms"/> ', safe)
    # Comma micro-pause
    safe = re.sub(r',\s+', ',<break time="120ms"/> ', safe)

    # Emphasis on key Oracle terms (case-preserving)
    def _emph(m: re.Match) -> str:
        return f'<emphasis level="moderate">{m.group(1)}</emphasis>'
    safe = _EMPHASIS_RE.sub(_emph, safe)

    # Build rate string for prosody
    ssml = (
        f'<speak>'
        f'<voice name="{voice_id}">'
        f'<prosody rate="{rate}" pitch="+0%">'
        f'{safe}'
        f'</prosody>'
        f'</voice>'
        f'</speak>'
    )
    return ssml


# ── Speed → Edge TTS rate string ──────────────────────────────────────────────
def _speed_to_rate(speed: float) -> str:
    """Convert a 0.5–2.0 speed multiplier to Edge TTS '+N%' rate string."""
    pct = int(round((speed - 1.0) * 100))
    return f"+{pct}%" if pct >= 0 else f"{pct}%"


# ── Core synthesis ─────────────────────────────────────────────────────────────
async def _synthesize_edge(ssml: str, voice_id: str, rate: str) -> bytes:
    """Run Edge TTS with SSML and return raw MP3 bytes."""
    import edge_tts
    # Pass SSML directly; Communicate detects the <speak> wrapper
    communicate = edge_tts.Communicate(ssml, voice_id, rate=rate)
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

    Pipeline:
      1. Build SSML with emotion/pause/emphasis layer
      2. Primary: Edge TTS neural voice
      3. Fallback: Piper local TTS (plain text, if edge_tts fails)
    """
    text = text.strip()[:4500]
    if not text:
        raise ValueError("text is empty")

    voice_info = VOICES.get(voice_key, VOICES[DEFAULT_VOICE])
    voice_id   = voice_info["id"]
    rate       = _speed_to_rate(max(0.5, min(2.0, speed)))

    # Build SSML
    ssml = _build_ssml(text, voice_id, rate)

    # ── Primary: Edge TTS ──────────────────────────────────────────────────
    try:
        loop = asyncio.new_event_loop()
        try:
            audio = loop.run_until_complete(
                _synthesize_edge(ssml, voice_id, rate)
            )
        finally:
            loop.close()
        logger.info(
            f"[TTS] Edge TTS SSML: {voice_key} ({voice_id}) "
            f"speed={speed} → {len(audio)} bytes MP3"
        )
        return audio, "audio/mpeg"
    except Exception as e:
        logger.warning(f"[TTS] Edge TTS failed ({e}), trying Piper fallback…")

    # ── Fallback: Piper (plain text, no SSML) ─────────────────────────────
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
    logger.info("[TTS] Edge TTS neural engine active — no warmup needed.")
    return {"engine": "edge_tts", "voice": voice_name, "engine_ready": True}
