# Arkadia OS — Android

Native Android shell for the full Arkadia Knowledge Operating System.

Loads the **Prism** React frontend in a full-screen WebView — all Oracle Temple routes,
Knowledge OS APIs, provider adapters, vault, timeline, and graph work exactly as on desktop.
No feature duplication. One codebase, two surfaces.

---

## Architecture

```
Arkadia Android (WebView)
    └── Loads → Prism React frontend  (web/public_prism/)
                    └── Calls → Oracle Temple API  (/api/*)
                                    └── Knowledge OS, Providers, Vault
```

The app is the **surface**. The backend is the **system**.

---

## Features

| Feature | How |
|---|---|
| Full Knowledge OS UI | WebView loads the Prism frontend |
| Oracle · Search · Timeline · Vault | All via existing React components |
| TTS | Exposed to frontend as `window.ArkadiaAndroid.speakText(text)` |
| Process Text | Select text in any app → "Send to Arkadia Oracle" |
| Share from Oracle | `window.ArkadiaAndroid.shareText(text)` |
| Open Settings | `window.ArkadiaAndroid.openSettings()` from JS |
| Backend URL | Configurable in Settings — survives app restarts |

---

## JavaScript Bridge

The `window.ArkadiaAndroid` object is available when running inside the APK:

```javascript
// Detect Android context
if (window.ArkadiaAndroid) {
    // TTS
    window.ArkadiaAndroid.speakText("Knowledge is sovereign.")
    window.ArkadiaAndroid.stopSpeaking()

    // Share
    window.ArkadiaAndroid.shareText("Selected vault entry...")

    // Settings
    window.ArkadiaAndroid.openSettings()

    // Info
    const url     = window.ArkadiaAndroid.getArkadiaUrl()   // configured URL
    const version = window.ArkadiaAndroid.getVersion()       // "1.0.0"
    const info    = window.ArkadiaAndroid.getDeviceInfo()    // JSON string
}
```

### Receiving Process Text (frontend side)

When the user selects text from another app and sends it to Arkadia, the app
dispatches a DOM event. Add this listener in the frontend to receive it:

```typescript
window.addEventListener('arkadia-process-text', (e: Event) => {
    const { text } = (e as CustomEvent).detail
    // Navigate to Oracle and pre-fill text
})
```

---

## Setup

### Requirements
- Android Studio Hedgehog (2023.1) or newer
- JDK 17
- Android SDK 34 (min API 29)

### Build

```bash
# Debug (installable immediately)
./gradlew assembleDebug
adb install app/build/outputs/apk/debug/app-debug.apk

# Release (unsigned)
./gradlew assembleRelease
```

### Configure the app

In the app → Settings:

1. Enter your Arkadia deployment URL: `https://arkadia-xxxx.replit.app`
2. For emulator + local dev: `http://10.0.2.2:5000`
3. Tap **Save** → the WebView reloads

---

## CI — GitHub Actions

Every push builds a debug APK and uploads it as an artifact.
Main branch also builds a release APK (signed if secrets are configured).

| Secret | How to generate |
|---|---|
| `SIGNING_KEY` | `base64 -w 0 your-keystore.jks` |
| `KEY_ALIAS` | Alias used when creating the keystore |
| `KEY_STORE_PASSWORD` | Keystore password |
| `KEY_PASSWORD` | Key password |

---

## Permissions

| Permission | Why |
|---|---|
| `INTERNET` | Load the Arkadia frontend + API calls |
| `POST_NOTIFICATIONS` | Future: Oracle push notifications |
| `VIBRATE` | Haptic feedback via JS bridge |
