"""
Piper TTS local fallback — used only when Edge TTS is unavailable.
"""
import io
import logging
from pathlib import Path

logger = logging.getLogger("arkadia.piper_fallback")

VOICE_DIR = Path(__file__).parent.parent / "voices"
VOICE_DIR.mkdir(exist_ok=True)

_voice = None
_voice_name = None


def piper_synthesize(text: str, speed: float = 1.0) -> bytes:
    """Attempt synthesis via piper-tts. Returns WAV bytes."""
    global _voice, _voice_name

    if _voice is None:
        _load_voice()

    if _voice is None:
        raise RuntimeError("Piper voice not loaded")

    import numpy as np, wave
    from piper import SynthesisConfig

    length_scale = 1.0 / speed if speed > 0 else 1.0
    config = SynthesisConfig(
        length_scale=length_scale,
        noise_scale=0.667,
        noise_w=0.8,
    )
    audio = _voice.synthesize(text, config)

    if audio.dtype != np.float32:
        audio = audio.astype(np.float32)
    audio = np.clip(audio, -1.0, 1.0)
    audio_int16 = (audio * 32767).astype(np.int16)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(22050)
        wf.writeframes(audio_int16.tobytes())
    return buf.getvalue()


def _load_voice():
    global _voice, _voice_name
    onnx = VOICE_DIR / "amy-medium.onnx"
    cfg  = VOICE_DIR / "amy-medium.onnx.json"
    if not onnx.exists() or not cfg.exists():
        logger.info("[PIPER] Voice model not cached, skipping.")
        return
    try:
        from piper import PiperVoice, PiperConfig
        config = PiperConfig.load(str(cfg))
        _voice = PiperVoice(str(onnx), config=config, espeak_data_dir=None)
        _voice_name = "amy-medium"
        logger.info("[PIPER] Fallback voice loaded: amy-medium")
    except Exception as e:
        logger.warning(f"[PIPER] Could not load fallback voice: {e}")
