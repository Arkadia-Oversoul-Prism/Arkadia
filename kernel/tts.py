"""
Piper TTS Engine for Arkadia
Offline, high-quality text-to-speech using Piper ONNX models.
"""
import os
import io
import logging
import struct
import threading
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

import numpy as np

logger = logging.getLogger("arkadia.piper_tts")

# ── Model Configuration ───────────────────────────────────────────────────────
# Using en_US/amy medium quality - warm, natural female voice
PIPER_MODEL_URL = "https://github.com/rhasspy/piper-phonemize/releases/download/v1.0.0/en_US/amy/amy-medium.onnx"
PIPER_MODEL_URL_ALT = "https://github.com/rhasspy/piper/raw/master/src/python_api/test_data/amy_medium.onnx"

# Fallback - lighter model
PIPER_LITE_MODEL = "https://github.com/rhasspy/piper-phonemize/releases/download/v1.0.0/en_US/amy/amy-low.onnx"

# Voice configuration
DEFAULT_VOICE = "amy-medium"
AVAILABLE_VOICES = {
    "amy-medium": {
        "onnx": "https://github.com/rhasspy/piper-phonemize/releases/download/v1.2.0/voices/en_US/amy/amy-medium.onnx",
        "config": "https://github.com/rhasspy/piper-phonemize/releases/download/v1.2.0/voices/en_US/amy/amy-medium.onnx.json",
        "description": "Amy - American English, Female, Medium quality",
    },
    "amy-low": {
        "onnx": "https://github.com/rhasspy/piper-phonemize/releases/download/v1.2.0/voices/en_US/amy/amy-low.onnx",
        "config": "https://github.com/rhasspy/piper-phonemize/releases/download/v1.2.0/voices/en_US/amy/amy-low.onnx.json",
        "description": "Amy - American English, Female, Low quality (faster)",
    },
}

# Directory for voice models
VOICE_DIR = Path(__file__).parent.parent / "voices"
VOICE_DIR.mkdir(exist_ok=True)


class PiperTTS:
    """Piper Text-to-Speech engine with lazy loading and caching."""

    _instance: Optional["PiperTTS"] = None
    _lock = threading.Lock()

    def __init__(self):
        self.voice = None
        self.voice_name = None
        self._loading = False
        self._ready = False
        self._executor = ThreadPoolExecutor(max_workers=1)

    @classmethod
    def get_instance(cls) -> "PiperTTS":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _download_model(self, voice_name: str = DEFAULT_VOICE) -> bool:
        """Download Piper voice model if not present."""
        voice_info = AVAILABLE_VOICES.get(voice_name, AVAILABLE_VOICES[DEFAULT_VOICE])
        onnx_path = VOICE_DIR / f"{voice_name}.onnx"
        config_path = VOICE_DIR / f"{voice_name}.onnx.json"

        if onnx_path.exists() and config_path.exists():
            logger.info(f"[PIPER] Voice model already cached: {voice_name}")
            return True

        logger.info(f"[PIPER] Downloading voice model: {voice_name}...")
        try:
            import urllib.request

            # Download ONNX model
            urllib.request.urlretrieve(voice_info["onnx"], onnx_path)
            logger.info(f"[PIPER] Downloaded: {onnx_path.name}")

            # Download config JSON
            urllib.request.urlretrieve(voice_info["config"], config_path)
            logger.info(f"[PIPER] Downloaded: {config_path.name}")

            return True
        except Exception as e:
            logger.error(f"[PIPER] Download failed: {e}")
            return False

    def load_voice(self, voice_name: str = DEFAULT_VOICE) -> bool:
        """Load Piper voice (lazy loading)."""
        if self._loading:
            return False

        if self.voice is not None and self.voice_name == voice_name:
            return True

        self._loading = True
        try:
            # Ensure model is downloaded
            if not self._download_model(voice_name):
                raise RuntimeError("Failed to download voice model")

            onnx_path = VOICE_DIR / f"{voice_name}.onnx"
            config_path = VOICE_DIR / f"{voice_name}.onnx.json"

            if not onnx_path.exists():
                raise FileNotFoundError(f"Model not found: {onnx_path}")

            from piper import PiperVoice, PiperConfig

            # Load voice
            config = PiperConfig.load(str(config_path))
            self.voice = PiperVoice(
                str(onnx_path),
                config=config,
                espeak_data_dir=None,  # Use default
            )
            self.voice_name = voice_name
            self._ready = True
            logger.info(f"[PIPER] Voice loaded successfully: {voice_name}")
            return True

        except Exception as e:
            logger.error(f"[PIPER] Failed to load voice: {e}")
            self._ready = False
            return False
        finally:
            self._loading = False

    def is_ready(self) -> bool:
        """Check if TTS engine is ready."""
        return self._ready and self.voice is not None

    def synthesize(self, text: str, speed: float = 1.0) -> bytes:
        """Synthesize text to WAV audio."""
        if not self.is_ready():
            # Try lazy load
            if not self.load_voice():
                raise RuntimeError("Piper TTS not ready")

        # Clean text
        text = text.strip()[:4500]  # Max length
        if not text:
            raise ValueError("Empty text")

        from piper import SynthesisConfig

        # Adjust rate based on speed (1.0 = normal)
        # Piper uses "length_scale" where lower = faster
        length_scale = 1.0 / speed if speed > 0 else 1.0

        config = SynthesisConfig(
            length_scale=length_scale,
            noise_scale=0.667,
            noise_w=0.8,
        )

        # Synthesize to numpy array
        audio = self.voice.synthesize(text, config)

        # Convert to WAV bytes
        return self._audio_to_wav(audio)

    def _audio_to_wav(self, audio: np.ndarray, sample_rate: int = 22050) -> bytes:
        """Convert numpy audio to WAV format."""
        # Ensure float32
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        # Normalize to valid range
        audio = np.clip(audio, -1.0, 1.0)

        # Convert to 16-bit PCM
        audio_int16 = (audio * 32767).astype(np.int16)

        # Create WAV header
        import wave

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int16.tobytes())

        return buffer.getvalue()

    def synthesize_async(self, text: str, speed: float = 1.0) -> bytes:
        """Synchronous synthesis (for use in async context)."""
        future = self._executor.submit(self.synthesize, text, speed)
        return future.result(timeout=120)


