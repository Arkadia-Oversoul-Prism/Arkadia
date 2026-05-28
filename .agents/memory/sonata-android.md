---
name: Sonata Android Project
description: Location, structure, and push workflow for the SONATA Android TTS app
---

**Rule:** The Android project lives in `sonata-android/` in this workspace. To push to `Arkadia-Oversoul-Prism/sonata`, run `GITHUB_TOKEN=<token> bash sonata-android/push-to-sonata.sh`.

**Why:** The Replit GITHUB_TOKEN doesn't have org-level push access to the SONATA repo, so pushing must be done manually with a token that has the right scope.

**Project package:** `com.arkadia.sonata` | Min SDK 29 | Target SDK 34 | Kotlin + ViewBinding

**Key files:**
- `AndroidManifest.xml` — PROCESS_TEXT intent, overlay permission, foreground service
- `ProcessTextActivity.kt` — text-selection menu handler, fires SpeechService + overlay
- `SpeechService.kt` — foreground service, MediaSession notification (pause/resume/stop)
- `FloatingOverlayService.kt` — draggable TYPE_APPLICATION_OVERLAY glass window
- `TtsEngine.kt` — tier-1 Arkadia /api/tts (online neural), tier-2 Android TTS (offline)
- `Prefs.kt` — SharedPreferences typed wrapper
- `.github/workflows/build-apk.yml` — CI builds APK on every push; signs if SIGNING_KEY secret set

**How to apply:** When adding new features to the Android app, edit files in `sonata-android/`, then run the push script. CI auto-builds the APK. The gradle-wrapper.jar is NOT included (binary); user must run `gradle wrapper` or Android Studio will regenerate it.

**Signing:** Set 4 GitHub Secrets (SIGNING_KEY, KEY_ALIAS, KEY_STORE_PASSWORD, KEY_PASSWORD). Without them CI builds unsigned APK (still installable via `adb install`).
