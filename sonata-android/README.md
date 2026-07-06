# Sonata — Arkadia Voice + Knowledge OS

Android 10+ companion app for the Arkadia Intelligence System.  
Voice layer (Sonata) + Knowledge OS client (Prism) in a single APK.

## Features

### Voice (Sonata)
| Feature | Detail |
|---|---|
| **PROCESS_TEXT** | Appears as "Speak with Sonata" in every app's text-selection menu |
| **Floating Overlay** | Draggable black-glass player — play, pause, stop, speed, close |
| **Foreground Service** | Notification with pause/resume/stop — audio continues in background |
| **Two TTS tiers** | Online: Arkadia neural voices (Edge TTS via `/api/tts`) · Offline: Android built-in TTS |
| **Settings** | Voice, speed, pitch, auto-read, backend URL, storage management |
| **Performance** | Cold start < 1 s · Speech start < 2 s · No wakelock abuse |

### Knowledge OS (Phase 4 — Prism Android)
| Feature | Detail |
|---|---|
| **◈ Search** | Semantic + full-text search of the Knowledge Vault (`/api/knowledge/search/*`) |
| **∞ Oracle** | Chat directly with the Knowledge OS — context-aware, auto-ingests responses |
| **◎ Timeline** | Live immutable event log from the backend (`/api/knowledge/timeline`) |
| **ArkadiaRepository** | Single OkHttp client for all Knowledge OS API calls — no extra dependencies |

## Building

### Requirements
- Android Studio Hedgehog (2023.1) or newer
- JDK 17
- Android SDK 34 (API 29 min)

### Debug build
```bash
./gradlew assembleDebug
adb install app/build/outputs/apk/debug/app-debug.apk
```

### Release build (unsigned)
```bash
./gradlew assembleRelease
```

### CI — GitHub Actions

Every push to `main` or `feature/**` triggers `.github/workflows/build-apk.yml`.

**To enable APK signing**, add these GitHub Secrets to the SONATA repo:

| Secret | How to generate |
|---|---|
| `SIGNING_KEY` | `base64 -w 0 your-keystore.jks` |
| `KEY_ALIAS` | Alias used when creating the keystore |
| `KEY_STORE_PASSWORD` | Keystore password |
| `KEY_PASSWORD` | Key password |

Generate a keystore (one-time):
```bash
keytool -genkey -v -keystore sonata-release.jks \
  -alias sonata -keyalg RSA -keysize 2048 -validity 10000 \
  -dname "CN=Sonata, OU=Arkadia, O=Arkadia Intelligence Systems, L=Pankshin, ST=Plateau, C=NG"
```

## Configuration

In the Settings screen, enter your Arkadia backend URL (e.g. `https://arkadia-n26k.onrender.com`) to enable neural voice quality. Leave blank to use offline Android TTS.

## Permissions

| Permission | Why |
|---|---|
| `SYSTEM_ALERT_WINDOW` | Floating overlay |
| `FOREGROUND_SERVICE` | Background playback |
| `POST_NOTIFICATIONS` | Playback notification (Android 13+) |
| `INTERNET` | Neural voice via Arkadia backend (optional) |