# ── Global singleton ───────────────────────────────────────────────────────────
_piper: Optional[PiperTTS] = None


def get_piper() -> PiperTTS:
    """Get or create Piper TTS singleton."""
    global _piper
    if _piper is None:
        _piper = PiperTTS.get_instance()
    return _piper


def init_piper(voice_name: str = DEFAULT_VOICE) -> bool:
    """Initialize Piper TTS with specified voice."""
    piper = get_piper()
    return piper.load_voice(voice_name)


def warm_up_piper(voice_name: str = DEFAULT_VOICE) -> dict:
    """
    Pre-initialize Piper TTS at startup.
    Downloads voice model and loads the engine for immediate use.
    Returns status dict for logging.
    """
    import urllib.request
    
    piper = get_piper()
    voice_info = AVAILABLE_VOICES.get(voice_name, AVAILABLE_VOICES[DEFAULT_VOICE])
    onnx_path = VOICE_DIR / f"{voice_name}.onnx"
    config_path = VOICE_DIR / f"{voice_name}.onnx.json"
    
    status = {
        "voice": voice_name,
        "model_downloaded": False,
        "engine_ready": False,
        "error": None,
    }
    
    # Download model if needed
    try:
        if not onnx_path.exists():
            logger.info(f"[PIPER] Pre-downloading voice model: {voice_name}...")
            urllib.request.urlretrieve(voice_info["onnx"], onnx_path)
            logger.info(f"[PIPER] Downloaded: {onnx_path.name}")
        else:
            logger.info(f"[PIPER] Model already exists: {onnx_path.name}")
        
        if not config_path.exists():
            urllib.request.urlretrieve(voice_info["config"], config_path)
            logger.info(f"[PIPER] Downloaded: {config_path.name}")
        
        status["model_downloaded"] = True
        
    except Exception as e:
        logger.error(f"[PIPER] Model download failed: {e}")
        status["error"] = str(e)
        return status
    
    # Load the engine
    try:
        success = piper.load_voice(voice_name)
        status["engine_ready"] = success
        if success:
            logger.info(f"[PIPER] Engine ready: {voice_name}")
        else:
            status["error"] = "Failed to load voice"
    except Exception as e:
        logger.error(f"[PIPER] Engine load failed: {e}")
        status["error"] = str(e)
    
    return status