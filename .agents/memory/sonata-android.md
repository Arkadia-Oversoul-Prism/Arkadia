---
name: Sonata Android Project
description: Location, structure, and push workflow for the SONATA Android TTS + Knowledge OS app
---

**Rule:** The Android project lives in `sonata-android/` in this workspace. To push to `Arkadia-Oversoul-Prism/sonata`, run `GITHUB_TOKEN=<token> bash sonata-android/push-to-sonata.sh`.

**Why:** The Replit GITHUB_TOKEN doesn't have org-level push access to the SONATA repo, so pushing must be done manually with a token that has the right scope.

**Project package:** `com.arkadia.sonata` | Min SDK 29 | Target SDK 34 | Kotlin + ViewBinding

**Key files (Voice/TTS — original):**
- `AndroidManifest.xml` — PROCESS_TEXT intent, overlay permission, foreground service, KnowledgeActivity
- `ProcessTextActivity.kt` — text-selection menu handler, fires SpeechService + overlay
- `SpeechService.kt` — foreground service, MediaSession notification (pause/resume/stop)
- `FloatingOverlayService.kt` — draggable TYPE_APPLICATION_OVERLAY glass window
- `TtsEngine.kt` — tier-1 Arkadia /api/tts (online neural), tier-2 Android TTS (offline)
- `Prefs.kt` — SharedPreferences typed wrapper; `edgeTtsUrl` is reused as the Knowledge OS base URL
- `.github/workflows/build-apk.yml` — CI builds APK on every push; signs if SIGNING_KEY secret set

**Key files (Knowledge OS — Phase 4):**
- `ArkadiaRepository.kt` — OkHttp client for all Knowledge OS API calls; no new dependencies
- `KnowledgeActivity.kt` — container with BottomNavigationView; 3 tabs: Search / Oracle / Timeline
- `SearchFragment.kt` — semantic/fulltext search via GET /api/knowledge/search/{semantic|fulltext}
- `OracleFragment.kt` — chat UI; sends POST /api/knowledge/providers/send with `messages` list
- `TimelineFragment.kt` — reads GET /api/knowledge/timeline → flat JSONArray (NOT wrapped in "events")
- Layouts: `activity_knowledge.xml`, `fragment_{search,oracle,timeline}.xml`
- Menu: `res/menu/bottom_nav_knowledge.xml`
- Icons: `res/drawable/ic_{search,oracle,timeline}.xml`
- Color selector: `res/color/nav_tint.xml`

**Critical API shape gotchas:**
- `GET /api/knowledge/search/semantic?q=...&top_k=N` → flat JSONArray; fields: note_uuid, title, note_type, content, score (NOT `results` key)
- `GET /api/knowledge/search/fulltext?q=...&limit=N` → flat JSONArray; same fields
- `GET /api/knowledge/timeline?limit=N` → flat JSONArray; fields: id, event_type, created_at, title, summary (NOT wrapped in `{"events": [...]}`, timestamp field is `created_at`)
- `POST /api/knowledge/providers/send` → body: `{messages: [{role, content}], provider, persona, ingest_response}`; response: `{content, provider}`
- `unified_search` (POST /api/knowledge/search) returns dict-of-modes `{semantic: [...], fulltext: [...]}` — NOT a flat list; avoid using it from Android

**Entry point from MainActivity:** `btnKnowledgeOs` OutlinedButton navigates to `KnowledgeActivity`. Shows Snackbar if `edgeTtsUrl` is not set.

**How to apply:** When adding new features to the Android app, edit files in `sonata-android/`, then run the push script. CI auto-builds the APK. The gradle-wrapper.jar is NOT included (binary); user must run `gradle wrapper` or Android Studio will regenerate it.

**Signing:** Set 4 GitHub Secrets (SIGNING_KEY, KEY_ALIAS, KEY_STORE_PASSWORD, KEY_PASSWORD). Without them CI builds unsigned APK (still installable via `adb install`).
