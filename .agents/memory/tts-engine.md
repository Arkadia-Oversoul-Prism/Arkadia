---
name: TTS Engine Choice
description: Why Edge TTS replaced Piper for Oracle voice synthesis
---

**Rule:** Use `edge-tts` Python package as the Oracle voice engine. Piper model URLs were broken (404) and voice quality was robotic regardless.

**Why:** `edge-tts` gives Microsoft Neural voices (Aria, Jenny, Sonia, Christopher, George, Ryan) — natural breath, pacing, emotional range. Free, no API key, no model storage. Returns MP3 (audio/mpeg), not WAV. Kokoro/PyTorch too heavy for Replit RAM.

**How to apply:** `kernel/tts.py` has `synthesize(text, voice_key, speed)` returning `(bytes, media_type)`. The `/api/tts` endpoint calls it. Fallback to `kernel/_piper_fallback.py` if edge-tts fails.

**Voices catalogue in `kernel/tts.py` VOICES dict:** aria (default), jenny, sonia, christopher, george, ryan.

**SSML emotion layer (Cycle 17):** `_build_ssml()` in `kernel/tts.py` wraps every Oracle response in `<speak>/<voice>/<prosody>` with punctuation-driven breaks (480ms sentence, 120ms comma, 600ms ellipsis) and `<emphasis level="moderate">` on Arkadia-domain terms. This increased audio size from ~30KB to ~180KB for typical responses — reflecting the natural breathing and pacing. Always pass SSML, not plain text, to `_synthesize_edge()`.
