# Sonata - Android Text-to-Speech Utility

A minimal, elegant Android utility that appears in the native Android text-selection menu and instantly reads selected text aloud using a natural human voice.

## Features

- **System-wide text selection integration** - Works in Chrome, Twitter, WhatsApp, Telegram, Kindle, PDFs, Notes, Gmail, Discord, Reddit, and any other app with selectable text
- **Natural human-quality TTS** - Uses Piper ONNX-based inference for realistic, warm voices
- **Offline operation** - Works 100% offline after initial voice download
- **Background playback** - Continues playing when app is closed with notification controls
- **Floating player overlay** - Minimal black glass overlay with play/pause/stop controls
- **Customizable settings** - Adjustable speed, pitch, and overlay opacity

## Architecture

- **UI**: Jetpack Compose with Material 3 design
- **Architecture**: MVVM with Clean Architecture layers
- **DI**: Hilt for dependency injection
- **Storage**: DataStore for preferences
- **TTS**: Android TTS engine with Piper ONNX integration

### Project Structure

```
app/src/main/java/com/sonata/app/
├── SonataApplication.kt      # Application class
├── di/                        # Dependency injection modules
├── data/
│   └── local/                 # DataStore preferences
├── domain/
│   └── model/                 # Domain models
├── service/                   # TTS playback service & ProcessText
├── tts/
│   ├── piper/                # Piper ONNX engine
│   └── phonemizer/           # English phonemizer
└── ui/
    ├── theme/                # Compose theme
    ├── screens/              # Main screen & ViewModel
    └── MainActivity.kt       # Main entry point
```

## Building

### Prerequisites

- Android Studio Arctic Fox or newer
- JDK 17+
- Android SDK 34 (API level 34)

### Build Commands

```bash
# Build debug APK
./gradlew assembleDebug

# Build release APK
./gradlew assembleRelease

# Clean and rebuild
./gradlew clean assembleDebug
```

## Installation

1. Build the debug APK using the commands above
2. Transfer the APK to your Android device
3. Enable "Install from unknown sources" in Settings
4. Install the APK
5. Open Sonata and download a voice model
6. Grant notification permissions when prompted
7. Select text in any app and tap "Speak with Sonata"

## Voice Models

The app includes support for:
- English (US) - Female (Amy)
- English (US) - Male (Ryan)
- English (UK) - Male (Alan)
- English (UK) - Female (Sonia)

## Permissions

- `FOREGROUND_SERVICE` - Required for background audio playback
- `FOREGROUND_SERVICE_MEDIA_PLAYBACK` - For media session
- `POST_NOTIFICATIONS` - For playback controls notification
- `INTERNET` - For downloading voice models
- `WAKE_LOCK` - Keep device awake during playback

## License

MIT License

## Product Philosophy

Sonata should feel like "the native voice layer Android should have shipped with."

- Invisible
- Elegant
- Human

Minimal surface area. Maximum usefulness.