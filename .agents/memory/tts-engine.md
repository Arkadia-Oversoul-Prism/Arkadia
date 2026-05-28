---
name: TTS Engine Choice
description: Why Edge TTS replaced Piper for Oracle voice synthesis
---

**Rule:** Use `edge-tts` Python package as the Oracle voice engine. Piper model URLs were broken (404) and voice quality was robotic regardless.

**Why:** `edge-tts` gives Microsoft Neural voices (Aria, Jenny, Sonia, Christopher, George, Ryan) — natural breath, pacing, emotional range. Free, no API key, no model storage. Returns MP3 (audio/mpeg), not WAV. Kokoro/PyTorch too heavy for Replit RAM.

**How to apply:** `kernel/tts.py` has `synthesize(text, voice_key, speed)` returning `(bytes, media_type)`. The `/api/tts` endpoint calls it. Fallback to `kernel/_piper_fallback.py` if edge-tts fails.

**Voices catalogue in `kernel/tts.py` VOICES dict:** aria (default), jenny, sonia, christopher, george, ryan.
