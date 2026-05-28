---
name: Oracle Voice Architecture
description: How TTS playback state is shared across the SPA
---

**Rule:** Three-layer voice system: OracleVoicePlayer (inline per-message) → voiceContext singleton → SonataBar (global persistent footer).

**Why:** User navigates away from Oracle page while audio plays; SonataBar keeps controls accessible. SPA navigation would destroy inline players without the singleton.

**How to apply:**
- `lib/voiceContext.ts` — broadcasts `{text, label, voice}` when playback starts
- `lib/audioManager.ts` — singleton HTMLAudioElement, survives navigation
- `components/SonataBar.tsx` — fixed bottom bar, visible when audio loaded, spring-animates in/out
- `components/OracleVoicePlayer.tsx` — calls `voiceContext.set()` before loading audio; has 6-voice selector
- `App.tsx` — `<SonataBar />` renders inside AppInner (above AnimatePresence)
