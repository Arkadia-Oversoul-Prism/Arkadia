"""
Arkadia TTS Engine

Priority chain:
  1. ElevenLabs (premium neural — requires ELEVENLABS_API_KEY env var or key manager)
  2. Edge TTS   (Microsoft Neural — free, no key required)
  3. Piper      (local fallback)

Cycle 17 addition: SSML emotion layer — intelligent pauses, emphasis on
Arkadia-domain terms, prosody shaping for Oracle delivery quality.
"""
import asyncio
import logging
import os
import re
from typing import Optional

logger = logging.getLogger("arkadia.tts")

# ── ElevenLabs voice map ───────────────────────────────────────────────────────
# Maps the shared voice keys (used in both frontend and Edge TTS) to ElevenLabs
# voice IDs. These are stable, publicly documented IDs from the pre-made library.
ELEVENLABS_VOICE_MAP: dict[str, str] = {
    "aria":        "21m00Tcm4TlvDq8ikWAM",  # Rachel  — warm, expressive female (Oracle default)
    "jenny":       "EXAVITQu4vr4xnSDxMaL",  # Bella   — soft, clear American female
    "sonia":       "ThT5KcBeYPX3keUQqHPh",  # Dorothy — eloquent British female
    "christopher": "TxGEqnHWrfWFTfGW9XjX",  # Josh    — rich American male
    "george":      "VR6AewLTigWG4xSOukaG",  # Arnold  — authoritative, warm male
    "ryan":        "yoZ06aMxZJJ28mfd3POQ",  # Sam     — casual, approachable male
}

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

# ── ElevenLabs key resolver ───────────────────────────────────────────────────

def _get_elevenlabs_key() -> str:
    """Return the active ElevenLabs API key, or '' if none is configured.

    Resolution order (most-persistent first):
      1. ELEVENLABS_API_KEY environment variable  (set on Render/Vercel — survives deploys)
      2. tts_key_manager JSON store              (added via Settings UI — ephemeral on Render)
    """
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if key:
        return key
    try:
        from api.tts_key_manager import get_active_key
        return get_active_key()
    except Exception:
        pass
    return ""


# ── ElevenLabs synthesis ──────────────────────────────────────────────────────

async def _synthesize_elevenlabs(text: str, voice_key: str, api_key: str) -> bytes:
    """POST to ElevenLabs TTS API and return MP3 bytes.

    Raises:
        RuntimeError("ELEVENLABS_429") on quota / rate-limit
        RuntimeError("ELEVENLABS_401") on bad/expired key
        RuntimeError(...)              on any other failure
    """
    import httpx

    el_voice_id = ELEVENLABS_VOICE_MAP.get(voice_key, ELEVENLABS_VOICE_MAP["aria"])
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{el_voice_id}"

    payload = {
        "text": text[:5000],
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.45,
            "similarity_boost": 0.78,
            "style": 0.10,
            "use_speaker_boost": True,
        },
    }
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload, headers=headers)

    if resp.status_code == 429:
        raise RuntimeError("ELEVENLABS_429")
    if resp.status_code == 401:
        raise RuntimeError("ELEVENLABS_401: invalid or expired API key")
    if not resp.is_success:
        snippet = resp.text[:200] if hasattr(resp, "text") else str(resp.status_code)
        raise RuntimeError(f"ElevenLabs HTTP {resp.status_code}: {snippet}")

    data = resp.content
    if len(data) < 500:
        raise RuntimeError(
            f"ElevenLabs returned suspiciously small payload ({len(data)} bytes) — "
            "likely an error JSON masquerading as audio"
        )
    return data

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
    elevenlabs_key: str = "",
) -> tuple[bytes, str, str]:
    """Synthesize text and return (audio_bytes, media_type, engine_used).

    Priority:
      1. ElevenLabs  — if key available (ELEVENLABS_API_KEY env or key manager)
      2. Edge TTS    — Microsoft Neural, free, no key required
      3. Piper       — local fallback

    The third return value is a short engine label: 'elevenlabs', 'edge_tts', 'piper'.
    """
    text = text.strip()[:5000]
    if not text:
        raise ValueError("text is empty")

    voice_info = VOICES.get(voice_key, VOICES[DEFAULT_VOICE])
    voice_id   = voice_info["id"]
    rate       = _speed_to_rate(max(0.5, min(2.0, speed)))

    plain = _clean_text(text)
    if not plain:
        raise ValueError("text is empty after cleaning")

    # ── 1. ElevenLabs ─────────────────────────────────────────────────────
    el_key = elevenlabs_key or _get_elevenlabs_key()
    if el_key:
        try:
            loop = asyncio.new_event_loop()
            try:
                audio = loop.run_until_complete(
                    _synthesize_elevenlabs(plain, voice_key, el_key)
                )
            finally:
                loop.close()
            logger.info(
                f"[TTS] ElevenLabs ✓ voice={voice_key} chars={len(plain)} → {len(audio)} bytes MP3"
            )
            return audio, "audio/mpeg", "elevenlabs"

        except RuntimeError as e:
            err = str(e)
            if "ELEVENLABS_429" in err:
                # Rotate to next key and retry once
                rotated = ""
                try:
                    from api.tts_key_manager import rotate_key
                    rotated = rotate_key(el_key)
                except Exception:
                    pass
                if rotated and rotated != el_key:
                    try:
                        loop2 = asyncio.new_event_loop()
                        try:
                            audio = loop2.run_until_complete(
                                _synthesize_elevenlabs(plain, voice_key, rotated)
                            )
                        finally:
                            loop2.close()
                        logger.info(f"[TTS] ElevenLabs ✓ (rotated key) → {len(audio)} bytes")
                        return audio, "audio/mpeg", "elevenlabs"
                    except Exception:
                        pass
                logger.warning("[TTS] ElevenLabs quota exhausted — falling back to Edge TTS")
            elif "ELEVENLABS_401" in err:
                logger.warning("[TTS] ElevenLabs key invalid/expired — falling back to Edge TTS")
            else:
                logger.warning(f"[TTS] ElevenLabs failed ({err}) — falling back to Edge TTS")

        except Exception as e:
            logger.warning(f"[TTS] ElevenLabs unexpected error ({e}) — falling back to Edge TTS")
    else:
        logger.debug("[TTS] No ElevenLabs key configured — using Edge TTS directly")

    # ── 2. Edge TTS ───────────────────────────────────────────────────────
    edge_exc: Exception | None = None
    try:
        loop = asyncio.new_event_loop()
        try:
            audio = loop.run_until_complete(_synthesize_edge(plain, voice_id, rate))
        finally:
            loop.close()
        logger.info(
            f"[TTS] Edge TTS ✓ voice={voice_key} ({voice_id}) "
            f"speed={speed} chars={len(plain)} → {len(audio)} bytes MP3"
        )
        return audio, "audio/mpeg", "edge_tts"
    except Exception as e:
        edge_exc = e
        logger.warning(f"[TTS] Edge TTS failed ({e}) — trying Piper fallback…")

    # ── 3. Piper ──────────────────────────────────────────────────────────
    try:
        from kernel._piper_fallback import piper_synthesize
        audio = piper_synthesize(plain, speed)
        logger.info(f"[TTS] Piper ✓ {len(audio)} bytes WAV")
        return audio, "audio/wav", "piper"
    except Exception as e2:
        logger.error(f"[TTS] All TTS engines failed. Edge: {edge_exc}. Piper: {e2}")
        raise RuntimeError(f"All TTS engines failed. Edge: {edge_exc}. Piper: {e2}")


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
