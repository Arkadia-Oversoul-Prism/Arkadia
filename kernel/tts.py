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

def _clean_text(text: str) -> str:
    """
    Strip all markdown, HTML, code blocks, and special characters from text
    so Edge TTS receives clean, speakable prose.

    Edge TTS 7.x does NOT accept SSML input — passing XML tags causes them to
    be read aloud literally ("forward slash", "greater than", etc.).
    Always pass plain text; use the rate/pitch parameters on Communicate instead.
    """
    import re as _re

    # Remove fenced code blocks entirely
    text = _re.sub(r'```[\s\S]*?```', ' ', text)
    # Remove inline code — keep the inner text
    text = _re.sub(r'`([^`]+)`', r'\1', text)
    # Remove HTML/XML tags
    text = _re.sub(r'<[^>]+>', ' ', text)
    # Remove markdown images
    text = _re.sub(r'!\[[^\]]*\]\([^)]*\)', ' ', text)
    # Convert markdown links to link text only
    text = _re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)
    # Remove markdown headers (# symbols)
    text = _re.sub(r'^#{1,6}\s+', '', text, flags=_re.MULTILINE)
    # Remove blockquotes
    text = _re.sub(r'^\s*>\s?', '', text, flags=_re.MULTILINE)
    # Remove list markers, keep content
    text = _re.sub(r'^\s*[-*+]\s+', '', text, flags=_re.MULTILINE)
    text = _re.sub(r'^\s*\d+\.\s+', '', text, flags=_re.MULTILINE)
    # Remove bold/italic markers
    text = _re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)
    text = _re.sub(r'(\*|_)(.*?)\1', r'\2', text)
    # Remove table rows / separators
    text = _re.sub(r'\|[^\n]*\|', lambda m: ' '.join(
        c.strip() for c in m.group(0).split('|') if c.strip()
    ), text)
    text = _re.sub(r'^[\s|=\-]+$', '', text, flags=_re.MULTILINE)
    # Remove URLs
    text = _re.sub(r'https?://\S+', ' ', text)
    # Remove JSON/bracket structures (non-nested)
    text = _re.sub(r'\{[^{}]*\}', ' ', text)
    text = _re.sub(r'\[[^\[\]]*\]', ' ', text)
    # Remove math expressions
    text = _re.sub(r'\$\$?[^$]+\$\$?', ' ', text)
    # Remove escape sequences
    text = _re.sub(r'\\[nrt\\*_`#\[\]{}|]', ' ', text)
    # Remove pipe and backslash characters
    text = _re.sub(r'[|\\]', ' ', text)
    # Remove repeated symbol runs (**, --, ==, etc.)
    text = _re.sub(r'[*_~`#>]{2,}', ' ', text)
    # Remove special Unicode decoration
    text = _re.sub(r'[⟐✦◆☥⟁◎⧫⚝•··⋯⋮⸮«»‹›「」『』【】〔〕〘〙〚〛〈〉《》≫◀▶]+', ' ', text)
    # Remove control characters
    text = _re.sub(r'[\x00-\x1F\x7F]', ' ', text)
    # Collapse multiple newlines into sentence breaks
    text = _re.sub(r'\n{3,}', '. ', text)
    text = _re.sub(r'\n{2,}', '. ', text)
    text = _re.sub(r'\n', ' ', text)
    # Collapse whitespace
    text = _re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip()


# ── Speed → Edge TTS rate string ──────────────────────────────────────────────
def _speed_to_rate(speed: float) -> str:
    """Convert a 0.5–2.0 speed multiplier to Edge TTS '+N%' rate string."""
    pct = int(round((speed - 1.0) * 100))
    return f"+{pct}%" if pct >= 0 else f"{pct}%"


# ── Core synthesis ─────────────────────────────────────────────────────────────
async def _synthesize_edge(plain: str, voice_id: str, rate: str) -> bytes:
    """Run Edge TTS with plain text and return raw MP3 bytes.

    Edge TTS 7.x does NOT support SSML input — XML tags are read aloud literally.
    Always pass clean plain text here; prosody is controlled via the rate parameter.
    """
    import edge_tts
    communicate = edge_tts.Communicate(plain, voice_id, rate=rate)
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
      1. Clean markdown/HTML/code from text → plain speakable prose
      2. Primary: Edge TTS neural voice (plain text + rate parameter)
      3. Fallback: Piper local TTS
    """
    text = text.strip()[:4500]
    if not text:
        raise ValueError("text is empty")

    voice_info = VOICES.get(voice_key, VOICES[DEFAULT_VOICE])
    voice_id   = voice_info["id"]
    rate       = _speed_to_rate(max(0.5, min(2.0, speed)))

    # Strip all markdown/HTML/code — Edge TTS reads plain prose only
    plain = _clean_text(text)
    if not plain:
        raise ValueError("text is empty after cleaning")

    # ── Primary: Edge TTS ──────────────────────────────────────────────────
    try:
        loop = asyncio.new_event_loop()
        try:
            audio = loop.run_until_complete(
                _synthesize_edge(plain, voice_id, rate)
            )
        finally:
            loop.close()
        logger.info(
            f"[TTS] Edge TTS: {voice_key} ({voice_id}) "
            f"speed={speed} chars={len(plain)} → {len(audio)} bytes MP3"
        )
        return audio, "audio/mpeg"
    except Exception as e:
        logger.warning(f"[TTS] Edge TTS failed ({e}), trying Piper fallback…")

    # ── Fallback: Piper (plain text) ───────────────────────────────────────
    try:
        from kernel._piper_fallback import piper_synthesize
        audio = piper_synthesize(plain, speed)
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
